from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json
from agents import Agent, Runner,SQLiteSession
from my_configuration.configuration import model
from openai.types.responses import ResponseTextDeltaEvent
from my_supabase.supaabse import store_in_supabase

app = FastAPI(title="Promptify API", version="1.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# REQUEST MODEL
# =========================================================
class PromptRequest(BaseModel):
    user_input: str
    user_id: str = "user_default"

# =========================================================
# AGENTS INITIALIZATION
# =========================================================
def initialize_agents():
    """Initialize all prompt refinement agents"""
    
    # 1️⃣ PROMPT IMPROVER
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

    Prompt_Improver_as_tool = Prompt_Improver.as_tool(
        tool_name="prompt_improver_tool",
        tool_description="Turns vague user input into a clear, structured prompt ready for any AI model.",
    )

    # 2️⃣ STYLE ENHANCER
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

    Style_Enhancer_as_tool = Style_Enhancer.as_tool(
        tool_name="style_enhancer_tool",
        tool_description="Polishes the prompt for clarity and professional tone.",
    )

    # 3️⃣ CONTEXT ENRICHER
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

    Context_Enricher_as_tool = Context_Enricher.as_tool(
        tool_name="context_enricher_tool",
        tool_description="Adds small but relevant context so the prompt is complete.",
    )

    # 4️⃣ PROMPT EXPANDER
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

    Prompt_Expander_as_tool = Prompt_Expander.as_tool(
        tool_name="prompt_expander_tool",
        tool_description="Creates 3 stylistic variations (technical, creative, concise) of the improved prompt.",
    )

    # 5️⃣ RESPONDER (ORCHESTRATOR)
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
            Prompt_Improver_as_tool,
            Style_Enhancer_as_tool,
            Context_Enricher_as_tool,
            Prompt_Expander_as_tool,
        ],
    )

    return Responder

# Initialize agents
responder_agent = initialize_agents()

# =========================================================
# ROUTES
# =========================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Promptify API",
        "version": "1.0.0",
        "endpoints": {
            "improve": "POST /api/improve",
            "improve-stream": "POST /api/improve-stream",
            "health": "GET /health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/api/improve")
async def improve_prompt(request: PromptRequest):
    """
    Improve a prompt and return the full result.
    """
    try:
        session = SQLiteSession("prompt_stream.db")
        
        result = Runner.run_streamed(
            responder_agent,
            input=request.user_input,
            session=session
        )
        
        full_output = ""
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                full_output += event.data.delta

        improved_prompt = full_output.strip()
        
        # Store in Supabase
        store_in_supabase(request.user_id, request.user_input, improved_prompt)
        
        return {
            "status": "success",
            "original_prompt": request.user_input,
            "improved_prompt": improved_prompt,
            "user_id": request.user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/improve-stream")
async def improve_prompt_stream(request: PromptRequest):
    """
    Improve a prompt with streaming response.
    """
    async def generate():
        try:
            session = SQLiteSession("prompt_stream.db")
            
            result = Runner.run_streamed(
                responder_agent,
                input=request.user_input,
                session=session
            )
            
            full_output = ""
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    delta = event.data.delta
                    full_output += delta
                    # Stream as JSON lines
                    yield json.dumps({"chunk": delta}) + "\n"
            
            # Store in Supabase after streaming completes
            store_in_supabase(request.user_id, request.user_input, full_output.strip())
            
            # Send completion signal
            yield json.dumps({"status": "complete", "full_output": full_output.strip()}) + "\n"
            
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)