"""
Prosody Analyzer for Voice Scam Detection

Extracts prosodic features that indicate scam calls:
- Speaking rate (scammers often speak fast to create urgency)
- Pause patterns (scripted calls have unnatural pauses)
- Pitch variations (stress and emphasis patterns)
"""

import librosa
import numpy as np
from dataclasses import dataclass
from typing import Optional, Union, List, Tuple
import logging
import io
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ProsodyFeatures:
    """Prosodic feature set"""
    # Speaking rate
    duration_seconds: float
    estimated_wpm: float  # Words per minute (estimated from audio length)

    # Pause analysis
    num_pauses: int
    total_pause_duration: float
    avg_pause_duration: float
    pause_ratio: float

    # Pitch features
    pitch_mean: float
    pitch_std: float
    pitch_range: float
    pitch_median: float

    # Energy features
    energy_mean: float
    energy_std: float
    energy_range: float

    # Derived indicators
    speaking_rate_indicator: str  # slow, normal, fast, very_fast
    variability_indicator: str    # low (scripted), normal, high
    stress_indicator: str         # low, normal, high

    def to_dict(self) -> dict:
        return {
            "duration_seconds": round(self.duration_seconds, 2),
            "estimated_wpm": round(self.estimated_wpm, 1),
            "num_pauses": self.num_pauses,
            "total_pause_duration": round(self.total_pause_duration, 2),
            "avg_pause_duration": round(self.avg_pause_duration, 3),
            "pause_ratio": round(self.pause_ratio, 3),
            "pitch_mean": round(self.pitch_mean, 2),
            "pitch_std": round(self.pitch_std, 2),
            "pitch_range": round(self.pitch_range, 2),
            "energy_mean": round(self.energy_mean, 4),
            "energy_std": round(self.energy_std, 4),
            "indicators": {
                "speaking_rate": self.speaking_rate_indicator,
                "variability": self.variability_indicator,
                "stress": self.stress_indicator,
            },
        }


class ProsodyAnalyzer:
    """
    Analyze prosodic features of audio for scam detection

    Key scam indicators:
    1. Fast speaking rate (creates urgency)
    2. Low variability (scripted speech)
    3. Unusual pause patterns (reading from script)
    4. High pitch/stress on certain words
    """

    # Thresholds for indicators
    WPM_THRESHOLDS = {
        'slow': 100,
        'normal': 150,
        'fast': 180,
        'very_fast': 200,
    }

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def load_audio(
        self,
        audio_source: Union[str, bytes, Path],
    ) -> Tuple[np.ndarray, int]:
        """Load audio file or bytes"""
        if isinstance(audio_source, bytes):
            audio_buffer = io.BytesIO(audio_source)
            y, sr = librosa.load(audio_buffer, sr=self.sample_rate)
        else:
            y, sr = librosa.load(str(audio_source), sr=self.sample_rate)

        return y, sr

    def analyze(
        self,
        audio_source: Union[str, bytes, Path],
        transcript: Optional[str] = None,
    ) -> ProsodyFeatures:
        """
        Analyze prosodic features of audio

        Args:
            audio_source: Audio file or bytes
            transcript: Optional transcript for word-level analysis

        Returns:
            ProsodyFeatures object
        """
        # Load audio
        y, sr = self.load_audio(audio_source)

        # Basic metrics
        duration = len(y) / sr

        # Pause detection
        pause_metrics = self._analyze_pauses(y, sr)

        # Pitch analysis
        pitch_metrics = self._analyze_pitch(y, sr)

        # Energy analysis
        energy_metrics = self._analyze_energy(y, sr)

        # Estimate WPM (rough estimate based on audio characteristics)
        estimated_wpm = self._estimate_wpm(y, sr, transcript)

        # Derive indicators
        speaking_rate_indicator = self._get_rate_indicator(estimated_wpm)
        variability_indicator = self._get_variability_indicator(
            pitch_metrics['std'], energy_metrics['std']
        )
        stress_indicator = self._get_stress_indicator(pitch_metrics, energy_metrics)

        return ProsodyFeatures(
            duration_seconds=duration,
            estimated_wpm=estimated_wpm,
            num_pauses=pause_metrics['num_pauses'],
            total_pause_duration=pause_metrics['total_pause'],
            avg_pause_duration=pause_metrics['avg_pause'],
            pause_ratio=pause_metrics['pause_ratio'],
            pitch_mean=pitch_metrics['mean'],
            pitch_std=pitch_metrics['std'],
            pitch_range=pitch_metrics['range'],
            pitch_median=pitch_metrics['median'],
            energy_mean=energy_metrics['mean'],
            energy_std=energy_metrics['std'],
            energy_range=energy_metrics['range'],
            speaking_rate_indicator=speaking_rate_indicator,
            variability_indicator=variability_indicator,
            stress_indicator=stress_indicator,
        )

    def _analyze_pauses(self, y: np.ndarray, sr: int) -> dict:
        """Detect and analyze pauses in speech"""
        # Compute short-term energy
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)    # 10ms hop

        energy = librosa.feature.rms(
            y=y, frame_length=frame_length, hop_length=hop_length
        )[0]

        # Dynamic threshold based on energy distribution
        threshold = np.percentile(energy, 30)

        # Detect silent regions (pauses)
        is_silent = energy < threshold

        # Find pause segments
        pauses = []
        in_pause = False
        pause_start = 0

        for i, silent in enumerate(is_silent):
            if silent and not in_pause:
                in_pause = True
                pause_start = i
            elif not silent and in_pause:
                in_pause = False
                pause_duration = (i - pause_start) * hop_length / sr
                if pause_duration > 0.1:  # Only count pauses > 100ms
                    pauses.append(pause_duration)

        duration = len(y) / sr
        total_pause = sum(pauses)

        return {
            'num_pauses': len(pauses),
            'total_pause': total_pause,
            'avg_pause': total_pause / len(pauses) if pauses else 0,
            'pause_ratio': total_pause / duration if duration > 0 else 0,
        }

    def _analyze_pitch(self, y: np.ndarray, sr: int) -> dict:
        """Extract pitch (F0) features"""
        # Extract pitch using pYIN
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y, fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=sr,
        )

        # Filter out unvoiced frames
        f0_voiced = f0[voiced_flag]

        if len(f0_voiced) == 0:
            return {
                'mean': 0, 'std': 0, 'range': 0, 'median': 0
            }

        return {
            'mean': float(np.mean(f0_voiced)),
            'std': float(np.std(f0_voiced)),
            'range': float(np.max(f0_voiced) - np.min(f0_voiced)),
            'median': float(np.median(f0_voiced)),
        }

    def _analyze_energy(self, y: np.ndarray, sr: int) -> dict:
        """Extract energy features"""
        # RMS energy
        rms = librosa.feature.rms(y=y)[0]

        return {
            'mean': float(np.mean(rms)),
            'std': float(np.std(rms)),
            'range': float(np.max(rms) - np.min(rms)),
        }

    def _estimate_wpm(
        self,
        y: np.ndarray,
        sr: int,
        transcript: Optional[str] = None,
    ) -> float:
        """Estimate words per minute"""
        duration = len(y) / sr

        if duration < 1:
            return 0

        if transcript:
            # Use actual word count
            word_count = len(transcript.split())
            return (word_count / duration) * 60
        else:
            # Estimate based on syllable rate
            # Average English speech: ~4-5 syllables per second ≈ 150 WPM
            # Use energy envelope to estimate syllables

            # Get onset envelope
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            num_onsets = len(librosa.onset.onset_detect(onset_envelope=onset_env))

            # Rough estimate: 1.5 syllables per onset
            estimated_syllables = num_onsets * 1.5
            # Average 1.3 syllables per word
            estimated_words = estimated_syllables / 1.3

            return (estimated_words / duration) * 60

    def _get_rate_indicator(self, wpm: float) -> str:
        """Categorize speaking rate"""
        if wpm < self.WPM_THRESHOLDS['slow']:
            return 'slow'
        elif wpm < self.WPM_THRESHOLDS['normal']:
            return 'normal'
        elif wpm < self.WPM_THRESHOLDS['fast']:
            return 'fast'
        else:
            return 'very_fast'

    def _get_variability_indicator(
        self,
        pitch_std: float,
        energy_std: float,
    ) -> str:
        """
        Assess speech variability

        Low variability may indicate scripted speech
        """
        # Normalize (these thresholds are empirical)
        pitch_var_norm = pitch_std / 50  # Normalize to ~1.0 for normal speech
        energy_var_norm = energy_std / 0.05

        combined = (pitch_var_norm + energy_var_norm) / 2

        if combined < 0.5:
            return 'low'  # Possibly scripted
        elif combined < 1.5:
            return 'normal'
        else:
            return 'high'

    def _get_stress_indicator(
        self,
        pitch_metrics: dict,
        energy_metrics: dict,
    ) -> str:
        """Assess stress/emphasis level"""
        # High pitch range and energy range indicate emphasized speech
        pitch_range_norm = pitch_metrics.get('range', 0) / 100
        energy_range_norm = energy_metrics.get('range', 0) / 0.1

        combined = (pitch_range_norm + energy_range_norm) / 2

        if combined < 0.5:
            return 'low'
        elif combined < 1.5:
            return 'normal'
        else:
            return 'high'


def get_scam_indicators(features: ProsodyFeatures) -> List[dict]:
    """
    Identify potential scam indicators from prosody

    Returns list of warning indicators
    """
    indicators = []

    # Fast speaking (creates urgency)
    if features.speaking_rate_indicator in ['fast', 'very_fast']:
        indicators.append({
            'type': 'urgency',
            'description': f'Fast speaking rate ({features.estimated_wpm:.0f} WPM)',
            'severity': 'medium' if features.speaking_rate_indicator == 'fast' else 'high',
        })

    # Low variability (scripted)
    if features.variability_indicator == 'low':
        indicators.append({
            'type': 'scripted',
            'description': 'Low speech variability suggests scripted content',
            'severity': 'medium',
        })

    # High stress (pressure tactics)
    if features.stress_indicator == 'high':
        indicators.append({
            'type': 'pressure',
            'description': 'High emphasis/stress patterns detected',
            'severity': 'medium',
        })

    # Unusual pause patterns
    if features.pause_ratio < 0.1:
        indicators.append({
            'type': 'unnatural',
            'description': 'Very few pauses (may be reading quickly)',
            'severity': 'low',
        })
    elif features.pause_ratio > 0.4:
        indicators.append({
            'type': 'hesitation',
            'description': 'Excessive pauses (possible deception)',
            'severity': 'low',
        })

    return indicators
