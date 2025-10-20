import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from agents import Runner, SQLiteSession
from my_supabase.supaabse import store_in_supabase
from image_agents import PortraitPrompt_Enhancer
from ogcode import Ultimate_Prompt_Refiner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================================
# 🚀 Import your agents (with error handling)
# =========================================================

try:
    from agents import Runner, SQLiteSession
    from my_supabase.supaabse import store_in_supabase
    from image_agents import PortraitPrompt_Enhancer
    from ogcode import Ultimate_Prompt_Refiner
except ImportError as e:
    logger.warning(f"Import warning: {e}. Using mock implementations for development.")
    # Mock implementations for development/testing
    class Runner:
        @staticmethod
        async def run(starting_agent, session, input):
            class MockOutput:
                final_output = f"Enhanced: {input}"
            return MockOutput()
    
    class SQLiteSession:
        def __init__(self, user_id):
            self.user_id = user_id
    
    def store_in_supabase(user_id, prompt, improved_prompt):
        logger.info(f"Mock: Stored prompt for user {user_id}")
    
    class Ultimate_Prompt_Refiner:
        pass
    
    class PortraitPrompt_Enhancer:
        pass

# =========================================================
# 🧩 Request/Response Models
# =========================================================

class PromptRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    prompt: str = Field(..., description="The prompt to enhance", min_length=1, max_length=5000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "prompt": "A girl with blue eyes"
            }
        }

class PromptResponse(BaseModel):
    status: str
    type: str
    improved_prompt: str

class HealthResponse(BaseModel):
    status: str
    version: str

# =========================================================
# 📋 Lifespan Events
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 AI Prompt Enhancement API starting...")
    yield
    # Shutdown
    logger.info("🛑 API shutting down...")

# =========================================================
# 🚀 FastAPI App Setup
# =========================================================

app = FastAPI(
    title="AI Prompt Enhancement API",
    description="FastAPI service for refining text and image prompts using multi-agent systems.",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# 🏠 Health Check Endpoint
# =========================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring and deployment."""
    return {"status": "healthy", "version": "1.0.0"}

# =========================================================
# 🏠 Root Route
# =========================================================

@app.get("/", response_model=dict)
async def root():
    """Welcome endpoint with API documentation."""
    return {
        "message": "Welcome to the AI Prompt Enhancement API 🚀",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "GET /health": "Health check endpoint",
            "POST /enhance-text": "Refine any text or general prompt",
            "POST /enhance-image": "Enhance portrait/image generation prompts"
        }
    }

# =========================================================
# 🧠 Text Prompt Enhancer Endpoint
# =========================================================

@app.post("/enhance-text", response_model=PromptResponse)
async def enhance_text(request: PromptRequest):
    """
    Enhance and refine text prompts using the Ultimate Prompt Refiner agent.
    
    Args:
        request: PromptRequest containing user_id and prompt
        
    Returns:
        PromptResponse with enhanced prompt
    """
    try:
        logger.info(f"Processing text enhancement for user: {request.user_id}")
        
        session = SQLiteSession(request.user_id)
        runner = await Runner.run(
            starting_agent=Ultimate_Prompt_Refiner,
            session=session,
            input=request.prompt
        )

        improved_prompt = runner.final_output.strip()
        
        # Store in Supabase
        try:
            store_in_supabase(request.user_id, request.prompt, improved_prompt)
        except Exception as e:
            logger.error(f"Supabase storage failed: {e}")
            # Don't fail the request, just log the error
        
        logger.info(f"✅ Text enhancement completed for user: {request.user_id}")
        return PromptResponse(
            status="success",
            type="text",
            improved_prompt=improved_prompt
        )

    except Exception as e:
        logger.error(f"❌ Text enhancement error for user {request.user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing text prompt: {str(e)}"
        )

# =========================================================
# 🎨 Image Prompt Enhancer Endpoint
# =========================================================

@app.post("/enhance-image", response_model=PromptResponse)
async def enhance_image(request: PromptRequest):
    """
    Enhance image/portrait generation prompts using the Portrait Prompt Enhancer agent.
    
    Args:
        request: PromptRequest containing user_id and prompt
        
    Returns:
        PromptResponse with enhanced prompt
    """
    try:
        logger.info(f"Processing image enhancement for user: {request.user_id}")
        
        session = SQLiteSession(request.user_id)
        runner = await Runner.run(
            starting_agent=PortraitPrompt_Enhancer,
            session=session,
            input=request.prompt
        )

        improved_prompt = runner.final_output.strip()
        
        # Store in Supabase
        try:
            store_in_supabase(request.user_id, request.prompt, improved_prompt)
        except Exception as e:
            logger.error(f"Supabase storage failed: {e}")
            # Don't fail the request, just log the error
        
        logger.info(f"✅ Image enhancement completed for user: {request.user_id}")
        return PromptResponse(
            status="success",
            type="image",
            improved_prompt=improved_prompt
        )

    except Exception as e:
        logger.error(f"❌ Image enhancement error for user {request.user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image prompt: {str(e)}"
        )

# =========================================================
# 🚀 Entry Point
# =========================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to True for development only
        workers=4,
        log_level="info"
    )