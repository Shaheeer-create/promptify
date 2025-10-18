from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agents import Agent, Runner, SQLiteSession, set_tracing_disabled
from my_configuration.configuration import model
from openai.types.responses import ResponseTextDeltaEvent
from my_supabase.supaabse import store_in_supabase
from supabase import create_client
import asyncio, os

# =========================================================
# 🧩 FastAPI + Supabase Setup
# =========================================================
app = FastAPI(title="Promptify AI Backend", version="1.0")

# Enable frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, use ["https://yourfrontend.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

set_tracing_disabled(True)

# =========================================================
# 🧠 Define All Agents
# =========================================================
Prompt_Improver = Agent(
    name="Prompt Improver",
    instructions="""
You are **PromptSmith**, a professional prompt engineer.
Your goal is to take a vague or lazy user prompt and rewrite it into a **clear, detailed, and professional version**
that can be directly pasted into another AI model.

Rules:
- Keep the same intent, never answer it.
- Add clarity and structure only.
- Be concise (max 40 words).
- Output only the rewritten prompt — no explanations or JSON.
Example:
User: "tell me about ai"
Output: "Explain Artificial Intelligence, its main subfields, and real-world applications in a concise and informative way."
""",
    model=model,
)

Style_Enhancer = Agent(
    name="Style Enhancer",
    instructions="""
You are **ToneMaster**, a writing specialist.
Take the improved prompt and polish its tone for professionalism and fluency — keeping meaning identical.

Rules:
- Fix grammar and flow only.
- Never change the intent.
- Output one clean line — no JSON, no extra text.
""",
    model=model,
)

Context_Enricher = Agent(
    name="Context Enricher",
    instructions="""
You are **ContextGuru**, a reasoning enhancer.
Add short, helpful context so the prompt is self-contained and ready for any LLM.

Rules:
- Do not answer the question.
- Add only minimal, relevant context.
- Output one single-line final prompt, nothing else.
""",
    model=model,
)

Prompt_Expander = Agent(
    name="Prompt Expander",
    instructions="""
You are **PromptExpander**, an expert prompt designer.
Your job is to take a refined, professional prompt and create 3 alternative versions optimized for different purposes.

Return ONLY plain text (no JSON or markup), in this structure:

Technical Version:
<version_1>

Creative/Explanatory Version:
<version_2>

Concise Version:
<version_3>

Rules:
- Keep all versions faithful to the core meaning.
- Make each distinct in style and detail level.
- Do not include bullet points, markdown, or explanations.
- Each version should be between 1–3 sentences.
""",
    model=model,
)

# Convert them to tools
Prompt_Improver_tool = Prompt_Improver.as_tool("prompt_improver_tool", "Improves vague prompts")
Style_Enhancer_tool = Style_Enhancer.as_tool("style_enhancer_tool", "Enhances style and grammar")
Context_Enricher_tool = Context_Enricher.as_tool("context_enricher_tool", "Adds useful context")
Prompt_Expander_tool = Prompt_Expander.as_tool("prompt_expander_tool", "Creates 3 style variations")

# =========================================================
# 🧩 Orchestrator Agent
# =========================================================
Responder = Agent(
    name="Prompt Orchestrator",
    model=model,
    instructions="""
You are **PromptOrchestrator**, a master prompt refiner.

Goal:
Transform a lazy or vague user prompt into a **set of clean, professional AI-ready prompts** suitable for direct use in any LLM.

You have access to these tools:
- prompt_improver_tool
- style_enhancer_tool
- context_enricher_tool
- prompt_expander_tool

Process:
1. Always treat the user input as a prompt to be improved, not as a question to answer.
2. Use:
   - prompt_improver_tool → to structure and clarify.
   - style_enhancer_tool → to polish tone.
   - context_enricher_tool → to make it self-contained.
   - prompt_expander_tool → to generate stylistic variants.
3. Return all final versions as plain text, directly copyable into other AI models.

Output Rules:
- Output only text (no JSON, no markup, no labels beyond the section headers).
- Keep tone natural and professional.
""",
    tools=[
        Prompt_Improver_tool,
        Style_Enhancer_tool,
        Context_Enricher_tool,
        Prompt_Expander_tool,
    ],
)

# =========================================================
# 🧾 Utility: Verify Supabase Token
# =========================================================
def get_user_id(token: str):
    try:
        user = supabase.auth.get_user(token)
        return user.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or missing Supabase token")

# =========================================================
# 🚀 API Route: Run Agent
# =========================================================
@app.post("/run-agent")
async def run_agent(request: Request):
    data = await request.json()
    user_input = data.get("input")
    token = request.headers.get("Authorization", "").replace("Bearer ", "")

    if not user_input:
        raise HTTPException(status_code=400, detail="Missing input text")

    user_id = get_user_id(token)
    session = SQLiteSession(user_id, "prompt_stream.db")

    # Run the responder agent
    result = Runner.run(Responder, input=user_input, session=session)
    output = result.output_text.strip()

    # Save results in Supabase
    store_in_supabase(user_id, user_input, output)

    return {"user_id": user_id, "input": user_input, "output": output}


# =========================================================
# 🧠 Health Check
# =========================================================
@app.get("/")
async def root():
    return {"message": "Promptify AI Backend is running 🚀"}


# =========================================================
# 🏁 Run Locally
# =========================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
