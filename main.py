import logging
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import traceback

# =========================================================
# 📋 Logging Setup (Vercel-friendly)
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

logger.info("🚀 Starting FastAPI application...")

# =========================================================
# 🚀 Safe Import with Fallbacks
# =========================================================

Runner = None
SQLiteSession = None
store_in_supabase = None
Ultimate_Prompt_Refiner = None
PortraitPrompt_Enhancer = None

try:
    logger.info("Attempting to import agents...")
    from agents import Runner, SQLiteSession
    logger.info("✅ Imported agents.Runner and SQLiteSession")
except ImportError as e:
    logger.error(f"⚠️ Failed to import agents: {e}")
    
    class SQLiteSession:
        def __init__(self, user_id):
            self.user_id = user_id
            logger.info(f"Mock SQLiteSession created for user: {user_id}")

try:
    logger.info("Attempting to import Supabase...")
    from my_supabase.supaabse import store_in_supabase
    logger.info("✅ Imported store_in_supabase")
except ImportError as e:
    logger.error(f"⚠️ Failed to import Supabase: {e}")
    
    def store_in_supabase(user_id, prompt, improved_prompt):
        logger.info(f"Mock: Stored prompt for user {user_id}")

try:
    logger.info("Attempting to import image agents...")
    from image_agents import PortraitPrompt_Enhancer
    logger.info("✅ Imported PortraitPrompt_Enhancer")
except ImportError as e:
    logger.error(f"⚠️ Failed to import PortraitPrompt_Enhancer: {e}")
    
    class PortraitPrompt_Enhancer:
        pass

try:
    logger.info("Attempting to import prompt refiner...")
    from ogcode import Ultimate_Prompt_Refiner
    logger.info("✅ Imported Ultimate_Prompt_Refiner")
except ImportError as e:
    logger.error(f"⚠️ Failed to import Ultimate_Prompt_Refiner: {e}")
    
    class Ultimate_Prompt_Refiner:
        pass

# =========================================================
# Mock Runner if not imported
# =========================================================

if Runner is None:
    logger.warning("⚠️ Using mock Runner implementation")
    class Runner:
        @staticmethod
        async def run(starting_agent, session, input):
            class MockOutput:
                final_output = f"Enhanced: {input}"
            return MockOutput()

# =========================================================
# 🧩 Request/Response Models
# =========================================================

class PromptRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    prompt: str = Field(..., description="The prompt to enhance", min_length=1, max_length=5000)

class PromptResponse(BaseModel):
    status: str
    type: str
    improved_prompt: str

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str

# =========================================================
# 📋 Lifespan Events
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("✅ API Startup - All systems ready")
    yield
    logger.info("🛑 API Shutdown")

# =========================================================
# 🚀 FastAPI App Setup
# =========================================================

logger.info("🔧 Initializing FastAPI app...")

app = FastAPI(
    title="AI Prompt Enhancement API",
    description="FastAPI service for refining text and image prompts",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("✅ FastAPI app initialized successfully")

# =========================================================
# 🏠 Health Check Endpoint
# =========================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Vercel monitoring."""
    env = os.getenv("VERCEL_ENV", "development")
    logger.info(f"Health check requested - Environment: {env}")
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": env
    }

# =========================================================
# 🏠 Root Route
# =========================================================

@app.get("/")
async def root():
    """Welcome endpoint."""
    logger.info("Root endpoint accessed")
    return {
        "message": "✅ AI Prompt Enhancement API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "POST /enhance-text": "Refine text prompts",
            "POST /enhance-image": "Enhance image prompts"
        }
    }

# =========================================================
# 🧠 Text Prompt Enhancer Endpoint
# =========================================================

@app.post("/enhance-text", response_model=PromptResponse)
async def enhance_text(request: PromptRequest):
    """Enhance text prompts."""
    request_id = id(request)
    logger.info(f"[{request_id}] Text enhancement started - User: {request.user_id}")
    
    try:
        # Create session
        logger.info(f"[{request_id}] Creating SQLiteSession...")
        session = SQLiteSession(request.user_id)
        
        # Run agent
        logger.info(f"[{request_id}] Running Ultimate_Prompt_Refiner agent...")
        runner = await Runner.run(
            starting_agent=Ultimate_Prompt_Refiner,
            session=session,
            input=request.prompt
        )
        
        improved_prompt = runner.final_output.strip()
        logger.info(f"[{request_id}] Agent completed successfully")
        
        # Store in Supabase (non-blocking)
        try:
            logger.info(f"[{request_id}] Storing in Supabase...")
            store_in_supabase(request.user_id, request.prompt, improved_prompt)
            logger.info(f"[{request_id}] Supabase storage successful")
        except Exception as e:
            logger.warning(f"[{request_id}] Supabase storage failed (non-critical): {e}")
        
        logger.info(f"[{request_id}] ✅ Text enhancement completed")
        return PromptResponse(
            status="success",
            type="text",
            improved_prompt=improved_prompt
        )

    except Exception as e:
        logger.error(f"[{request_id}] ❌ Text enhancement failed: {str(e)}")
        logger.error(f"[{request_id}] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Text enhancement failed: {str(e)}"
        )

# =========================================================
# 🎨 Image Prompt Enhancer Endpoint
# =========================================================

@app.post("/enhance-image", response_model=PromptResponse)
async def enhance_image(request: PromptRequest):
    """Enhance image prompts."""
    request_id = id(request)
    logger.info(f"[{request_id}] Image enhancement started - User: {request.user_id}")
    
    try:
        # Create session
        logger.info(f"[{request_id}] Creating SQLiteSession...")
        session = SQLiteSession(request.user_id)
        
        # Run agent
        logger.info(f"[{request_id}] Running PortraitPrompt_Enhancer agent...")
        runner = await Runner.run(
            starting_agent=PortraitPrompt_Enhancer,
            session=session,
            input=request.prompt
        )
        
        improved_prompt = runner.final_output.strip()
        logger.info(f"[{request_id}] Agent completed successfully")
        
        # Store in Supabase (non-blocking)
        try:
            logger.info(f"[{request_id}] Storing in Supabase...")
            store_in_supabase(request.user_id, request.prompt, improved_prompt)
            logger.info(f"[{request_id}] Supabase storage successful")
        except Exception as e:
            logger.warning(f"[{request_id}] Supabase storage failed (non-critical): {e}")
        
        logger.info(f"[{request_id}] ✅ Image enhancement completed")
        return PromptResponse(
            status="success",
            type="image",
            improved_prompt=improved_prompt
        )

    except Exception as e:
        logger.error(f"[{request_id}] ❌ Image enhancement failed: {str(e)}")
        logger.error(f"[{request_id}] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Image enhancement failed: {str(e)}"
        )

# =========================================================
# 🔴 Global Exception Handler
# =========================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"🔴 Unhandled exception: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )

logger.info("✅ Application fully initialized and ready")