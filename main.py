from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import AsyncGenerator
from agents import Agent, Runner, SQLiteSession, set_tracing_disabled
from my_configuration.configuration import model
from openai.types.responses import ResponseTextDeltaEvent
from my_supabase.supaabse import store_in_supabase
import json
import logging

# =========================================================
# LOGGING
# =========================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================================
# REQUEST/RESPONSE MODELS
# =========================================================
class PromptRequest(BaseModel):
    user_input: str = Field(..., min_length=1, max_length=5000)
    user_id: str = Field(..., min_length=1)

class ErrorResponse(BaseModel):
    error: str
    detail: str = None

# =========================================================
# FASTAPI SETUP
# =========================================================
app = FastAPI(
    title="Promptify AI API",
    description="AI-powered prompt enhancement and optimization",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# AGENT INITIALIZATION
# =========================================================
set_tracing_disabled(True)

# === TOOL AGENTS ===
Prompt_Clarity = Agent(
    name="Prompt Clarity Enhancer",
    instructions="You are ClarityMaster. Refine vague or confusing prompts into clear, specific, unambiguous statements. Keep intent intact. Output max 35 words.",
    model=model,
).as_tool("prompt_clarity_tool", "Refines vague prompts into clear, specific versions.")

Prompt_Context = Agent(
    name="Prompt Context Enricher",
    instructions="You are ContextGuru. Add relevant background or examples. Keep intent intact. Output max 40 words.",
    model=model,
).as_tool("prompt_context_tool", "Adds context/examples to prompts.")

Prompt_Instructions = Agent(
    name="Prompt Instruction Designer",
    instructions="You are InstructionSmith. Add structured guidance or steps. Keep intent intact. Output max 40 words.",
    model=model,
).as_tool("prompt_instruction_tool", "Adds structured instructions to prompts.")

Prompt_Role = Agent(
    name="Prompt Role Assigner",
    instructions="You are RoleMaster. Add role, persona, or tone if needed. Keep intent intact. Output max 35 words.",
    model=model,
).as_tool("prompt_role_tool", "Adds role or tone to prompts.")

Prompt_Formatter = Agent(
    name="Prompt Output Formatter",
    instructions="You are FormatGuru. Specify output format like bullet points, tables, etc. Keep intent intact. Output max 40 words.",
    model=model,
).as_tool("prompt_formatter_tool", "Specifies output format for prompts.")

Prompt_Improver = Agent(
    name="Prompt Improver",
    instructions="You are PromptSmith. Polish prompts for clarity and professionalism. Output max 40 words.",
    model=model,
).as_tool("prompt_improver_tool", "Polishes prompts for clarity and professionalism.")

# === SHORT PROMPT AGENT ===
ShortPromptRefiner = Agent(
    name="Short Prompt Refiner",
    instructions="""
You are ShortPromptSmith. Refine user prompt to be fully optimized, clear, structured, and concise (max 40 words).
Apply all tools in this order:
1. Clarity
2. Context
3. Instructions
4. Role
5. Formatter
6. Improver
Return only:
{"improved_prompt": "Final refined prompt text"}
""",
    model=model,
    tools=[
        Prompt_Clarity,
        Prompt_Context,
        Prompt_Instructions,
        Prompt_Role,
        Prompt_Formatter,
        Prompt_Improver,
    ],
).as_tool("short_prompt_refiner_tool", "Generates short refined prompts.")

# === DETAILED PROMPT AGENT ===
DetailedPromptRefiner = Agent(
    name="Detailed Prompt Refiner",
    instructions="""
You are DetailedPromptSmith. Refine user prompt to be fully optimized, clear, structured, and detailed (up to 100 words).
Apply all tools in this order:
1. Clarity
2. Context
3. Instructions
4. Role
5. Formatter
6. Improver
Return only:
{"improved_prompt": "Final detailed prompt text"}
""",
    model=model,
    tools=[
        Prompt_Clarity,
        Prompt_Context,
        Prompt_Instructions,
        Prompt_Role,
        Prompt_Formatter,
        Prompt_Improver,
    ],
).as_tool("detailed_prompt_refiner_tool", "Generates detailed refined prompts.")

# === ULTIMATE PROMPT AGENT ===
Ultimate_Prompt_Refiner = Agent(
    name="Ultimate Prompt Refiner",
    instructions="""
You are PromptSmith Pro. Transform vague or incomplete prompts into powerful, structured ones.
Ask once for context and preferred style ("short" or "detailed").
Use the corresponding refiner tool based on style.
Return only:
{"improved_prompt": "Final refined prompt text"}
""",
    model=model,
    tools=[ShortPromptRefiner, DetailedPromptRefiner],
)

# =========================================================
# ROUTES
# =========================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring."""
    return {"status": "healthy", "service": "Promptify AI API"}

@app.post("/api/improve-stream")
async def improve_prompt_stream(request: PromptRequest):
    """
    Improve a prompt with streaming response.
    Returns NDJSON (newline-delimited JSON).
    """
    
    async def generate() -> AsyncGenerator[str, None]:
        try:
            session = SQLiteSession("prompt_stream.db")
            
            result = Runner.run_streamed(
                Ultimate_Prompt_Refiner,
                input=request.user_input,
                session=session
            )
            
            full_output = ""
            
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    delta = event.data.delta
                    full_output += delta
                    yield json.dumps({"chunk": delta}) + "\n"
            
            # Store in Supabase after streaming completes
            try:
                store_in_supabase(request.user_id, request.user_input, full_output.strip())
            except Exception as e:
                logger.error(f"Supabase storage error: {str(e)}")
            
            # Send completion signal with full output
            yield json.dumps({"status": "complete", "full_output": full_output.strip()}) + "\n"
            
        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            yield json.dumps({"error": "stream_failed", "detail": str(e)}) + "\n"
    
    return StreamingResponse(generate(), media_type="application/x-ndjson")

@app.post("/api/improve")
async def improve_prompt(request: PromptRequest):
    """
    Non-streaming endpoint for prompt improvement.
    Useful for clients that don't support streaming.
    """
    try:
        session = SQLiteSession("prompt_stream.db")
        
        result = Runner.run(
            Ultimate_Prompt_Refiner,
            input=request.user_input,
            session=session
        )
        
        # Store in Supabase
        try:
            store_in_supabase(request.user_id, request.user_input, str(result))
        except Exception as e:
            logger.error(f"Supabase storage error: {str(e)}")
        
        return {"improved_prompt": result}
        
    except Exception as e:
        logger.error(f"Prompt improvement error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Welcome endpoint."""
    return {
        "message": "Welcome to Promptify AI API",
        "endpoints": {
            "health": "/health",
            "streaming": "/api/improve-stream",
            "non-streaming": "/api/improve",
            "docs": "/docs"
        }
    }

# =========================================================
# ERROR HANDLERS
# =========================================================
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(status_code=400, detail=str(exc))

# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )