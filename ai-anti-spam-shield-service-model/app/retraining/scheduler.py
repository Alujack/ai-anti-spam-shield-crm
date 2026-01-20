"""
Retraining Scheduler

Runs weekly retraining jobs automatically.
Can be triggered manually or via cron job.
"""

import asyncio
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional
import os

from .feedback_collector import FeedbackCollector, prepare_training_data, filter_by_quality
from .incremental_trainer import IncrementalTrainer, RetrainingScheduler
from ..registry.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class WeeklyRetrainingScheduler:
    """
    Schedules and runs weekly retraining jobs.
    """

    def __init__(
        self,
        backend_url: str,
        model_paths: Dict[str, str],
        registry_path: str = "./model_registry",
        min_samples: int = 50,
        api_key: str = None,
    ):
        """
        Initialize the weekly scheduler.

        Args:
            backend_url: Backend API URL for fetching feedback
            model_paths: Dictionary mapping model types to paths
            registry_path: Path to model registry
            min_samples: Minimum samples required for retraining
            api_key: API key for backend authentication
        """
        self.collector = FeedbackCollector(backend_url, api_key)
        self.registry = ModelRegistry(registry_path)
        self.model_paths = model_paths
        self.min_samples = min_samples

        # Track last run
        self.last_run = {}
        self.is_running = False

    async def run_weekly_job(self) -> Dict:
        """
        Run retraining for all model types.

        Returns:
            Dictionary with results for each model type
        """
        if self.is_running:
            logger.warning("Retraining job already in progress")
            return {"status": "skipped", "reason": "already_running"}

        self.is_running = True
        logger.info("Starting weekly retraining job")

        results = {}
        start_time = datetime.now()

        try:
            for model_type, model_path in self.model_paths.items():
                try:
                    logger.info(f"Processing {model_type}...")
                    result = await self._retrain_model(model_type, model_path)
                    results[model_type] = result
                    logger.info(f"{model_type} result: {result.get('status')}")

                except Exception as e:
                    logger.error(f"Error retraining {model_type}: {e}")
                    results[model_type] = {
                        "status": "error",
                        "error": str(e),
                    }

            # Record run time
            self.last_run[start_time.isoformat()] = results

            # Cleanup old versions
            for model_type in self.model_paths.keys():
                removed = self.registry.cleanup_old_versions(model_type, keep_count=5)
                if removed > 0:
                    logger.info(f"Cleaned up {removed} old versions for {model_type}")

        finally:
            self.is_running = False

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Weekly retraining completed in {duration:.2f}s")

        return {
            "status": "completed",
            "duration": duration,
            "results": results,
            "timestamp": start_time.isoformat(),
        }

    async def _retrain_model(self, model_type: str, model_path: str) -> Dict:
        """
        Retrain a single model type.

        Args:
            model_type: Type of model to retrain
            model_path: Path to current model

        Returns:
            Retraining result
        """
        # Collect feedback
        scan_type = "text" if model_type == "sms" else model_type
        feedback = await self.collector.fetch_approved_feedback(
            scan_type=scan_type
        )

        if len(feedback) < self.min_samples:
            return {
                "status": "skipped",
                "reason": "insufficient_feedback",
                "sample_count": len(feedback),
                "required": self.min_samples,
            }

        # Filter by quality
        feedback = filter_by_quality(feedback)

        if len(feedback) < self.min_samples:
            return {
                "status": "skipped",
                "reason": "insufficient_quality_feedback",
                "sample_count": len(feedback),
            }

        # Prepare training data
        texts, labels, sufficient = prepare_training_data(
            feedback,
            min_samples=self.min_samples,
            balance_classes=True,
        )

        if not sufficient:
            return {
                "status": "skipped",
                "reason": "preparation_failed",
            }

        # Initialize trainer
        if not os.path.exists(model_path):
            return {
                "status": "skipped",
                "reason": "model_not_found",
                "model_path": model_path,
            }

        trainer = IncrementalTrainer(
            model_path=model_path,
            model_type=model_type,
        )

        # Train
        result = trainer.train_on_feedback(texts, labels)

        if not result["success"]:
            return {
                "status": "failed",
                "reason": "metrics_degraded",
                "baseline_metrics": result["baseline_metrics"],
                "new_metrics": result["new_metrics"],
            }

        # Register and deploy new version
        await self.registry.register_version(
            model_type=model_type,
            version=result["version"],
            model_path=result["model_path"],
            metrics=result["new_metrics"],
            changelog=f"Retrained with {len(feedback)} feedback samples",
        )

        await self.registry.deploy_version(
            model_type=model_type,
            version=result["version"],
        )

        return {
            "status": "success",
            "version": result["version"],
            "sample_count": len(feedback),
            "metrics": result["new_metrics"],
            "improvement": {
                "recall": result["new_metrics"].get("eval_recall", 0) -
                         result["baseline_metrics"].get("eval_recall", 0),
                "f1": result["new_metrics"].get("eval_f1", 0) -
                     result["baseline_metrics"].get("eval_f1", 0),
            },
        }

    async def start_scheduler(self, interval_days: int = 7):
        """
        Start the scheduler loop.

        Args:
            interval_days: Days between retraining jobs
        """
        logger.info(f"Starting retraining scheduler (every {interval_days} days)")

        while True:
            try:
                # Run job
                await self.run_weekly_job()

                # Wait for next run
                wait_seconds = interval_days * 24 * 60 * 60
                logger.info(f"Next retraining in {interval_days} days")
                await asyncio.sleep(wait_seconds)

            except asyncio.CancelledError:
                logger.info("Scheduler cancelled")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                # Wait before retry
                await asyncio.sleep(60 * 60)  # 1 hour

    def get_last_run_status(self) -> Optional[Dict]:
        """Get status of the last run."""
        if not self.last_run:
            return None

        # Get most recent run
        latest_timestamp = max(self.last_run.keys())
        return {
            "timestamp": latest_timestamp,
            "results": self.last_run[latest_timestamp],
        }

    def get_schedule_info(self) -> Dict:
        """Get scheduler information."""
        return {
            "is_running": self.is_running,
            "last_run": self.get_last_run_status(),
            "model_types": list(self.model_paths.keys()),
            "min_samples": self.min_samples,
            "registry_stats": self.registry.get_registry_stats(),
        }


async def run_retraining_cli():
    """CLI entry point for manual retraining."""
    import argparse

    parser = argparse.ArgumentParser(description="Run model retraining")
    parser.add_argument("--backend", default="http://localhost:3000",
                       help="Backend API URL")
    parser.add_argument("--model-type", default="sms",
                       help="Model type to retrain")
    parser.add_argument("--model-path", required=True,
                       help="Path to current model")
    parser.add_argument("--min-samples", type=int, default=50,
                       help="Minimum samples required")
    parser.add_argument("--registry-path", default="./model_registry",
                       help="Path to model registry")
    args = parser.parse_args()

    scheduler = WeeklyRetrainingScheduler(
        backend_url=args.backend,
        model_paths={args.model_type: args.model_path},
        registry_path=args.registry_path,
        min_samples=args.min_samples,
    )

    result = await scheduler.run_weekly_job()
    print(f"Result: {result}")
    return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(run_retraining_cli())
