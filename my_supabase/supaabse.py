from datetime import datetime,timezone
from supabase import create_client, Client
from decouple import config



# Environment variables or config
SUPABASE_URL =config("SUPABASE_URL", "https://sixijthpfirczkbdwvhh.supabase.co")
SUPABASE_API_KEY = config("SUPABASE_API_KEY", "your-anon-or-service-key")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)


def store_in_supabase(session_id: str, user_input: str, agent_output: str):
    data = {
        "session_id": session_id,
        "user_input": user_input,
        "agent_output": agent_output,
        # Use timezone-aware UTC timestamp
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    # Run insert silently (no print)
    supabase.table("conversations").insert(data).execute()


