"""
Combined Voice Scam Detector

Integrates:
- wav2vec2 audio embeddings
- Prosody analysis
- Text analysis (from transcription)
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
import logging

from .audio_embeddings import AudioEmbedder, AudioScamClassifier
from .prosody_analyzer import ProsodyAnalyzer, ProsodyFeatures, get_scam_indicators

logger = logging.getLogger(__name__)


@dataclass
class VoiceScamResult:
    """Complete voice scam detection result"""
    is_scam: bool
    confidence: float
    threat_level: str

    # Component scores
    text_score: float
    audio_score: float
    prosody_score: float

    # Detailed results
    transcript: Optional[str]
    prosody_features: Optional[Dict]
    indicators: List[Dict]

    # Elder mode warnings
    warnings: List[str]

    model_version: str

    def to_dict(self) -> Dict:
        return {
            "is_scam": self.is_scam,
            "confidence": round(self.confidence, 4),
            "threat_level": self.threat_level,
            "scores": {
                "text": round(self.text_score, 4),
                "audio": round(self.audio_score, 4),
                "prosody": round(self.prosody_score, 4),
            },
            "transcript": self.transcript,
            "prosody_features": self.prosody_features,
            "indicators": self.indicators,
            "warnings": self.warnings,
            "model_version": self.model_version,
        }


class VoiceScamDetector:
    """
    Multi-modal voice scam detection

    Combines:
    - Text analysis (40%) - What is said
    - Audio embeddings (35%) - How it sounds
    - Prosody analysis (25%) - Speaking patterns
    """

    # Weights for combining scores
    TEXT_WEIGHT = 0.40
    AUDIO_WEIGHT = 0.35
    PROSODY_WEIGHT = 0.25

    def __init__(
        self,
        text_predictor=None,
        use_gpu: bool = False,
    ):
        self.text_predictor = text_predictor
        self.embedder = AudioEmbedder(device="cuda" if use_gpu else "cpu")
        self.audio_classifier = AudioScamClassifier(self.embedder)
        self.prosody_analyzer = ProsodyAnalyzer()

        self.model_version = "voice-v2.0.0"

    def detect(
        self,
        audio_source: Union[str, bytes],
        transcript: Optional[str] = None,
    ) -> VoiceScamResult:
        """
        Detect if audio is a scam call

        Args:
            audio_source: Audio file path or bytes
            transcript: Pre-computed transcript (optional)

        Returns:
            VoiceScamResult with complete analysis
        """
        indicators = []
        warnings = []

        # 1. Transcription (if not provided)
        if transcript is None:
            transcript = self._transcribe(audio_source)

        # 2. Text analysis
        text_score = 0.0
        if transcript and self.text_predictor:
            try:
                text_result = self.text_predictor.predict(transcript)
                if hasattr(text_result, 'confidence'):
                    text_score = text_result.confidence
                elif isinstance(text_result, dict):
                    text_score = text_result.get('confidence', 0)

                if text_score > 0.5:
                    indicators.append({
                        'source': 'text_analysis',
                        'type': 'content',
                        'description': 'Suspicious content detected in speech',
                        'severity': 'high' if text_score > 0.8 else 'medium',
                    })
            except Exception as e:
                logger.warning(f"Text analysis failed: {e}")

        # 3. Audio embedding analysis
        audio_score = 0.0
        try:
            audio_result = self.audio_classifier.predict(audio_source)
            audio_score = audio_result.get('confidence', 0)

            if audio_score > 0.5:
                indicators.append({
                    'source': 'audio_analysis',
                    'type': 'audio_pattern',
                    'description': 'Audio patterns match known scam calls',
                    'severity': 'medium',
                })
        except Exception as e:
            logger.warning(f"Audio analysis failed: {e}")

        # 4. Prosody analysis
        prosody_score = 0.0
        prosody_features = None
        try:
            features = self.prosody_analyzer.analyze(audio_source, transcript)
            prosody_features = features.to_dict()

            # Get prosody-based indicators
            prosody_indicators = get_scam_indicators(features)
            indicators.extend([{**i, 'source': 'prosody'} for i in prosody_indicators])

            # Calculate prosody score based on indicators
            if features.speaking_rate_indicator in ['fast', 'very_fast']:
                prosody_score += 0.3
            if features.variability_indicator == 'low':
                prosody_score += 0.3
            if features.stress_indicator == 'high':
                prosody_score += 0.2

            prosody_score = min(1.0, prosody_score)

        except Exception as e:
            logger.warning(f"Prosody analysis failed: {e}")

        # 5. Combine scores
        combined_score = (
            text_score * self.TEXT_WEIGHT +
            audio_score * self.AUDIO_WEIGHT +
            prosody_score * self.PROSODY_WEIGHT
        )

        # Boost if multiple sources agree
        agreement_count = sum([
            text_score > 0.5,
            audio_score > 0.5,
            prosody_score > 0.3,
        ])

        if agreement_count >= 2:
            combined_score = min(1.0, combined_score * 1.2)

        # Determine threat level
        threat_level = self._get_threat_level(combined_score)

        # Generate warnings
        warnings = self._generate_warnings(
            combined_score, indicators, prosody_features
        )

        return VoiceScamResult(
            is_scam=combined_score > 0.5,
            confidence=combined_score,
            threat_level=threat_level,
            text_score=text_score,
            audio_score=audio_score,
            prosody_score=prosody_score,
            transcript=transcript,
            prosody_features=prosody_features,
            indicators=indicators,
            warnings=warnings,
            model_version=self.model_version,
        )

    def _transcribe(self, audio_source: Union[str, bytes]) -> Optional[str]:
        """Transcribe audio using speech recognition"""
        try:
            import speech_recognition as sr

            recognizer = sr.Recognizer()

            if isinstance(audio_source, bytes):
                # Save to temp file for speech_recognition
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                    f.write(audio_source)
                    temp_path = f.name

                with sr.AudioFile(temp_path) as source:
                    audio = recognizer.record(source)

                import os
                os.unlink(temp_path)
            else:
                with sr.AudioFile(str(audio_source)) as source:
                    audio = recognizer.record(source)

            # Use Google Speech Recognition
            transcript = recognizer.recognize_google(audio)
            return transcript

        except Exception as e:
            logger.warning(f"Transcription failed: {e}")
            return None

    def _get_threat_level(self, score: float) -> str:
        """Map score to threat level"""
        if score < 0.3:
            return "NONE"
        elif score < 0.5:
            return "LOW"
        elif score < 0.7:
            return "MEDIUM"
        elif score < 0.9:
            return "HIGH"
        else:
            return "CRITICAL"

    def _generate_warnings(
        self,
        score: float,
        indicators: List[Dict],
        prosody: Optional[Dict],
    ) -> List[str]:
        """Generate elder-friendly warnings"""
        if score < 0.3:
            return []

        warnings = []

        # General warnings
        if score > 0.5:
            warnings.append("Be cautious - this call shows signs of a scam.")

        # Based on prosody
        if prosody:
            rate = prosody.get('indicators', {}).get('speaking_rate')
            if rate in ['fast', 'very_fast']:
                warnings.append(
                    "The caller is speaking very fast. "
                    "Legitimate callers will give you time to think."
                )

            variability = prosody.get('indicators', {}).get('variability')
            if variability == 'low':
                warnings.append(
                    "The speech sounds scripted. "
                    "This is common in scam calls."
                )

        # Based on indicators
        for indicator in indicators:
            if indicator.get('severity') == 'high':
                if 'urgency' in indicator.get('type', ''):
                    warnings.append(
                        "The caller is creating urgency. "
                        "Take your time - real organizations won't pressure you."
                    )

        # Standard safety warnings
        if score > 0.7:
            warnings.extend([
                "Never share personal information over the phone with unsolicited callers.",
                "If in doubt, hang up and call the organization directly using an official number.",
            ])

        return warnings[:5]  # Limit to 5 warnings
