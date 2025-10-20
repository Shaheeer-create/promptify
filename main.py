from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents import Runner, SQLiteSession, set_tracing_disabled
from my_supabase.supaabse import store_in_supabase
from my_configuration.configuration import model

# Import your existing agents
from ogcode import Ultimate_Prompt_Refiner
from image_agents import PortraitPrompt_Enhancer

# ------------------------------
# FASTAPI SETUP
# ------------------------------
app = FastAPI(
    title="Prompt Refinement API",
    description="API for refining and enhancing prompts using specialized AI agents",
    version="1.0.0"
)

# Enable CORS for all origins (you can restrict later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Disable tracing for production cleanliness
set_tracing_disabled(True)

# ------------------------------
# MODELS
# ------------------------------
class PromptRequest(BaseModel):
    user_id: str
    prompt: str


# ------------------------------
# ENDPOINTS
# ------------------------------

@app.post("/refine-general")
async def refine_general(data: PromptRequest):
    """
    Refine general prompts using the Ultimate_Prompt_Refiner.
    """
    try:
        session = SQLiteSession(data.user_id)
        runner = await Runner.run(
            starting_agent=Ultimate_Prompt_Refiner,
            session=session,
            input=data.prompt
        )

        improved_prompt = runner.final_output.strip()

        # Store in Supabase
        try:
            store_in_supabase(data.user_id, data.prompt, improved_prompt)
        except Exception as e:
            print("⚠️ Supabase error:", e)

        return {"success": True, "improved_prompt": improved_prompt}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refine-portrait")
async def refine_portrait(data: PromptRequest):
    """
    Enhance portrait photography prompts using PortraitPrompt_Enhancer.
    """
    try:
        session = SQLiteSession(data.user_id)
        runner = await Runner.run(
            starting_agent=PortraitPrompt_Enhancer,
            session=session,
            input=data.prompt
        )

        improved_prompt = runner.final_output.strip()

        # Store in Supabase
        try:
            store_in_supabase(data.user_id, data.prompt, improved_prompt)
        except Exception as e:
            print("⚠️ Supabase error:", e)

        return {"success": True, "improved_prompt": improved_prompt}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------
# ROOT ENDPOINT
# ------------------------------
@app.get("/")
async def root():
    return {"message": "🚀 Prompt Refinement API is running successfully!"}
