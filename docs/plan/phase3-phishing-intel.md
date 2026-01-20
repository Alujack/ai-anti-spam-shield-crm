# Phase 3: Phishing Intelligence Engine

> **Duration:** 1 Week
> **Priority:** High
> **Dependencies:** Phase 1 (Infrastructure)

---

## Overview

Build a comprehensive phishing detection engine that goes beyond text analysis by incorporating domain intelligence, SSL analysis, ASN reputation, and visual analysis.

### Goals

1. Add domain intelligence (WHOIS, domain age, DNS)
2. Implement SSL certificate analysis
3. Add ASN and IP reputation checks
4. Create screenshot analysis for visual phishing detection
5. Build combined risk scoring system

### Deliverables

- [ ] Domain intelligence service
- [ ] SSL analyzer
- [ ] Screenshot analyzer with headless browser
- [ ] Risk scoring engine
- [ ] `/analyze-url-deep` endpoint

---

## 1. Architecture

### 1.1 Intelligence Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    PHISHING INTELLIGENCE ENGINE                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Input URL ──────────────────────────────────────────────────>   │
│       │                                                           │
│       ├──> Text Analysis (40%)                                   │
│       │    └── Transformer model (Phase 2)                       │
│       │                                                           │
│       ├──> URL Features (25%)                                    │
│       │    ├── Suspicious patterns                               │
│       │    ├── URL length                                        │
│       │    └── Encoded characters                                │
│       │                                                           │
│       ├──> Domain Intelligence (20%)                             │
│       │    ├── Domain age (WHOIS)                                │
│       │    ├── SSL certificate age                               │
│       │    ├── ASN reputation                                    │
│       │    └── DNS records (MX, SPF)                             │
│       │                                                           │
│       └──> Visual Analysis (15%)                                 │
│            ├── Screenshot capture                                 │
│            ├── Brand logo detection                              │
│            └── Login form detection                              │
│                                                                   │
│       ═══════════════════════════════════════════                │
│                           │                                       │
│                           ▼                                       │
│                   RISK SCORE (0-100)                             │
│                   ├── NONE (0-20)                                │
│                   ├── LOW (21-40)                                │
│                   ├── MEDIUM (41-60)                             │
│                   ├── HIGH (61-80)                               │
│                   └── CRITICAL (81-100)                          │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Domain Intelligence

### 2.1 Domain Intel Service

**Create:** `/ai-anti-spam-shield-service-model/app/intel/domain_intel.py`

```python
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
                except:
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
        except:
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
```

---

## 3. Screenshot Analyzer

### 3.1 Visual Analysis Service

**Create:** `/ai-anti-spam-shield-service-model/app/intel/screenshot_analyzer.py`

```python
"""
Screenshot Analyzer for Visual Phishing Detection

Uses headless browser to capture screenshots and
analyzes them for phishing indicators:
- Brand logo detection
- Login form detection
- Visual similarity to known brands
"""

import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from PIL import Image
import io
import base64
from dataclasses import dataclass
from typing import Optional, List, Dict
import logging
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class VisualAnalysisResult:
    """Visual analysis result"""
    screenshot_taken: bool
    screenshot_base64: Optional[str]
    page_title: Optional[str]
    has_login_form: bool
    has_password_field: bool
    brand_indicators: List[str]
    visual_risk_score: float
    error: Optional[str]

    def to_dict(self) -> Dict:
        return {
            "screenshot_taken": self.screenshot_taken,
            "screenshot_base64": self.screenshot_base64,
            "page_title": self.page_title,
            "has_login_form": self.has_login_form,
            "has_password_field": self.has_password_field,
            "brand_indicators": self.brand_indicators,
            "visual_risk_score": self.visual_risk_score,
            "error": self.error,
        }


class ScreenshotAnalyzer:
    """
    Captures and analyzes website screenshots for phishing detection

    Features:
    - Headless browser capture
    - Login form detection
    - Brand impersonation detection
    - Visual hashing for similarity search
    """

    # Brand keywords to detect
    BRAND_KEYWORDS = {
        "paypal": ["paypal", "pay pal"],
        "amazon": ["amazon", "prime"],
        "apple": ["apple", "icloud", "itunes"],
        "microsoft": ["microsoft", "outlook", "office", "onedrive"],
        "google": ["google", "gmail", "youtube"],
        "facebook": ["facebook", "meta", "instagram"],
        "netflix": ["netflix"],
        "bank": ["bank", "banking", "account", "secure"],
        "dropbox": ["dropbox"],
        "linkedin": ["linkedin"],
    }

    def __init__(self, timeout: int = 10000):
        self.timeout = timeout
        self._playwright = None
        self._browser = None

    async def initialize(self):
        """Initialize playwright browser"""
        if self._browser:
            return

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ]
        )
        logger.info("Screenshot analyzer initialized")

    async def close(self):
        """Close browser"""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def analyze(self, url: str, capture_screenshot: bool = True) -> VisualAnalysisResult:
        """
        Analyze a URL for visual phishing indicators

        Args:
            url: URL to analyze
            capture_screenshot: Whether to capture and return screenshot

        Returns:
            Visual analysis result
        """
        await self.initialize()

        try:
            # Create new context with realistic settings
            context = await self._browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            )

            page = await context.new_page()

            # Navigate to URL
            try:
                await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            except PlaywrightTimeout:
                logger.warning(f"Timeout loading {url}")
                return VisualAnalysisResult(
                    screenshot_taken=False,
                    screenshot_base64=None,
                    page_title=None,
                    has_login_form=False,
                    has_password_field=False,
                    brand_indicators=[],
                    visual_risk_score=0,
                    error="Page load timeout",
                )

            # Get page title
            page_title = await page.title()

            # Check for login form indicators
            has_login_form = await self._detect_login_form(page)
            has_password_field = await self._detect_password_field(page)

            # Detect brand indicators
            page_content = await page.content()
            brand_indicators = self._detect_brands(page_content.lower(), page_title.lower())

            # Capture screenshot
            screenshot_base64 = None
            if capture_screenshot:
                screenshot_bytes = await page.screenshot(type='png')
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode()

            # Calculate visual risk score
            visual_risk_score = self._calculate_visual_risk(
                has_login_form,
                has_password_field,
                brand_indicators,
            )

            await context.close()

            return VisualAnalysisResult(
                screenshot_taken=capture_screenshot,
                screenshot_base64=screenshot_base64,
                page_title=page_title,
                has_login_form=has_login_form,
                has_password_field=has_password_field,
                brand_indicators=brand_indicators,
                visual_risk_score=visual_risk_score,
                error=None,
            )

        except Exception as e:
            logger.error(f"Screenshot analysis failed for {url}: {e}")
            return VisualAnalysisResult(
                screenshot_taken=False,
                screenshot_base64=None,
                page_title=None,
                has_login_form=False,
                has_password_field=False,
                brand_indicators=[],
                visual_risk_score=0,
                error=str(e),
            )

    async def _detect_login_form(self, page) -> bool:
        """Detect if page has a login form"""
        login_selectors = [
            'form[action*="login"]',
            'form[action*="signin"]',
            'form[action*="auth"]',
            'input[name="username"]',
            'input[name="email"][type="email"]',
            'input[name="user"]',
            'button[type="submit"]:has-text("Sign in")',
            'button[type="submit"]:has-text("Log in")',
        ]

        for selector in login_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    return True
            except:
                pass

        return False

    async def _detect_password_field(self, page) -> bool:
        """Detect if page has a password field"""
        try:
            password_field = await page.query_selector('input[type="password"]')
            return password_field is not None
        except:
            return False

    def _detect_brands(self, content: str, title: str) -> List[str]:
        """Detect brand mentions in page content"""
        detected = []

        combined = content + " " + title

        for brand, keywords in self.BRAND_KEYWORDS.items():
            for keyword in keywords:
                if keyword in combined:
                    if brand not in detected:
                        detected.append(brand)
                    break

        return detected

    def _calculate_visual_risk(
        self,
        has_login_form: bool,
        has_password_field: bool,
        brand_indicators: List[str],
    ) -> float:
        """Calculate visual risk score"""
        score = 0

        # Login form is suspicious if combined with brand indicators
        if has_login_form:
            score += 20

        if has_password_field:
            score += 20

        # Brand indicators increase suspicion
        if brand_indicators:
            score += 15 * min(len(brand_indicators), 3)

        # Combination is especially suspicious
        if has_login_form and has_password_field and brand_indicators:
            score += 20

        return min(100, score)


# Singleton instance
_analyzer = None


async def get_analyzer() -> ScreenshotAnalyzer:
    """Get or create analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = ScreenshotAnalyzer()
        await _analyzer.initialize()
    return _analyzer
```

---

## 4. Risk Scorer

### 4.1 Combined Risk Scoring

**Create:** `/ai-anti-spam-shield-service-model/app/intel/risk_scorer.py`

```python
"""
Combined Risk Scorer for Phishing Detection

Combines all analysis components:
- Text analysis (40%)
- URL features (25%)
- Domain intelligence (20%)
- Visual analysis (15%)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RiskScore:
    """Combined risk assessment"""
    total_score: float
    threat_level: ThreatLevel
    text_score: float
    url_score: float
    domain_score: float
    visual_score: float
    indicators: List[Dict]
    recommendation: str
    confidence: float

    def to_dict(self) -> Dict:
        return {
            "total_score": round(self.total_score, 2),
            "threat_level": self.threat_level.value,
            "text_score": round(self.text_score, 2),
            "url_score": round(self.url_score, 2),
            "domain_score": round(self.domain_score, 2),
            "visual_score": round(self.visual_score, 2),
            "indicators": self.indicators,
            "recommendation": self.recommendation,
            "confidence": round(self.confidence, 2),
        }


class PhishingRiskScorer:
    """
    Combined risk scoring for phishing detection

    Weights:
    - Text analysis: 40%
    - URL features: 25%
    - Domain intelligence: 20%
    - Visual analysis: 15%
    """

    # Suspicious URL patterns
    URL_PATTERNS = {
        'ip_address': (r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', 25),
        'long_url': (r'.{100,}', 10),
        'many_subdomains': (r'([a-z0-9-]+\.){4,}', 15),
        'suspicious_keywords': (r'(login|signin|verify|secure|account|update|confirm)', 10),
        'encoded_chars': (r'%[0-9a-fA-F]{2}', 5),
        'at_symbol': (r'@', 20),
        'double_slash': (r'https?://[^/]*//+', 15),
        'suspicious_tld': (r'\.(tk|ml|ga|cf|gq|xyz|top|work|click)$', 15),
    }

    # Recommendations based on threat level
    RECOMMENDATIONS = {
        ThreatLevel.NONE: "This appears to be safe. No phishing indicators detected.",
        ThreatLevel.LOW: "Low risk detected. Proceed with normal caution.",
        ThreatLevel.MEDIUM: "Some suspicious indicators found. Verify the source before proceeding.",
        ThreatLevel.HIGH: "High risk of phishing. Do not enter any personal information.",
        ThreatLevel.CRITICAL: "DANGER: This is very likely a phishing attempt. Do not interact with this site.",
    }

    def __init__(
        self,
        text_weight: float = 0.40,
        url_weight: float = 0.25,
        domain_weight: float = 0.20,
        visual_weight: float = 0.15,
    ):
        self.text_weight = text_weight
        self.url_weight = url_weight
        self.domain_weight = domain_weight
        self.visual_weight = visual_weight

    def calculate_risk(
        self,
        url: str,
        text_result: Optional[Dict] = None,
        domain_intel: Optional[Dict] = None,
        visual_result: Optional[Dict] = None,
    ) -> RiskScore:
        """
        Calculate combined phishing risk score

        Args:
            url: The URL being analyzed
            text_result: Result from text/ML analysis
            domain_intel: Result from domain intelligence
            visual_result: Result from screenshot analysis

        Returns:
            Combined risk score
        """
        indicators = []

        # Calculate text score (from ML model)
        text_score = 0
        if text_result:
            text_score = text_result.get('confidence', 0) * 100
            if text_result.get('is_phishing') or text_result.get('is_spam'):
                indicators.append({
                    'source': 'text_analysis',
                    'description': 'ML model detected phishing patterns',
                    'severity': 'high',
                    'score': text_score,
                })

        # Calculate URL score
        url_score, url_indicators = self._analyze_url(url)
        indicators.extend(url_indicators)

        # Calculate domain score
        domain_score = 0
        if domain_intel:
            domain_score = domain_intel.get('risk_score', 0)
            for indicator in domain_intel.get('risk_indicators', []):
                indicators.append({
                    'source': 'domain_intelligence',
                    'description': indicator,
                    'severity': 'medium',
                    'score': domain_score / len(domain_intel.get('risk_indicators', [1])),
                })

        # Calculate visual score
        visual_score = 0
        if visual_result:
            visual_score = visual_result.get('visual_risk_score', 0)
            if visual_result.get('has_login_form'):
                indicators.append({
                    'source': 'visual_analysis',
                    'description': 'Login form detected',
                    'severity': 'medium',
                    'score': 20,
                })
            if visual_result.get('brand_indicators'):
                brands = ', '.join(visual_result['brand_indicators'])
                indicators.append({
                    'source': 'visual_analysis',
                    'description': f'Brand impersonation detected: {brands}',
                    'severity': 'high',
                    'score': 30,
                })

        # Calculate weighted total
        total_score = (
            text_score * self.text_weight +
            url_score * self.url_weight +
            domain_score * self.domain_weight +
            visual_score * self.visual_weight
        )

        # Boost score if multiple high-severity indicators
        high_severity_count = sum(1 for i in indicators if i.get('severity') == 'high')
        if high_severity_count >= 2:
            total_score = min(100, total_score * 1.3)

        # Determine threat level
        threat_level = self._get_threat_level(total_score)

        # Calculate confidence based on data completeness
        confidence = self._calculate_confidence(
            text_result is not None,
            domain_intel is not None,
            visual_result is not None,
        )

        return RiskScore(
            total_score=total_score,
            threat_level=threat_level,
            text_score=text_score,
            url_score=url_score,
            domain_score=domain_score,
            visual_score=visual_score,
            indicators=indicators,
            recommendation=self.RECOMMENDATIONS[threat_level],
            confidence=confidence,
        )

    def _analyze_url(self, url: str) -> tuple:
        """Analyze URL for phishing patterns"""
        score = 0
        indicators = []

        url_lower = url.lower()

        for pattern_name, (pattern, points) in self.URL_PATTERNS.items():
            if re.search(pattern, url_lower):
                score += points
                indicators.append({
                    'source': 'url_analysis',
                    'description': f'Suspicious URL pattern: {pattern_name}',
                    'severity': 'medium' if points < 15 else 'high',
                    'score': points,
                })

        return min(100, score), indicators

    def _get_threat_level(self, score: float) -> ThreatLevel:
        """Map score to threat level"""
        if score < 20:
            return ThreatLevel.NONE
        elif score < 40:
            return ThreatLevel.LOW
        elif score < 60:
            return ThreatLevel.MEDIUM
        elif score < 80:
            return ThreatLevel.HIGH
        else:
            return ThreatLevel.CRITICAL

    def _calculate_confidence(
        self,
        has_text: bool,
        has_domain: bool,
        has_visual: bool,
    ) -> float:
        """Calculate confidence based on available data"""
        base_confidence = 0.5  # URL analysis always available

        if has_text:
            base_confidence += 0.25
        if has_domain:
            base_confidence += 0.15
        if has_visual:
            base_confidence += 0.10

        return base_confidence


# Usage example
def analyze_phishing_risk(
    url: str,
    text_confidence: float = 0,
    domain_age_days: int = 365,
    has_valid_ssl: bool = True,
) -> Dict:
    """Quick phishing risk analysis"""
    scorer = PhishingRiskScorer()

    # Simulate component results
    text_result = {
        'is_phishing': text_confidence > 0.5,
        'confidence': text_confidence,
    }

    domain_intel = {
        'risk_score': max(0, 50 - domain_age_days / 10),
        'risk_indicators': [],
    }
    if domain_age_days < 30:
        domain_intel['risk_indicators'].append('Domain is less than 30 days old')

    if not has_valid_ssl:
        domain_intel['risk_score'] += 25
        domain_intel['risk_indicators'].append('Invalid SSL certificate')

    result = scorer.calculate_risk(
        url=url,
        text_result=text_result,
        domain_intel=domain_intel,
    )

    return result.to_dict()
```

---

## 5. FastAPI Integration

### 5.1 New Endpoints

**Add to:** `/ai-anti-spam-shield-service-model/app/main.py`

```python
from app.intel.domain_intel import DomainIntelligence
from app.intel.screenshot_analyzer import get_analyzer
from app.intel.risk_scorer import PhishingRiskScorer

# Initialize services
domain_intel = DomainIntelligence()
risk_scorer = PhishingRiskScorer()


class DeepURLRequest(BaseModel):
    url: str
    include_screenshot: bool = False
    include_domain_intel: bool = True


@app.post("/analyze-url-deep")
async def analyze_url_deep(request: DeepURLRequest):
    """
    Deep URL analysis with domain intelligence and visual analysis

    Returns comprehensive phishing risk assessment including:
    - Domain age and registration info
    - SSL certificate analysis
    - ASN reputation
    - Visual analysis (optional)
    - Combined risk score
    """
    try:
        results = {}

        # Text/ML analysis (using existing predictor)
        text_result = None
        if v2_available:
            text_result = multi_predictor_v2.predict_phishing(request.url)
        else:
            text_result = {"confidence": 0, "is_phishing": False}

        results["text_analysis"] = text_result

        # Domain intelligence
        domain_result = None
        if request.include_domain_intel:
            domain_result = await domain_intel.analyze(request.url)
            results["domain_intelligence"] = domain_result.to_dict()

        # Visual analysis
        visual_result = None
        if request.include_screenshot:
            analyzer = await get_analyzer()
            visual_result = await analyzer.analyze(request.url)
            results["visual_analysis"] = visual_result.to_dict()

        # Combined risk score
        risk_result = risk_scorer.calculate_risk(
            url=request.url,
            text_result=text_result if isinstance(text_result, dict) else text_result.to_dict() if hasattr(text_result, 'to_dict') else None,
            domain_intel=domain_result.to_dict() if domain_result else None,
            visual_result=visual_result.to_dict() if visual_result else None,
        )

        results["risk_assessment"] = risk_result.to_dict()

        return {
            "url": request.url,
            "is_phishing": risk_result.threat_level.value in ["HIGH", "CRITICAL"],
            "threat_level": risk_result.threat_level.value,
            "confidence": risk_result.confidence,
            "risk_score": risk_result.total_score,
            "recommendation": risk_result.recommendation,
            "details": results,
        }

    except Exception as e:
        logger.error(f"Deep URL analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/intel/domain/{domain}")
async def get_domain_intel(domain: str):
    """
    Get domain intelligence for a specific domain
    """
    try:
        result = await domain_intel.analyze(f"https://{domain}")
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 6. Dependencies

### 6.1 Update requirements.txt

**Add to:** `/ai-anti-spam-shield-service-model/requirements.txt`

```
# Domain Intelligence
python-whois>=0.8.0
dnspython>=2.5.0
aiohttp>=3.9.0

# Screenshot Analysis
playwright>=1.40.0
Pillow>=10.2.0

# Install playwright browsers after pip install:
# playwright install chromium
```

### 6.2 Installation Script

**Create:** `/ai-anti-spam-shield-service-model/scripts/install-intel.sh`

```bash
#!/bin/bash

echo "Installing phishing intelligence dependencies..."

# Install Python packages
pip install python-whois dnspython aiohttp playwright Pillow

# Install Playwright browsers
playwright install chromium

echo "Installation complete!"
```

---

## 7. Verification Checklist

### 7.1 Domain Intelligence

- [ ] WHOIS lookup returns domain age
- [ ] SSL certificate info is retrieved
- [ ] ASN info is retrieved for domain IP
- [ ] DNS records are checked

### 7.2 Visual Analysis

- [ ] Playwright browser launches successfully
- [ ] Screenshot is captured
- [ ] Login forms are detected
- [ ] Brand keywords are identified

### 7.3 Risk Scoring

- [ ] Combined score is calculated correctly
- [ ] Threat levels are assigned appropriately
- [ ] Indicators are aggregated from all sources

### 7.4 API

- [ ] `/analyze-url-deep` returns complete analysis
- [ ] `/intel/domain/{domain}` returns domain info
- [ ] Caching reduces repeated lookups

---

## 8. Example Response

```json
{
  "url": "http://paypa1-secure-login.xyz/verify",
  "is_phishing": true,
  "threat_level": "CRITICAL",
  "confidence": 0.92,
  "risk_score": 87.5,
  "recommendation": "DANGER: This is very likely a phishing attempt. Do not interact with this site.",
  "details": {
    "text_analysis": {
      "is_phishing": true,
      "confidence": 0.89,
      "indicators": ["credential_theft", "urgency"]
    },
    "domain_intelligence": {
      "domain": "paypa1-secure-login.xyz",
      "domain_age": {
        "age_days": 5,
        "is_new": true
      },
      "ssl_info": {
        "is_valid": true,
        "is_free_cert": true,
        "issuer": "Let's Encrypt"
      },
      "risk_indicators": [
        "Domain is only 5 days old",
        "Free SSL on new domain",
        "Suspicious TLD: .xyz"
      ],
      "risk_score": 45
    },
    "risk_assessment": {
      "total_score": 87.5,
      "indicators": [
        {"source": "text_analysis", "description": "ML model detected phishing patterns"},
        {"source": "url_analysis", "description": "Suspicious URL pattern: suspicious_keywords"},
        {"source": "domain_intelligence", "description": "Domain is only 5 days old"}
      ]
    }
  }
}
```

---

## Next Steps

After completing Phase 3:
1. Test with known phishing URLs
2. Tune risk scoring weights
3. Proceed to [Phase 4: Voice Scam Detection](./phase4-voice-detection.md)
