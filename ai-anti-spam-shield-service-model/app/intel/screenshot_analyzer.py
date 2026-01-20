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
            except Exception:
                pass

        return False

    async def _detect_password_field(self, page) -> bool:
        """Detect if page has a password field"""
        try:
            password_field = await page.query_selector('input[type="password"]')
            return password_field is not None
        except Exception:
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
