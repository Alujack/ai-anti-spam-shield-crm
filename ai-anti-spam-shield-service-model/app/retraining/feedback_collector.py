"""
Feedback Collector

Fetches approved feedback from the backend API
and prepares it for retraining.
"""

import aiohttp
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class FeedbackItem:
    """Single feedback item for training."""
    id: str
    text: str
    original_label: str
    corrected_label: str
    feedback_type: str
    scan_type: str
    timestamp: str

    @property
    def label(self) -> int:
        """Convert string label to int (1 = spam/phishing, 0 = ham/safe)."""
        return 1 if self.corrected_label in ['spam', 'phishing'] else 0

    @property
    def is_spam(self) -> bool:
        """Check if this is a spam sample."""
        return self.corrected_label in ['spam', 'phishing']


class FeedbackCollector:
    """
    Collect feedback from backend API for retraining.

    Handles:
    - Fetching approved feedback
    - Filtering by scan type
    - Preparing data for training
    """

    def __init__(self, backend_url: str, api_key: str = None):
        """
        Initialize the feedback collector.

        Args:
            backend_url: Base URL of the backend API
            api_key: Optional API key for authentication
        """
        self.backend_url = backend_url.rstrip('/')
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'

    async def fetch_approved_feedback(
        self,
        since: Optional[datetime] = None,
        scan_type: Optional[str] = None,
    ) -> List[FeedbackItem]:
        """
        Fetch approved feedback from backend.

        Args:
            since: Only fetch feedback after this date
            scan_type: Filter by scan type (text, voice, phishing)

        Returns:
            List of FeedbackItem objects
        """
        url = f"{self.backend_url}/api/v1/feedback/export"
        params = {}

        if since:
            params['since'] = since.isoformat()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch feedback: {response.status}")
                        return []

                    data = await response.json()

                    if not data.get('status') == 'success':
                        logger.error(f"API error: {data}")
                        return []

                    feedback_data = data.get('data', {}).get('data', [])

                    # Convert to FeedbackItem objects
                    items = []
                    for f in feedback_data:
                        # Filter by scan type if specified
                        if scan_type and f.get('scanType') != scan_type:
                            continue

                        # Skip items without text
                        if not f.get('text'):
                            continue

                        items.append(FeedbackItem(
                            id=f['id'],
                            text=f['text'],
                            original_label=f['originalLabel'],
                            corrected_label=f['correctedLabel'],
                            feedback_type=f['feedbackType'],
                            scan_type=f['scanType'],
                            timestamp=f['timestamp'],
                        ))

                    logger.info(f"Fetched {len(items)} feedback items")
                    return items

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error fetching feedback: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching feedback: {e}")
            return []

    async def get_feedback_stats(self) -> Dict:
        """Get feedback statistics from backend."""
        url = f"{self.backend_url}/api/v1/feedback/stats"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        return {}

                    data = await response.json()
                    return data.get('data', {})

        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            return {}

    def fetch_approved_feedback_sync(
        self,
        since: Optional[datetime] = None,
        scan_type: Optional[str] = None,
    ) -> List[FeedbackItem]:
        """
        Synchronous version of fetch_approved_feedback.

        Useful when running outside of async context.
        """
        return asyncio.run(self.fetch_approved_feedback(since, scan_type))


def prepare_training_data(
    feedback_items: List[FeedbackItem],
    min_samples: int = 50,
    balance_classes: bool = True,
) -> tuple:
    """
    Prepare feedback items for training.

    Args:
        feedback_items: List of FeedbackItem
        min_samples: Minimum samples required
        balance_classes: Whether to balance class distribution

    Returns:
        Tuple of (texts, labels, is_sufficient)
    """
    if len(feedback_items) < min_samples:
        logger.warning(
            f"Insufficient feedback: {len(feedback_items)} < {min_samples}"
        )
        return [], [], False

    texts = [item.text for item in feedback_items]
    labels = [item.label for item in feedback_items]

    # Log class distribution
    spam_count = sum(labels)
    ham_count = len(labels) - spam_count
    logger.info(f"Training data: {spam_count} spam, {ham_count} ham")

    # Optionally balance classes
    if balance_classes and spam_count > 0 and ham_count > 0:
        # Simple oversampling of minority class
        if spam_count < ham_count:
            minority_indices = [i for i, l in enumerate(labels) if l == 1]
            oversample_count = ham_count - spam_count
            for i in range(oversample_count):
                idx = minority_indices[i % len(minority_indices)]
                texts.append(texts[idx])
                labels.append(labels[idx])
        elif ham_count < spam_count:
            minority_indices = [i for i, l in enumerate(labels) if l == 0]
            oversample_count = spam_count - ham_count
            for i in range(oversample_count):
                idx = minority_indices[i % len(minority_indices)]
                texts.append(texts[idx])
                labels.append(labels[idx])

        logger.info(f"After balancing: {sum(labels)} spam, {len(labels) - sum(labels)} ham")

    return texts, labels, True


def filter_by_quality(
    feedback_items: List[FeedbackItem],
    min_text_length: int = 10,
    max_text_length: int = 5000,
) -> List[FeedbackItem]:
    """
    Filter feedback items by quality criteria.

    Args:
        feedback_items: List of FeedbackItem
        min_text_length: Minimum text length
        max_text_length: Maximum text length

    Returns:
        Filtered list of FeedbackItem
    """
    filtered = []
    for item in feedback_items:
        # Check text length
        if len(item.text) < min_text_length:
            continue
        if len(item.text) > max_text_length:
            continue

        # Skip empty or whitespace-only text
        if not item.text.strip():
            continue

        filtered.append(item)

    logger.info(f"Filtered {len(feedback_items)} -> {len(filtered)} items")
    return filtered
