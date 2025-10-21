from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio, json
from agents import Runner, SQLiteSession, set_tracing_disabled
from ogcode import Ultimate_Prompt_Refiner

app = FastAPI(title="Prompt Refinement API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

set_tracing_disabled(True)

class PromptRequest(BaseModel):
    user_id: str
    prompt: str


@app.post("/refine-general")
async def refine_general(data: PromptRequest):
    try:
        # ✅ Use /tmp to avoid Vercel read-only file system errors
        TMP_DIR = Path("/tmp/promptify_db")
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        db_path = TMP_DIR / f"{data.user_id}_promptify.db"
        session = SQLiteSession(data.user_id, str(db_path))

        # ✅ Use thread-safe async wrapper
        result = await asyncio.to_thread(
            lambda: asyncio.run(
                Runner.run(
                    starting_agent=Ultimate_Prompt_Refiner,
                    session=session,
                    input=data.prompt,
                )
            )
        )

        # ✅ Parse output safely
        try:
            parsed = json.loads(result.strip())
            return parsed
        except json.JSONDecodeError:
            return {"refined_prompt": result.strip()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


@app.get("/")
def root():
    return {"message": "Promptify Refine API active"}
