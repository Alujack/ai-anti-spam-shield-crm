"""
Domain Intelligence Service

Analyzes domains for phishing indicators:
- Domain age (new domains are suspicious)
- SSL certificate information
- ASN reputation
- DNS configuration
"""

import whois
import ssl
import socket
import dns.resolver
import aiohttp
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class DomainAge:
    """Domain age information"""
    creation_date: Optional[datetime]
    expiration_date: Optional[datetime]
    age_days: int
    is_new: bool  # Less than 30 days old
    registrar: Optional[str]

    def to_dict(self) -> Dict:
        return {
            "creation_date": self.creation_date.isoformat() if self.creation_date else None,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "age_days": self.age_days,
            "is_new": self.is_new,
            "registrar": self.registrar,
        }


@dataclass
class SSLInfo:
    """SSL certificate information"""
    is_valid: bool
    issuer: Optional[str]
    subject: Optional[str]
    not_before: Optional[datetime]
    not_after: Optional[datetime]
    days_until_expiry: int
    is_self_signed: bool
    is_free_cert: bool  # Let's Encrypt, etc.

    def to_dict(self) -> Dict:
        return {
            "is_valid": self.is_valid,
            "issuer": self.issuer,
            "subject": self.subject,
            "not_before": self.not_before.isoformat() if self.not_before else None,
            "not_after": self.not_after.isoformat() if self.not_after else None,
            "days_until_expiry": self.days_until_expiry,
            "is_self_signed": self.is_self_signed,
            "is_free_cert": self.is_free_cert,
        }


@dataclass
class ASNInfo:
    """Autonomous System Number information"""
    asn: Optional[str]
    organization: Optional[str]
    country: Optional[str]
    is_hosting: bool  # Hosted on cloud/VPS
    reputation_score: float  # 0-1

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DNSInfo:
    """DNS records information"""
    has_mx: bool
    has_spf: bool
    has_dmarc: bool
    nameservers: List[str]
    ip_addresses: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DomainIntelResult:
    """Combined domain intelligence result"""
    domain: str
    domain_age: Optional[DomainAge]
    ssl_info: Optional[SSLInfo]
    asn_info: Optional[ASNInfo]
    dns_info: Optional[DNSInfo]
    risk_indicators: List[str]
    risk_score: float

    def to_dict(self) -> Dict:
        return {
            "domain": self.domain,
            "domain_age": self.domain_age.to_dict() if self.domain_age else None,
            "ssl_info": self.ssl_info.to_dict() if self.ssl_info else None,
            "asn_info": self.asn_info.to_dict() if self.asn_info else None,
            "dns_info": self.dns_info.to_dict() if self.dns_info else None,
            "risk_indicators": self.risk_indicators,
            "risk_score": self.risk_score,
        }


class DomainIntelligence:
    """
    Domain Intelligence Analyzer

    Performs comprehensive domain analysis for phishing detection
    """

    # Known malicious ASNs (hosting providers commonly used by phishers)
    SUSPICIOUS_ASNS = {
        "AS14061": "DigitalOcean",  # Often abused
        "AS16276": "OVH",
        "AS24940": "Hetzner",
    }

    # Free SSL providers (not inherently bad, but worth noting)
    FREE_SSL_ISSUERS = [
        "Let's Encrypt",
        "ZeroSSL",
        "Buypass",
        "SSL.com",
    ]

    # Suspicious TLDs
    SUSPICIOUS_TLDS = [
        ".tk", ".ml", ".ga", ".cf", ".gq",  # Free TLDs
        ".xyz", ".top", ".work", ".click",   # Cheap TLDs
        ".loan", ".date", ".racing",
    ]

    def __init__(self, cache_client=None):
        self.cache = cache_client
        self.cache_ttl = 3600 * 24  # 24 hours

    async def analyze(self, url: str) -> DomainIntelResult:
        """
        Perform full domain analysis

        Args:
            url: URL to analyze

        Returns:
            Complete domain intelligence result
        """
        domain = self._extract_domain(url)
        logger.info(f"Analyzing domain: {domain}")

        # Check cache
        if self.cache:
            cached = await self._get_cached(domain)
            if cached:
                logger.info(f"Cache hit for {domain}")
                return cached

        # Run all checks in parallel
        results = await asyncio.gather(
            self._get_domain_age(domain),
            self._get_ssl_info(domain),
            self._get_asn_info(domain),
            self._get_dns_info(domain),
            return_exceptions=True,
        )

        domain_age = results[0] if not isinstance(results[0], Exception) else None
        ssl_info = results[1] if not isinstance(results[1], Exception) else None
        asn_info = results[2] if not isinstance(results[2], Exception) else None
        dns_info = results[3] if not isinstance(results[3], Exception) else None

        # Calculate risk indicators and score
        risk_indicators, risk_score = self._calculate_risk(
            domain, domain_age, ssl_info, asn_info, dns_info
        )

        result = DomainIntelResult(
            domain=domain,
            domain_age=domain_age,
            ssl_info=ssl_info,
            asn_info=asn_info,
            dns_info=dns_info,
            risk_indicators=risk_indicators,
            risk_score=risk_score,
        )

        # Cache result
        if self.cache:
            await self._cache_result(domain, result)

        return result

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        parsed = urlparse(url)
        return parsed.netloc.lower()

    async def _get_domain_age(self, domain: str) -> Optional[DomainAge]:
        """Get domain age via WHOIS lookup"""
        try:
            loop = asyncio.get_event_loop()
            w = await loop.run_in_executor(None, whois.whois, domain)

            creation_date = w.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]

            expiration_date = w.expiration_date
            if isinstance(expiration_date, list):
                expiration_date = expiration_date[0]

            age_days = 0
            is_new = True
            if creation_date:
                age_days = (datetime.now() - creation_date).days
                is_new = age_days < 30

            return DomainAge(
                creation_date=creation_date,
                expiration_date=expiration_date,
                age_days=age_days,
                is_new=is_new,
                registrar=w.registrar,
            )
        except Exception as e:
            logger.warning(f"WHOIS lookup failed for {domain}: {e}")
            return None

    async def _get_ssl_info(self, domain: str) -> Optional[SSLInfo]:
        """Get SSL certificate information"""
        try:
            context = ssl.create_default_context()
            loop = asyncio.get_event_loop()

            def get_cert():
                with socket.create_connection((domain, 443), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        return ssock.getpeercert()

            cert = await loop.run_in_executor(None, get_cert)

            # Parse dates
            not_before = datetime.strptime(
                cert['notBefore'], '%b %d %H:%M:%S %Y %Z'
            )
            not_after = datetime.strptime(
                cert['notAfter'], '%b %d %H:%M:%S %Y %Z'
            )

            # Get issuer
            issuer = dict(x[0] for x in cert['issuer'])
            issuer_name = issuer.get('organizationName', 'Unknown')

            # Get subject
            subject = dict(x[0] for x in cert['subject'])
            subject_name = subject.get('commonName', domain)

            # Check if self-signed
            is_self_signed = issuer_name == subject_name

            # Check if free certificate
            is_free_cert = any(
                free in issuer_name for free in self.FREE_SSL_ISSUERS
            )

            return SSLInfo(
                is_valid=True,
                issuer=issuer_name,
                subject=subject_name,
                not_before=not_before,
                not_after=not_after,
                days_until_expiry=(not_after - datetime.now()).days,
                is_self_signed=is_self_signed,
                is_free_cert=is_free_cert,
            )
        except Exception as e:
            logger.warning(f"SSL check failed for {domain}: {e}")
            return SSLInfo(
                is_valid=False,
                issuer=None,
                subject=None,
                not_before=None,
                not_after=None,
                days_until_expiry=0,
                is_self_signed=False,
                is_free_cert=False,
            )

    async def _get_asn_info(self, domain: str) -> Optional[ASNInfo]:
        """Get ASN information for the domain's IP"""
        try:
            # Resolve domain to IP
            loop = asyncio.get_event_loop()
            ip = await loop.run_in_executor(
                None, socket.gethostbyname, domain
            )

            # Query IP info API (free tier available)
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://ipapi.co/{ip}/json/",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        asn = data.get('asn')
                        org = data.get('org', '')

                        # Check if it's a hosting provider
                        is_hosting = any(
                            keyword in org.lower()
                            for keyword in [
                                'hosting', 'cloud', 'vps', 'digital',
                                'amazon', 'google', 'microsoft', 'linode'
                            ]
                        )

                        # Basic reputation (can be enhanced with threat intel)
                        reputation = 0.5
                        if asn in self.SUSPICIOUS_ASNS:
                            reputation = 0.3

                        return ASNInfo(
                            asn=asn,
                            organization=org,
                            country=data.get('country_code'),
                            is_hosting=is_hosting,
                            reputation_score=reputation,
                        )
        except Exception as e:
            logger.warning(f"ASN lookup failed for {domain}: {e}")
            return None

    async def _get_dns_info(self, domain: str) -> Optional[DNSInfo]:
        """Get DNS records for the domain"""
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 5
            resolver.lifetime = 5

            # Check various record types
            loop = asyncio.get_event_loop()

            async def resolve(rtype):
                try:
                    answers = await loop.run_in_executor(
                        None, resolver.resolve, domain, rtype
                    )
                    return [str(r) for r in answers]
                except Exception:
                    return []

            results = await asyncio.gather(
                resolve('A'),
                resolve('MX'),
                resolve('TXT'),
                resolve('NS'),
                return_exceptions=True,
            )

            a_records = results[0] if isinstance(results[0], list) else []
            mx_records = results[1] if isinstance(results[1], list) else []
            txt_records = results[2] if isinstance(results[2], list) else []
            ns_records = results[3] if isinstance(results[3], list) else []

            # Check for SPF and DMARC in TXT records
            has_spf = any('v=spf1' in txt.lower() for txt in txt_records)
            has_dmarc = any('v=dmarc1' in txt.lower() for txt in txt_records)

            return DNSInfo(
                has_mx=len(mx_records) > 0,
                has_spf=has_spf,
                has_dmarc=has_dmarc,
                nameservers=ns_records,
                ip_addresses=a_records,
            )
        except Exception as e:
            logger.warning(f"DNS lookup failed for {domain}: {e}")
            return None

    def _calculate_risk(
        self,
        domain: str,
        domain_age: Optional[DomainAge],
        ssl_info: Optional[SSLInfo],
        asn_info: Optional[ASNInfo],
        dns_info: Optional[DNSInfo],
    ) -> Tuple[List[str], float]:
        """Calculate risk score based on all indicators"""
        indicators = []
        score = 0

        # Check TLD
        for tld in self.SUSPICIOUS_TLDS:
            if domain.endswith(tld):
                indicators.append(f"Suspicious TLD: {tld}")
                score += 15
                break

        # Domain age checks
        if domain_age:
            if domain_age.is_new:
                indicators.append(f"Domain is only {domain_age.age_days} days old")
                score += 20
            elif domain_age.age_days < 90:
                indicators.append(f"Domain is relatively new ({domain_age.age_days} days)")
                score += 10

        # SSL checks
        if ssl_info:
            if not ssl_info.is_valid:
                indicators.append("Invalid or missing SSL certificate")
                score += 25
            elif ssl_info.is_self_signed:
                indicators.append("Self-signed SSL certificate")
                score += 20
            elif ssl_info.is_free_cert and domain_age and domain_age.is_new:
                indicators.append("Free SSL on new domain")
                score += 10

        # ASN checks
        if asn_info:
            if asn_info.asn in self.SUSPICIOUS_ASNS:
                indicators.append(f"Hosted on frequently abused provider: {asn_info.organization}")
                score += 10
            if asn_info.is_hosting:
                # Not inherently bad, but worth noting
                score += 5

        # DNS checks
        if dns_info:
            if not dns_info.has_mx and not dns_info.has_spf:
                indicators.append("No email configuration (MX/SPF records)")
                score += 10

        # Normalize score to 0-100
        score = min(100, score)

        return indicators, score

    async def _get_cached(self, domain: str) -> Optional[DomainIntelResult]:
        """Get cached result"""
        try:
            cached = await self.cache.get(f"domain_intel:{domain}")
            if cached:
                return DomainIntelResult(**json.loads(cached))
        except Exception:
            pass
        return None

    async def _cache_result(self, domain: str, result: DomainIntelResult):
        """Cache result"""
        try:
            await self.cache.setex(
                f"domain_intel:{domain}",
                self.cache_ttl,
                json.dumps(result.to_dict()),
            )
        except Exception as e:
            logger.warning(f"Failed to cache domain intel: {e}")
