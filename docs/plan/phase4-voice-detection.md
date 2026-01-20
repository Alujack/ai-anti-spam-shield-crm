# Phase 4: Voice Scam Real Detection

> **Duration:** 1 Week
> **Priority:** Medium-High
> **Dependencies:** Phase 1 (Infrastructure), Phase 2 (Model Upgrade)

---

## Overview

Upgrade voice scam detection from simple "transcription → text model" to true audio analysis using wav2vec2 embeddings and prosodic features.

### Current Limitation

```
Current Flow:
Audio → Google Speech API → Text → TF-IDF → Prediction
                ↑
       Only analyzes WHAT is said
       Ignores HOW it's said
```

### Target Architecture

```
Enhanced Flow:
Audio ─┬─→ Transcription → Text Analysis (40%)
       │
       ├─→ wav2vec2 → Audio Embeddings (35%)
       │
       └─→ Prosody Analysis (25%)
              ├── Speaking rate
              ├── Pause patterns
              └── Stress/pitch
```

### Goals

1. Implement wav2vec2 for audio embeddings
2. Build prosody analyzer for speaking patterns
3. Combine audio + text signals
4. Create `/predict-voice-v2` endpoint
5. Target: 85%+ recall on voice scams

---

## 1. Audio Embeddings with wav2vec2

### 1.1 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AUDIO EMBEDDING PIPELINE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Raw Audio (WAV/MP3)                                           │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────────┐                                           │
│   │ Preprocessing   │  Resample to 16kHz, normalize              │
│   └────────┬────────┘                                           │
│            │                                                     │
│            ▼                                                     │
│   ┌─────────────────┐                                           │
│   │   wav2vec2      │  facebook/wav2vec2-base                   │
│   │   Encoder       │  768-dim embeddings                       │
│   └────────┬────────┘                                           │
│            │                                                     │
│            ▼                                                     │
│   ┌─────────────────┐                                           │
│   │ Mean Pooling    │  Variable length → Fixed vector           │
│   └────────┬────────┘                                           │
│            │                                                     │
│            ▼                                                     │
│   768-dimensional audio representation                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Audio Embeddings Module

**Create:** `/ai-anti-spam-shield-service-model/app/audio/audio_embeddings.py`

```python
"""
Audio Embeddings using wav2vec2

Extracts semantic representations from audio that capture:
- Speech patterns
- Speaker characteristics
- Emotional cues
- Acoustic features
"""

import torch
import torchaudio
import numpy as np
from transformers import Wav2Vec2Model, Wav2Vec2Processor
from typing import Union, Tuple, Optional
import logging
import io
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioEmbedder:
    """
    Extract audio embeddings using wav2vec2

    wav2vec2 is a self-supervised model that learns speech representations.
    These embeddings capture rich acoustic and linguistic information.
    """

    def __init__(
        self,
        model_name: str = "facebook/wav2vec2-base",
        device: str = None,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        logger.info(f"Loading wav2vec2 model: {model_name}")
        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2Model.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

        # Target sample rate for wav2vec2
        self.target_sample_rate = 16000

        logger.info(f"Audio embedder initialized on {self.device}")

    def load_audio(
        self,
        audio_source: Union[str, bytes, Path],
        target_sr: int = 16000,
    ) -> Tuple[torch.Tensor, int]:
        """
        Load and preprocess audio from file or bytes

        Args:
            audio_source: Path to audio file or raw bytes
            target_sr: Target sample rate

        Returns:
            Tuple of (waveform tensor, sample rate)
        """
        # Load audio
        if isinstance(audio_source, bytes):
            audio_buffer = io.BytesIO(audio_source)
            waveform, sample_rate = torchaudio.load(audio_buffer)
        else:
            waveform, sample_rate = torchaudio.load(str(audio_source))

        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        # Resample if necessary
        if sample_rate != target_sr:
            resampler = torchaudio.transforms.Resample(
                orig_freq=sample_rate,
                new_freq=target_sr,
            )
            waveform = resampler(waveform)
            sample_rate = target_sr

        # Normalize
        waveform = waveform / (torch.max(torch.abs(waveform)) + 1e-6)

        return waveform.squeeze(), sample_rate

    def extract_embeddings(
        self,
        audio_source: Union[str, bytes, Path],
        pooling: str = "mean",
    ) -> np.ndarray:
        """
        Extract embeddings from audio

        Args:
            audio_source: Audio file path or bytes
            pooling: Pooling method ('mean', 'max', 'first', 'last')

        Returns:
            768-dimensional embedding vector
        """
        # Load and preprocess audio
        waveform, sample_rate = self.load_audio(audio_source)

        # Prepare input
        inputs = self.processor(
            waveform.numpy(),
            sampling_rate=sample_rate,
            return_tensors="pt",
            padding=True,
        )

        # Move to device
        input_values = inputs.input_values.to(self.device)

        # Extract features
        with torch.no_grad():
            outputs = self.model(input_values)
            hidden_states = outputs.last_hidden_state  # (1, seq_len, 768)

        # Pool to fixed-size vector
        if pooling == "mean":
            embeddings = hidden_states.mean(dim=1)
        elif pooling == "max":
            embeddings = hidden_states.max(dim=1).values
        elif pooling == "first":
            embeddings = hidden_states[:, 0, :]
        elif pooling == "last":
            embeddings = hidden_states[:, -1, :]
        else:
            raise ValueError(f"Unknown pooling method: {pooling}")

        return embeddings.cpu().numpy().squeeze()

    def extract_frame_embeddings(
        self,
        audio_source: Union[str, bytes, Path],
    ) -> np.ndarray:
        """
        Extract frame-level embeddings (before pooling)

        Useful for temporal analysis of audio patterns

        Returns:
            (seq_len, 768) array of frame embeddings
        """
        waveform, sample_rate = self.load_audio(audio_source)

        inputs = self.processor(
            waveform.numpy(),
            sampling_rate=sample_rate,
            return_tensors="pt",
            padding=True,
        )

        input_values = inputs.input_values.to(self.device)

        with torch.no_grad():
            outputs = self.model(input_values)
            hidden_states = outputs.last_hidden_state

        return hidden_states.cpu().numpy().squeeze()

    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
    ) -> float:
        """
        Compute cosine similarity between two embeddings
        """
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return np.dot(embedding1, embedding2) / (norm1 * norm2)


class AudioScamClassifier:
    """
    Classifier for detecting scam audio using embeddings

    Uses a simple MLP on top of wav2vec2 embeddings
    """

    def __init__(self, embedder: AudioEmbedder = None):
        self.embedder = embedder or AudioEmbedder()
        self.classifier = None  # Trained MLP model
        self._is_trained = False

    def train(self, audio_paths: list, labels: list):
        """
        Train the classifier on labeled audio samples

        This would be called during the training phase
        """
        from sklearn.neural_network import MLPClassifier

        # Extract embeddings for all samples
        embeddings = []
        for path in audio_paths:
            try:
                emb = self.embedder.extract_embeddings(path)
                embeddings.append(emb)
            except Exception as e:
                logger.warning(f"Failed to extract embeddings for {path}: {e}")
                embeddings.append(np.zeros(768))

        X = np.array(embeddings)
        y = np.array(labels)

        # Train simple classifier
        self.classifier = MLPClassifier(
            hidden_layer_sizes=(256, 64),
            activation='relu',
            max_iter=500,
            random_state=42,
        )
        self.classifier.fit(X, y)
        self._is_trained = True

        logger.info("Audio scam classifier trained")

    def predict(self, audio_source: Union[str, bytes]) -> dict:
        """
        Predict if audio is a scam

        Returns:
            Dictionary with prediction results
        """
        # Extract embeddings
        embeddings = self.embedder.extract_embeddings(audio_source)

        if self._is_trained and self.classifier:
            # Use trained classifier
            proba = self.classifier.predict_proba([embeddings])[0]
            is_scam = proba[1] > 0.5
            confidence = float(proba[1])
        else:
            # Fallback: Use embedding statistics
            # This is a placeholder until the model is trained
            logger.warning("Classifier not trained, using embedding heuristics")
            is_scam = False
            confidence = 0.0

        return {
            "is_scam": is_scam,
            "confidence": confidence,
            "embedding_norm": float(np.linalg.norm(embeddings)),
        }
```

---

## 2. Prosody Analyzer

### 2.1 Prosodic Features

```
┌─────────────────────────────────────────────────────────────────┐
│                     PROSODIC FEATURES                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Speaking Rate                                                   │
│  ├── Words per minute                                           │
│  ├── Syllables per second                                       │
│  └── Articulation rate                                          │
│                                                                  │
│  Pause Patterns                                                  │
│  ├── Number of pauses                                           │
│  ├── Average pause duration                                     │
│  ├── Pause ratio (pause time / total time)                      │
│  └── Hesitation markers                                         │
│                                                                  │
│  Pitch Features                                                  │
│  ├── Mean pitch (F0)                                            │
│  ├── Pitch range                                                │
│  ├── Pitch variability (std dev)                                │
│  └── Pitch contour patterns                                     │
│                                                                  │
│  Energy Features                                                 │
│  ├── Mean energy/volume                                         │
│  ├── Energy variability                                         │
│  └── Energy contour                                             │
│                                                                  │
│  Scam Indicators                                                 │
│  ├── Unusual urgency (fast speech)                              │
│  ├── Scripted feel (low variability)                            │
│  └── Stress patterns (emphasis on keywords)                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Prosody Analysis Module

**Create:** `/ai-anti-spam-shield-service-model/app/audio/prosody_analyzer.py`

```python
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
```

---

## 3. Combined Voice Scam Detector

### 3.1 Integration Module

**Create:** `/ai-anti-spam-shield-service-model/app/audio/voice_scam_detector.py`

```python
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
```

---

## 4. FastAPI Integration

### 4.1 New Endpoint

**Add to:** `/ai-anti-spam-shield-service-model/app/main.py`

```python
from app.audio.voice_scam_detector import VoiceScamDetector

# Initialize voice detector (add near top)
try:
    voice_detector = VoiceScamDetector(
        text_predictor=multi_predictor_v2.predictors.get('sms') if v2_available else None,
    )
    voice_v2_available = True
except Exception as e:
    logger.warning(f"Voice v2 not available: {e}")
    voice_v2_available = False


@app.post("/predict-voice-v2")
async def predict_voice_v2(audio: UploadFile = File(...)):
    """
    Enhanced voice scam detection with audio analysis

    Analyzes:
    - Transcribed text content
    - Audio embeddings (wav2vec2)
    - Prosodic features (speaking rate, pauses, stress)

    Returns comprehensive scam assessment
    """
    if not voice_v2_available:
        raise HTTPException(
            status_code=503,
            detail="Voice v2 not available. Use /predict-voice for v1."
        )

    try:
        # Read audio file
        audio_bytes = await audio.read()

        # Run detection
        result = voice_detector.detect(audio_bytes)

        return {
            "is_spam": result.is_scam,
            "confidence": result.confidence,
            "prediction": "scam" if result.is_scam else "legitimate",
            "threat_level": result.threat_level,
            "transcribed_text": result.transcript,
            "scores": {
                "text": result.text_score,
                "audio": result.audio_score,
                "prosody": result.prosody_score,
            },
            "prosody_analysis": result.prosody_features,
            "indicators": result.indicators,
            "warnings": result.warnings,
            "model_version": result.model_version,
        }

    except Exception as e:
        logger.error(f"Voice v2 prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-audio-prosody")
async def analyze_prosody(audio: UploadFile = File(...)):
    """
    Analyze prosodic features of audio

    Returns speaking rate, pause patterns, pitch features, etc.
    """
    try:
        audio_bytes = await audio.read()

        from app.audio.prosody_analyzer import ProsodyAnalyzer, get_scam_indicators

        analyzer = ProsodyAnalyzer()
        features = analyzer.analyze(audio_bytes)
        indicators = get_scam_indicators(features)

        return {
            "prosody_features": features.to_dict(),
            "scam_indicators": indicators,
        }

    except Exception as e:
        logger.error(f"Prosody analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 5. Dependencies

### 5.1 Update requirements.txt

**Add to:** `/ai-anti-spam-shield-service-model/requirements.txt`

```
# Audio Processing
librosa>=0.10.0
soundfile>=0.12.0
torchaudio>=2.2.0

# Speech Recognition (already present, verify version)
SpeechRecognition>=3.10.0
pydub>=0.25.0
```

---

## 6. Example Response

```json
{
  "is_spam": true,
  "confidence": 0.78,
  "prediction": "scam",
  "threat_level": "HIGH",
  "transcribed_text": "This is an urgent call from your bank. Your account has been compromised. Press 1 now to speak to a representative.",
  "scores": {
    "text": 0.92,
    "audio": 0.65,
    "prosody": 0.58
  },
  "prosody_analysis": {
    "duration_seconds": 8.5,
    "estimated_wpm": 185,
    "pause_ratio": 0.08,
    "pitch_std": 25.3,
    "indicators": {
      "speaking_rate": "fast",
      "variability": "low",
      "stress": "high"
    }
  },
  "indicators": [
    {
      "source": "text_analysis",
      "type": "content",
      "description": "Suspicious content detected in speech",
      "severity": "high"
    },
    {
      "source": "prosody",
      "type": "urgency",
      "description": "Fast speaking rate (185 WPM)",
      "severity": "medium"
    },
    {
      "source": "prosody",
      "type": "scripted",
      "description": "Low speech variability suggests scripted content",
      "severity": "medium"
    }
  ],
  "warnings": [
    "Be cautious - this call shows signs of a scam.",
    "The caller is speaking very fast. Legitimate callers will give you time to think.",
    "The speech sounds scripted. This is common in scam calls.",
    "Never share personal information over the phone with unsolicited callers."
  ],
  "model_version": "voice-v2.0.0"
}
```

---

## 7. Verification Checklist

- [ ] wav2vec2 embeddings extracted successfully
- [ ] Prosody features calculated correctly
- [ ] Combined scoring produces reasonable results
- [ ] `/predict-voice-v2` returns enhanced response
- [ ] Elder mode warnings are helpful and clear
- [ ] Processing time < 5 seconds for typical audio

---

## Next Steps

After completing Phase 4:
1. Collect labeled voice scam samples for training
2. Train audio classifier on embeddings
3. Proceed to [Phase 5: Continuous Learning](./phase5-continuous-learning.md)
