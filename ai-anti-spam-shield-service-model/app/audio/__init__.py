"""
Audio Analysis Module for Voice Scam Detection

Phase 4: Real audio analysis using wav2vec2 embeddings and prosodic features.

Modules:
- audio_embeddings: wav2vec2-based audio embeddings
- prosody_analyzer: Prosodic feature extraction (speaking rate, pauses, pitch)
- voice_scam_detector: Combined multi-modal voice scam detection
"""

from .audio_embeddings import AudioEmbedder, AudioScamClassifier
from .prosody_analyzer import ProsodyAnalyzer, ProsodyFeatures, get_scam_indicators
from .voice_scam_detector import VoiceScamDetector, VoiceScamResult

__all__ = [
    "AudioEmbedder",
    "AudioScamClassifier",
    "ProsodyAnalyzer",
    "ProsodyFeatures",
    "get_scam_indicators",
    "VoiceScamDetector",
    "VoiceScamResult",
]
