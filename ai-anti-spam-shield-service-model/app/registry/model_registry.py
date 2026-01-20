"""
Model Registry

Tracks model versions, metrics, and deployments.
Supports A/B testing and rollback capability.
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelVersionInfo:
    """Model version metadata."""
    model_type: str
    version: str
    model_path: str
    metrics: Dict
    trained_at: str
    deployed_at: Optional[str] = None
    status: str = "testing"  # training, testing, deployed, rolled_back
    feedback_batch: Optional[str] = None
    changelog: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'ModelVersionInfo':
        return cls(**data)


class ModelRegistry:
    """
    Model versioning and deployment registry.

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
        """
        Initialize the model registry.

        Args:
            storage_path: Path to store model versions
            db_client: Optional database client for persistence
        """
        self.storage_path = storage_path
        self.db = db_client
        os.makedirs(storage_path, exist_ok=True)

        # Load registry state
        self.registry_file = os.path.join(storage_path, "registry.json")
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict:
        """Load registry from file."""
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {
            "versions": {},
            "deployed": {},
            "history": [],
        }

    def _save_registry(self):
        """Save registry to file."""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2, default=str)

    async def register_version(
        self,
        model_type: str,
        version: str,
        model_path: str,
        metrics: Dict,
        feedback_batch: str = None,
        changelog: str = None,
    ) -> ModelVersionInfo:
        """
        Register a new model version.

        Args:
            model_type: Type of model (sms, phishing, voice)
            version: Version string
            model_path: Path to model files
            metrics: Training/validation metrics
            feedback_batch: ID of feedback batch used for training
            changelog: Description of changes
        """
        version_key = f"{model_type}_{version}"

        # Copy model to registry storage
        registry_model_path = os.path.join(
            self.storage_path, "models", model_type, version
        )
        os.makedirs(registry_model_path, exist_ok=True)

        if os.path.isdir(model_path):
            shutil.copytree(model_path, registry_model_path, dirs_exist_ok=True)
        elif os.path.isfile(model_path):
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
            changelog=changelog,
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
        Deploy a model version to production.

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
        Rollback to a previous version.

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
        """Get currently deployed version."""
        version = self.registry["deployed"].get(model_type)
        if not version:
            return None

        info = self.registry["versions"].get(model_type, {}).get(version)
        if info:
            return ModelVersionInfo.from_dict(info)
        return None

    def get_deployed_model_path(self, model_type: str) -> Optional[str]:
        """Get path to currently deployed model."""
        version_info = self.get_deployed_version(model_type)
        if version_info:
            return version_info.model_path
        return None

    def get_all_versions(self, model_type: str) -> List[ModelVersionInfo]:
        """Get all versions for a model type."""
        versions = self.registry["versions"].get(model_type, {})
        return [ModelVersionInfo.from_dict(v) for v in versions.values()]

    def get_version_history(self, model_type: str = None) -> List[Dict]:
        """Get deployment history."""
        history = self.registry["history"]
        if model_type:
            history = [h for h in history if h["model_type"] == model_type]
        return history

    def get_version_info(self, model_type: str, version: str) -> Optional[ModelVersionInfo]:
        """Get info for a specific version."""
        info = self.registry["versions"].get(model_type, {}).get(version)
        if info:
            return ModelVersionInfo.from_dict(info)
        return None

    def list_model_types(self) -> List[str]:
        """List all registered model types."""
        return list(self.registry["versions"].keys())

    def get_registry_stats(self) -> Dict:
        """Get registry statistics."""
        stats = {
            "model_types": self.list_model_types(),
            "versions_by_type": {},
            "deployed": self.registry["deployed"],
            "total_versions": 0,
            "total_deployments": len(self.registry["history"]),
        }

        for model_type in self.list_model_types():
            versions = self.get_all_versions(model_type)
            stats["versions_by_type"][model_type] = len(versions)
            stats["total_versions"] += len(versions)

        return stats

    async def _save_to_db(self, info: ModelVersionInfo):
        """Save version info to database (if db client provided)."""
        # This would use Prisma or another DB client
        # Implementation depends on the specific database client
        pass

    def cleanup_old_versions(
        self,
        model_type: str,
        keep_count: int = 5,
    ) -> int:
        """
        Remove old versions to save disk space.

        Keeps the N most recent versions and the currently deployed version.

        Args:
            model_type: Type of model
            keep_count: Number of versions to keep

        Returns:
            Number of versions removed
        """
        versions = self.registry["versions"].get(model_type, {})
        if len(versions) <= keep_count:
            return 0

        deployed_version = self.registry["deployed"].get(model_type)

        # Sort by trained_at date
        sorted_versions = sorted(
            versions.items(),
            key=lambda x: x[1].get("trained_at", ""),
            reverse=True
        )

        # Keep the most recent and deployed versions
        to_keep = set()
        for i, (version, _) in enumerate(sorted_versions):
            if i < keep_count or version == deployed_version:
                to_keep.add(version)

        # Remove old versions
        removed = 0
        for version in list(versions.keys()):
            if version not in to_keep:
                info = versions[version]
                # Delete model files
                if os.path.exists(info["model_path"]):
                    shutil.rmtree(info["model_path"], ignore_errors=True)
                # Remove from registry
                del self.registry["versions"][model_type][version]
                removed += 1
                logger.info(f"Removed old version: {model_type}/{version}")

        self._save_registry()
        return removed
