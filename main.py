from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents import Agent, Runner, SQLiteSession, set_tracing_disabled
from my_configuration.configuration import model
from openai.types.responses import ResponseTextDeltaEvent
from my_supabase.supaabse import store_in_supabase
import json
import os

# =========================================================
# REQUEST MODEL
# =========================================================
class PromptRequest(BaseModel):
    user_input: str
    user_id: str

# =========================================================
# FASTAPI SETUP
# =========================================================
app = FastAPI(title="Promptify AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your frontend URL later
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
# ROUTE: IMPROVE PROMPT
# =========================================================
@app.post("/api/improve")
async def improve_prompt(request: PromptRequest):
    try:
        db_path = os.path.abspath("prompt_stream.db")
        session = SQLiteSession(request.user_id, db_path)

        # Run agent pipeline
        combined_input = (
            f"User prompt: {request.user_input}\n"
            f"Ask for context and preferred style, then refine accordingly."
        )

        result = Runner.run_streamed(Ultimate_Prompt_Refiner, input=combined_input, session=session)

        full_output = ""
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                full_output += event.data.delta

        # Extract JSON safely
        try:
            json_output = json.loads(full_output.strip())
        except json.JSONDecodeError:
            json_output = {"improved_prompt": full_output.strip()}

        # Save in Supabase
        await store_in_supabase(
            user_id=request.user_id,
            user_message=request.user_input,
            ai_message=json_output.get("improved_prompt", "N/A"),
        )

        return json_output

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def home():
    return {"message": "Promptify AI API is running 🚀"}
