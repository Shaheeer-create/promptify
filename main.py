from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
from agents import Agent, Runner, SQLiteSession, set_tracing_disabled
from my_configuration.configuration import model
from my_supabase.supaabse import store_in_supabase
from openai.types.responses import ResponseTextDeltaEvent


# =========================================================
# FASTAPI SETUP
# =========================================================
app = FastAPI(title="Promptify Ultimate API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For deployment, limit to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# REQUEST / RESPONSE MODELS
# =========================================================
class PromptRequest(BaseModel):
    user_input: str
    user_id: str = "user_default"


class AgentOutput(BaseModel):
    improved_prompt: str


# =========================================================
# BUILD AGENTS (Initialize Once)
# =========================================================
set_tracing_disabled(True)

# ---------- Base Tools ----------
Prompt_Clarity = Agent(
    name="Prompt Clarity Enhancer",
    instructions="""You are ClarityMaster. Refine vague or confusing prompts into clear, specific, unambiguous statements. Keep intent intact. Output max 35 words. Only provide the refined prompt.""",
    model=model
).as_tool("prompt_clarity_tool", "Refines vague prompts into clear, specific versions.")

Prompt_Context = Agent(
    name="Prompt Context Enricher",
    instructions="""You are ContextGuru. Enrich prompts with relevant background, examples, or scenario. Keep intent intact. Output max 40 words. Only provide the refined prompt.""",
    model=model
).as_tool("prompt_context_tool", "Adds context/examples to prompts.")

Prompt_Instructions = Agent(
    name="Prompt Instruction Designer",
    instructions="""You are InstructionSmith. Add step-by-step guidance or structured tasks to prompts. Keep intent intact. Output max 40 words. Only provide the refined prompt.""",
    model=model
).as_tool("prompt_instruction_tool", "Adds structured instructions to prompts.")

Prompt_Role = Agent(
    name="Prompt Role Assigner",
    instructions="""You are RoleMaster. Add role, persona, or tone if needed. Keep intent intact. Output max 35 words. Only provide the refined prompt.""",
    model=model
).as_tool("prompt_role_tool", "Adds role or tone to prompts.")

Prompt_Formatter = Agent(
    name="Prompt Output Formatter",
    instructions="""You are FormatGuru. Specify output format (bullet points, table, code, summary, etc.). Keep intent intact. Output max 40 words. Only provide the refined prompt.""",
    model=model
).as_tool("prompt_formatter_tool", "Specifies output format for prompts.")

Prompt_Improver = Agent(
    name="Prompt Improver",
    instructions="""You are PromptSmith. Polish prompts to make them concise, clear, and professional. Keep intent intact. Output max 40 words. Only provide the refined prompt.""",
    model=model
).as_tool("prompt_improver_tool", "Polishes prompts for clarity and professionalism.")


# ---------- Short Prompt Refiner ----------
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
Return your final answer as:
{"improved_prompt": "Final refined prompt text here"}
Do not use Markdown or commentary.
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
).as_tool("short_prompt_refiner_tool", "Generates short, concise refined prompts.")


# ---------- Detailed Prompt Refiner ----------
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
Return as:
{"improved_prompt": "Final refined prompt text here"}
No Markdown or commentary.
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
).as_tool("detailed_prompt_refiner_tool", "Generates long, detailed refined prompts.")


# ---------- Ultimate Prompt Refiner ----------
Ultimate_Prompt_Refiner = Agent(
    name="Ultimate Prompt Refiner",
    instructions="""
You are PromptSmith Pro — a professional prompt optimizer.
Goal: Turn any user prompt into a clear, structured, and professional version.

Rules:
1. Ask the user once if they want a "short" or "detailed" refined prompt.
2. If they skip, default to "short".
3. For:
   - "short" → use ShortPromptRefiner
   - "detailed" → use DetailedPromptRefiner
4. Output must be JSON:
   {"improved_prompt": "Refined prompt here"}
No Markdown, greetings, or code fences.
""",
    model=model,
    tools=[ShortPromptRefiner, DetailedPromptRefiner],
)


# =========================================================
# FASTAPI ENDPOINT
# =========================================================
@app.post("/api/improve", response_model=AgentOutput)
async def improve_prompt(request: PromptRequest):
    """
    Accepts user_input and user_id, processes via Ultimate Prompt Refiner,
    stores conversation in Supabase, and returns improved prompt.
    """
    try:
        session = SQLiteSession(request.user_id, "promptify_session.db")
        combined_input = f"User prompt: {request.user_input}\nAsk for context and preferred style, then refine using the appropriate short or detailed agent."

        result = Runner.run_streamed(Ultimate_Prompt_Refiner, input=combined_input, session=session)

        full_output = ""
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                full_output += event.data.delta

        # Store conversation in Supabase
        store_in_supabase(request.user_id, request.user_input, full_output.strip())

        # Clean output JSON
        try:
            parsed = json.loads(full_output.strip())
            return parsed
        except json.JSONDecodeError:
            return {"improved_prompt": full_output.strip()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================
# ROOT ENDPOINT
# =========================================================
@app.get("/")
def root():
    return {"message": "Welcome to Promptify Ultimate API! Use POST /api/improve to refine prompts."}
