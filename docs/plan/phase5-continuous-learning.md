# Phase 5: Continuous Learning System

> **Duration:** 1 Week
> **Priority:** High
> **Dependencies:** Phase 1 (Infrastructure), Phase 2 (Model Upgrade)

---

## Overview

Build a system that learns from user feedback and automatically improves model accuracy over time.

### Why This Matters

```
┌─────────────────────────────────────────────────────────────────┐
│               THE MODEL DEGRADATION PROBLEM                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Scam tactics evolve → Static models become outdated            │
│                                                                  │
│  Timeline:                                                       │
│  Week 1:  █████████████████████ 95% accuracy                    │
│  Month 1: ████████████████░░░░░ 88% accuracy                    │
│  Month 3: ██████████████░░░░░░░ 82% accuracy                    │
│  Month 6: ████████████░░░░░░░░░ 75% accuracy (unusable)         │
│                                                                  │
│  Solution: Continuous learning from user feedback                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Goals

1. User feedback collection API
2. Feedback queue with admin review
3. Automatic weekly retraining pipeline
4. Model versioning and registry
5. A/B testing and rollback capability

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CONTINUOUS LEARNING PIPELINE                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │   Mobile     │───>│   Backend    │───>│   Feedback   │           │
│  │   App        │    │   API        │    │   Queue      │           │
│  └──────────────┘    └──────────────┘    └──────┬───────┘           │
│        │                                        │                    │
│        │ User reports                           ▼                    │
│        │ "This was wrong"            ┌──────────────────┐           │
│        │                             │   Admin Review   │           │
│        │                             │   Dashboard      │           │
│        │                             └────────┬─────────┘           │
│        │                                      │                      │
│        │                                      │ Approved feedback    │
│        │                                      ▼                      │
│        │                             ┌──────────────────┐           │
│        │                             │   Training       │           │
│        │                             │   Dataset        │           │
│        │                             └────────┬─────────┘           │
│        │                                      │                      │
│        │                                      │ Weekly cron          │
│        │                                      ▼                      │
│        │                             ┌──────────────────┐           │
│        │                             │   Retraining     │           │
│        │                             │   Pipeline       │           │
│        │                             └────────┬─────────┘           │
│        │                                      │                      │
│        │                                      ▼                      │
│        │                             ┌──────────────────┐           │
│        │                             │   Model          │           │
│        │                             │   Registry       │           │
│        │                             └────────┬─────────┘           │
│        │                                      │                      │
│        │                                      │ Deploy best model    │
│        │                                      ▼                      │
│        │                             ┌──────────────────┐           │
│        └────────────────────────────>│   Production     │           │
│          Improved predictions        │   Model          │           │
│                                      └──────────────────┘           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. User Feedback API

### 2.1 Feedback Routes

**Create:** `/ai-anti-spam-shield-backend/src/routes/feedback.routes.js`

```javascript
const express = require('express');
const router = express.Router();
const feedbackController = require('../controllers/feedback.controller');
const { authenticate, authorize } = require('../middlewares/auth');

/**
 * @swagger
 * /api/v2/feedback:
 *   post:
 *     summary: Submit feedback on a scan result
 *     tags: [Feedback]
 */
router.post('/',
  authenticate,
  feedbackController.submitFeedback
);

/**
 * @swagger
 * /api/v2/feedback/pending:
 *   get:
 *     summary: Get pending feedback for review (admin)
 *     tags: [Feedback]
 */
router.get('/pending',
  authenticate,
  authorize('ADMIN'),
  feedbackController.getPendingFeedback
);

/**
 * @swagger
 * /api/v2/feedback/:id:
 *   put:
 *     summary: Review feedback (approve/reject)
 *     tags: [Feedback]
 */
router.put('/:id',
  authenticate,
  authorize('ADMIN'),
  feedbackController.reviewFeedback
);

/**
 * @swagger
 * /api/v2/feedback/stats:
 *   get:
 *     summary: Get feedback statistics
 *     tags: [Feedback]
 */
router.get('/stats',
  authenticate,
  feedbackController.getFeedbackStats
);

/**
 * @swagger
 * /api/v2/feedback/export:
 *   get:
 *     summary: Export approved feedback for training
 *     tags: [Feedback]
 */
router.get('/export',
  authenticate,
  authorize('ADMIN'),
  feedbackController.exportForTraining
);

module.exports = router;
```

### 2.2 Feedback Controller

**Create:** `/ai-anti-spam-shield-backend/src/controllers/feedback.controller.js`

```javascript
const feedbackService = require('../services/feedback/feedback.service');
const asyncHandler = require('../utils/asyncHandler');
const ApiError = require('../utils/apiError');

/**
 * Submit feedback on a scan result
 */
exports.submitFeedback = asyncHandler(async (req, res) => {
  const { scanId, scanType, feedbackType, actualLabel, comment } = req.body;

  // Validate input
  if (!scanId || !feedbackType) {
    throw new ApiError(400, 'scanId and feedbackType are required');
  }

  const validFeedbackTypes = ['false_positive', 'false_negative', 'confirmed'];
  if (!validFeedbackTypes.includes(feedbackType)) {
    throw new ApiError(400, `feedbackType must be one of: ${validFeedbackTypes.join(', ')}`);
  }

  const feedback = await feedbackService.submitFeedback({
    userId: req.user.id,
    scanId,
    scanType: scanType || 'text',
    feedbackType,
    actualLabel,
    comment,
  });

  res.status(201).json({
    success: true,
    message: 'Feedback submitted successfully',
    data: feedback,
  });
});

/**
 * Get pending feedback for admin review
 */
exports.getPendingFeedback = asyncHandler(async (req, res) => {
  const { page = 1, limit = 20, type } = req.query;

  const result = await feedbackService.getPendingFeedback({
    page: parseInt(page),
    limit: parseInt(limit),
    feedbackType: type,
  });

  res.json({
    success: true,
    data: result.feedback,
    pagination: result.pagination,
  });
});

/**
 * Review feedback (approve/reject)
 */
exports.reviewFeedback = asyncHandler(async (req, res) => {
  const { id } = req.params;
  const { action, notes } = req.body;

  if (!['approve', 'reject'].includes(action)) {
    throw new ApiError(400, 'action must be approve or reject');
  }

  const feedback = await feedbackService.reviewFeedback({
    feedbackId: id,
    action,
    reviewerId: req.user.id,
    notes,
  });

  res.json({
    success: true,
    message: `Feedback ${action}d successfully`,
    data: feedback,
  });
});

/**
 * Get feedback statistics
 */
exports.getFeedbackStats = asyncHandler(async (req, res) => {
  const stats = await feedbackService.getStatistics();

  res.json({
    success: true,
    data: stats,
  });
});

/**
 * Export approved feedback for training
 */
exports.exportForTraining = asyncHandler(async (req, res) => {
  const { format = 'json', since } = req.query;

  const data = await feedbackService.exportApprovedFeedback({
    format,
    since: since ? new Date(since) : null,
  });

  if (format === 'csv') {
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename=training_feedback.csv');
  }

  res.json({
    success: true,
    data,
  });
});
```

### 2.3 Feedback Service

**Create:** `/ai-anti-spam-shield-backend/src/services/feedback/feedback.service.js`

```javascript
const prisma = require('../../config/database');
const logger = require('../../utils/logger');
const { getQueue, QUEUES } = require('../../config/queue');

class FeedbackService {
  /**
   * Submit user feedback on a scan result
   */
  async submitFeedback({
    userId,
    scanId,
    scanType,
    feedbackType,
    actualLabel,
    comment,
  }) {
    // Get the original scan
    let originalPrediction;
    let scanHistoryId = null;
    let phishingHistoryId = null;

    if (scanType === 'phishing') {
      const scan = await prisma.phishingScanHistory.findUnique({
        where: { id: scanId },
      });
      if (!scan) {
        throw new Error('Scan not found');
      }
      originalPrediction = scan.isPhishing ? 'phishing' : 'safe';
      phishingHistoryId = scanId;
    } else {
      const scan = await prisma.scanHistory.findUnique({
        where: { id: scanId },
      });
      if (!scan) {
        throw new Error('Scan not found');
      }
      originalPrediction = scan.prediction;
      scanHistoryId = scanId;
    }

    // Create feedback record
    const feedback = await prisma.userFeedback.create({
      data: {
        userId,
        scanHistoryId,
        phishingHistoryId,
        originalPrediction,
        actualLabel: actualLabel || this._inferActualLabel(feedbackType, originalPrediction),
        feedbackType,
        userComment: comment,
        status: 'pending',
      },
    });

    logger.info('Feedback submitted', {
      feedbackId: feedback.id,
      userId,
      feedbackType,
    });

    // Queue for processing
    const queue = getQueue(QUEUES.FEEDBACK);
    await queue.add('process-feedback', {
      feedbackId: feedback.id,
    });

    return feedback;
  }

  /**
   * Get pending feedback for admin review
   */
  async getPendingFeedback({ page, limit, feedbackType }) {
    const skip = (page - 1) * limit;

    const where = {
      status: 'pending',
      ...(feedbackType && { feedbackType }),
    };

    const [feedback, total] = await Promise.all([
      prisma.userFeedback.findMany({
        where,
        include: {
          user: {
            select: { id: true, name: true, email: true },
          },
        },
        orderBy: { createdAt: 'desc' },
        skip,
        take: limit,
      }),
      prisma.userFeedback.count({ where }),
    ]);

    // Enrich with original scan data
    const enriched = await Promise.all(
      feedback.map(async (f) => {
        let scanData = null;
        if (f.scanHistoryId) {
          scanData = await prisma.scanHistory.findUnique({
            where: { id: f.scanHistoryId },
            select: {
              messageEncrypted: true,
              isSpam: true,
              confidence: true,
              scanType: true,
            },
          });
        } else if (f.phishingHistoryId) {
          scanData = await prisma.phishingScanHistory.findUnique({
            where: { id: f.phishingHistoryId },
            select: {
              inputText: true,
              inputUrl: true,
              isPhishing: true,
              confidence: true,
            },
          });
        }
        return { ...f, scanData };
      })
    );

    return {
      feedback: enriched,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  /**
   * Review feedback (approve/reject)
   */
  async reviewFeedback({ feedbackId, action, reviewerId, notes }) {
    const status = action === 'approve' ? 'approved' : 'rejected';

    const feedback = await prisma.userFeedback.update({
      where: { id: feedbackId },
      data: {
        status,
        reviewedBy: reviewerId,
        reviewedAt: new Date(),
      },
    });

    logger.info('Feedback reviewed', {
      feedbackId,
      action,
      reviewerId,
    });

    return feedback;
  }

  /**
   * Get feedback statistics
   */
  async getStatistics() {
    const [byStatus, byType, recentTrend] = await Promise.all([
      // By status
      prisma.userFeedback.groupBy({
        by: ['status'],
        _count: true,
      }),

      // By feedback type
      prisma.userFeedback.groupBy({
        by: ['feedbackType'],
        _count: true,
      }),

      // Recent trend (last 30 days)
      prisma.$queryRaw`
        SELECT DATE(createdAt) as date, COUNT(*) as count
        FROM UserFeedback
        WHERE createdAt > datetime('now', '-30 days')
        GROUP BY DATE(createdAt)
        ORDER BY date DESC
      `,
    ]);

    // Calculate false positive/negative rates
    const approved = await prisma.userFeedback.findMany({
      where: { status: 'approved' },
      select: { feedbackType: true, originalPrediction: true },
    });

    const falsePositives = approved.filter(f => f.feedbackType === 'false_positive').length;
    const falseNegatives = approved.filter(f => f.feedbackType === 'false_negative').length;
    const total = approved.length;

    return {
      byStatus: byStatus.reduce((acc, s) => ({ ...acc, [s.status]: s._count }), {}),
      byType: byType.reduce((acc, t) => ({ ...acc, [t.feedbackType]: t._count }), {}),
      rates: {
        falsePositiveRate: total > 0 ? (falsePositives / total).toFixed(4) : 0,
        falseNegativeRate: total > 0 ? (falseNegatives / total).toFixed(4) : 0,
      },
      recentTrend,
      pendingCount: byStatus.find(s => s.status === 'pending')?._count || 0,
    };
  }

  /**
   * Export approved feedback for training
   */
  async exportApprovedFeedback({ format, since }) {
    const where = {
      status: 'approved',
      includedInTraining: false,
      ...(since && { createdAt: { gte: since } }),
    };

    const feedback = await prisma.userFeedback.findMany({
      where,
      include: {
        user: {
          select: { id: true },
        },
      },
    });

    // Get associated scan data
    const trainingData = await Promise.all(
      feedback.map(async (f) => {
        let text = '';
        let scanType = 'text';

        if (f.scanHistoryId) {
          const scan = await prisma.scanHistory.findUnique({
            where: { id: f.scanHistoryId },
          });
          text = scan?.messageEncrypted || '';
          scanType = scan?.scanType || 'text';
        } else if (f.phishingHistoryId) {
          const scan = await prisma.phishingScanHistory.findUnique({
            where: { id: f.phishingHistoryId },
          });
          text = scan?.inputText || scan?.inputUrl || '';
          scanType = 'phishing';
        }

        return {
          id: f.id,
          text,
          originalLabel: f.originalPrediction,
          correctedLabel: f.actualLabel,
          feedbackType: f.feedbackType,
          scanType,
          timestamp: f.createdAt.toISOString(),
        };
      })
    );

    // Mark as exported
    const feedbackIds = feedback.map(f => f.id);
    if (feedbackIds.length > 0) {
      const batchId = `batch_${Date.now()}`;
      await prisma.userFeedback.updateMany({
        where: { id: { in: feedbackIds } },
        data: {
          includedInTraining: true,
          trainingBatch: batchId,
        },
      });
    }

    return {
      batchId: `batch_${Date.now()}`,
      count: trainingData.length,
      data: trainingData,
    };
  }

  /**
   * Infer actual label from feedback type
   */
  _inferActualLabel(feedbackType, originalPrediction) {
    if (feedbackType === 'confirmed') {
      return originalPrediction;
    }
    if (feedbackType === 'false_positive') {
      // Predicted spam/phishing but was actually safe
      return originalPrediction === 'spam' ? 'ham' : 'safe';
    }
    if (feedbackType === 'false_negative') {
      // Predicted safe but was actually spam/phishing
      return originalPrediction === 'ham' ? 'spam' : 'phishing';
    }
    return originalPrediction;
  }
}

module.exports = new FeedbackService();
```

---

## 3. Retraining Pipeline

### 3.1 Feedback Collector

**Create:** `/ai-anti-spam-shield-service-model/app/retraining/feedback_collector.py`

```python
"""
Feedback Collector

Fetches approved feedback from the backend API
and prepares it for retraining
"""

import aiohttp
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class FeedbackItem:
    """Single feedback item for training"""
    id: str
    text: str
    original_label: str
    corrected_label: str
    feedback_type: str
    scan_type: str
    timestamp: str

    @property
    def label(self) -> int:
        """Convert string label to int"""
        return 1 if self.corrected_label in ['spam', 'phishing'] else 0


class FeedbackCollector:
    """
    Collect feedback from backend API for retraining
    """

    def __init__(self, backend_url: str, api_key: str = None):
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
        Fetch approved feedback from backend

        Args:
            since: Only fetch feedback after this date
            scan_type: Filter by scan type (text, voice, phishing)

        Returns:
            List of FeedbackItem
        """
        url = f"{self.backend_url}/api/v2/feedback/export"
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

                    if not data.get('success'):
                        logger.error(f"API error: {data}")
                        return []

                    feedback_data = data.get('data', {}).get('data', [])

                    # Convert to FeedbackItem objects
                    items = []
                    for f in feedback_data:
                        # Filter by scan type if specified
                        if scan_type and f.get('scanType') != scan_type:
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

        except Exception as e:
            logger.error(f"Error fetching feedback: {e}")
            return []

    async def get_feedback_stats(self) -> Dict:
        """Get feedback statistics from backend"""
        url = f"{self.backend_url}/api/v2/feedback/stats"

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


def prepare_training_data(
    feedback_items: List[FeedbackItem],
    min_samples: int = 50,
) -> tuple:
    """
    Prepare feedback items for training

    Args:
        feedback_items: List of FeedbackItem
        min_samples: Minimum samples required

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

    return texts, labels, True
```

### 3.2 Incremental Trainer

**Create:** `/ai-anti-spam-shield-service-model/app/retraining/incremental_trainer.py`

```python
"""
Incremental Trainer

Fine-tunes existing models on new feedback data
without full retraining
"""

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)
from datasets import Dataset
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from typing import Dict, List, Optional, Tuple
import logging
import os
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class IncrementalTrainer:
    """
    Fine-tune existing models on new feedback

    Key features:
    - Small learning rate (prevents catastrophic forgetting)
    - Few epochs (quick adaptation)
    - Validation on held-out set
    - Automatic rollback if metrics degrade
    """

    def __init__(
        self,
        model_path: str,
        model_type: str = "sms",
        output_dir: str = "./retrained_models",
    ):
        self.model_path = model_path
        self.model_type = model_type
        self.output_dir = os.path.join(output_dir, model_type)
        os.makedirs(self.output_dir, exist_ok=True)

        # Load existing model
        logger.info(f"Loading model from {model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)

        # Store original metrics for comparison
        self.original_metrics = None

    def train_on_feedback(
        self,
        texts: List[str],
        labels: List[int],
        validation_split: float = 0.2,
        epochs: int = 2,
        learning_rate: float = 1e-5,  # Very small LR for fine-tuning
        batch_size: int = 8,
    ) -> Dict:
        """
        Fine-tune model on feedback data

        Args:
            texts: List of text samples
            labels: List of labels (0 or 1)
            validation_split: Fraction for validation
            epochs: Number of training epochs
            learning_rate: Learning rate (should be small)
            batch_size: Training batch size

        Returns:
            Training metrics and new model path
        """
        # Create dataset
        dataset = Dataset.from_dict({
            "text": texts,
            "label": labels,
        })

        # Tokenize
        def tokenize(examples):
            return self.tokenizer(
                examples["text"],
                padding="max_length",
                truncation=True,
                max_length=128,
            )

        dataset = dataset.map(tokenize, batched=True)

        # Split
        split = dataset.train_test_split(test_size=validation_split, seed=42)
        train_dataset = split["train"]
        val_dataset = split["test"]

        # Training arguments
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_output_dir = os.path.join(self.output_dir, f"v_{version}")

        training_args = TrainingArguments(
            output_dir=run_output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            learning_rate=learning_rate,
            warmup_ratio=0.1,
            weight_decay=0.01,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="recall",
            greater_is_better=True,
            logging_steps=10,
            save_total_limit=1,
            fp16=torch.cuda.is_available(),
        )

        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            tokenizer=self.tokenizer,
            compute_metrics=self._compute_metrics,
        )

        # Evaluate before training (baseline)
        logger.info("Evaluating baseline...")
        baseline_metrics = trainer.evaluate()
        self.original_metrics = baseline_metrics

        # Train
        logger.info("Starting fine-tuning...")
        train_result = trainer.train()

        # Evaluate after training
        logger.info("Evaluating after training...")
        new_metrics = trainer.evaluate()

        # Compare metrics
        improved = self._compare_metrics(baseline_metrics, new_metrics)

        if improved:
            # Save new model
            final_path = os.path.join(self.output_dir, "latest")
            trainer.save_model(final_path)
            self.tokenizer.save_pretrained(final_path)
            logger.info(f"New model saved to {final_path}")

            return {
                "success": True,
                "version": version,
                "baseline_metrics": baseline_metrics,
                "new_metrics": new_metrics,
                "model_path": final_path,
                "improved": True,
            }
        else:
            logger.warning("Metrics degraded, not saving new model")
            return {
                "success": False,
                "version": version,
                "baseline_metrics": baseline_metrics,
                "new_metrics": new_metrics,
                "model_path": None,
                "improved": False,
            }

    def _compute_metrics(self, eval_pred) -> Dict:
        """Compute evaluation metrics"""
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)

        accuracy = accuracy_score(labels, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, predictions, average='binary'
        )

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    def _compare_metrics(
        self,
        baseline: Dict,
        new: Dict,
        threshold: float = 0.02,
    ) -> bool:
        """
        Compare metrics to decide if new model is better

        Primary metric: recall (we want to catch more spam)
        Secondary: f1 (balance)

        Degradation threshold: 2%
        """
        baseline_recall = baseline.get("eval_recall", 0)
        new_recall = new.get("eval_recall", 0)

        baseline_f1 = baseline.get("eval_f1", 0)
        new_f1 = new.get("eval_f1", 0)

        # Recall should not decrease significantly
        recall_ok = new_recall >= baseline_recall - threshold

        # F1 should not decrease significantly
        f1_ok = new_f1 >= baseline_f1 - threshold

        # At least one should improve
        improved = new_recall > baseline_recall or new_f1 > baseline_f1

        logger.info(
            f"Metric comparison: recall {baseline_recall:.4f}->{new_recall:.4f}, "
            f"f1 {baseline_f1:.4f}->{new_f1:.4f}"
        )

        return recall_ok and f1_ok and improved


class RetrainingScheduler:
    """
    Schedule and manage retraining jobs
    """

    def __init__(
        self,
        feedback_collector,
        trainer: IncrementalTrainer,
        model_registry,
        min_samples: int = 50,
    ):
        self.collector = feedback_collector
        self.trainer = trainer
        self.registry = model_registry
        self.min_samples = min_samples

    async def run_retraining_job(
        self,
        model_type: str = "sms",
    ) -> Dict:
        """
        Run a complete retraining job

        Steps:
        1. Collect approved feedback
        2. Check if enough samples
        3. Train new model
        4. Compare with current
        5. Deploy if better
        """
        logger.info(f"Starting retraining job for {model_type}")

        # 1. Collect feedback
        feedback = await self.collector.fetch_approved_feedback(
            scan_type=model_type if model_type != "sms" else "text"
        )

        if len(feedback) < self.min_samples:
            logger.warning(
                f"Not enough feedback: {len(feedback)} < {self.min_samples}"
            )
            return {
                "status": "skipped",
                "reason": "insufficient_feedback",
                "sample_count": len(feedback),
            }

        # 2. Prepare data
        texts = [f.text for f in feedback]
        labels = [f.label for f in feedback]

        # 3. Train
        result = self.trainer.train_on_feedback(texts, labels)

        if not result["success"]:
            return {
                "status": "failed",
                "reason": "metrics_degraded",
                "baseline": result["baseline_metrics"],
                "new": result["new_metrics"],
            }

        # 4. Register new version
        if self.registry:
            version_info = await self.registry.register_version(
                model_type=model_type,
                version=result["version"],
                model_path=result["model_path"],
                metrics=result["new_metrics"],
            )

            # 5. Deploy
            await self.registry.deploy_version(
                model_type=model_type,
                version=result["version"],
            )

        return {
            "status": "success",
            "version": result["version"],
            "metrics": result["new_metrics"],
            "improvement": {
                "recall": result["new_metrics"]["eval_recall"] - result["baseline_metrics"]["eval_recall"],
                "f1": result["new_metrics"]["eval_f1"] - result["baseline_metrics"]["eval_f1"],
            },
        }
```

### 3.3 Model Registry

**Create:** `/ai-anti-spam-shield-service-model/app/registry/model_registry.py`

```python
"""
Model Registry

Tracks model versions, metrics, and deployments
Supports A/B testing and rollback
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class ModelVersionInfo:
    """Model version metadata"""
    model_type: str
    version: str
    model_path: str
    metrics: Dict
    trained_at: str
    deployed_at: Optional[str]
    status: str  # training, testing, deployed, rolled_back
    feedback_batch: Optional[str]

    def to_dict(self) -> Dict:
        return asdict(self)


class ModelRegistry:
    """
    Model versioning and deployment registry

    Features:
    - Version tracking
    - Metrics history
    - A/B testing support
    - Rollback capability
    """

    def __init__(
        self,
        storage_path: str = "./model_registry",
        db_client=None,
    ):
        self.storage_path = storage_path
        self.db = db_client
        os.makedirs(storage_path, exist_ok=True)

        # Load registry state
        self.registry_file = os.path.join(storage_path, "registry.json")
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict:
        """Load registry from file"""
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {
            "versions": {},
            "deployed": {},
            "history": [],
        }

    def _save_registry(self):
        """Save registry to file"""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)

    async def register_version(
        self,
        model_type: str,
        version: str,
        model_path: str,
        metrics: Dict,
        feedback_batch: str = None,
    ) -> ModelVersionInfo:
        """
        Register a new model version

        Args:
            model_type: Type of model (sms, phishing, voice)
            version: Version string
            model_path: Path to model files
            metrics: Training/validation metrics
            feedback_batch: ID of feedback batch used for training
        """
        # Create version key
        version_key = f"{model_type}_{version}"

        # Copy model to registry storage
        registry_model_path = os.path.join(
            self.storage_path, "models", model_type, version
        )
        os.makedirs(registry_model_path, exist_ok=True)

        if os.path.isdir(model_path):
            shutil.copytree(model_path, registry_model_path, dirs_exist_ok=True)
        else:
            shutil.copy(model_path, registry_model_path)

        # Create version info
        info = ModelVersionInfo(
            model_type=model_type,
            version=version,
            model_path=registry_model_path,
            metrics=metrics,
            trained_at=datetime.now().isoformat(),
            deployed_at=None,
            status="testing",
            feedback_batch=feedback_batch,
        )

        # Save to registry
        if model_type not in self.registry["versions"]:
            self.registry["versions"][model_type] = {}

        self.registry["versions"][model_type][version] = info.to_dict()
        self._save_registry()

        logger.info(f"Registered model version: {version_key}")

        # Save to database if available
        if self.db:
            await self._save_to_db(info)

        return info

    async def deploy_version(
        self,
        model_type: str,
        version: str,
    ) -> bool:
        """
        Deploy a model version to production

        Args:
            model_type: Type of model
            version: Version to deploy

        Returns:
            Success status
        """
        version_key = f"{model_type}_{version}"

        # Check version exists
        if model_type not in self.registry["versions"]:
            logger.error(f"Model type not found: {model_type}")
            return False

        if version not in self.registry["versions"][model_type]:
            logger.error(f"Version not found: {version}")
            return False

        # Get current deployed version for rollback history
        current_deployed = self.registry["deployed"].get(model_type)

        # Update deployment
        self.registry["versions"][model_type][version]["status"] = "deployed"
        self.registry["versions"][model_type][version]["deployed_at"] = datetime.now().isoformat()
        self.registry["deployed"][model_type] = version

        # Add to history
        self.registry["history"].append({
            "action": "deploy",
            "model_type": model_type,
            "version": version,
            "previous_version": current_deployed,
            "timestamp": datetime.now().isoformat(),
        })

        self._save_registry()

        logger.info(f"Deployed model version: {version_key}")
        return True

    async def rollback(
        self,
        model_type: str,
        target_version: str = None,
    ) -> bool:
        """
        Rollback to a previous version

        Args:
            model_type: Type of model
            target_version: Version to rollback to (default: previous)

        Returns:
            Success status
        """
        if target_version is None:
            # Find previous version from history
            for entry in reversed(self.registry["history"]):
                if entry["model_type"] == model_type and entry["action"] == "deploy":
                    target_version = entry.get("previous_version")
                    break

        if not target_version:
            logger.error("No previous version to rollback to")
            return False

        # Mark current as rolled back
        current = self.registry["deployed"].get(model_type)
        if current:
            self.registry["versions"][model_type][current]["status"] = "rolled_back"

        # Deploy target
        return await self.deploy_version(model_type, target_version)

    def get_deployed_version(self, model_type: str) -> Optional[ModelVersionInfo]:
        """Get currently deployed version"""
        version = self.registry["deployed"].get(model_type)
        if not version:
            return None

        info = self.registry["versions"].get(model_type, {}).get(version)
        if info:
            return ModelVersionInfo(**info)
        return None

    def get_all_versions(self, model_type: str) -> List[ModelVersionInfo]:
        """Get all versions for a model type"""
        versions = self.registry["versions"].get(model_type, {})
        return [ModelVersionInfo(**v) for v in versions.values()]

    def get_version_history(self, model_type: str = None) -> List[Dict]:
        """Get deployment history"""
        history = self.registry["history"]
        if model_type:
            history = [h for h in history if h["model_type"] == model_type]
        return history

    async def _save_to_db(self, info: ModelVersionInfo):
        """Save version info to database"""
        # This would use Prisma or another DB client
        pass
```

---

## 4. Weekly Cron Job

### 4.1 Scheduler

**Create:** `/ai-anti-spam-shield-service-model/app/retraining/scheduler.py`

```python
"""
Retraining Scheduler

Runs weekly retraining jobs automatically
"""

import asyncio
from datetime import datetime, timedelta
import logging
from typing import Dict

from .feedback_collector import FeedbackCollector
from .incremental_trainer import IncrementalTrainer, RetrainingScheduler
from ..registry.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class WeeklyRetrainingScheduler:
    """
    Schedules and runs weekly retraining jobs
    """

    def __init__(
        self,
        backend_url: str,
        model_paths: Dict[str, str],
        registry_path: str = "./model_registry",
        min_samples: int = 50,
    ):
        self.collector = FeedbackCollector(backend_url)
        self.registry = ModelRegistry(registry_path)
        self.model_paths = model_paths
        self.min_samples = min_samples

        # Track last run
        self.last_run = {}

    async def run_weekly_job(self):
        """
        Run retraining for all model types
        """
        logger.info("Starting weekly retraining job")
        results = {}

        for model_type, model_path in self.model_paths.items():
            try:
                logger.info(f"Processing {model_type}...")

                # Initialize trainer
                trainer = IncrementalTrainer(
                    model_path=model_path,
                    model_type=model_type,
                )

                # Create scheduler
                scheduler = RetrainingScheduler(
                    feedback_collector=self.collector,
                    trainer=trainer,
                    model_registry=self.registry,
                    min_samples=self.min_samples,
                )

                # Run retraining
                result = await scheduler.run_retraining_job(model_type)
                results[model_type] = result

                logger.info(f"{model_type} result: {result['status']}")

            except Exception as e:
                logger.error(f"Error retraining {model_type}: {e}")
                results[model_type] = {
                    "status": "error",
                    "error": str(e),
                }

        self.last_run[datetime.now().isoformat()] = results
        return results

    async def start_scheduler(self, interval_days: int = 7):
        """
        Start the scheduler loop

        Args:
            interval_days: Days between retraining jobs
        """
        logger.info(f"Starting retraining scheduler (every {interval_days} days)")

        while True:
            try:
                # Run job
                await self.run_weekly_job()

                # Wait for next run
                await asyncio.sleep(interval_days * 24 * 60 * 60)

            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                # Wait before retry
                await asyncio.sleep(60 * 60)  # 1 hour


# CLI entry point
async def main():
    """Run retraining job manually"""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="http://localhost:3000")
    parser.add_argument("--model-type", default="sms")
    parser.add_argument("--model-path", required=True)
    args = parser.parse_args()

    scheduler = WeeklyRetrainingScheduler(
        backend_url=args.backend,
        model_paths={args.model_type: args.model_path},
    )

    result = await scheduler.run_weekly_job()
    print(f"Result: {result}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
```

---

## 5. FastAPI Integration

**Add to:** `/ai-anti-spam-shield-service-model/app/main.py`

```python
from app.registry.model_registry import ModelRegistry

# Initialize registry
model_registry = ModelRegistry()


@app.get("/models/versions")
async def get_model_versions():
    """Get all registered model versions"""
    versions = {}
    for model_type in ["sms", "phishing", "voice"]:
        versions[model_type] = {
            "deployed": None,
            "all": [],
        }

        deployed = model_registry.get_deployed_version(model_type)
        if deployed:
            versions[model_type]["deployed"] = deployed.to_dict()

        all_versions = model_registry.get_all_versions(model_type)
        versions[model_type]["all"] = [v.to_dict() for v in all_versions]

    return versions


@app.get("/models/history")
async def get_deployment_history(model_type: str = None):
    """Get model deployment history"""
    return model_registry.get_version_history(model_type)


@app.post("/models/rollback")
async def rollback_model(model_type: str, version: str = None):
    """Rollback to a previous model version"""
    success = await model_registry.rollback(model_type, version)
    return {"success": success}
```

---

## 6. Mobile App Integration

### 6.1 Feedback Button

Add a feedback button to scan results in the Flutter app.

**Modify:** `/ai_anti_spam_shield_mobile/lib/widgets/scan_result_card.dart`

```dart
class FeedbackButton extends StatelessWidget {
  final String scanId;
  final String scanType;
  final bool isSpam;

  const FeedbackButton({
    required this.scanId,
    required this.scanType,
    required this.isSpam,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        TextButton.icon(
          icon: Icon(Icons.thumb_up_outlined),
          label: Text('Correct'),
          onPressed: () => _submitFeedback(context, 'confirmed'),
        ),
        SizedBox(width: 16),
        TextButton.icon(
          icon: Icon(Icons.thumb_down_outlined),
          label: Text('Wrong'),
          onPressed: () => _showFeedbackDialog(context),
        ),
      ],
    );
  }

  void _showFeedbackDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => FeedbackDialog(
        scanId: scanId,
        scanType: scanType,
        currentPrediction: isSpam ? 'spam' : 'ham',
      ),
    );
  }

  Future<void> _submitFeedback(BuildContext context, String type) async {
    // Submit via API
    try {
      await ApiService().submitFeedback(
        scanId: scanId,
        feedbackType: type,
      );
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Thanks for your feedback!')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to submit feedback')),
      );
    }
  }
}
```

---

## 7. Verification Checklist

- [ ] Feedback API accepts user corrections
- [ ] Admin can review pending feedback
- [ ] Approved feedback is exported correctly
- [ ] Incremental trainer improves metrics
- [ ] Model registry tracks versions
- [ ] Rollback restores previous model
- [ ] Weekly job runs successfully
- [ ] Mobile app shows feedback buttons

---

## 8. Metrics to Track

| Metric | Description | Target |
|--------|-------------|--------|
| Feedback rate | Feedback per 1000 scans | >5% |
| Approval rate | Approved / Total feedback | >70% |
| Model improvement | Recall increase per cycle | >1% |
| Retrain success | Successful retrains / Total | >80% |
| Rollback rate | Rollbacks / Deployments | <10% |

---

## Summary

The continuous learning system enables the AI Anti-Spam Shield to:

1. **Collect feedback** from users on scan results
2. **Review and approve** corrections via admin dashboard
3. **Automatically retrain** models weekly
4. **Deploy improvements** safely with rollback capability
5. **Track metrics** to measure system improvement

This creates a virtuous cycle where the system gets smarter over time as users interact with it.
