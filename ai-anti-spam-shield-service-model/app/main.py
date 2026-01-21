from fastapi import FastAPI, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import uvicorn
from datetime import datetime
import os
import speech_recognition as sr
import tempfile
import io
from model.predictor import SpamPredictor, MultiModelPredictor
from core.logging_config import setup_logging

# Import V2 transformer-based predictor
try:
    from model.predictor_v2 import MultiModelPredictor as MultiModelPredictorV2
    HAS_V2_MODELS = True
except ImportError:
    HAS_V2_MODELS = False

# Import V3 pre-trained transformer predictor and ensemble
try:
    from model.predictor_v3 import MultiModelPredictorV3, get_predictor as get_predictor_v3
    from model.ensemble_predictor import EnsemblePredictor, get_ensemble_predictor
    HAS_V3_MODELS = True
except ImportError:
    HAS_V3_MODELS = False

# Import Phase 3: Phishing Intelligence Engine
try:
    from intel.domain_intel import DomainIntelligence
    from intel.screenshot_analyzer import get_analyzer
    from intel.risk_scorer import PhishingRiskScorer
    HAS_INTEL_ENGINE = True
except ImportError:
    HAS_INTEL_ENGINE = False

# Import Phase 4: Voice Scam Real Detection
try:
    from audio.voice_scam_detector import VoiceScamDetector, VoiceScamResult
    from audio.prosody_analyzer import ProsodyAnalyzer, get_scam_indicators
    HAS_VOICE_V2 = True
except ImportError:
    HAS_VOICE_V2 = False

# Initialize logger
logger = setup_logging('ai-anti-spam-shield.model-service')

# Import phishing detector
try:
    from detectors.phishing_detector import PhishingDetector
    HAS_PHISHING_DETECTOR = True
except ImportError:
    HAS_PHISHING_DETECTOR = False
    logger.warning("PhishingDetector not available")

# Initialize FastAPI app
app = FastAPI(
    title="AI Anti-Spam Shield API",
    description="Spam detection service using machine learning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize predictor
try:
    predictor = SpamPredictor(model_dir='model')
    print("Spam predictor initialized successfully!")
except Exception as e:
    print(f"Warning: Could not initialize predictor: {e}")
    print("Please train the model first using: python model/train.py")
    predictor = None

# Initialize phishing detector
phishing_detector = None
if HAS_PHISHING_DETECTOR:
    try:
        phishing_detector = PhishingDetector(model_dir='models')
        print("Phishing detector initialized successfully!")
    except Exception as e:
        print(f"Warning: Could not initialize phishing detector: {e}")
        phishing_detector = None

# Initialize multi-model predictor for specialized models
multi_predictor = None
try:
    multi_predictor = MultiModelPredictor(models_dir='model/trained_models')
    print(f"Multi-model predictor initialized with models: {list(multi_predictor.models.keys())}")
except Exception as e:
    print(f"Warning: Could not initialize multi-model predictor: {e}")
    print("Train separate models using: python model/train_separate_models.py --all")

# Initialize V2 transformer-based predictor (Phase 2)
multi_predictor_v2 = None
v2_available = False
if HAS_V2_MODELS:
    try:
        multi_predictor_v2 = MultiModelPredictorV2(model_dir='model/onnx_models')
        if multi_predictor_v2.is_loaded():
            v2_available = True
            print(f"V2 predictor initialized with models: {multi_predictor_v2.get_available_models()}")
        else:
            print("Warning: V2 predictor loaded but no models available")
    except Exception as e:
        print(f"Warning: Could not initialize V2 predictor: {e}")
        print("Train and export V2 models using: python -m model.transformer_trainer && python -m model.onnx_exporter")

# Initialize V3 pre-trained transformer predictor (Phase 6)
multi_predictor_v3 = None
ensemble_predictor = None
v3_available = False
if HAS_V3_MODELS:
    try:
        multi_predictor_v3 = get_predictor_v3(model_dir='model/trained_models_v3')
        ensemble_predictor = get_ensemble_predictor(model_dir='model/trained_models_v3')
        v3_available = True
        print("V3 pre-trained predictor initialized successfully!")
        print("  - Uses HuggingFace pre-trained models for better generalization")
        print("  - Ensemble predictor combines transformers + rules + URL analysis")
    except Exception as e:
        print(f"Warning: Could not initialize V3 predictor: {e}")
        print("V3 models will be downloaded automatically on first use")
        # Try to initialize with fallback to HuggingFace models
        try:
            multi_predictor_v3 = MultiModelPredictorV3(model_dir='model/trained_models_v3')
            v3_available = True
            print("V3 predictor initialized with HuggingFace fallback")
        except Exception as e2:
            print(f"V3 predictor unavailable: {e2}")

# Initialize Phase 3: Phishing Intelligence Engine
domain_intel = None
risk_scorer = None
intel_available = False
if HAS_INTEL_ENGINE:
    try:
        domain_intel = DomainIntelligence()
        risk_scorer = PhishingRiskScorer()
        intel_available = True
        print("Phishing Intelligence Engine initialized successfully!")
    except Exception as e:
        print(f"Warning: Could not initialize Phishing Intelligence Engine: {e}")

# Initialize Phase 4: Voice Scam Real Detection
voice_detector = None
voice_v2_available = False
if HAS_VOICE_V2:
    try:
        # Use V2 text predictor if available, otherwise fall back to multi_predictor
        text_pred = None
        if v2_available and multi_predictor_v2:
            text_pred = multi_predictor_v2.predictors.get('sms') if hasattr(multi_predictor_v2, 'predictors') else None

        voice_detector = VoiceScamDetector(
            text_predictor=text_pred,
            use_gpu=False,  # Set to True if GPU available
        )
        voice_v2_available = True
        print("Voice Scam Detector V2 initialized successfully!")
    except Exception as e:
        print(f"Warning: Could not initialize Voice Scam Detector V2: {e}")

# Request/Response Models


class PredictionRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000,
                         description="Text message to analyze")


class BatchPredictionRequest(BaseModel):
    messages: List[str] = Field(..., min_items=1, max_items=100,
                                description="List of messages to analyze")


class PredictionResponse(BaseModel):
    is_spam: bool
    prediction: str
    confidence: float
    probability: float
    probabilities: dict
    details: Optional[dict] = None
    timestamp: str


class VoicePredictionResponse(BaseModel):
    transcribed_text: str
    is_spam: bool
    prediction: str
    confidence: float
    probability: float
    probabilities: dict
    details: Optional[dict] = None
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    timestamp: str
    version: str


# Phishing Detection Models
class PhishingRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000,
                      description="Text message or URL to analyze for phishing")
    scan_type: Literal['email', 'sms', 'url', 'auto'] = Field(
        default='auto',
        description="Type of scan: email, sms, url, or auto-detect"
    )


class URLScanRequest(BaseModel):
    url: str = Field(..., min_length=5, max_length=2000,
                     description="URL to analyze for phishing")


class BatchPhishingRequest(BaseModel):
    items: List[str] = Field(..., min_items=1, max_items=100,
                             description="List of texts/URLs to analyze")
    scan_type: Literal['email', 'sms', 'url', 'auto'] = Field(
        default='auto',
        description="Type of scan for all items"
    )


class URLAnalysisResponse(BaseModel):
    url: str
    is_suspicious: bool
    score: float
    reasons: List[str]


class BrandImpersonationResponse(BaseModel):
    detected: bool
    brand: Optional[str]
    similarity_score: float


class PhishingResponse(BaseModel):
    is_phishing: bool
    confidence: float
    phishing_type: str
    threat_level: str
    indicators: List[str]
    urls_analyzed: List[dict]
    brand_impersonation: Optional[dict]
    recommendation: str
    details: dict
    timestamp: str


# ============================================
# SPECIALIZED MODEL REQUEST/RESPONSE MODELS
# ============================================

class SMSPredictionRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000,
                         description="SMS message to analyze")


class VoiceScamRequest(BaseModel):
    dialogue: str = Field(..., min_length=1, max_length=50000,
                          description="Transcribed voice call dialogue to analyze")


class PhishingV2Request(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000,
                      description="Text, email, or URL to analyze for phishing")


class AutoDetectRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000,
                      description="Any text content - model will auto-detect type")


class SpecializedPredictionResponse(BaseModel):
    is_threat: bool
    prediction: str
    confidence: float
    threat_probability: float
    probabilities: dict
    model_type: str
    threshold: float
    details: Optional[dict] = None
    timestamp: str


class BatchSpecializedRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1, max_items=100,
                             description="List of texts to analyze")
    model_type: Literal['sms', 'voice', 'phishing', 'auto'] = Field(
        default='auto',
        description="Model to use: sms, voice, phishing, or auto-detect"
    )


# V2 Request/Response Models (Phase 2 - Transformer-based)
class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000,
                         description="Text message to analyze")


class V2PredictionResponse(BaseModel):
    is_spam: bool
    confidence: float
    prediction: str
    risk_level: str
    category: Optional[str]
    explanation: str
    indicators: List[dict]
    model_version: str


class V2ElderModeResponse(V2PredictionResponse):
    elder_warnings: List[str]


# Phase 3: Deep URL Analysis Request/Response Models
class DeepURLRequest(BaseModel):
    url: str = Field(..., min_length=5, max_length=2000,
                     description="URL to analyze for phishing")
    include_screenshot: bool = Field(
        default=False,
        description="Whether to capture and analyze screenshot (slower)"
    )
    include_domain_intel: bool = Field(
        default=True,
        description="Whether to include domain intelligence"
    )


class DomainIntelRequest(BaseModel):
    domain: str = Field(..., min_length=3, max_length=255,
                        description="Domain to analyze")


class RiskIndicator(BaseModel):
    source: str
    description: str
    severity: str
    score: float


class RiskAssessmentResponse(BaseModel):
    total_score: float
    threat_level: str
    text_score: float
    url_score: float
    domain_score: float
    visual_score: float
    indicators: List[dict]
    recommendation: str
    confidence: float


class DeepURLResponse(BaseModel):
    url: str
    is_phishing: bool
    threat_level: str
    confidence: float
    risk_score: float
    recommendation: str
    details: dict
    timestamp: str


# Phase 4: Voice Scam V2 Response Models
class VoiceScamScores(BaseModel):
    text: float
    audio: float
    prosody: float


class ProsodyIndicators(BaseModel):
    speaking_rate: str
    variability: str
    stress: str


class VoiceV2PredictionResponse(BaseModel):
    is_spam: bool
    confidence: float
    prediction: str
    threat_level: str
    transcribed_text: Optional[str]
    scores: VoiceScamScores
    prosody_analysis: Optional[dict]
    indicators: List[dict]
    warnings: List[str]
    model_version: str


class ProsodyAnalysisResponse(BaseModel):
    prosody_features: dict
    scam_indicators: List[dict]


# Routes


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "AI Anti-Spam Shield API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "predict_voice": "/predict-voice",
            "batch_predict": "/batch-predict",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if predictor is not None else "model_not_loaded",
        "model_loaded": predictor is not None,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(request: PredictionRequest):
    """
    Predict if a message is spam or not

    - **message**: The text message to analyze

    Returns spam prediction with confidence score
    """
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Please train the model first."
        )

    try:
        result = predictor.predict(request.message)
        result['timestamp'] = datetime.utcnow().isoformat()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}"
        )


@app.post("/batch-predict", tags=["Prediction"])
async def batch_predict(request: BatchPredictionRequest):
    """
    Predict multiple messages at once

    - **messages**: List of text messages to analyze

    Returns list of predictions
    """
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Please train the model first."
        )

    try:
        results = predictor.batch_predict(request.messages)
        return {
            "predictions": results,
            "count": len(results),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction error: {str(e)}"
        )


@app.post("/predict-voice", response_model=VoicePredictionResponse, tags=["Prediction"])
async def predict_voice(audio: UploadFile = File(...)):
    """
    Predict if a voice message is spam or not

    - **audio**: Audio file (WAV, MP3, OGG, FLAC, M4A, AAC, WEBM)

    Transcribes audio to text, then analyzes for spam
    """
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Please train the model first."
        )

    temp_audio_path = None
    wav_path = None

    try:
        # Read audio file
        audio_data = await audio.read()
        file_ext = os.path.splitext(audio.filename)[1].lower() if audio.filename else '.wav'

        # Create temporary file with original format
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_audio:
            temp_audio.write(audio_data)
            temp_audio_path = temp_audio.name

        # Formats that need conversion (speech_recognition only supports WAV, AIFF, FLAC natively)
        formats_needing_conversion = ['.m4a', '.aac', '.mp3', '.ogg', '.webm', '.mp4', '.opus']

        if file_ext in formats_needing_conversion:
            # Try to convert using pydub (requires ffmpeg)
            try:
                from pydub import AudioSegment

                # Detect format
                format_map = {
                    '.m4a': 'mp4',
                    '.aac': 'aac',
                    '.mp3': 'mp3',
                    '.ogg': 'ogg',
                    '.webm': 'webm',
                    '.mp4': 'mp4',
                    '.opus': 'opus'
                }
                input_format = format_map.get(file_ext, file_ext[1:])

                # Load and convert to WAV
                audio_segment = AudioSegment.from_file(temp_audio_path, format=input_format)

                # Create WAV file
                wav_path = temp_audio_path + '.wav'
                audio_segment.export(wav_path, format='wav')

                # Use the converted WAV file
                audio_file_to_use = wav_path
                logger.info(f"Converted {file_ext} to WAV for processing")

            except ImportError:
                logger.warning("pydub not installed. Install with: pip install pydub")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Audio format {file_ext} requires conversion. Please upload WAV or FLAC format, or install pydub and ffmpeg on the server."
                )
            except Exception as conv_error:
                logger.error(f"Audio conversion failed: {conv_error}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to convert audio format {file_ext}. Please try WAV or FLAC format. Error: {str(conv_error)}"
                )
        else:
            audio_file_to_use = temp_audio_path

        # Initialize speech recognizer
        recognizer = sr.Recognizer()

        # Load audio file
        try:
            with sr.AudioFile(audio_file_to_use) as source:
                audio_content = recognizer.record(source)
        except Exception as audio_error:
            logger.error(f"Failed to load audio file: {audio_error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to process audio file. Please ensure it's a valid audio format. Error: {str(audio_error)}"
            ) from None

        # Transcribe audio to text using Google Speech Recognition
        try:
            transcribed_text = recognizer.recognize_google(audio_content)
        except sr.UnknownValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not understand audio. Please speak clearly."
            ) from None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Speech recognition service is unavailable. Please try again later."
            ) from None

        # Analyze transcribed text for spam
        result = predictor.predict(transcribed_text)
        result['transcribed_text'] = transcribed_text
        result['timestamp'] = datetime.utcnow().isoformat()

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice prediction error: {str(e)}"
        )
    finally:
        # Clean up temporary files
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)
        if wav_path and os.path.exists(wav_path):
            os.unlink(wav_path)


@app.get("/stats", tags=["Statistics"])
async def get_stats():
    """Get model statistics"""
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )

    return {
        "model_type": predictor.model.__class__.__name__,
        "features_count": predictor.vectorizer.get_feature_names_out().shape[0] if hasattr(predictor.vectorizer, 'get_feature_names_out') else "N/A",
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================
# PHISHING DETECTION ENDPOINTS
# ============================================

@app.post("/predict-phishing", response_model=PhishingResponse, tags=["Phishing"])
async def predict_phishing(request: PhishingRequest):
    """
    Detect phishing in text messages or URLs

    - **text**: The text message or URL to analyze
    - **scan_type**: Type of content (email, sms, url, or auto-detect)

    Returns comprehensive phishing analysis with:
    - Phishing classification and confidence
    - Threat level (CRITICAL, HIGH, MEDIUM, LOW, NONE)
    - Detected indicators
    - URL analysis results
    - Brand impersonation detection
    - Actionable recommendations
    """
    if phishing_detector is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Phishing detector not available"
        )

    try:
        result = phishing_detector.detect(request.text, request.scan_type)
        response = result.to_dict()
        response['timestamp'] = datetime.utcnow().isoformat()
        return response
    except Exception as e:
        logger.error(f"Phishing detection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Phishing detection error: {str(e)}"
        )


@app.post("/scan-url", tags=["Phishing"])
async def scan_url(request: URLScanRequest):
    """
    Scan a specific URL for phishing indicators

    - **url**: The URL to analyze

    Returns URL-specific analysis including:
    - Suspicious indicators
    - TLD analysis
    - Brand impersonation check
    - Obfuscation detection
    """
    if phishing_detector is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Phishing detector not available"
        )

    try:
        result = phishing_detector.detect(request.url, scan_type='url')
        response = result.to_dict()
        response['timestamp'] = datetime.utcnow().isoformat()
        return response
    except Exception as e:
        logger.error(f"URL scan error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"URL scan error: {str(e)}"
        )


@app.post("/batch-phishing", tags=["Phishing"])
async def batch_phishing_scan(request: BatchPhishingRequest):
    """
    Scan multiple texts/URLs for phishing at once

    - **items**: List of texts or URLs to analyze (max 100)
    - **scan_type**: Type of content for all items

    Returns list of phishing analysis results
    """
    if phishing_detector is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Phishing detector not available"
        )

    try:
        results = []
        for item in request.items:
            result = phishing_detector.detect(item, request.scan_type)
            result_dict = result.to_dict()
            result_dict['input'] = item[:100] + '...' if len(item) > 100 else item
            results.append(result_dict)

        # Summary statistics
        phishing_count = sum(1 for r in results if r['is_phishing'])
        threat_levels = {}
        for r in results:
            level = r['threat_level']
            threat_levels[level] = threat_levels.get(level, 0) + 1

        return {
            "results": results,
            "summary": {
                "total": len(results),
                "phishing_detected": phishing_count,
                "safe": len(results) - phishing_count,
                "threat_levels": threat_levels
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Batch phishing scan error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch phishing scan error: {str(e)}"
        )


@app.get("/phishing-health", tags=["Phishing"])
async def phishing_health():
    """Check phishing detector health status"""
    return {
        "status": "healthy" if phishing_detector is not None else "unavailable",
        "detector_loaded": phishing_detector is not None,
        "ml_enabled": phishing_detector.ml_model is not None if phishing_detector else False,
        "transformer_enabled": phishing_detector.transformer_model is not None if phishing_detector else False,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================
# SPECIALIZED MODEL ENDPOINTS
# ============================================

@app.post("/predict-sms", response_model=SpecializedPredictionResponse, tags=["Specialized Models"])
async def predict_sms(request: SMSPredictionRequest):
    """
    Detect SMS spam using specialized SMS model

    - **message**: The SMS text message to analyze

    Uses model trained specifically on SMS spam dataset (Deysi/spam-detection-dataset)
    """
    if multi_predictor is None or not multi_predictor.is_model_loaded('sms'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SMS model not loaded. Train using: python model/train_separate_models.py --model sms"
        )

    try:
        result = multi_predictor.predict_sms(request.message)
        result['timestamp'] = datetime.utcnow().isoformat()
        return result
    except Exception as e:
        logger.error(f"SMS prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMS prediction error: {str(e)}"
        )


@app.post("/predict-voice-scam", response_model=SpecializedPredictionResponse, tags=["Specialized Models"])
async def predict_voice_scam(request: VoiceScamRequest):
    """
    Detect voice call scams using specialized voice model

    - **dialogue**: Transcribed voice call dialogue to analyze

    Uses model trained specifically on scam dialogue dataset (BothBosu/scam-dialogue)
    """
    if multi_predictor is None or not multi_predictor.is_model_loaded('voice'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice model not loaded. Train using: python model/train_separate_models.py --model voice"
        )

    try:
        result = multi_predictor.predict_voice(request.dialogue)
        result['timestamp'] = datetime.utcnow().isoformat()
        return result
    except Exception as e:
        logger.error(f"Voice scam prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice scam prediction error: {str(e)}"
        )


@app.post("/predict-phishing-v2", response_model=SpecializedPredictionResponse, tags=["Specialized Models"])
async def predict_phishing_v2(request: PhishingV2Request):
    """
    Detect phishing using specialized phishing model (v2)

    - **text**: Text, email content, or URL to analyze

    Uses model trained specifically on phishing dataset (ealvaradob/phishing-dataset combined_reduced)
    """
    if multi_predictor is None or not multi_predictor.is_model_loaded('phishing'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Phishing model not loaded. Train using: python model/train_separate_models.py --model phishing"
        )

    try:
        result = multi_predictor.predict_phishing(request.text)
        result['timestamp'] = datetime.utcnow().isoformat()
        return result
    except Exception as e:
        logger.error(f"Phishing v2 prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Phishing v2 prediction error: {str(e)}"
        )


@app.post("/predict-auto", response_model=SpecializedPredictionResponse, tags=["Specialized Models"])
async def predict_auto(request: AutoDetectRequest):
    """
    Auto-detect content type and predict using appropriate specialized model

    - **text**: Any text content (SMS, email, URL, voice dialogue)

    Automatically detects content type and selects the best model:
    - URLs/emails -> Phishing model
    - Dialogue format (caller/receiver) -> Voice scam model
    - Short messages -> SMS spam model
    """
    if multi_predictor is None or len(multi_predictor.models) == 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No specialized models loaded. Train using: python model/train_separate_models.py --all"
        )

    try:
        result = multi_predictor.predict_auto(request.text)
        result['timestamp'] = datetime.utcnow().isoformat()
        return result
    except Exception as e:
        logger.error(f"Auto prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auto prediction error: {str(e)}"
        )


@app.post("/batch-specialized", tags=["Specialized Models"])
async def batch_specialized_predict(request: BatchSpecializedRequest):
    """
    Batch prediction using specialized models

    - **texts**: List of texts to analyze (max 100)
    - **model_type**: Model to use (sms, voice, phishing, or auto)

    Returns list of predictions with summary statistics
    """
    if multi_predictor is None or len(multi_predictor.models) == 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No specialized models loaded. Train using: python model/train_separate_models.py --all"
        )

    try:
        results = multi_predictor.batch_predict(request.texts, model_type=request.model_type)

        # Add timestamps
        for r in results:
            r['timestamp'] = datetime.utcnow().isoformat()

        # Summary statistics
        threat_count = sum(1 for r in results if r.get('is_threat', False))
        model_usage = {}
        for r in results:
            model = r.get('model_type', 'unknown')
            model_usage[model] = model_usage.get(model, 0) + 1

        return {
            "predictions": results,
            "summary": {
                "total": len(results),
                "threats_detected": threat_count,
                "safe": len(results) - threat_count,
                "models_used": model_usage
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Batch specialized prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction error: {str(e)}"
        )


@app.get("/model-stats", tags=["Specialized Models"])
async def get_model_stats():
    """
    Get statistics and information about all loaded specialized models

    Returns:
    - List of loaded models
    - Training metrics for each model
    - Algorithm used
    - Confidence thresholds
    """
    if multi_predictor is None:
        return {
            "status": "unavailable",
            "loaded_models": [],
            "message": "No specialized models loaded. Train using: python model/train_separate_models.py --all",
            "timestamp": datetime.utcnow().isoformat()
        }

    model_info = multi_predictor.get_model_info()
    model_info['status'] = 'ready' if model_info['loaded_models'] else 'no_models'
    model_info['timestamp'] = datetime.utcnow().isoformat()

    return model_info


@app.get("/specialized-health", tags=["Specialized Models"])
async def specialized_health():
    """Check health status of all specialized models"""
    return {
        "status": "healthy" if multi_predictor and len(multi_predictor.models) > 0 else "unavailable",
        "predictor_initialized": multi_predictor is not None,
        "models_loaded": list(multi_predictor.models.keys()) if multi_predictor else [],
        "models_count": len(multi_predictor.models) if multi_predictor else 0,
        "available_endpoints": {
            "sms": multi_predictor.is_model_loaded('sms') if multi_predictor else False,
            "voice": multi_predictor.is_model_loaded('voice') if multi_predictor else False,
            "phishing": multi_predictor.is_model_loaded('phishing') if multi_predictor else False
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================
# V2 TRANSFORMER-BASED ENDPOINTS (Phase 2)
# ============================================

@app.post("/predict-v2", response_model=V2PredictionResponse, tags=["V2 Models"])
async def predict_v2(request: MessageRequest):
    """
    Predict spam using transformer model (v2)

    Returns enhanced response with:
    - Risk level (NONE, LOW, MEDIUM, HIGH, CRITICAL)
    - Scam category detection
    - Human-readable explanation
    - Indicator breakdown
    """
    if not v2_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="V2 model not available. Use /predict for v1."
        )

    try:
        result = multi_predictor_v2.predict_sms(request.message)
        return result
    except Exception as e:
        logger.error(f"V2 prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/predict-v2/elder-mode", response_model=V2ElderModeResponse, tags=["V2 Models"])
async def predict_v2_elder(request: MessageRequest):
    """
    Predict with elder-friendly warnings

    Includes additional safety warnings designed for users
    who may be more vulnerable to scams
    """
    if not v2_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="V2 model not available."
        )

    try:
        result = multi_predictor_v2.predict_with_elder_mode(
            request.message,
            model_type="sms"
        )
        return result
    except Exception as e:
        logger.error(f"V2 elder mode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/predict-phishing-v2-transformer", tags=["V2 Models"])
async def predict_phishing_v2_transformer(request: PhishingRequest):
    """
    Predict phishing using transformer model (v2)

    Uses DistilBERT-based model for improved accuracy
    """
    if not v2_available or "phishing" not in multi_predictor_v2.get_available_models():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="V2 phishing model not available."
        )

    try:
        result = multi_predictor_v2.predict_phishing(request.text)
        return {
            **result,
            "is_phishing": result["is_spam"],
            "phishing_type": result.get("category", "NONE"),
            "threat_level": result["risk_level"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"V2 phishing prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/model/versions", tags=["V2 Models"])
async def get_model_versions():
    """Get available model versions and their status"""
    versions = {
        "v1": {
            "sms": "TF-IDF + Logistic Regression",
            "phishing": "TF-IDF + Random Forest",
            "voice": "TF-IDF + Logistic Regression",
            "status": "available" if multi_predictor and len(multi_predictor.models) > 0 else "unavailable",
            "loaded_models": list(multi_predictor.models.keys()) if multi_predictor else []
        }
    }

    if v2_available:
        versions["v2"] = {
            "sms": "DistilBERT (ONNX)",
            "phishing": "DistilBERT (ONNX)",
            "status": "available",
            "loaded_models": multi_predictor_v2.get_available_models()
        }
    else:
        versions["v2"] = {
            "status": "unavailable",
            "message": "Train and export V2 models to enable"
        }

    return {
        "versions": versions,
        "recommended": "v2" if v2_available else "v1",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v2-health", tags=["V2 Models"])
async def v2_health():
    """Check health status of V2 transformer models"""
    return {
        "status": "healthy" if v2_available else "unavailable",
        "v2_available": v2_available,
        "models_loaded": multi_predictor_v2.get_available_models() if v2_available else [],
        "onnx_runtime": "enabled",
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================
# PHASE 3: PHISHING INTELLIGENCE ENGINE
# ============================================

@app.post("/analyze-url-deep", response_model=DeepURLResponse, tags=["Phishing Intelligence"])
async def analyze_url_deep(request: DeepURLRequest):
    """
    Deep URL analysis with domain intelligence and visual analysis

    Returns comprehensive phishing risk assessment including:
    - Domain age and registration info
    - SSL certificate analysis
    - ASN reputation
    - Visual analysis (optional)
    - Combined risk score

    This is the most thorough analysis available for URL-based phishing detection.
    """
    if not intel_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Phishing Intelligence Engine not available. Install required dependencies."
        )

    try:
        results = {}

        # Text/ML analysis (using existing predictor)
        text_result = None
        if v2_available:
            try:
                text_result = multi_predictor_v2.predict_phishing(request.url)
            except Exception as e:
                logger.warning(f"V2 text analysis failed: {e}")
                text_result = {"confidence": 0, "is_phishing": False}
        else:
            text_result = {"confidence": 0, "is_phishing": False}

        results["text_analysis"] = text_result

        # Domain intelligence
        domain_result = None
        if request.include_domain_intel:
            domain_result = await domain_intel.analyze(request.url)
            results["domain_intelligence"] = domain_result.to_dict()

        # Visual analysis
        visual_result = None
        if request.include_screenshot:
            try:
                analyzer = await get_analyzer()
                visual_result = await analyzer.analyze(request.url)
                results["visual_analysis"] = visual_result.to_dict()
            except Exception as e:
                logger.warning(f"Visual analysis failed: {e}")
                results["visual_analysis"] = {"error": str(e)}

        # Prepare text result dict for risk scorer
        text_result_dict = None
        if text_result:
            if hasattr(text_result, 'to_dict'):
                text_result_dict = text_result.to_dict()
            elif isinstance(text_result, dict):
                text_result_dict = text_result
                # Normalize keys
                if 'is_spam' in text_result_dict and 'is_phishing' not in text_result_dict:
                    text_result_dict['is_phishing'] = text_result_dict['is_spam']

        # Combined risk score
        risk_result = risk_scorer.calculate_risk(
            url=request.url,
            text_result=text_result_dict,
            domain_intel=domain_result.to_dict() if domain_result else None,
            visual_result=visual_result.to_dict() if visual_result else None,
        )

        results["risk_assessment"] = risk_result.to_dict()

        return {
            "url": request.url,
            "is_phishing": risk_result.threat_level.value in ["HIGH", "CRITICAL"],
            "threat_level": risk_result.threat_level.value,
            "confidence": risk_result.confidence,
            "risk_score": risk_result.total_score,
            "recommendation": risk_result.recommendation,
            "details": results,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Deep URL analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/intel/domain/{domain}", tags=["Phishing Intelligence"])
async def get_domain_intel(domain: str):
    """
    Get domain intelligence for a specific domain

    Returns:
    - Domain age (WHOIS data)
    - SSL certificate information
    - ASN and IP reputation
    - DNS configuration (MX, SPF, DMARC)
    - Risk indicators
    """
    if not intel_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Phishing Intelligence Engine not available"
        )

    try:
        result = await domain_intel.analyze(f"https://{domain}")
        response = result.to_dict()
        response["timestamp"] = datetime.utcnow().isoformat()
        return response
    except Exception as e:
        logger.error(f"Domain intel failed for {domain}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/intel/screenshot", tags=["Phishing Intelligence"])
async def analyze_screenshot(request: DeepURLRequest):
    """
    Capture and analyze screenshot of a URL

    Returns:
    - Screenshot (base64 encoded if requested)
    - Login form detection
    - Password field detection
    - Brand impersonation indicators
    - Visual risk score
    """
    if not intel_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Phishing Intelligence Engine not available"
        )

    try:
        analyzer = await get_analyzer()
        result = await analyzer.analyze(
            request.url,
            capture_screenshot=request.include_screenshot
        )
        response = result.to_dict()
        response["url"] = request.url
        response["timestamp"] = datetime.utcnow().isoformat()
        return response
    except Exception as e:
        logger.error(f"Screenshot analysis failed for {request.url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/intel/risk-score", tags=["Phishing Intelligence"])
async def calculate_risk_score(
    url: str,
    text_confidence: float = 0,
    domain_risk: float = 0,
    visual_risk: float = 0,
):
    """
    Calculate combined phishing risk score

    Manually provide component scores to get a combined risk assessment.
    Useful for testing or when you have pre-computed component scores.
    """
    if not intel_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Phishing Intelligence Engine not available"
        )

    try:
        text_result = {"confidence": text_confidence, "is_phishing": text_confidence > 0.5}
        domain_intel_result = {"risk_score": domain_risk, "risk_indicators": []}
        visual_result = {"visual_risk_score": visual_risk}

        result = risk_scorer.calculate_risk(
            url=url,
            text_result=text_result,
            domain_intel=domain_intel_result,
            visual_result=visual_result,
        )

        response = result.to_dict()
        response["url"] = url
        response["timestamp"] = datetime.utcnow().isoformat()
        return response
    except Exception as e:
        logger.error(f"Risk score calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/intel-health", tags=["Phishing Intelligence"])
async def intel_health():
    """Check health status of Phishing Intelligence Engine"""
    return {
        "status": "healthy" if intel_available else "unavailable",
        "intel_available": intel_available,
        "components": {
            "domain_intelligence": domain_intel is not None,
            "risk_scorer": risk_scorer is not None,
            "screenshot_analyzer": HAS_INTEL_ENGINE,
        },
        "v2_models_available": v2_available,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================
# PHASE 4: VOICE SCAM REAL DETECTION (V2)
# ============================================

@app.post("/predict-voice-v2", response_model=VoiceV2PredictionResponse, tags=["Voice V2"])
async def predict_voice_v2(audio: UploadFile = File(...)):
    """
    Enhanced voice scam detection with audio analysis (V2)

    Analyzes:
    - Transcribed text content (40% weight)
    - Audio embeddings using wav2vec2 (35% weight)
    - Prosodic features: speaking rate, pauses, stress (25% weight)

    Returns comprehensive scam assessment with:
    - Combined confidence score
    - Threat level (NONE, LOW, MEDIUM, HIGH, CRITICAL)
    - Prosody analysis (speaking patterns)
    - Scam indicators from multiple sources
    - Elder-friendly warnings
    """
    if not voice_v2_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice V2 not available. Use /predict-voice for v1."
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
        logger.error(f"Voice V2 prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-audio-prosody", response_model=ProsodyAnalysisResponse, tags=["Voice V2"])
async def analyze_prosody(audio: UploadFile = File(...)):
    """
    Analyze prosodic features of audio

    Returns speaking rate, pause patterns, pitch features, etc.
    Useful for understanding HOW something is said, not just WHAT is said.

    Prosodic features extracted:
    - Speaking rate (words per minute)
    - Pause patterns (count, duration, ratio)
    - Pitch features (mean, std, range)
    - Energy features (volume patterns)
    - Derived indicators (urgency, scripted, stress)
    """
    if not HAS_VOICE_V2:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice V2 module not available."
        )

    try:
        audio_bytes = await audio.read()

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


@app.get("/voice-v2-health", tags=["Voice V2"])
async def voice_v2_health():
    """Check health status of Voice V2 detection system"""
    return {
        "status": "healthy" if voice_v2_available else "unavailable",
        "voice_v2_available": voice_v2_available,
        "components": {
            "voice_detector": voice_detector is not None,
            "wav2vec2_embedder": voice_v2_available,
            "prosody_analyzer": HAS_VOICE_V2,
            "text_predictor": voice_detector.text_predictor is not None if voice_detector else False,
        },
        "model_version": voice_detector.model_version if voice_detector else "N/A",
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================
# PHASE 5: CONTINUOUS LEARNING & MODEL REGISTRY
# ============================================

# Import Phase 5: Continuous Learning
try:
    from registry.model_registry import ModelRegistry
    from retraining.feedback_collector import FeedbackCollector, prepare_training_data
    from retraining.incremental_trainer import IncrementalTrainer
    from retraining.scheduler import WeeklyRetrainingScheduler
    HAS_CONTINUOUS_LEARNING = True
except ImportError:
    HAS_CONTINUOUS_LEARNING = False
    logger.warning("Continuous Learning module not available")

# Initialize Model Registry
model_registry = None
retraining_scheduler = None
if HAS_CONTINUOUS_LEARNING:
    try:
        model_registry = ModelRegistry(storage_path='./model_registry')
        logger.info("Model Registry initialized")
    except Exception as e:
        logger.warning(f"Could not initialize Model Registry: {e}")


# Phase 5 Request/Response Models
class RetrainingRequest(BaseModel):
    model_type: str = Field(default="sms", description="Model type to retrain: sms, phishing, voice")
    min_samples: int = Field(default=50, description="Minimum samples required")
    force: bool = Field(default=False, description="Force retraining even if insufficient samples")


class RetrainingResponse(BaseModel):
    status: str
    message: str
    details: Optional[dict] = None
    timestamp: str


class ModelVersionResponse(BaseModel):
    model_type: str
    version: str
    status: str
    metrics: dict
    trained_at: str
    deployed_at: Optional[str]


class TrainingDataRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1, description="List of text samples")
    labels: List[int] = Field(..., min_items=1, description="List of labels (0 or 1)")
    model_type: str = Field(default="sms", description="Model type to train")


@app.get("/models/versions", tags=["Model Registry"])
async def get_all_model_versions():
    """
    Get all registered model versions

    Returns versions for all model types with their metrics and deployment status.
    """
    if not HAS_CONTINUOUS_LEARNING or model_registry is None:
        return {
            "status": "unavailable",
            "message": "Model Registry not available",
            "versions": {},
            "timestamp": datetime.utcnow().isoformat()
        }

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

    return {
        "status": "success",
        "versions": versions,
        "stats": model_registry.get_registry_stats(),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/models/versions/{model_type}", tags=["Model Registry"])
async def get_model_versions_by_type(model_type: str):
    """
    Get all versions for a specific model type

    - **model_type**: sms, phishing, or voice
    """
    if not HAS_CONTINUOUS_LEARNING or model_registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model Registry not available"
        )

    versions = model_registry.get_all_versions(model_type)
    deployed = model_registry.get_deployed_version(model_type)

    return {
        "model_type": model_type,
        "deployed": deployed.to_dict() if deployed else None,
        "versions": [v.to_dict() for v in versions],
        "count": len(versions),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/models/history", tags=["Model Registry"])
async def get_deployment_history(model_type: str = None):
    """
    Get model deployment history

    - **model_type**: Optional filter by model type
    """
    if not HAS_CONTINUOUS_LEARNING or model_registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model Registry not available"
        )

    history = model_registry.get_version_history(model_type)

    return {
        "history": history,
        "count": len(history),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/models/rollback", tags=["Model Registry"])
async def rollback_model(model_type: str, version: str = None):
    """
    Rollback to a previous model version

    - **model_type**: Model type to rollback
    - **version**: Target version (optional, defaults to previous)
    """
    if not HAS_CONTINUOUS_LEARNING or model_registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model Registry not available"
        )

    try:
        success = await model_registry.rollback(model_type, version)
        if success:
            return {
                "status": "success",
                "message": f"Rolled back {model_type} to {version or 'previous version'}",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rollback failed - no previous version available"
            )
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/retrain", response_model=RetrainingResponse, tags=["Continuous Learning"])
async def trigger_retraining(request: RetrainingRequest):
    """
    Trigger model retraining with new data

    This endpoint is called by the backend when approved feedback
    reaches the threshold, or can be triggered manually.
    """
    if not HAS_CONTINUOUS_LEARNING:
        return {
            "status": "unavailable",
            "message": "Continuous Learning module not available",
            "details": None,
            "timestamp": datetime.utcnow().isoformat()
        }

    try:
        # Get backend URL from environment
        backend_url = os.getenv("BACKEND_URL", "http://localhost:3000")

        # Initialize scheduler
        model_paths = {
            "sms": "model/onnx_models/sms" if v2_available else "model/trained_models/sms",
            "phishing": "model/onnx_models/phishing" if v2_available else "model/trained_models/phishing",
            "voice": "model/onnx_models/voice" if v2_available else "model/trained_models/voice",
        }

        scheduler = WeeklyRetrainingScheduler(
            backend_url=backend_url,
            model_paths=model_paths,
            registry_path="./model_registry",
            min_samples=request.min_samples,
        )

        # Run retraining
        result = await scheduler.run_weekly_job()

        return {
            "status": result.get("status", "completed"),
            "message": f"Retraining completed for {request.model_type}",
            "details": result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Retraining failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "details": None,
            "timestamp": datetime.utcnow().isoformat()
        }


@app.post("/retrain/direct", tags=["Continuous Learning"])
async def retrain_with_data(request: TrainingDataRequest):
    """
    Directly retrain model with provided data

    Used for testing or when training data is provided directly
    rather than fetched from the feedback API.
    """
    if not HAS_CONTINUOUS_LEARNING:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Continuous Learning module not available"
        )

    if len(request.texts) != len(request.labels):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="texts and labels must have the same length"
        )

    if len(request.texts) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 10 samples required for training"
        )

    try:
        # Get model path
        model_paths = {
            "sms": "model/onnx_models/sms" if v2_available else "model/trained_models/sms",
            "phishing": "model/onnx_models/phishing" if v2_available else "model/trained_models/phishing",
            "voice": "model/onnx_models/voice" if v2_available else "model/trained_models/voice",
        }

        model_path = model_paths.get(request.model_type)
        if not model_path or not os.path.exists(model_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model not found for type: {request.model_type}"
            )

        # Initialize trainer
        trainer = IncrementalTrainer(
            model_path=model_path,
            model_type=request.model_type,
        )

        # Train
        result = trainer.train_on_feedback(
            texts=request.texts,
            labels=request.labels,
        )

        # Register version if successful
        if result["success"] and model_registry:
            await model_registry.register_version(
                model_type=request.model_type,
                version=result["version"],
                model_path=result["model_path"],
                metrics=result["new_metrics"],
                changelog=f"Direct training with {len(request.texts)} samples",
            )

            # Deploy if improved
            if result["improved"]:
                await model_registry.deploy_version(
                    request.model_type,
                    result["version"],
                )

        return {
            "status": "success" if result["success"] else "failed",
            "version": result["version"],
            "improved": result["improved"],
            "baseline_metrics": result["baseline_metrics"],
            "new_metrics": result["new_metrics"],
            "model_path": result["model_path"],
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Direct training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/retrain/status", tags=["Continuous Learning"])
async def get_retraining_status():
    """
    Get status of the retraining system

    Returns information about:
    - Available model types
    - Registry statistics
    - Last retraining run (if any)
    """
    return {
        "status": "available" if HAS_CONTINUOUS_LEARNING else "unavailable",
        "continuous_learning_enabled": HAS_CONTINUOUS_LEARNING,
        "model_registry_enabled": model_registry is not None,
        "v2_models_available": v2_available,
        "model_types": ["sms", "phishing", "voice"],
        "registry_stats": model_registry.get_registry_stats() if model_registry else None,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/continuous-learning-health", tags=["Continuous Learning"])
async def continuous_learning_health():
    """Check health status of Continuous Learning system"""
    return {
        "status": "healthy" if HAS_CONTINUOUS_LEARNING else "unavailable",
        "continuous_learning_available": HAS_CONTINUOUS_LEARNING,
        "components": {
            "model_registry": model_registry is not None,
            "feedback_collector": HAS_CONTINUOUS_LEARNING,
            "incremental_trainer": HAS_CONTINUOUS_LEARNING,
            "retraining_scheduler": HAS_CONTINUOUS_LEARNING,
        },
        "v2_models_available": v2_available,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================
# PHASE 6: V3 PRE-TRAINED MODELS
# ============================================

class V3PredictionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000,
                      description="Text to analyze for spam/phishing")
    model_type: Optional[str] = Field(
        default="auto",
        description="Model type: 'sms', 'phishing', 'voice', or 'auto'"
    )


class V3PredictionResponse(BaseModel):
    is_spam: bool
    confidence: float
    prediction: str
    risk_level: str
    category: Optional[str]
    explanation: str
    indicators: List[dict]
    model_version: str
    model_source: str
    timestamp: str


class V3EnsembleResponse(BaseModel):
    is_threat: bool
    confidence: float
    threat_level: str
    prediction: str
    transformer_score: float
    rule_score: float
    url_score: float
    indicators: List[dict]
    urls_analyzed: List[dict]
    explanation: str
    recommendation: str
    model_version: str
    ensemble_weights: dict
    timestamp: str


@app.post("/predict-v3", response_model=V3PredictionResponse, tags=["V3 Models"])
async def predict_v3(request: V3PredictionRequest):
    """
    V3 Prediction using pre-trained HuggingFace models

    Uses state-of-the-art pre-trained transformers for maximum accuracy:
    - SMS: mrm8488/bert-tiny-finetuned-sms-spam-detection
    - Phishing: cybersectony/phishing-email-detection-distilbert_v2.4.1

    Features:
    - Better generalization to real-world data
    - Automatic model download from HuggingFace
    - Fine-tuned models used if available
    """
    if not v3_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="V3 models not available. Ensure transformers library is installed."
        )

    try:
        model_type = request.model_type.lower()

        if model_type == "auto":
            result = multi_predictor_v3.predict_auto(request.text)
        elif model_type == "sms":
            result = multi_predictor_v3.predict_sms(request.text)
        elif model_type == "phishing":
            result = multi_predictor_v3.predict_phishing(request.text)
        elif model_type == "voice":
            result = multi_predictor_v3.predict_voice(request.text)
        else:
            result = multi_predictor_v3.predict_auto(request.text)

        return {
            **result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"V3 prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/predict-v3/elder-mode", tags=["V3 Models"])
async def predict_v3_elder_mode(request: V3PredictionRequest):
    """
    V3 Prediction with elder-friendly warnings

    Same as /predict-v3 but includes additional warnings designed
    for users who may be more vulnerable to scams.
    """
    if not v3_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="V3 models not available."
        )

    try:
        model_type = request.model_type.lower() if request.model_type else "sms"
        result = multi_predictor_v3.predict_with_elder_mode(request.text, model_type)

        return {
            **result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"V3 elder mode prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/predict-ensemble", response_model=V3EnsembleResponse, tags=["V3 Models"])
async def predict_ensemble(request: V3PredictionRequest):
    """
    Ensemble Prediction combining multiple detection methods

    Combines:
    - Pre-trained transformer models (60% weight)
    - Rule-based pattern matching (25% weight)
    - URL/feature analysis (15% weight)

    This provides the most accurate and explainable predictions.
    """
    if not v3_available or ensemble_predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ensemble predictor not available."
        )

    try:
        model_type = request.model_type.lower() if request.model_type else "auto"
        result = ensemble_predictor.predict(request.text, model_type)

        return {
            **result.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Ensemble prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/batch-predict-v3", tags=["V3 Models"])
async def batch_predict_v3(request: BatchPredictionRequest):
    """
    Batch V3 prediction for multiple texts

    Efficiently processes multiple texts using the V3 pre-trained models.
    """
    if not v3_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="V3 models not available."
        )

    try:
        results = []
        for text in request.messages:
            result = multi_predictor_v3.predict_auto(text)
            results.append({
                **result,
                "text_preview": text[:50] + "..." if len(text) > 50 else text
            })

        return {
            "predictions": results,
            "total": len(results),
            "spam_count": sum(1 for r in results if r.get("is_spam", False)),
            "model_version": "v3-pretrained",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Batch V3 prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/v3-health", tags=["V3 Models"])
async def v3_health():
    """Check health status of V3 pre-trained models"""
    return {
        "status": "healthy" if v3_available else "unavailable",
        "v3_available": v3_available,
        "ensemble_available": ensemble_predictor is not None,
        "models_loaded": multi_predictor_v3.get_loaded_models() if v3_available and multi_predictor_v3 else [],
        "available_model_types": ["sms", "phishing", "voice"],
        "features": [
            "Pre-trained HuggingFace transformers",
            "Fine-tuned models (if available)",
            "Ensemble prediction",
            "Elder-friendly mode"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/model/versions", tags=["Model Info"])
async def get_all_model_versions():
    """Get all available model versions and their status"""
    versions = {
        "v1": {
            "description": "TF-IDF + Traditional ML",
            "models": {
                "sms": "Logistic Regression",
                "phishing": "Random Forest",
                "voice": "Logistic Regression"
            },
            "status": "available" if multi_predictor and len(multi_predictor.models) > 0 else "unavailable",
            "loaded_models": list(multi_predictor.models.keys()) if multi_predictor else []
        },
        "v2": {
            "description": "ONNX-optimized Transformers",
            "models": {
                "sms": "DistilBERT (ONNX)",
                "phishing": "DistilBERT (ONNX)"
            },
            "status": "available" if v2_available else "unavailable",
            "loaded_models": multi_predictor_v2.get_available_models() if v2_available else []
        },
        "v3": {
            "description": "Pre-trained HuggingFace Transformers",
            "models": {
                "sms": "bert-tiny-finetuned-sms-spam-detection",
                "phishing": "phishing-email-detection-distilbert_v2.4.1",
                "voice": "Transfer from SMS model"
            },
            "status": "available" if v3_available else "unavailable",
            "loaded_models": multi_predictor_v3.get_loaded_models() if v3_available and multi_predictor_v3 else [],
            "features": ["Auto-download from HuggingFace", "Ensemble predictions", "Elder mode"]
        }
    }

    # Determine recommended version
    if v3_available:
        recommended = "v3"
    elif v2_available:
        recommended = "v2"
    else:
        recommended = "v1"

    return {
        "versions": versions,
        "recommended": recommended,
        "recommendation_reason": {
            "v3": "Best accuracy and generalization with pre-trained transformers",
            "v2": "Fast inference with ONNX optimization",
            "v1": "Lightweight, works without GPU"
        }.get(recommended, ""),
        "timestamp": datetime.utcnow().isoformat()
    }


# Run server
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
