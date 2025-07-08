from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uuid
from datetime import datetime
from detoxify import Detoxify
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import time


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection (optional for offline mode)
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME')
use_mongo = False
client = None

db = None
in_memory_db = {
    'text_analyses': [],
    'user_settings': {},
    'status_checks': []
}

if mongo_url and db_name:
    try:
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=2000)
        db = client[db_name]
        # Try a quick command to check connection
        import asyncio
        async def check_mongo():
            try:
                await db.command('ping')
                return True
            except Exception:
                return False
        if asyncio.get_event_loop().run_until_complete(check_mongo()):
            use_mongo = True
            logging.info('Connected to MongoDB.')
        else:
            logging.warning('MongoDB not available, using in-memory storage.')
    except Exception as e:
        logging.warning(f'MongoDB connection failed: {e}. Using in-memory storage.')
else:
    logging.warning('MongoDB env vars not set. Using in-memory storage.')

# Create the main app without a prefix
app = FastAPI(title="ThinkTwice API", description="Real-time regret prevention for your messages")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Global variables for the toxicity detection model
detox_model = None
model_lock = threading.Lock()
executor = ThreadPoolExecutor(max_workers=4)
model_load_time = None

# Custom exception handler
@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"}
    )

# Load the model at startup
def load_detoxify_model():
    global detox_model, model_load_time
    try:
        start_time = time.time()
        detox_model = Detoxify('original')
        model_load_time = time.time() - start_time
        logging.info(f"Detoxify model loaded successfully in {model_load_time:.2f} seconds")
    except Exception as e:
        logging.error(f"Failed to load Detoxify model: {e}")
        detox_model = None

# Load model in a separate thread to avoid blocking startup
threading.Thread(target=load_detoxify_model, daemon=True).start()

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class TextAnalysisRequest(BaseModel):
    text: str
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)

class TextAnalysisResponse(BaseModel):
    text: str
    regret_score: float
    should_warn: bool
    analysis: Dict[str, float]
    threshold: float
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class UserSettingsRequest(BaseModel):
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class UserSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    threshold: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Toxicity analysis function with improved error handling
def analyze_text_toxicity(text: str) -> Dict[str, float]:
    global detox_model
    if detox_model is None:
        logging.warning("Detoxify model not loaded, returning default scores")
        return {
            "toxicity": 0.0,
            "severe_toxicity": 0.0,
            "obscene": 0.0,
            "threat": 0.0,
            "insult": 0.0,
            "identity_attack": 0.0
        }
    
    try:
        # Ensure text is not too long (model has limits)
        if len(text) > 2000:
            text = text[:2000]
        
        results = detox_model.predict(text)
        
        # Ensure all values are valid floats
        return {
            "toxicity": max(0.0, min(1.0, float(results.get('toxicity', 0.0)))),
            "severe_toxicity": max(0.0, min(1.0, float(results.get('severe_toxicity', 0.0)))),
            "obscene": max(0.0, min(1.0, float(results.get('obscene', 0.0)))),
            "threat": max(0.0, min(1.0, float(results.get('threat', 0.0)))),
            "insult": max(0.0, min(1.0, float(results.get('insult', 0.0)))),
            "identity_attack": max(0.0, min(1.0, float(results.get('identity_attack', 0.0))))
        }
    except Exception as e:
        logging.error(f"Error analyzing text: {e}")
        return {
            "toxicity": 0.0,
            "severe_toxicity": 0.0,
            "obscene": 0.0,
            "threat": 0.0,
            "insult": 0.0,
            "identity_attack": 0.0
        }

# Calculate overall regret score with improved algorithm
def calculate_regret_score(analysis: Dict[str, float]) -> float:
    # Weighted scoring system with emphasis on more harmful content
    weights = {
        "toxicity": 0.25,
        "severe_toxicity": 0.30,
        "obscene": 0.10,
        "threat": 0.25,
        "insult": 0.15,
        "identity_attack": 0.20
    }
    
    # Calculate weighted score
    weighted_score = sum(analysis.get(key, 0.0) * weight for key, weight in weights.items())
    
    # Apply non-linear scaling to make high scores more prominent
    if weighted_score > 0.3:
        weighted_score = 0.3 + (weighted_score - 0.3) * 1.5
    
    return max(0.0, min(1.0, weighted_score))

# API Routes
@api_router.get("/")
async def root():
    return {
        "message": "ThinkTwice API - Real-time Regret Prevention",
        "version": "1.0.0",
        "model_status": "loaded" if detox_model else "loading"
    }

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": detox_model is not None,
        "model_load_time": model_load_time,
        "timestamp": datetime.utcnow(),
        "api_version": "1.0.0"
    }

@api_router.post("/analyze-text", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    start_time = time.time()
    
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    if len(request.text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long (max 5000 characters)")
    
    try:
        # Run toxicity analysis in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        analysis = await loop.run_in_executor(executor, analyze_text_toxicity, request.text)
        
        # Calculate regret score
        regret_score = calculate_regret_score(analysis)
        
        # Determine if warning should be shown
        should_warn = regret_score >= request.threshold
        
        processing_time = time.time() - start_time
        
        response = TextAnalysisResponse(
            text=request.text,
            regret_score=regret_score,
            should_warn=should_warn,
            analysis=analysis,
            threshold=request.threshold,
            processing_time=processing_time
        )
        
        # Store analysis in database for future analysis (async)
        asyncio.create_task(store_analysis(response.dict()))
        
        return response
        
    except Exception as e:
        logging.error(f"Error in analyze_text: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during text analysis")

async def store_analysis(analysis_data: dict):
    """Store analysis in database asynchronously or in-memory if offline"""
    if use_mongo:
        try:
            await db.text_analyses.insert_one(analysis_data)
        except Exception as e:
            logging.error(f"Error storing analysis: {e}")
    else:
        in_memory_db['text_analyses'].append(analysis_data)

@api_router.post("/user-settings", response_model=UserSettings)
async def save_user_settings(request: UserSettingsRequest):
    try:
        settings = UserSettings(
            user_id=request.user_id,
            threshold=request.threshold
        )
        if use_mongo:
            await db.user_settings.replace_one(
                {"user_id": request.user_id},
                settings.dict(),
                upsert=True
            )
        else:
            in_memory_db['user_settings'][request.user_id] = settings.dict()
        return settings
    except Exception as e:
        logging.error(f"Error saving user settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to save user settings")

@api_router.get("/user-settings/{user_id}")
async def get_user_settings(user_id: str):
    try:
        if use_mongo:
            settings = await db.user_settings.find_one({"user_id": user_id})
            if settings:
                return UserSettings(**settings)
        else:
            settings = in_memory_db['user_settings'].get(user_id)
            if settings:
                return UserSettings(**settings)
        # Return default settings
        return UserSettings(user_id=user_id, threshold=0.5)
    except Exception as e:
        logging.error(f"Error getting user settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user settings")

@api_router.get("/analytics")
async def get_analytics():
    try:
        if use_mongo:
            total_analyses = await db.text_analyses.count_documents({})
            warned_analyses = await db.text_analyses.count_documents({"should_warn": True})
            pipeline = [
                {"$group": {"_id": None, "avg_processing_time": {"$avg": "$processing_time"}}}
            ]
            avg_time_result = await db.text_analyses.aggregate(pipeline).to_list(1)
            avg_processing_time = avg_time_result[0]["avg_processing_time"] if avg_time_result else 0
            recent_analyses = await db.text_analyses.find(
                {},
                {"text": 1, "regret_score": 1, "should_warn": 1, "timestamp": 1, "_id": 0}
            ).sort("timestamp", -1).limit(10).to_list(10)
        else:
            total_analyses = len(in_memory_db['text_analyses'])
            warned_analyses = sum(1 for a in in_memory_db['text_analyses'] if a.get('should_warn'))
            avg_processing_time = (
                sum(a.get('processing_time', 0) for a in in_memory_db['text_analyses']) / total_analyses
                if total_analyses > 0 else 0
            )
            recent_analyses = in_memory_db['text_analyses'][-10:][::-1]
        return {
            "total_analyses": total_analyses,
            "warned_analyses": warned_analyses,
            "warning_rate": warned_analyses / max(total_analyses, 1),
            "avg_processing_time": avg_processing_time,
            "recent_analyses": recent_analyses,
            "model_loaded": detox_model is not None
        }
    except Exception as e:
        logging.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

# Original status check endpoints
@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    if use_mongo:
        _ = await db.status_checks.insert_one(status_obj.dict())
    else:
        in_memory_db['status_checks'].append(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    if use_mongo:
        status_checks = await db.status_checks.find().to_list(1000)
        return [StatusCheck(**status_check) for status_check in status_checks]
    else:
        return [StatusCheck(**status_check) for status_check in in_memory_db['status_checks']]

# Include the router in the main app
app.include_router(api_router)

# Enhanced CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 ThinkTwice API starting up...")
    # Give the model loading thread some time
    await asyncio.sleep(2)
    if detox_model:
        logger.info("✅ Detoxify model ready for analysis")
    else:
        logger.warning("⚠️ Detoxify model still loading...")

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("🔄 Shutting down ThinkTwice API...")
    if client:
        client.close()
    executor.shutdown(wait=True)
    logger.info("✅ Shutdown complete")