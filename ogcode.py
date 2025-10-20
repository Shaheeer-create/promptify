from pydantic import BaseModel
from agents import Agent, Runner, SQLiteSession, set_tracing_disabled
from my_configuration.configuration import model
from my_supabase.supaabse import store_in_supabase
from openai.types.responses import ResponseTextDeltaEvent
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

# ---------- Schema ----------
class Improved_Prompt(BaseModel):
    improved_prompt: str


# ---------- Setup ----------
set_tracing_disabled(True)
USER_ID = "user123"  # Replace with actual logged-in user's ID


# ---------- Agents ----------
ClarityAgent = Agent(
    name="ClarityAgent",
    instructions="""
Refine the user's prompt to be crystal clear, concise, and unambiguous.
Preserve the original intent, remove contradictions, and use precise action verbs.
Do NOT answer the prompt. Only improve the wording.
Return the refined prompt strictly as plain text in English.
""",
    model=model
)

ClarityAgent_as_tool = ClarityAgent.as_tool(
    tool_name="clarity_tool",
    tool_description="Improves clarity, precision, and task specificity."
)

ContextAgent = Agent(
    name="ContextAgent",
    instructions="""
Enhance the user's prompt with relevant context, examples, and guidance steps to make it actionable.
Keep all examples short and aligned with the task.
Do NOT answer the prompt. Only improve the wording.
Return the refined prompt strictly as plain text in English.
""",
    model=model
)

ContextAgent_as_tool = ContextAgent.as_tool(
    tool_name="context_tool",
    tool_description="Adds context, examples, guidance, and optional tone/role."
)

FormatAgent = Agent(
    name="FormatAgent",
    instructions="""
Polish the user's prompt for professional tone, clarity, and structure.
Suggest output organization if useful (like bullets or numbered lists), but avoid markdown or bold text.
Do NOT answer the prompt. Only improve the wording.
Return the refined prompt strictly as plain text in English.
""",
    model=model
)

FormatAgent_as_tool = FormatAgent.as_tool(
    tool_name="format_tool",
    tool_description="Polishes prompt with structure and professional tone."
)

PromptImprover = Agent(
    name="PromptImprover",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
Take a vague or unclear prompt and produce a clear, high-quality, actionable one.
Always return plain English output.
Use these tools in sequence:
1) clarity_tool
2) context_tool
3) format_tool
Do NOT answer the prompt.
Return the refined prompt strictly as plain text in English.
""",
    model=model,
    tools=[ClarityAgent_as_tool, ContextAgent_as_tool, FormatAgent_as_tool]
)

Ultimate_Prompt_Refiner = Agent(
    name="Ultimate Refiner",
    instructions="""
Take any user input and refine it to be clear, concise, professional, and actionable.
Do NOT answer the question — only improve the prompt.
Use the PromptImprover agent as a handoff for clarity, context, and formatting.
Return ONLY the refined prompt as plain text in English — no JSON, markdown, or examples.
""",
    model=model,
    handoffs=[PromptImprover],
)

# ---------- Runner ----------
session = SQLiteSession(USER_ID)
while True:
    user_input = input("Enter a prompt to improve (or 'exit' to quit): ")
    if user_input.lower() == 'exit':
        break

    runner = Runner.run_sync(
        starting_agent=Ultimate_Prompt_Refiner,
        session=session,
        input=user_input
    )

    improved_prompt = runner.final_output.strip()
    print("Improved Prompt:", improved_prompt)

    # ✅ Store conversation in Supabase
    try:
        store_in_supabase(USER_ID, user_input, improved_prompt)
        print("✅ Stored successfully in Supabase.\n")
    except Exception as e:
        print("⚠️ Failed to store in Supabase:", e, "\n")
