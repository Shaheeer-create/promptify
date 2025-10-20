from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json
from typing import AsyncGenerator
from agents import Agent, Runner, SQLiteSession, set_tracing_disabled
from my_configuration.configuration import model
from openai.types.responses import ResponseTextDeltaEvent
from my_supabase.supaabse import store_in_supabase
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
    user_input: str
    user_id: str = "user_default"
    style: str = "short"  # "short" or "detailed"


class PromptResponse(BaseModel):
    improved_prompt: str
    user_id: str


# =========================================================
# INITIALIZE FASTAPI APP
# =========================================================
app = FastAPI(
    title="Promptify API",
    description="Professional Prompt Refinement Service",
    version="1.0.0"
)

# =========================================================
# CORS MIDDLEWARE
# =========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# GLOBAL AGENTS INITIALIZATION
# =========================================================
agents_initialized = False
Ultimate_Prompt_Refiner = None
ShortPromptRefiner = None
DetailedPromptRefiner = None


async def initialize_agents():
    """Initialize all agents once on startup"""
    global agents_initialized, Ultimate_Prompt_Refiner, ShortPromptRefiner, DetailedPromptRefiner
    
    if agents_initialized:
        return
    
    set_tracing_disabled(True)

    # =========================
    # Tool Agents
    # =========================
    Prompt_Clarity = Agent(
        name="Prompt Clarity Enhancer",
        instructions="""
You are ClarityMaster. Refine vague or confusing prompts into clear, specific, unambiguous statements. Keep intent intact. Output max 35 words. Only provide the refined prompt.
""",
        model=model
    ).as_tool(
        tool_name="prompt_clarity_tool",
        tool_description="Refines vague prompts into clear, specific versions."
    )

    Prompt_Context = Agent(
        name="Prompt Context Enricher",
        instructions="""
You are ContextGuru. Enrich prompts with relevant background, examples, or scenario. Keep intent intact. Output max 40 words. Only provide the refined prompt.
""",
        model=model
    ).as_tool(
        tool_name="prompt_context_tool",
        tool_description="Adds context/examples to prompts."
    )

    Prompt_Instructions = Agent(
        name="Prompt Instruction Designer",
        instructions="""
You are InstructionSmith. Add step-by-step guidance or structured tasks to prompts. Keep intent intact. Output max 40 words. Only provide the refined prompt.
""",
        model=model
    ).as_tool(
        tool_name="prompt_instruction_tool",
        tool_description="Adds structured instructions to prompts."
    )

    Prompt_Role = Agent(
        name="Prompt Role Assigner",
        instructions="""
You are RoleMaster. Add role, persona, or tone if needed. Keep intent intact. Output max 35 words. Only provide the refined prompt.
""",
        model=model
    ).as_tool(
        tool_name="prompt_role_tool",
        tool_description="Adds role or tone to prompts."
    )

    Prompt_Formatter = Agent(
        name="Prompt Output Formatter",
        instructions="""
You are FormatGuru. Specify output format (bullet points, table, code, summary, etc.). Keep intent intact. Output max 40 words. Only provide the refined prompt.
""",
        model=model
    ).as_tool(
        tool_name="prompt_formatter_tool",
        tool_description="Specifies output format for prompts."
    )

    Prompt_Improver = Agent(
        name="Prompt Improver",
        instructions="""
You are PromptSmith. Polish prompts to make them concise, clear, and professional. Keep intent intact. Output max 40 words. Only provide the refined prompt.
""",
        model=model
    ).as_tool(
        tool_name="prompt_improver_tool",
        tool_description="Polishes prompts for clarity and professionalism."
    )

    # =========================
    # Short Prompt Agent
    # =========================
    ShortPromptRefiner = Agent(
        name="Short Prompt Refiner",
        instructions="""
You are ShortPromptSmith. Refine user prompt to be fully optimized, clear, structured, and concise (max 40 words). Apply all tools in order:
1. Clarity
2. Context
3. Instructions
4. Role
5. Formatter
6. Improver
Return your final answer as a plain text JSON-like object, like this:
{"improved_prompt": "Final refined prompt text here"}
Do not use Markdown formatting, code blocks, or commentary.
Output only the final short prompt.
""",
        model=model,
        tools=[
            Prompt_Clarity,
            Prompt_Context,
            Prompt_Instructions,
            Prompt_Role,
            Prompt_Formatter,
            Prompt_Improver
        ],
    ).as_tool(
        tool_name="short_prompt_refiner_tool",
        tool_description="Generates short, concise refined prompts."
    )

    # =========================
    # Detailed Prompt Agent
    # =========================
    DetailedPromptRefiner = Agent(
        name="Detailed Prompt Refiner",
        instructions="""
You are DetailedPromptSmith. Refine user prompt to be fully optimized, clear, structured, and detailed (up to 80 words). Apply all tools in order:
1. Clarity
2. Context
3. Instructions
4. Role
5. Formatter
6. Improver
Return your final answer as a plain text JSON-like object, like this:
{"improved_prompt": "Final refined prompt text here"}
Do not use Markdown formatting, code blocks, or commentary.
Output only the final detailed prompt with practical examples.
""",
        model=model,
        tools=[
            Prompt_Clarity,
            Prompt_Context,
            Prompt_Instructions,
            Prompt_Role,
            Prompt_Formatter,
            Prompt_Improver
        ],
    ).as_tool(
        tool_name="detailed_prompt_refiner_tool",
        tool_description="Generates long, detailed refined prompts."
    )

    # =========================
    # Ultimate Prompt Refiner Agent
    # =========================
    Ultimate_Prompt_Refiner = Agent(
        name="Ultimate Prompt Refiner",
        instructions="""
You are PromptSmith Pro — a professional prompt optimizer.

Goal:
Turn any user prompt into a clear, structured, and professional version.

Rules:
1. For "short" → use ShortPromptRefiner (≤40 words)
2. For "detailed" → use DetailedPromptRefiner (≤80 words)
3. Output must be plain text JSON:
   {"improved_prompt": "Refined prompt here"}
4. No Markdown, no commentary, no code fences, no greetings.
""",
        model=model,
        tools=[ShortPromptRefiner, DetailedPromptRefiner],
    )

    agents_initialized = True
    logger.info("Agents initialized successfully")


# =========================================================
# STARTUP EVENT
# =========================================================
@app.on_event("startup")
async def startup_event():
    """Initialize agents on application startup"""
    await initialize_agents()
    logger.info("FastAPI application started")


# =========================================================
# STREAMING RESPONSE GENERATOR
# =========================================================
async def stream_prompt_refinement(
    agent: Agent,
    user_input: str,
    session: SQLiteSession,
    user_id: str
) -> AsyncGenerator[str, None]:
    """Stream refined prompt from agent"""
    combined_input = f"User prompt: {user_input}\nRefine this prompt professionally."
    
    result = Runner.run_streamed(agent, input=combined_input, session=session)
    full_output = ""
    
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            chunk = event.data.delta
            full_output += chunk
            yield chunk
    
    # Store in Supabase after streaming completes
    try:
        store_in_supabase(user_id, user_input, full_output.strip())
    except Exception as e:
        logger.error(f"Error storing in Supabase: {e}")


# =========================================================
# API ENDPOINTS
# =========================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Promptify API",
        "version": "1.0.0"
    }


@app.post("/refine", response_model=PromptResponse)
async def refine_prompt(request: PromptRequest, background_tasks: BackgroundTasks):
    """
    Refine a prompt synchronously and return the result.
    
    - **user_input**: The prompt to refine
    - **user_id**: User identifier (default: "user_default")
    - **style**: "short" (≤40 words) or "detailed" (≤80 words)
    """
    try:
        session = SQLiteSession(request.user_id, "prompt_stream.db")
        
        # Select agent based on style
        agent = DetailedPromptRefiner if request.style == "detailed" else ShortPromptRefiner
        
        combined_input = f"User prompt: {request.user_input}\nRefine this prompt professionally."
        
        result = Runner.run_streamed(agent, input=combined_input, session=session)
        full_output = ""
        
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                full_output += event.data.delta
        
        full_output = full_output.strip()
        
        # Background task to store in Supabase
        background_tasks.add_task(
            store_in_supabase,
            request.user_id,
            request.user_input,
            full_output
        )
        
        # Parse JSON response
        try:
            response_data = json.loads(full_output)
            improved_prompt = response_data.get("improved_prompt", full_output)
        except json.JSONDecodeError:
            improved_prompt = full_output
        
        return PromptResponse(
            improved_prompt=improved_prompt,
            user_id=request.user_id
        )
    
    except Exception as e:
        logger.error(f"Error refining prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refine/stream")
async def refine_prompt_stream(request: PromptRequest):
    """
    Refine a prompt and stream the response in real-time.
    
    - **user_input**: The prompt to refine
    - **user_id**: User identifier (default: "user_default")
    - **style**: "short" (≤40 words) or "detailed" (≤80 words)
    """
    try:
        session = SQLiteSession(request.user_id, "prompt_stream.db")
        
        # Select agent based on style
        agent = DetailedPromptRefiner if request.style == "detailed" else ShortPromptRefiner
        
        return StreamingResponse(
            stream_prompt_refinement(agent, request.user_input, session, request.user_id),
            media_type="text/event-stream"
        )
    
    except Exception as e:
        logger.error(f"Error streaming prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return {
        "service": "Promptify API",
        "version": "1.0.0",
        "description": "Professional Prompt Refinement Service",
        "endpoints": {
            "health": "/health",
            "refine": "/refine (POST)",
            "stream": "/refine/stream (POST)",
            "docs": "/docs"
        }
    }


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


# =========================================================
# RUN (for development)
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