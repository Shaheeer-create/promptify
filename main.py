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
from image_agents import PortraitPrompt_Enhancer

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
# ---------- Base Tools (Token-Optimized) ----------
Prompt_Clarity = Agent(
    name="Clarity",
    instructions="Make the prompt clear and unambiguous. Keep intent same. Max 30 words. Return only refined text.",
    model=model
)
Prompt_Clarity_as_tool = Prompt_Clarity.as_tool(tool_name="clarity_tool", tool_description="Improves clarity.")

Prompt_Context = Agent(
    name="Context",
    instructions="Add helpful background or example if needed. Max 35 words. Return only refined text.",
    model=model
)
Prompt_Context_as_tool = Prompt_Context.as_tool(tool_name="context_tool",tool_description= "Adds relevant context.")

Prompt_Instructions = Agent(
    name="Instruction",
    instructions="Add structured steps or guidance if relevant. Max 35 words. Return only refined text.",
    model=model
)
Prompt_Instructions_as_tool = Prompt_Instructions.as_tool(tool_name="instruction_tool", tool_description="Adds clear steps.")

Prompt_Role = Agent(
    name="Role",
    instructions="Add role or tone (teacher, expert, friendly, etc.) only if it improves prompt. Max 30 words.",
    model=model
)
Prompt_Role_as_tool = Prompt_Role.as_tool(tool_name="role_tool", tool_description="Adds helpful tone or role.")

Prompt_Formatter = Agent(
    name="Formatter",
    instructions="If helpful, specify output format (bullets, code, table, summary). Max 30 words.",
    model=model
)
Prompt_Formatter_as_tool = Prompt_Formatter.as_tool(tool_name="format_tool", tool_description="Defines output format.")

Prompt_Improver = Agent(
    name="Improver",
    instructions="Polish to sound concise and professional. Max 30 words.",
    model=model
)
Prompt_Improver_as_tool = Prompt_Improver.as_tool(tool_name="improver_tool", tool_description="Polishes final prompt.")


# ---------- Short Refiner ----------
ShortPromptRefiner = Agent(
    name="Short Refiner",
    instructions="""Refine the prompt clearly and concisely (max 40 words).
Use all tools once in order: Clarity → Context → Instructions → Role → Formatter → Improver.
Return as JSON: {"improved_prompt": "Final refined prompt"}.""",
    model=model,
    tools=[
        Prompt_Clarity_as_tool,
        Prompt_Context_as_tool,
        Prompt_Instructions_as_tool,
        Prompt_Role_as_tool,
        Prompt_Formatter_as_tool,
        Prompt_Improver_as_tool,
    ],
)
ShortPromptRefiner_as_tool = ShortPromptRefiner.as_tool(tool_name="short_refiner_tool",tool_description= "Makes short refined prompts.")


# ---------- Detailed Refiner ----------
DetailedPromptRefiner = Agent(
    name="Detailed Refiner",
    instructions="""Refine the prompt with more detail and examples (max 80 words).
Use same tool sequence as short version.
Return as JSON: {"improved_prompt": "Final refined prompt"}.""",
    model=model,
    tools=[
        Prompt_Clarity_as_tool,
        Prompt_Context_as_tool,
        Prompt_Instructions_as_tool,
        Prompt_Role_as_tool,
        Prompt_Formatter_as_tool,
        Prompt_Improver_as_tool,
    ],
)
DetailedPromptRefiner_as_tool = DetailedPromptRefiner.as_tool(tool_name="detailed_refiner_tool",tool_description="Makes detailed refined prompts.")


# ---------- Ultimate Refiner ----------
Ultimate_Prompt_Refiner = Agent(
    name="Ultimate Refiner",
    instructions="""Refine any user prompt clearly and professionally.
"short" or "detailed" version. Default = short use detailed when user said that.
If short → use short_refiner_tool. If detailed → use detailed_refiner_tool.
Return JSON only: {"improved_prompt": "Refined prompt"}.""",
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


@app.post("/api/improve-image", response_model=AgentOutput)
async def improve_image_prompt(request: PromptRequest):
    try:
        TMP_DIR = Path("/tmp/promptify_db")
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        db_path = TMP_DIR / f"{request.user_id}_portrait_prompt.db"

        session = SQLiteSession(request.user_id, str(db_path))

        # Run PortraitPrompt_Enhancer as a streamed agent
        result = Runner.run_streamed(
            PortraitPrompt_Enhancer,
            input=request.user_input,
            session=session
        )

        full_output = ""
        async for event in result.stream_events():
            if event.type == "raw_response_event" and hasattr(event.data, "delta"):
                full_output += event.data.delta

        final_prompt = full_output.strip()

        # Store in Supabase
        store_in_supabase(request.user_id, request.user_input, final_prompt)

        return {"improved_prompt": final_prompt}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")





# =========================================================
# ROOT ENDPOINT
# =========================================================
@app.get("/")
def root():
    return {"message": "Welcome to Promptify Ultimate API! Use POST /api/improve to refine prompts."}
