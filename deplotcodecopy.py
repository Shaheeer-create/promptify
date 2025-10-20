

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
