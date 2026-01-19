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
    multi_predictor = None

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
