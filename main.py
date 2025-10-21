from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from agents import Runner, SQLiteSession, set_tracing_disabled
from ogcode import Ultimate_Prompt_Refiner

# Initialize FastAPI app
app = FastAPI(
    title="Prompt Refinement API",
    description="API for refining and enhancing prompts using specialized AI agents",
    version="1.0.0",
)

# Enable CORS for all origins (you can restrict this later)
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
# HEALTH CHECK ROUTE
# ------------------------------
@app.get("/")
async def health():
    return {"status": "OK", "message": "Server running successfully on Vercel"}


# ------------------------------
# ENDPOINTS
# ------------------------------
@app.post("/refine-general")
async def refine_general(data: PromptRequest):
    """
    Refine general prompts using the Ultimate_Prompt_Refiner.
    """
    try:
        # ⚠️ Use in-memory DB (Vercel filesystem is read-only)
        session = SQLiteSession(":memory:")

        # Run the agent in a separate thread to avoid event loop issues
        result = await asyncio.to_thread(
            lambda: asyncio.run(
                Runner.run(
                    starting_agent=Ultimate_Prompt_Refiner,
                    session=session,
                    input=data.prompt,
                )
            )
        )

        # Return the refined prompt
        return {"refined_prompt": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
