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

        return float(np.dot(embedding1, embedding2) / (norm1 * norm2))


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

    def save(self, path: str):
        """Save trained classifier to disk"""
        import joblib
        if self._is_trained and self.classifier:
            joblib.dump(self.classifier, path)
            logger.info(f"Classifier saved to {path}")
        else:
            logger.warning("No trained classifier to save")

    def load(self, path: str):
        """Load trained classifier from disk"""
        import joblib
        try:
            self.classifier = joblib.load(path)
            self._is_trained = True
            logger.info(f"Classifier loaded from {path}")
        except Exception as e:
            logger.warning(f"Failed to load classifier: {e}")
            self._is_trained = False
