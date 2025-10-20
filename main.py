import logging
import os
import sys
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# =========================================================
# 📋 Logging Setup (Vercel / Production Friendly)
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)
logger.info("🚀 Starting FastAPI application...")

# =========================================================
# 🧩 Safe Imports with Mock Fallbacks
# =========================================================
try:
    from agents import Runner, SQLiteSession
    logger.info("✅ Imported: agents.Runner, agents.SQLiteSession")
except Exception as e:
    logger.warning(f"⚠️ Failed to import agents: {e}")

    class SQLiteSession:
        def __init__(self, user_id):
            self.user_id = user_id
            logger.info(f"Mock SQLiteSession created for user: {user_id}")

    class Runner:
        @staticmethod
        async def run(starting_agent, session, input):
            class MockOutput:
                final_output = f"Enhanced (mock): {input}"
            return MockOutput()

try:
    from my_supabase.supaabse import store_in_supabase
    logger.info("✅ Imported: store_in_supabase")
except Exception as e:
    logger.warning(f"⚠️ Failed to import Supabase: {e}")

    def store_in_supabase(user_id, prompt, improved_prompt):
        logger.info(f"Mock Supabase store for {user_id}: {improved_prompt[:50]}...")

try:
    from image_agents import PortraitPrompt_Enhancer
    logger.info("✅ Imported: PortraitPrompt_Enhancer")
except Exception as e:
    logger.warning(f"⚠️ Failed to import PortraitPrompt_Enhancer: {e}")

    class PortraitPrompt_Enhancer:
        pass

try:
    from ogcode import Ultimate_Prompt_Refiner
    logger.info("✅ Imported: Ultimate_Prompt_Refiner")
except Exception as e:
    logger.warning(f"⚠️ Failed to import Ultimate_Prompt_Refiner: {e}")

    class Ultimate_Prompt_Refiner:
        pass

# =========================================================
# 🧱 Models
# =========================================================
class PromptRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    prompt: str = Field(..., description="Prompt text to enhance", min_length=1, max_length=5000)


class PromptResponse(BaseModel):
    status: str
    type: str
    improved_prompt: str


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


# =========================================================
# 🌐 Lifespan Context
# =========================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("✅ Application startup complete")
    yield
    logger.info("🛑 Application shutdown")


# =========================================================
# 🚀 FastAPI App Setup
# =========================================================
app = FastAPI(
    title="AI Prompt Enhancement API",
    description="FastAPI service for refining text and image prompts",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Enable CORS for all origins (Vercel compatible)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# 🩺 Health Check
# =========================================================
@app.get("/health", response_model=HealthResponse)
async def health_check():
    env = os.getenv("VERCEL_ENV", "development")
    return {"status": "healthy", "version": "1.0.0", "environment": env}


# =========================================================
# 🏠 Root Endpoint
# =========================================================
@app.get("/")
async def root():
    return {
        "message": "✅ AI Prompt Enhancement API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "POST /enhance-text": "Refine text prompts",
            "POST /enhance-image": "Enhance image prompts",
        },
    }


# =========================================================
# 🧠 Text Prompt Enhancer
# =========================================================
@app.post("/enhance-text", response_model=PromptResponse)
async def enhance_text(request: PromptRequest):
    request_id = id(request)
    logger.info(f"[{request_id}] Enhancing text for user: {request.user_id}")

    try:
        session = SQLiteSession(request.user_id)
        runner = await Runner.run(Ultimate_Prompt_Refiner, session, request.prompt)
        improved_prompt = runner.final_output.strip()

        # Store result (non-blocking)
        try:
            store_in_supabase(request.user_id, request.prompt, improved_prompt)
        except Exception as e:
            logger.warning(f"Supabase store failed (non-critical): {e}")

        return PromptResponse(status="success", type="text", improved_prompt=improved_prompt)

    except Exception as e:
        logger.error(f"[{request_id}] Text enhancement failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Text enhancement failed: {e}")


# =========================================================
# 🎨 Image Prompt Enhancer
# =========================================================
@app.post("/enhance-image", response_model=PromptResponse)
async def enhance_image(request: PromptRequest):
    request_id = id(request)
    logger.info(f"[{request_id}] Enhancing image prompt for user: {request.user_id}")

    try:
        session = SQLiteSession(request.user_id)
        runner = await Runner.run(PortraitPrompt_Enhancer, session, request.prompt)
        improved_prompt = runner.final_output.strip()

        # Store result (non-blocking)
        try:
            store_in_supabase(request.user_id, request.prompt, improved_prompt)
        except Exception as e:
            logger.warning(f"Supabase store failed (non-critical): {e}")

        return PromptResponse(status="success", type="image", improved_prompt=improved_prompt)

    except Exception as e:
        logger.error(f"[{request_id}] Image enhancement failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Image enhancement failed: {e}")


# =========================================================
# 🔴 Global Exception Handler
# =========================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"🔴 Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


# =========================================================
# 🏁 Run Local (optional)
# =========================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
