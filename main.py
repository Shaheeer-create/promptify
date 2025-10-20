from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents import Runner, SQLiteSession
from my_supabase.supaabse import store_in_supabase
from image_agents import PortraitPrompt_Enhancer
from ogcode import Ultimate_Prompt_Refiner

# ✅ Import your existing agents

# =========================================================

# 🚀 FastAPI App Setup

# =========================================================

app = FastAPI(
    title="AI Prompt Enhancement API",
    description="FastAPI service for refining text and image prompts using multi-agent systems.",
    version="1.0.0"
)

# =========================================================

# 🧩 Request Model

# =========================================================

class PromptRequest(BaseModel):
    user_id: str
    prompt: str

# =========================================================

# 🧠 Text Prompt Enhancer Endpoint

# =========================================================

@app.post("/enhance-text")
async def enhance_text(request: PromptRequest):
    try:
        session = SQLiteSession(request.user_id)
        runner = await Runner.run(
            starting_agent=Ultimate_Prompt_Refiner,
            session=session,
            input=request.prompt
        )

        improved_prompt = runner.final_output.strip()

        # ✅ Store in Supabase
        store_in_supabase(request.user_id, request.prompt, improved_prompt)

        return {"status": "success", "type": "text", "improved_prompt": improved_prompt}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================

# 🎨 Image Prompt Enhancer Endpoint

# =========================================================

@app.post("/enhance-image")
async def enhance_image(request: PromptRequest):
    try:
        session = SQLiteSession(request.user_id)
        runner = await Runner.run(
            starting_agent=PortraitPrompt_Enhancer,
            session=session,
            input=request.prompt
        )

        improved_prompt = runner.final_output.strip()

        # ✅ Store in Supabase
        store_in_supabase(request.user_id, request.prompt, improved_prompt)

        return {"status": "success", "type": "image", "improved_prompt": improved_prompt}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================

# 🏠 Root Route

# =========================================================

@app.get("/")
async def root():
    return {
        "message": "Welcome to the AI Prompt Enhancement API 🚀",
        "endpoints": {
            "POST /enhance-text": "Refine any text or general prompt.",
            "POST /enhance-image": "Enhance portrait/image generation prompts."
        }
    }
