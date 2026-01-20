"""
Model Registry Module

Tracks model versions, metrics, and deployments.
Supports A/B testing and rollback capability.
"""

from .model_registry import ModelRegistry, ModelVersionInfo

__all__ = [
    'ModelRegistry',
    'ModelVersionInfo',
]
