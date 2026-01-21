"""
Enhanced Phishing Detector with ML-based Detection
Supports: Email phishing, SMS phishing (smishing), URL phishing

This module provides production-grade phishing detection using:
- ML-based ensemble classification (XGBoost, Random Forest)
- Rule-based pattern matching for explainability
- URL analysis with suspicious pattern detection
- Brand impersonation detection
- Pre-trained transformer fallback (optional)

Trained on: PhishTank, OpenPhish, Enron, UCI SMS, Tranco (legitimate)
"""

import re
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

try:
    import tldextract
    HAS_TLDEXTRACT = True
except ImportError:
    HAS_TLDEXTRACT = False

try:
    import joblib
    import numpy as np
    HAS_ML = True
except ImportError:
    HAS_ML = False

try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

# Import feature extractors
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from model.feature_extractors import (
        URLFeatureExtractor,
        TextFeatureExtractor,
        CombinedFeatureExtractor
    )
    HAS_EXTRACTORS = True
except ImportError:
    HAS_EXTRACTORS = False

logger = logging.getLogger(__name__)


class PhishingType(Enum):
    """Types of phishing attacks"""
    EMAIL = "EMAIL"
    SMS = "SMS"
    URL = "URL"
    NONE = "NONE"


class ThreatLevel(Enum):
    """Threat severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


@dataclass
class URLAnalysisResult:
    """Result of analyzing a single URL"""
    url: str
    is_suspicious: bool
    score: float
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BrandImpersonation:
    """Brand impersonation detection result"""
    detected: bool
    brand: Optional[str] = None
    similarity_score: float = 0.0

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PhishingResult:
    """Complete phishing detection result"""
    is_phishing: bool
    confidence: float
    phishing_type: str
    threat_level: str
    indicators: List[str]
    urls_analyzed: List[Dict]
    brand_impersonation: Optional[Dict]
    recommendation: str
    details: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


class PhishingDetector:
    """
    Enhanced phishing detection with ML ensemble

    Combines rule-based detection with ML models for
    accurate and explainable phishing detection.
    """

    # Known brands commonly impersonated (expanded list)
    KNOWN_BRANDS = [
        # Payment & Financial
        'paypal', 'venmo', 'zelle', 'cashapp', 'wise', 'stripe', 'square',
        # E-commerce
        'amazon', 'ebay', 'walmart', 'target', 'costco', 'bestbuy', 'aliexpress', 'shopify', 'etsy',
        # Streaming & Entertainment
        'netflix', 'spotify', 'hulu', 'disney', 'hbomax', 'primevideo', 'youtube', 'twitch',
        # Tech Giants
        'apple', 'microsoft', 'google', 'meta', 'oracle', 'salesforce', 'sap',
        # Social Media
        'facebook', 'instagram', 'whatsapp', 'twitter', 'tiktok', 'snapchat', 'telegram', 'discord', 'reddit',
        # Banks (US)
        'chase', 'wellsfargo', 'bankofamerica', 'citibank', 'usbank', 'pnc', 'capitalone', 'discover',
        # Banks (International)
        'hsbc', 'barclays', 'natwest', 'santander', 'ing', 'bnp', 'deutschebank',
        # Shipping & Logistics
        'usps', 'fedex', 'ups', 'dhl', 'royalmail', 'canadapost', 'auspost',
        # Government
        'irs', 'ssa', 'dmv', 'hmrc', 'medicare', 'socialsecurity',
        # Productivity & Cloud
        'dropbox', 'adobe', 'zoom', 'slack', 'teams', 'github', 'gitlab', 'notion', 'trello',
        'docusign', 'onedrive', 'icloud', 'gdrive',
        # Email Providers
        'yahoo', 'outlook', 'office365', 'gmail', 'protonmail', 'aol', 'hotmail',
        # Crypto
        'coinbase', 'binance', 'kraken', 'metamask', 'ledger', 'trezor', 'opensea',
        # Security & Antivirus
        'norton', 'mcafee', 'avast', 'kaspersky', 'bitdefender',
        # Telecom
        'verizon', 'att', 'tmobile', 'sprint', 'vodafone', 'comcast', 'spectrum',
        # Other commonly targeted
        'linkedin', 'indeed', 'glassdoor', 'airbnb', 'uber', 'lyft', 'doordash', 'grubhub',
    ]

    # Suspicious TLDs often used in phishing (expanded)
    SUSPICIOUS_TLDS = [
        # Free/cheap TLDs abused by phishers
        'tk', 'ml', 'ga', 'cf', 'gq', 'xyz', 'top', 'work', 'click',
        'link', 'info', 'online', 'site', 'website', 'space', 'pw',
        'cc', 'su', 'buzz', 'fit', 'loan', 'download', 'stream',
        'win', 'review', 'country', 'kim', 'science', 'party', 'date',
        'accountant', 'cricket', 'racing', 'gdn', 'men', 'faith',
        'webcam', 'bid', 'trade', 'icu', 'rest', 'life', 'live',
        'rocks', 'world', 'today', 'solutions', 'support', 'services',
        'center', 'zone', 'email', 'tech', 'host', 'fun', 'monster',
    ]

    # URL shorteners commonly abused (expanded)
    URL_SHORTENERS = [
        'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'is.gd',
        'buff.ly', 'adf.ly', 'j.mp', 'tr.im', 'cutt.ly', 'rb.gy',
        'shorturl.at', 'tiny.cc', 'lnkd.in', 'soo.gd', 'clck.ru',
        's.id', 'rotf.lol', 'v.gd', 'qr.ae', 'u.to', 'short.io',
        'rebrand.ly', 'bl.ink', 'shorte.st', 'ouo.io', 'bc.vc',
    ]

    # Urgency patterns (more comprehensive + generalized)
    URGENCY_PATTERNS = [
        r'\b(urgent|immediately|asap|right now|today only|expires?|expiring)\b',
        r'\b(act now|hurry|don\'t wait|final notice|last chance|limited time)\b',
        r'\b(within \d+ (hours?|days?|minutes?|seconds?))\b',
        r'\b(account (suspended|locked|compromised|restricted|disabled|terminated))\b',
        r'\b(verify (your )?(account|identity|password|email|phone))\b',
        r'\b(immediate (action|attention|response) (required|needed))\b',
        r'\b(failure to (respond|verify|confirm|act))\b',
        r'\b(time.?(sensitive|critical|limited))\b',
        r'\b(before it\'?s too late)\b',
        r'\b(only \d+ (left|remaining|available))\b',
        r'\b(offer (ends|expires|valid until))\b',
        # More generalized urgency
        r'\b(pay now|upgrade now|review now|see now|claim now)\b',
        r'\b(now or|or lose|or miss|or else)\b',
        r'\b(don\'t miss|don\'t lose)\b',
        r'\b(pending.{0,15}(action|approval|review))\b',
    ]

    # Credential request patterns (expanded + generalized)
    CREDENTIAL_PATTERNS = [
        r'\b(enter (your )?(password|pin|ssn|credit card|cvv|security code))\b',
        r'\b(confirm (your )?(account|identity|details|password|login))\b',
        r'\b(update (your )?(information|password|credentials|payment|billing))\b',
        r'\b(provide (your )?(password|credentials|information|details))\b',
        r'\b(reset (your )?(password|credentials|account))\b',
        r'\b(login (to )?(verify|confirm|secure|protect))\b',
        r'\b(sign.?in (to )?(verify|confirm|update))\b',
        r'\b(re.?enter (your )?(password|credentials))\b',
        r'\b(validate (your )?(account|identity|card))\b',
        r'\b(authenticate (your )?(account|identity))\b',
        # More generalized patterns
        r'\b(needs? verification)\b',
        r'\b(require[sd]? verification)\b',
        r'\b(verification (needed|required|process))\b',
        r'\b(complete.{0,15}(verification|process|form))\b',
    ]

    # Financial patterns (expanded)
    FINANCIAL_PATTERNS = [
        r'\b(bank|credit card|debit card|payment|transaction|billing)\b',
        r'\b(wire transfer|bitcoin|cryptocurrency|crypto|eth|btc)\b',
        r'[$£€¥₹]\s?\d+[,\d]*(\.\d{2})?',
        r'\b(refund|reimbursement|compensation|rebate)\b',
        r'\b(prize|winner|won|lottery|jackpot|sweepstakes)\b',
        r'\b(inheritance|beneficiary|unclaimed funds)\b',
        r'\b(investment opportunity|guaranteed returns|roi)\b',
        r'\b(tax (refund|return|rebate))\b',
        r'\b(overdue (payment|invoice|balance))\b',
        r'\b(outstanding (balance|debt|amount))\b',
        r'\b(free (gift|money|iphone|samsung|macbook))\b',
    ]

    # Threat/Fear patterns (NEW)
    THREAT_PATTERNS = [
        r'\b(unauthorized (access|activity|login|transaction|charge))\b',
        r'\b(security (alert|warning|breach|issue|concern|threat))\b',
        r'\b(suspicious (activity|login|attempt|transaction|behavior))\b',
        r'\b(unusual (activity|sign.?in|access|behavior))\b',
        r'\b(someone (tried|attempted|accessed|logged))\b',
        r'\b(your (account|data|information) (is|has been|was|may be) (at risk|compromised|hacked|breached))\b',
        r'\b(legal (action|consequences|proceedings))\b',
        r'\b(law enforcement|police|fbi|authorities)\b',
        r'\b(arrest warrant|court order|subpoena)\b',
        r'\b(identity (theft|stolen|compromised))\b',
        r'\b(malware|virus|infected|hacked)\b',
        # Verification code hijacking
        r'\b((verification|auth|security) code.{0,20}(another|different|new) device)\b',
        r'\b(code.{0,15}(used|being used|was used).{0,15}(another|different))\b',
        r'\b(if this wasn\'?t you)\b',
        r'\b(wasn\'?t you.{0,20}(secure|protect|verify))\b',
    ]

    # Social engineering patterns (NEW)
    SOCIAL_ENGINEERING_PATTERNS = [
        r'\b(dear (valued )?(customer|user|member|client|account holder))\b',
        r'\b(we (have|noticed|detected|observed|found))\b',
        r'\b(your (recent )?(order|purchase|transaction|shipment))\b',
        r'\b(as a (valued|loyal|special) (customer|member))\b',
        r'\b(for (your|account) (security|safety|protection))\b',
        r'\b(to (avoid|prevent) (suspension|termination|closure))\b',
        r'\b(routine (maintenance|security|verification|check))\b',
        r'\b(mandatory (update|verification|action))\b',
        r'\b(failed (delivery|payment|transaction|verification))\b',
        r'\b(undelivered (package|parcel|mail|item))\b',
        # Package/delivery social engineering
        r'\b(package|parcel|delivery|shipment) (could not|cannot|was not|unable)\b',
        r'\b(reschedule|schedule|arrange) (your )?(delivery|pickup)\b',
        r'\b((will be|be) returned)\b',
        r'\b(delivery (attempt|failed|unsuccessful))\b',
    ]

    # Action request patterns (expanded + generalized)
    ACTION_PATTERNS = [
        r'\b(click (here|the link|below|this|the button))\b',
        r'\b(follow (this|the) link)\b',
        r'\b(tap (here|the link|below|to))\b',
        r'\b(visit (this|our|the) (link|website|page|portal))\b',
        r'\b(go to|navigate to|access)\b',
        r'\b(download (the )?(attachment|file|document|form))\b',
        r'\b(open (the )?(attachment|file|document|link))\b',
        r'\b(scan (this|the) (qr|code|barcode))\b',
        r'\b(reply (with|to|immediately))\b',
        r'\b(call (this|the|us|now|immediately))\b',
        # More generalized action patterns
        r'\b(complete.{0,10}(here|now|process|form))\b',
        r'\b(see (who|what|why|here|now))\b',
        r'\b(find out|check (out|now|here))\b',
        r'\b(cancel.{0,10}(here|now|if))\b',
        r'\b(review (now|here|document|details))\b',
    ]

    # Crypto/NFT scam patterns (NEW)
    CRYPTO_SCAM_PATTERNS = [
        r'\b(airdrop|free (tokens?|coins?|nft|crypto))\b',
        r'\b(connect (your )?(wallet|metamask))\b',
        r'\b(claim (your )?(reward|tokens?|coins?|nft|prize))\b',
        r'\b(wallet (compromised|at risk|verification))\b',
        r'\b(seed phrase|private key|recovery phrase)\b',
        r'\b(mint (now|free|limited))\b',
        r'\b(whitelist|presale|early access)\b',
        r'\b(staking reward|yield|apr|apy)\b',
        r'\b(verified (contract|collection|project))\b',
        r'\b(rug.?pull|honeypot)\b',
    ]

    # Impersonation indicators (NEW)
    IMPERSONATION_INDICATORS = [
        r'\b(official (notice|notification|communication|update))\b',
        r'\b(from (the )?(support|security|admin|team|department))\b',
        r'\b(customer (service|support|care|team))\b',
        r'\b(account (team|department|services))\b',
        r'\b(do not (reply|respond|ignore))\b',
        r'\b(this (is|message is) (automated|auto.?generated))\b',
        r'\b(help desk|helpdesk|it department)\b',
        r'\b(administrator|admin team|system admin)\b',
    ]

    def __init__(self, model_dir: str = 'models', use_ml: bool = True):
        """
        Initialize the enhanced phishing detector

        Args:
            model_dir: Directory containing trained ML models
            use_ml: Whether to use ML models (if available)
        """
        self.model_dir = Path(model_dir)
        self.use_ml = use_ml and HAS_ML

        # Initialize ML components
        self.ml_model = None
        self.vectorizer = None
        self.transformer_model = None

        # Initialize feature extractors
        if HAS_EXTRACTORS:
            self.url_extractor = URLFeatureExtractor()
            self.text_extractor = TextFeatureExtractor()
            self.combined_extractor = CombinedFeatureExtractor()
        else:
            self.url_extractor = None
            self.text_extractor = None
            self.combined_extractor = None

        # Compile patterns
        self.urgency_patterns = [re.compile(p, re.IGNORECASE) for p in self.URGENCY_PATTERNS]
        self.credential_patterns = [re.compile(p, re.IGNORECASE) for p in self.CREDENTIAL_PATTERNS]
        self.financial_patterns = [re.compile(p, re.IGNORECASE) for p in self.FINANCIAL_PATTERNS]
        self.threat_patterns = [re.compile(p, re.IGNORECASE) for p in self.THREAT_PATTERNS]
        self.social_engineering_patterns = [re.compile(p, re.IGNORECASE) for p in self.SOCIAL_ENGINEERING_PATTERNS]
        self.action_patterns = [re.compile(p, re.IGNORECASE) for p in self.ACTION_PATTERNS]
        self.crypto_scam_patterns = [re.compile(p, re.IGNORECASE) for p in self.CRYPTO_SCAM_PATTERNS]
        self.impersonation_patterns = [re.compile(p, re.IGNORECASE) for p in self.IMPERSONATION_INDICATORS]

        # Brand pattern
        self.brand_pattern = re.compile(
            r'\b(' + '|'.join(self.KNOWN_BRANDS) + r')\b',
            re.IGNORECASE
        )

        # URL patterns (improved)
        self.url_pattern = re.compile(
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            re.IGNORECASE
        )

        # Obfuscated URL patterns
        self.obfuscated_url_patterns = [
            re.compile(r'hxxp', re.IGNORECASE),  # Defanged URLs
            re.compile(r'\[dot\]|\[.\]', re.IGNORECASE),  # [dot] notation
            re.compile(r'%[0-9a-fA-F]{2}'),  # URL encoding
            re.compile(r'&#\d+;'),  # HTML entity encoding
            re.compile(r'@.*\.'),  # @ symbol before domain
        ]

        # Homoglyph/lookalike character detection
        self.homoglyph_map = {
            'a': ['а', 'ɑ', 'α', '@'],  # Cyrillic a, Latin alpha, etc.
            'e': ['е', 'ε', 'ё'],
            'o': ['о', 'ο', '0'],
            'i': ['і', 'ı', '1', 'l', '|'],
            'c': ['с', 'ϲ'],
            'p': ['р', 'ρ'],
            's': ['ѕ', '$', '5'],
            'x': ['х', '×'],
            'y': ['у', 'γ'],
            'n': ['п'],
            'h': ['һ'],
            'g': ['ɡ', '9'],
            't': ['τ', '+'],
            'b': ['ь', '6'],
            'd': ['ԁ'],
            'k': ['κ'],
            'l': ['1', 'I', '|'],
            'm': ['rn'],
            'w': ['vv', 'ω'],
        }

        # Load ML models
        if self.use_ml:
            self._load_ml_models()

        # Load transformer model (optional)
        if HAS_TRANSFORMERS:
            self._load_transformer_model()

        logger.info(f"PhishingDetector initialized (ML: {self.ml_model is not None})")

    def _load_ml_models(self):
        """Load trained ML models"""
        try:
            model_path = self.model_dir / 'phishing_model.pkl'
            vectorizer_path = self.model_dir / 'phishing_model_vectorizer.pkl'

            if model_path.exists():
                self.ml_model = joblib.load(model_path)
                logger.info(f"Loaded ML model from {model_path}")

            if vectorizer_path.exists():
                self.vectorizer = joblib.load(vectorizer_path)
                logger.info(f"Loaded vectorizer from {vectorizer_path}")

        except Exception as e:
            logger.warning(f"Failed to load ML models: {e}")
            self.ml_model = None
            self.vectorizer = None

    def _load_transformer_model(self):
        """Load pre-trained transformer model for phishing detection"""
        # Try the latest specialized phishing models (best accuracy first)
        models_to_try = [
            "cybersectony/phishing-email-detection-distilbert_v2.4.1",  # Best accuracy for phishing
            "ealvaradob/bert-finetuned-phishing",  # Fallback
        ]

        for model_name in models_to_try:
            try:
                logger.info(f"Loading transformer model: {model_name}")
                self.transformer_model = pipeline(
                    "text-classification",
                    model=model_name,
                    truncation=True,
                    max_length=512
                )
                logger.info(f"Successfully loaded {model_name} for phishing detection")
                return
            except Exception as e:
                logger.warning(f"Failed to load {model_name}: {e}")
                continue

        logger.warning("No transformer models available for phishing detection")
        self.transformer_model = None

    def detect(self, text: str, scan_type: str = 'auto') -> PhishingResult:
        """
        Main phishing detection method

        Args:
            text: Message text or URL to analyze
            scan_type: 'email', 'sms', 'url', or 'auto'

        Returns:
            PhishingResult with comprehensive analysis
        """
        if not text or len(text.strip()) < 3:
            return self._empty_result()

        text = text.strip()

        # Auto-detect scan type
        if scan_type == 'auto':
            scan_type = self._detect_scan_type(text)

        # Extract URLs
        urls = self.extract_urls(text)

        # Run all detection methods
        ml_score = self._ml_detection(text)
        rule_score, rule_indicators = self._rule_based_detection(text)
        url_results = self._analyze_urls(urls)
        brand_result = self._detect_brand_impersonation(text, urls)
        transformer_score = self._transformer_detection(text)

        # Calculate ensemble score
        final_score = self._ensemble_score(
            ml_score,
            rule_score,
            url_results,
            brand_result,
            transformer_score
        )

        # Collect all indicators
        indicators = self._collect_indicators(
            text, urls, brand_result, rule_indicators
        )

        # Determine threat level
        threat_level = self._determine_threat_level(final_score, indicators)

        # Determine if it's phishing (threshold adjusted based on indicators)
        # Use dynamic threshold based on indicator quality
        threshold = 0.45
        if len(indicators) >= 3:
            threshold = 0.40  # Lower threshold when multiple indicators present
        if len(indicators) >= 5:
            threshold = 0.35  # Even lower for many indicators

        # Special handling for URL-only analysis - suspicious URLs are highly indicative
        if scan_type == 'url' or (urls and len(text.strip()) < 100):
            # For URL-focused content, check if URL analysis found issues
            url_suspicious = any(r.is_suspicious for r in url_results)
            if url_suspicious:
                threshold = 0.32  # Lower threshold for URL-based phishing

        is_phishing = final_score >= threshold

        # Determine phishing type (only if actually phishing)
        phishing_type = self._determine_phishing_type(
            scan_type, indicators, url_results, is_phishing
        )

        # Generate recommendation
        recommendation = self._generate_recommendation(
            final_score, phishing_type, threat_level
        )

        return PhishingResult(
            is_phishing=is_phishing,
            confidence=round(final_score, 4),
            phishing_type=phishing_type.value,
            threat_level=threat_level.value,
            indicators=indicators,
            urls_analyzed=[u.to_dict() for u in url_results],
            brand_impersonation=brand_result.to_dict() if brand_result.detected else None,
            recommendation=recommendation,
            details={
                'ml_score': ml_score,
                'rule_score': rule_score,
                'transformer_score': transformer_score,
                'url_count': len(urls),
                'scan_type': scan_type
            }
        )

    def _empty_result(self) -> PhishingResult:
        """Return empty/safe result"""
        return PhishingResult(
            is_phishing=False,
            confidence=0.0,
            phishing_type=PhishingType.NONE.value,
            threat_level=ThreatLevel.NONE.value,
            indicators=[],
            urls_analyzed=[],
            brand_impersonation=None,
            recommendation="No suspicious content detected.",
            details={}
        )

    def _detect_scan_type(self, text: str) -> str:
        """Auto-detect the type of content"""
        text_lower = text.lower()

        # Check if it's primarily a URL
        if text.startswith('http://') or text.startswith('https://'):
            if len(text.split()) <= 3:
                return 'url'

        # Check for SMS patterns
        sms_patterns = [
            r'\b(txt|sms|text me)\b',
            r'\b(click link|tap here)\b',
            len(text) < 500  # SMS are typically short
        ]
        sms_score = sum(1 for p in sms_patterns[:2] if re.search(p, text_lower, re.IGNORECASE))
        if sms_score >= 1 and len(text) < 500:
            return 'sms'

        # Default to email for longer content
        return 'email'

    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        return self.url_pattern.findall(text)

    def _ml_detection(self, text: str) -> float:
        """Use trained ML model for detection"""
        if self.ml_model is None or self.combined_extractor is None:
            return 0.5  # Neutral if no model

        try:
            # Extract features
            features = self.combined_extractor.extract(text)
            feature_values = list(features.values())

            # Add TF-IDF features if available
            if self.vectorizer is not None:
                tfidf_features = self.vectorizer.transform([text]).toarray()[0]
                feature_values.extend(tfidf_features)

            # Predict
            X = np.array([feature_values])
            probability = self.ml_model.predict_proba(X)[0]

            return float(probability[1])  # Probability of phishing

        except Exception as e:
            logger.warning(f"ML detection failed: {e}")
            return 0.5

    def _transformer_detection(self, text: str) -> float:
        """Use transformer model for detection"""
        if self.transformer_model is None:
            return 0.5  # Neutral if no model

        try:
            result = self.transformer_model(text[:512])[0]  # Truncate for BERT

            # Map label to score
            if result['label'].lower() in ['phishing', 'spam', '1', 'positive']:
                return result['score']
            else:
                return 1.0 - result['score']

        except Exception as e:
            logger.warning(f"Transformer detection failed: {e}")
            return 0.5

    def _rule_based_detection(self, text: str) -> Tuple[float, List[str]]:
        """Enhanced rule-based detection for explainability"""
        indicators = []
        score = 0.0
        text_lower = text.lower()

        # Check for safe/legitimate context indicators that reduce phishing likelihood
        # These patterns indicate the message is more likely legitimate
        safe_context_score = 0.0
        safe_patterns = [
            r'\b(you requested|if this was you|if you did this)\b',  # User-initiated action
            r'\b(your (next )?billing date|subscription renews?|next payment)\b',  # Normal billing info
            r'\b(manage your subscription|subscription settings)\b',  # Self-service
            r'\b(order confirmed|thanks for your order|order #?\d+)\b',  # Order confirmation
            r'\b(receipt for|payment of \$[\d.]+ to)\b',  # Payment receipts
            r'\b(scheduled to be delivered|on its way|tracking number)\b',  # Delivery updates
            r'\b(statement is ready|view (your )?statement)\b',  # Account statements
            r'\b(meeting|reminder|appointment|calendar)\b',  # Calendar/scheduling
            r'\b(commented on|liked your|shared your|tagged you)\b',  # Social notifications
            r'\b(team meeting|project update|weekly|monthly digest)\b',  # Work communications
            r'\b(thanks for (using|your)|thank you for)\b',  # Thank you messages
            r'\bthanks,?\s+\w+\b',  # Signed thanks (e.g., "Thanks, Sarah")
        ]
        for pattern in safe_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                safe_context_score += 0.15

        # Check for official domain references (legitimate messages often reference official domains)
        official_domain_patterns = [
            r'\b(at |log in at |visit )?(wellsfargo|chase|paypal|amazon|microsoft|apple|google|fedex)\.com\b',
            r'\baccount\.(microsoft|google|amazon)\.com\b',
        ]
        for pattern in official_domain_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                safe_context_score += 0.20

        # Limit safe context reduction
        safe_context_score = min(safe_context_score, 0.5)

        # Check urgency patterns (high priority)
        urgency_count = sum(
            len(p.findall(text)) for p in self.urgency_patterns
        )
        if urgency_count > 0:
            score += min(0.30, urgency_count * 0.12)
            indicators.append(f"Urgency/pressure tactics detected ({urgency_count} instances)")

        # Check credential patterns (critical - highest weight)
        credential_count = sum(
            len(p.findall(text)) for p in self.credential_patterns
        )
        if credential_count > 0:
            score += min(0.40, credential_count * 0.18)
            indicators.append(f"Credential/password request detected ({credential_count} instances)")

        # Check threat/fear patterns (high priority)
        threat_count = sum(
            len(p.findall(text)) for p in self.threat_patterns
        )
        if threat_count > 0:
            score += min(0.30, threat_count * 0.12)
            indicators.append(f"Threatening language detected ({threat_count} instances)")

        # Check financial patterns
        financial_count = sum(
            len(p.findall(text)) for p in self.financial_patterns
        )
        if financial_count > 0:
            score += min(0.25, financial_count * 0.10)
            indicators.append(f"Financial/payment keywords detected ({financial_count} instances)")

        # Check social engineering patterns
        social_count = sum(
            len(p.findall(text)) for p in self.social_engineering_patterns
        )
        if social_count > 0:
            score += min(0.25, social_count * 0.10)
            indicators.append(f"Social engineering tactics detected ({social_count} instances)")

        # Check action request patterns
        action_count = sum(
            len(p.findall(text)) for p in self.action_patterns
        )
        if action_count > 0:
            score += min(0.20, action_count * 0.10)
            indicators.append(f"Suspicious action requests detected ({action_count} instances)")

        # Check crypto scam patterns
        crypto_count = sum(
            len(p.findall(text)) for p in self.crypto_scam_patterns
        )
        if crypto_count > 0:
            score += min(0.35, crypto_count * 0.15)
            indicators.append(f"Crypto/NFT scam indicators detected ({crypto_count} instances)")

        # Check impersonation patterns
        impersonation_count = sum(
            len(p.findall(text)) for p in self.impersonation_patterns
        )
        if impersonation_count > 0:
            score += min(0.20, impersonation_count * 0.08)
            indicators.append(f"Impersonation indicators detected ({impersonation_count} instances)")

        # Check for suspicious phrases (expanded list)
        suspicious_phrases = [
            # Classic phishing
            'click here', 'verify your', 'confirm your', 'update your',
            'unusual activity', 'security alert', 'account locked',
            'winner', 'congratulations', 'prize', 'free gift',
            # Package/delivery scams
            'delivery failed', 'package could not', 'reschedule delivery',
            'could not be delivered', 'will be returned', 'returned to sender',
            'tracking number', 'customs fee', 'delivery fee', 'redelivery',
            'undeliverable', 'attempted delivery', 'delivery attempt',
            # Account/subscription scams
            'subscription expired', 'subscription has expired', 'service interruption',
            'account has been', 'has been locked', 'has been suspended',
            'avoid suspension', 'avoid service', 'to avoid',
            'storage is full', 'storage full', 'upgrade now',
            # Tech support scams
            'virus detected', 'computer infected', 'call microsoft',
            'technical support', 'remote access', 'data loss',
            # Romance/relationship scams
            'send money', 'wire funds', 'western union', 'gift card',
            # Job/employment scams
            'work from home', 'easy money', 'no experience needed',
            'make money fast', 'guaranteed income',
            # Government impersonation
            'tax refund', 'irs notice', 'social security',
            'arrest warrant', 'legal action',
            # Generic urgency
            'immediately', 'right now', 'act now', 'expires',
            'limited time', 'before it', 'or it will',
            # Curiosity triggers
            'see who', 'find out who', 'someone viewed',
            'viewed your', 'looked at your',
            # Document/signature scams
            'document ready', 'ready for signature', 'sign document',
            'pending signature',
        ]
        phrase_count = sum(1 for p in suspicious_phrases if p in text_lower)
        if phrase_count > 0:
            score += min(0.35, phrase_count * 0.10)
            indicators.append(f"Known phishing phrases detected ({phrase_count})")

        # Check for brand + suspicious URL/domain combination (strong phishing indicator)
        brand_match = self.brand_pattern.search(text_lower)

        # Detect suspicious domains (with or without https://)
        suspicious_tld_pattern = r'[a-z0-9][-a-z0-9]*\.(' + '|'.join(self.SUSPICIOUS_TLDS) + r')\b'
        # Detect brand-keyword.tld patterns like "paypal-secure.com" or "binance-security.io"
        # Must have hyphen or extra words to be suspicious (official domains like microsoft.com are ok)
        brand_in_url_pattern = r'(' + '|'.join(self.KNOWN_BRANDS[:50]) + r')[-_][a-z0-9]+\.(com|net|org|io|co|xyz|top|click|site|info|me|app)\b'

        # Official domain patterns that should NOT be flagged
        official_domain_pattern = r'\b(account\.|www\.|mail\.|support\.)?(' + '|'.join(self.KNOWN_BRANDS[:50]) + r')\.(com|org|net|co)\b'
        has_official_domain = bool(re.search(official_domain_pattern, text_lower))

        has_suspicious_domain = (
            bool(re.search(suspicious_tld_pattern, text_lower)) or
            bool(re.search(brand_in_url_pattern, text_lower))
        )

        # Only flag if suspicious domain found AND no official domain present
        if brand_match and has_suspicious_domain and not has_official_domain:
            score += 0.30
            indicators.append(f"Brand '{brand_match.group()}' with suspicious URL/domain")
        elif has_suspicious_domain and not has_official_domain:
            # Suspicious domain without explicit brand mention - still add some score
            score += 0.15
            indicators.append("Suspicious domain TLD detected")

        # Additional check for crypto/finance brands with security-related URLs
        crypto_brands = ['binance', 'coinbase', 'metamask', 'kraken', 'ledger', 'trezor']
        has_crypto_brand = any(b in text_lower for b in crypto_brands)
        has_security_url = bool(re.search(r'(secur|verif|alert|withdraw|cancel).*\.(io|com|net|org)\b', text_lower))
        if has_crypto_brand and has_security_url:
            score += 0.20
            indicators.append("Crypto brand with security-themed URL")

        # Check for obfuscation attempts
        obfuscation_count = sum(
            1 for p in self.obfuscated_url_patterns if p.search(text)
        )
        if obfuscation_count > 0:
            score += min(0.2, obfuscation_count * 0.1)
            indicators.append(f"URL obfuscation detected ({obfuscation_count} techniques)")

        # Check for homoglyphs in brand names
        homoglyph_detected = self._detect_homoglyphs(text)
        if homoglyph_detected:
            score += 0.25
            indicators.append("Lookalike/homoglyph characters detected (possible spoofing)")

        # Check text characteristics
        if len(text) > 50:  # Only for substantial text
            # Excessive capitalization
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.3:
                score += 0.1
                indicators.append("Excessive capitalization (attention-grabbing tactic)")

            # Excessive punctuation
            punct_count = text.count('!') + text.count('?')
            if punct_count > 5:
                score += 0.08
                indicators.append("Excessive exclamation/question marks")

        # Apply safe context reduction - legitimate messages get score reduced
        if safe_context_score > 0 and score > 0:
            # Only reduce if we found safe patterns AND there's no malicious URL
            # Check for actual URL with suspicious TLD, not just TLD words in text
            suspicious_tld_in_url = bool(re.search(
                r'https?://[^\s]*\.(' + '|'.join(self.SUSPICIOUS_TLDS) + r')\b',
                text_lower
            ))

            if not suspicious_tld_in_url:
                score = max(0, score - safe_context_score)

        return min(score, 1.0), indicators

    def _detect_homoglyphs(self, text: str) -> bool:
        """Detect homoglyph/lookalike characters that might indicate spoofing"""
        # Only check for actual Unicode homoglyphs (non-ASCII lookalikes)
        # Exclude common ASCII substitutions that appear in normal text
        unicode_homoglyphs = {
            'а': 'a',  # Cyrillic
            'е': 'e',  # Cyrillic
            'о': 'o',  # Cyrillic
            'р': 'p',  # Cyrillic
            'с': 'c',  # Cyrillic
            'у': 'y',  # Cyrillic
            'х': 'x',  # Cyrillic
            'і': 'i',  # Cyrillic
            'ѕ': 's',  # Cyrillic
            'ɑ': 'a',  # Latin alpha
            'ε': 'e',  # Greek
            'ο': 'o',  # Greek
            'ι': 'i',  # Greek
            'κ': 'k',  # Greek
            'ρ': 'p',  # Greek
            'τ': 't',  # Greek
            'ν': 'v',  # Greek
            'ω': 'w',  # Greek
            'ɡ': 'g',  # Latin small letter script g
            'һ': 'h',  # Cyrillic
            'ԁ': 'd',  # Cyrillic
            'ь': 'b',  # Cyrillic soft sign
            'п': 'n',  # Cyrillic
        }

        # Check if text contains any Unicode homoglyphs
        for homoglyph in unicode_homoglyphs.keys():
            if homoglyph in text:
                return True

        return False

    def _analyze_urls(self, urls: List[str]) -> List[URLAnalysisResult]:
        """Enhanced URL analysis with more sophisticated detection"""
        results = []

        for url in urls:
            reasons = []
            score = 0.0
            url_lower = url.lower()

            # Check for IP address (high risk)
            if re.match(r'https?://\d+\.\d+\.\d+\.\d+', url):
                score += 0.55  # Increased - IP addresses are very suspicious
                reasons.append("URL uses IP address instead of domain name")

            # Check for hex-encoded IP
            if re.search(r'https?://0x[0-9a-f]+', url_lower):
                score += 0.5
                reasons.append("URL uses hexadecimal IP encoding (obfuscation)")

            if HAS_TLDEXTRACT:
                extracted = tldextract.extract(url)
                domain = extracted.domain.lower()
                suffix = extracted.suffix.lower()
                subdomain = extracted.subdomain.lower() if extracted.subdomain else ''

                # Check suspicious TLD
                if suffix in self.SUSPICIOUS_TLDS:
                    score += 0.3
                    reasons.append(f"Suspicious/free TLD: .{suffix}")

                # Check for brand in subdomain (typosquatting)
                if self.brand_pattern.search(subdomain):
                    score += 0.35
                    reasons.append("Brand name in subdomain (likely typosquatting)")

                # Check for brand name in domain (impersonation)
                # e.g., "appleid-support.info", "microsoft365-login.xyz"
                brand_in_domain = self.brand_pattern.search(domain)
                if brand_in_domain:
                    # Brand in domain + suspicious TLD = very suspicious
                    if suffix in self.SUSPICIOUS_TLDS:
                        score += 0.45
                        reasons.append(f"Brand '{brand_in_domain.group()}' in domain with suspicious TLD")
                    else:
                        # Brand in domain but not official (no hyphen in real brand domains)
                        if '-' in domain:
                            score += 0.35
                            reasons.append(f"Brand '{brand_in_domain.group()}' with hyphenated domain (suspicious)")

                # Check for brand misspelling in domain
                brand_misspell = self._detect_brand_misspelling(domain)
                if brand_misspell:
                    score += 0.4
                    reasons.append(f"Possible misspelling of '{brand_misspell}' in domain")

                # Check for lookalike domain patterns
                lookalike_patterns = [
                    (r'-login', 'login subdomain pattern'),
                    (r'-secure', 'secure subdomain pattern'),
                    (r'-verify', 'verify subdomain pattern'),
                    (r'-support', 'support subdomain pattern'),
                    (r'-account', 'account subdomain pattern'),
                    (r'-update', 'update subdomain pattern'),
                    (r'-alert', 'alert subdomain pattern'),
                    (r'login-', 'login prefix pattern'),
                    (r'secure-', 'secure prefix pattern'),
                    (r'account-', 'account prefix pattern'),
                ]
                for pattern, desc in lookalike_patterns:
                    if re.search(pattern, domain) or re.search(pattern, subdomain):
                        score += 0.2
                        reasons.append(f"Suspicious {desc}")
                        break

                # Very long subdomain chain
                subdomain_parts = subdomain.split('.') if subdomain else []
                if len(subdomain_parts) > 3:
                    score += 0.25
                    reasons.append(f"Excessive subdomain depth ({len(subdomain_parts)} levels)")

                # Check for random-looking domain (high entropy)
                if len(domain) > 8:
                    entropy = self._calculate_entropy(domain)
                    if entropy > 3.5:
                        score += 0.2
                        reasons.append("Domain appears randomly generated")

            # Check for URL shortener
            if any(shortener in url_lower for shortener in self.URL_SHORTENERS):
                score += 0.25
                reasons.append("URL shortener detected (hides real destination)")

            # Check for @ symbol (URL obfuscation - critical)
            if '@' in url:
                score += 0.45
                reasons.append("URL contains @ symbol (URL credential obfuscation)")

            # Check for excessive subdomains
            dot_count = url.count('.')
            if dot_count > 5:
                score += 0.2
                reasons.append(f"Unusual number of dots in URL ({dot_count})")

            # Check for suspicious keywords in URL path
            suspicious_url_keywords = [
                'login', 'signin', 'sign-in', 'logon', 'log-on',
                'verify', 'verification', 'validate', 'confirm',
                'secure', 'security', 'account', 'accounts',
                'update', 'upgrade', 'renew', 'restore',
                'password', 'passwd', 'credential',
                'authenticate', 'authentication', 'auth',
                'billing', 'payment', 'invoice',
                'suspended', 'locked', 'disabled',
                'webmail', 'webaccess', 'portal',
                'redirect', 'track', 'click',
            ]
            keyword_count = sum(1 for kw in suspicious_url_keywords if kw in url_lower)
            if keyword_count >= 2:
                score += min(0.25, keyword_count * 0.08)
                reasons.append(f"Multiple suspicious keywords in URL ({keyword_count})")

            # Check for data URI or javascript
            if url_lower.startswith('data:') or url_lower.startswith('javascript:'):
                score += 0.5
                reasons.append("Suspicious protocol (data: or javascript:)")

            # Check for port numbers (unusual for legitimate sites)
            if re.search(r':\d{4,5}/', url):
                score += 0.15
                reasons.append("Non-standard port number in URL")

            # Check for double extensions or unusual file types
            if re.search(r'\.(html?|php|asp|exe|scr|bat|cmd|js|vbs)\?', url_lower):
                score += 0.2
                reasons.append("Suspicious file extension in URL")

            # Check URL length (very long URLs are suspicious)
            if len(url) > 200:
                score += 0.15
                reasons.append("Unusually long URL")

            # Check for punycode (internationalized domain names)
            if 'xn--' in url_lower:
                score += 0.3
                reasons.append("Punycode domain detected (possible homograph attack)")

            results.append(URLAnalysisResult(
                url=url,
                is_suspicious=score >= 0.25,
                score=min(score, 1.0),
                reasons=reasons
            ))

        return results

    def _detect_brand_misspelling(self, domain: str) -> Optional[str]:
        """Detect common brand misspellings/typosquatting"""
        domain_lower = domain.lower()

        # Common typosquatting patterns
        for brand in self.KNOWN_BRANDS:
            if brand in domain_lower:
                continue  # Exact match, check if it's the real domain

            # Check for off-by-one character errors
            if len(domain_lower) == len(brand):
                diff_count = sum(1 for a, b in zip(domain_lower, brand) if a != b)
                if diff_count == 1:
                    return brand

            # Check for character insertion/deletion
            if abs(len(domain_lower) - len(brand)) == 1:
                # Simple check for similar strings
                if brand in domain_lower or domain_lower in brand:
                    return brand

            # Check for character swaps
            if len(domain_lower) == len(brand):
                for i in range(len(brand) - 1):
                    swapped = brand[:i] + brand[i+1] + brand[i] + brand[i+2:]
                    if domain_lower == swapped:
                        return brand

            # Check for common substitutions
            substitutions = {
                '0': 'o', 'o': '0',
                '1': 'l', 'l': '1', 'i': '1',
                '3': 'e', 'e': '3',
                '4': 'a', 'a': '4',
                '5': 's', 's': '5',
                '7': 't', 't': '7',
                '8': 'b', 'b': '8',
            }
            normalized = domain_lower
            for old, new in substitutions.items():
                normalized = normalized.replace(old, new)
            if normalized == brand:
                return brand

        return None

    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        if not text:
            return 0.0
        from collections import Counter
        import math
        freq = Counter(text.lower())
        length = len(text)
        entropy = 0.0
        for count in freq.values():
            if count > 0:
                prob = count / length
                entropy -= prob * math.log2(prob)
        return entropy

    def _detect_brand_impersonation(self, text: str, urls: List[str]) -> BrandImpersonation:
        """Enhanced brand impersonation detection"""
        text_combined = text + ' ' + ' '.join(urls)
        text_lower = text_combined.lower()
        matches = self.brand_pattern.findall(text_lower)

        if not matches:
            return BrandImpersonation(detected=False)

        # Get most common brand mentioned
        brand = max(set(matches), key=matches.count)

        # Official domains for known brands (partial list for most targeted)
        official_domains = {
            'paypal': ['paypal.com', 'paypal.me'],
            'amazon': ['amazon.com', 'amazon.co.uk', 'amazon.de', 'amazon.fr', 'amazon.ca', 'amazon.in', 'aws.amazon.com'],
            'netflix': ['netflix.com'],
            'apple': ['apple.com', 'icloud.com'],
            'microsoft': ['microsoft.com', 'live.com', 'outlook.com', 'office.com', 'office365.com', 'azure.com'],
            'google': ['google.com', 'gmail.com', 'youtube.com', 'accounts.google.com'],
            'facebook': ['facebook.com', 'fb.com', 'meta.com'],
            'instagram': ['instagram.com'],
            'whatsapp': ['whatsapp.com', 'wa.me'],
            'chase': ['chase.com'],
            'wellsfargo': ['wellsfargo.com'],
            'bankofamerica': ['bankofamerica.com', 'bofa.com'],
            'usps': ['usps.com'],
            'fedex': ['fedex.com'],
            'ups': ['ups.com'],
            'dhl': ['dhl.com'],
            'linkedin': ['linkedin.com'],
            'dropbox': ['dropbox.com'],
            'coinbase': ['coinbase.com'],
            'binance': ['binance.com', 'binance.us'],
        }

        is_impersonation = False
        similarity = 0.0
        impersonation_reasons = []

        # Check if brand is mentioned prominently
        brand_count = text_lower.count(brand)
        if brand_count >= 2:
            similarity += 0.2

        for url in urls:
            if HAS_TLDEXTRACT:
                extracted = tldextract.extract(url)
                full_domain = f"{extracted.domain}.{extracted.suffix}".lower()
                domain_lower = extracted.domain.lower()

                # Get official domains for this brand
                brand_domains = official_domains.get(brand, [f"{brand}.com"])

                # Check if URL domain matches official domain
                is_official = any(
                    full_domain == official or full_domain.endswith('.' + official)
                    for official in brand_domains
                )

                if not is_official:
                    # Brand mentioned but URL is not from official domain
                    is_impersonation = True
                    similarity = max(similarity, 0.7)
                    impersonation_reasons.append(f"URL domain '{full_domain}' doesn't match official {brand} domains")

                    # Higher confidence if brand is in subdomain but not main domain
                    if brand in extracted.subdomain.lower() and brand not in domain_lower:
                        similarity = max(similarity, 0.9)
                        impersonation_reasons.append(f"Brand '{brand}' used in subdomain of unrelated domain")

                    # Check for lookalike domain
                    misspelling = self._detect_brand_misspelling(domain_lower)
                    if misspelling == brand:
                        similarity = max(similarity, 0.95)
                        impersonation_reasons.append(f"Lookalike/typosquatting domain for '{brand}'")

        # Additional checks without URLs
        if not urls and brand_count >= 1:
            # Check for generic impersonation phrases
            impersonation_phrases = [
                f'{brand} team', f'{brand} support', f'{brand} security',
                f'{brand} account', f'{brand} service', f'from {brand}',
                f'{brand} customer', f'{brand} verification', f'{brand} notification',
            ]
            phrase_matches = sum(1 for p in impersonation_phrases if p in text_lower)
            if phrase_matches >= 2:
                is_impersonation = True
                similarity = max(similarity, 0.6)
                impersonation_reasons.append(f"Multiple {brand} impersonation phrases detected")

            # Check for credential requests mentioning brand
            cred_with_brand = any(
                p.search(text) and brand in text_lower
                for p in self.credential_patterns
            )
            if cred_with_brand:
                is_impersonation = True
                similarity = max(similarity, 0.75)
                impersonation_reasons.append(f"Credential request mentioning {brand}")

        return BrandImpersonation(
            detected=is_impersonation,
            brand=brand if is_impersonation else None,
            similarity_score=min(similarity, 1.0)
        )

    def _ensemble_score(self, ml_score: float, rule_score: float,
                        url_results: List[URLAnalysisResult],
                        brand_result: BrandImpersonation,
                        transformer_score: float) -> float:
        """Enhanced ensemble scoring with adaptive weighting"""

        # URL score - take max of all analyzed URLs
        url_score = 0.0
        url_suspicious_count = 0
        if url_results:
            url_score = max(r.score for r in url_results)
            url_suspicious_count = sum(1 for r in url_results if r.is_suspicious)

        # Brand score with confidence
        brand_score = brand_result.similarity_score if brand_result.detected else 0.0

        # Check which components are actually available/working
        ml_available = self.ml_model is not None and ml_score != 0.5
        transformer_available = self.transformer_model is not None and transformer_score != 0.5
        has_urls = len(url_results) > 0

        # Adaptive weights based on what detection methods are active
        if ml_available and transformer_available:
            # Full ensemble available
            if has_urls:
                weights = {'ml': 0.25, 'rule': 0.20, 'url': 0.25, 'brand': 0.10, 'transformer': 0.20}
            else:
                weights = {'ml': 0.30, 'rule': 0.25, 'url': 0.0, 'brand': 0.15, 'transformer': 0.30}
        elif ml_available or transformer_available:
            # Partial ML available
            if has_urls:
                weights = {'ml': 0.30, 'rule': 0.30, 'url': 0.20, 'brand': 0.10, 'transformer': 0.10}
            else:
                weights = {'ml': 0.35, 'rule': 0.40, 'url': 0.0, 'brand': 0.15, 'transformer': 0.10}
        else:
            # Rule-based only mode - rely heavily on pattern matching
            if has_urls:
                # If rule_score is low but URL score is high, URL is the main signal
                if rule_score < 0.25 and url_score > 0.35:
                    # URL-dominated content (bare URLs, short text with URLs)
                    weights = {'ml': 0.0, 'rule': 0.15, 'url': 0.65, 'brand': 0.20, 'transformer': 0.0}
                else:
                    weights = {'ml': 0.0, 'rule': 0.55, 'url': 0.25, 'brand': 0.20, 'transformer': 0.0}
            else:
                weights = {'ml': 0.0, 'rule': 0.75, 'url': 0.0, 'brand': 0.25, 'transformer': 0.0}

        # Calculate base weighted score
        score = (
            weights['ml'] * ml_score +
            weights['rule'] * rule_score +
            weights['url'] * url_score +
            weights['brand'] * brand_score +
            weights['transformer'] * transformer_score
        )

        # Multi-signal boosting - more aggressive when multiple indicators agree
        strong_indicators = []
        if ml_available and ml_score > 0.6:
            strong_indicators.append('ml')
        if rule_score > 0.20:  # Lower threshold for rule detection
            strong_indicators.append('rule')
        if url_score > 0.25:
            strong_indicators.append('url')
        if brand_result.detected and brand_result.similarity_score > 0.5:
            strong_indicators.append('brand')
        if transformer_available and transformer_score > 0.6:
            strong_indicators.append('transformer')

        indicator_count = len(strong_indicators)

        # Progressive boosting based on indicator agreement
        if indicator_count >= 4:
            score = min(score * 1.5, 1.0)  # Very high confidence
        elif indicator_count >= 3:
            score = min(score * 1.35, 1.0)  # High confidence
        elif indicator_count >= 2:
            score = min(score * 1.2, 1.0)  # Moderate confidence
        elif indicator_count >= 1 and rule_score > 0.35:
            score = min(score * 1.15, 1.0)  # Single strong indicator

        # Critical indicator override - certain patterns are almost always phishing
        # High brand impersonation with URL mismatch
        if brand_result.detected and brand_result.similarity_score > 0.85:
            score = max(score, 0.75)

        # Multiple suspicious URLs
        if url_suspicious_count >= 2:
            score = max(score, 0.65)

        # Very high rule-based score (multiple phishing patterns)
        if rule_score > 0.5:
            score = max(score, 0.65)
        elif rule_score > 0.4:
            score = max(score, 0.55)

        # Strong transformer + rule agreement
        if transformer_available and transformer_score > 0.7 and rule_score > 0.25:
            score = max(score, 0.65)

        # In rule-based only mode, trust high pattern scores more
        if not ml_available and not transformer_available:
            if rule_score > 0.35 and brand_result.detected:
                score = max(score, 0.6)
            elif rule_score > 0.40:
                score = max(score, 0.55)
            elif rule_score > 0.35:
                score = max(score, 0.5)

            # Boost for suspicious URL even with lower rule score
            if url_score > 0.25 and rule_score > 0.15:
                score = max(score, 0.5)

            # Brand impersonation with any suspicious indicators
            if brand_result.detected and (rule_score > 0.15 or url_score > 0.2):
                score = max(score, 0.55)

        # Check for brand mention combined with phishing patterns
        # (even if not detected as impersonation due to missing URL analysis)
        if not brand_result.detected and rule_score > 0.3:
            # Check if any known brand is mentioned in the text
            brand_mentioned = bool(self.brand_pattern.search(
                ' '.join([r.url for r in url_results]) if url_results else ''
            )) or any(brand in str(url_results).lower() for brand in self.KNOWN_BRANDS[:30])

        return min(max(score, 0.0), 1.0)

    def _collect_indicators(self, text: str, urls: List[str],
                            brand_result: BrandImpersonation,
                            rule_indicators: List[str]) -> List[str]:
        """Collect all detected indicators"""
        indicators = list(rule_indicators)

        # Add URL indicators
        for url in urls:
            if HAS_TLDEXTRACT:
                extracted = tldextract.extract(url)
                if extracted.suffix.lower() in self.SUSPICIOUS_TLDS:
                    indicators.append(f"Suspicious domain: {extracted.domain}.{extracted.suffix}")

        # Add brand impersonation
        if brand_result.detected:
            indicators.append(f"Possible {brand_result.brand} impersonation detected")

        # Add URL shortener warning
        for url in urls:
            if any(s in url.lower() for s in self.URL_SHORTENERS):
                indicators.append("URL shortener used (may hide destination)")
                break

        return list(set(indicators))  # Remove duplicates

    def _determine_threat_level(self, score: float, indicators: List[str]) -> ThreatLevel:
        """Determine threat level based on score, indicators, and indicator severity"""
        # Check for critical indicators
        critical_keywords = [
            'credential', 'password', 'lookalike', 'typosquatting',
            'homoglyph', 'spoofing', 'obfuscation', '@',
            'crypto', 'seed phrase', 'private key',
        ]
        has_critical = any(
            any(kw in ind.lower() for kw in critical_keywords)
            for ind in indicators
        )

        indicator_count = len(indicators)

        # Score-based with indicator severity adjustment
        if score >= 0.8 or (score >= 0.7 and has_critical) or indicator_count >= 6:
            return ThreatLevel.CRITICAL
        elif score >= 0.65 or (score >= 0.55 and has_critical) or indicator_count >= 4:
            return ThreatLevel.HIGH
        elif score >= 0.5 or indicator_count >= 3:
            return ThreatLevel.MEDIUM
        elif score >= 0.3 or indicator_count >= 1:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.NONE

    def _determine_phishing_type(self, scan_type: str, indicators: List[str],
                                  url_results: List[URLAnalysisResult],
                                  is_phishing: bool = False) -> PhishingType:
        """Determine the type of phishing attack"""
        # If not phishing, return NONE regardless of scan type
        if not is_phishing:
            return PhishingType.NONE

        if scan_type == 'url' or (url_results and all(r.is_suspicious for r in url_results)):
            return PhishingType.URL
        elif scan_type == 'sms':
            return PhishingType.SMS
        elif scan_type == 'email':
            return PhishingType.EMAIL
        elif url_results and any(r.is_suspicious for r in url_results):
            return PhishingType.URL
        else:
            return PhishingType.NONE

    def _generate_recommendation(self, score: float, phishing_type: PhishingType,
                                  threat_level: ThreatLevel) -> str:
        """Generate actionable recommendation"""
        if threat_level == ThreatLevel.NONE:
            return "This message appears to be safe. However, always verify sender identity for sensitive requests."

        if threat_level == ThreatLevel.LOW:
            return "Some suspicious elements detected. Verify the sender before taking any action."

        if threat_level == ThreatLevel.MEDIUM:
            return "This message contains suspicious content. Do not click links or provide personal information. Verify directly with the organization."

        if threat_level == ThreatLevel.HIGH:
            return "This message is likely a phishing attempt. Do not respond, click links, or provide any information. Report and delete."

        if threat_level == ThreatLevel.CRITICAL:
            return "DANGER: This is a phishing attack. Do not interact with this message in any way. Report to your IT department and delete immediately."

        return "Exercise caution with this message."

    # Legacy methods for backward compatibility
    def is_suspicious_domain(self, url: str) -> bool:
        """Check if domain is suspicious (legacy method)"""
        if HAS_TLDEXTRACT:
            extracted = tldextract.extract(url)
            return extracted.suffix in self.SUSPICIOUS_TLDS
        return False

    def check_suspicious_urls(self, urls: List[str]) -> bool:
        """Check for suspicious URLs (legacy method)"""
        return any(self.is_suspicious_domain(url) for url in urls)

    def check_brand_impersonation(self, text: str) -> bool:
        """Check for brand impersonation (legacy method)"""
        return bool(self.brand_pattern.search(text))

    def check_urgency_language(self, text: str) -> bool:
        """Check for urgency language (legacy method)"""
        return any(p.search(text) for p in self.urgency_patterns)
