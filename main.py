import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, Runner, SQLiteSession, set_tracing_disabled
from my_configuration.configuration import model
from my_supabase.supaabse import store_in_supabase

# =========================================================
# FastAPI App Config
# =========================================================
app = FastAPI(
    title="Promptify AI API",
    description="An API that refines vague prompts into professional AI-ready prompts.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev; limit in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# Request/Response Models
# =========================================================
class PromptRequest(BaseModel):
    user_id: str
    message: str

class PromptResponse(BaseModel):
    output: str
    success: bool
    error: str | None = None


# =========================================================
# Helper: Create all Agents Once (global)
# =========================================================
set_tracing_disabled(True)

Prompt_Improver = Agent(
    name="Prompt Improver",
    instructions="""
    You are **PromptSmith**, a professional prompt engineer.
    Rewrite vague user prompts into clear, detailed, professional versions.
    Keep intent same. Be concise (max 40 words). Output only rewritten prompt.
    """,
    model=model,
)

Prompt_Improver_as_tool = Prompt_Improver.as_tool("prompt_improver_tool", "Improves vague prompts.")

Style_Enhancer = Agent(
    name="Style Enhancer",
    instructions="You are **ToneMaster**, polish the tone and grammar while keeping the meaning same.",
    model=model,
)

Style_Enhancer_as_tool = Style_Enhancer.as_tool("style_enhancer_tool", "Polishes tone and flow.")

Context_Enricher = Agent(
    name="Context Enricher",
    instructions="Add minimal relevant context so the prompt is self-contained. Do not answer it.",
    model=model,
)

Context_Enricher_as_tool = Context_Enricher.as_tool("context_enricher_tool", "Adds context.")

Prompt_Expander = Agent(
    name="Prompt Expander",
    instructions="""
    Create 3 stylistic versions (Technical, Creative, Concise) of the improved prompt.
    Output only text. Each 1–3 sentences.
    """,
    model=model,
)

Prompt_Expander_as_tool = Prompt_Expander.as_tool("prompt_expander_tool", "Creates stylistic prompt versions.")

Responder = Agent(
    name="Prompt Orchestrator",
    model=model,
    instructions="""
    Combine tools to refine vague user input into multiple professional prompt versions.
    """,
    tools=[Prompt_Improver_as_tool, Style_Enhancer_as_tool, Context_Enricher_as_tool, Prompt_Expander_as_tool],
)


# =========================================================
# Routes
# =========================================================
@app.get("/")
async def root():
    return {"message": "Promptify API is running successfully!"}


@app.post("/generate", response_model=PromptResponse)
async def generate_prompt(request: PromptRequest):
    try:
        session = SQLiteSession(request.user_id, "prompt_stream.db")

        result = await Runner.run(Responder, input=request.message, session=session)
        final_output = result.final_output.strip()

        # Store in Supabase
        store_in_supabase(request.user_id, request.message, final_output)

        return PromptResponse(output=final_output, success=True)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================
# Local Dev Server (ignored by Vercel)
# =========================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
