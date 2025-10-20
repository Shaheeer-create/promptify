from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
from agents import Agent, Runner, SQLiteSession, set_tracing_disabled
from my_configuration.configuration import model
from my_supabase.supaabse import store_in_supabase
from openai.types.responses import ResponseTextDeltaEvent
from pathlib import Path

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
)
Prompt_Clarity_as_tool=Prompt_Clarity.as_tool(tool_name="prompt_clarity_tool",tool_description= "Refines vague prompts into clear, specific versions.")

Prompt_Context = Agent(
    name="Prompt Context Enricher",
    instructions="""You are ContextGuru. Enrich prompts with relevant background, examples, or scenario. Keep intent intact. Output max 40 words. Only provide the refined prompt.""",
    model=model
)
Prompt_Context_as_tool=Prompt_Context.as_tool(tool_name="prompt_context_tool", tool_description="Adds context/examples to prompts.")

Prompt_Instructions = Agent(
    name="Prompt Instruction Designer",
    instructions="""You are InstructionSmith. Add step-by-step guidance or structured tasks to prompts. Keep intent intact. Output max 40 words. Only provide the refined prompt.""",
    model=model
)
Prompt_Instructions_as_tool=Prompt_Instructions.as_tool(tool_name="prompt_instruction_tool",tool_description="Adds structured instructions to prompts.")

Prompt_Role = Agent(
    name="Prompt Role Assigner",
    instructions="""You are RoleMaster. Add role, persona, or tone if needed. Keep intent intact. Output max 35 words. Only provide the refined prompt.""",
    model=model
)
Prompt_Role_as_tool=Prompt_Role.as_tool(tool_name="prompt_role_tool",tool_description="Adds role or tone to prompts.")

Prompt_Formatter = Agent(
    name="Prompt Output Formatter",
    instructions="""You are FormatGuru. Specify output format (bullet points, table, code, summary, etc.). Keep intent intact. Output max 40 words. Only provide the refined prompt.""",
    model=model
)
Prompt_Formatter_as_tool=Prompt_Formatter.as_tool(tool_name="prompt_formatter_tool",tool_description="Specifies output format for prompts.")

Prompt_Improver = Agent(
    name="Prompt Improver",
    instructions="""You are PromptSmith. Polish prompts to make them concise, clear, and professional. Keep intent intact. Output max 40 words. Only provide the refined prompt.""",
    model=model
)
Prompt_Improver_as_tool=Prompt_Improver.as_tool(tool_name="prompt_improver_tool",tool_description="Polishes prompts for clarity and professionalism.")


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
        Prompt_Clarity_as_tool,
        Prompt_Context_as_tool,
        Prompt_Instructions_as_tool,
        Prompt_Role_as_tool,
        Prompt_Formatter_as_tool,
        Prompt_Improver_as_tool
    ],
)
ShortPromptRefiner_as_tool=ShortPromptRefiner.as_tool(tool_name="short_prompt_refiner_tool", tool_description="Generates short, concise refined prompts.")


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
        Prompt_Clarity_as_tool,
        Prompt_Context_as_tool,
        Prompt_Instructions_as_tool,
        Prompt_Role_as_tool,
        Prompt_Formatter_as_tool,
        Prompt_Improver_as_tool

    ],
)
DetailedPromptRefiner_as_tool=DetailedPromptRefiner.as_tool(tool_name="detailed_prompt_refiner_tool", tool_description="Generates long, detailed refined prompts.")


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
    tools=[ShortPromptRefiner_as_tool, DetailedPromptRefiner_as_tool],
)




# =========================================================
# FASTAPI ENDPOINT
# =========================================================
from pathlib import Path
import os

@app.post("/api/improve", response_model=AgentOutput)
async def improve_prompt(request: PromptRequest):
    try:
        # =========================================================
        # ✅ Use temporary writable directory for serverless environments
        # =========================================================
        TMP_DIR = Path("/tmp/promptify_db")
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        db_path = TMP_DIR / f"{request.user_id}_promptify.db"

        session = SQLiteSession(request.user_id, str(db_path))

        # =========================================================
        # Prepare user input for processing
        # =========================================================
        combined_input = (
            f"User prompt: {request.user_input}\n"
            "Ask for context and preferred style, then refine using the appropriate short or detailed agent."
        )

        # =========================================================
        # Run the Ultimate Prompt Refiner agent
        # =========================================================
        result = Runner.run_streamed(Ultimate_Prompt_Refiner, input=combined_input, session=session)

        full_output = ""
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                full_output += event.data.delta

        # =========================================================
        # Store the interaction in Supabase
        # =========================================================
        store_in_supabase(request.user_id, request.user_input, full_output.strip())

        # =========================================================
        # Parse JSON if valid, else return raw text
        # =========================================================
        try:
            parsed = json.loads(full_output.strip())
            return parsed
        except json.JSONDecodeError:
            return {"improved_prompt": full_output.strip()}

    except Exception as e:
        # Provide readable backend error message
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


@app.post("/api/improve-detailed", response_model=AgentOutput)
async def improve_prompt_detailed(request: PromptRequest):
    try:
        TMP_DIR = Path("/tmp/promptify_db")
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        db_path = TMP_DIR / f"{request.user_id}_promptify.db"

        session = SQLiteSession(request.user_id, str(db_path))

        combined_input = f"User prompt: {request.user_input}\nRefine this prompt in a detailed, structured way."

        result = Runner.run_streamed(DetailedPromptRefiner, input=combined_input, session=session)

        full_output = ""
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                full_output += event.data.delta

        store_in_supabase(request.user_id, request.user_input, full_output.strip())

        try:
            parsed = json.loads(full_output.strip())
            return parsed
        except json.JSONDecodeError:
            return {"improved_prompt": full_output.strip()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


# =========================================================
# ROOT ENDPOINT
# =========================================================
@app.get("/")
def root():
    return {"message": "Welcome to Promptify Ultimate API! Use POST /api/improve to refine prompts."}
