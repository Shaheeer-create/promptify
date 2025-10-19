from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json
from agents import Agent, Runner,SQLiteSession,set_tracing_disabled
from my_configuration.configuration import model
from openai.types.responses import ResponseTextDeltaEvent
from my_supabase.supaabse import store_in_supabase



# =========================================================
# REQUEST MODEL
# =========================================================

class AgentOutput(BaseModel):
    improved_prompt: str

class PromptRequest(BaseModel):
    user_input: str
    user_id: str = "user_default"


async def main():
    set_tracing_disabled(True)

    # =========================
    # Tool Agents
    # =========================
    Prompt_Clarity = Agent(
        name="Prompt Clarity Enhancer",
        instructions="""
You are ClarityMaster. Refine vague or confusing prompts into clear, specific, unambiguous statements. Keep intent intact. Output max 35 words. Only provide the refined prompt.
""",
        model=model
    ).as_tool(
        tool_name="prompt_clarity_tool",
        tool_description="Refines vague prompts into clear, specific versions."
    )

    Prompt_Context = Agent(
        name="Prompt Context Enricher",
        instructions="""
You are ContextGuru. Enrich prompts with relevant background, examples, or scenario. Keep intent intact. Output max 40 words. Only provide the refined prompt.
""",
        model=model
    ).as_tool(
        tool_name="prompt_context_tool",
        tool_description="Adds context/examples to prompts."
    )

    Prompt_Instructions = Agent(
        name="Prompt Instruction Designer",
        instructions="""
You are InstructionSmith. Add step-by-step guidance or structured tasks to prompts. Keep intent intact. Output max 40 words. Only provide the refined prompt.
""",
        model=model
    ).as_tool(
        tool_name="prompt_instruction_tool",
        tool_description="Adds structured instructions to prompts."
    )

    Prompt_Role = Agent(
        name="Prompt Role Assigner",
        instructions="""
You are RoleMaster. Add role, persona, or tone if needed. Keep intent intact. Output max 35 words. Only provide the refined prompt.
""",
        model=model
    ).as_tool(
        tool_name="prompt_role_tool",
        tool_description="Adds role or tone to prompts."
    )

    Prompt_Formatter = Agent(
        name="Prompt Output Formatter",
        instructions="""
You are FormatGuru. Specify output format (bullet points, table, code, summary, etc.). Keep intent intact. Output max 40 words. Only provide the refined prompt.
""",
        model=model
    ).as_tool(
        tool_name="prompt_formatter_tool",
        tool_description="Specifies output format for prompts."
    )

    Prompt_Improver = Agent(
        name="Prompt Improver",
        instructions="""
You are PromptSmith. Polish prompts to make them concise, clear, and professional. Keep intent intact. Output max 40 words. Only provide the refined prompt.
""",
        model=model
    ).as_tool(
        tool_name="prompt_improver_tool",
        tool_description="Polishes prompts for clarity and professionalism."
    )

    # =========================
    # Short Prompt Agent
    # =========================
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
4. Return your final answer **as a plain text JSON-like object**, like this:
   {"improved_prompt": "Final refined prompt text here"}
5. Do not use Markdown formatting, code blocks, or commentary
Output only the final short prompt.
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

    ).as_tool(
        tool_name="short_prompt_refiner_tool",
        tool_description="Generates short, concise refined prompts."
    )

    # =========================
    # Detailed Prompt Agent
    # =========================
    DetailedPromptRefiner = Agent(
        name="Detailed Prompt Refiner",
        instructions="""
You are DetailedPromptSmith. Refine user prompt to be fully optimized, clear, structured, and detailed (up to 100 words). Apply all tools in order:
1. Clarity
2. Context
3. Instructions
4. Role
5. Formatter
6. Improver

4. Return your final answer **as a plain text JSON-like object**, like this:
   {"improved_prompt": "Final refined prompt text here"}
5. Do not use Markdown formatting, code blocks, or commentary
Output only the final detailed prompt with practical examples.
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

    ).as_tool(
        tool_name="detailed_prompt_refiner_tool",
        tool_description="Generates long, detailed refined prompts."
    )

    # =========================
    # Ultimate Prompt Refiner Agent
    # =========================
# =========================
# Ultimate Prompt Refiner Agent (Improved)
# =========================
    Ultimate_Prompt_Refiner = Agent(
    name="Ultimate Prompt Refiner",
    instructions="""
You are PromptSmith Pro, an expert at transforming vague or incomplete user prompts into powerful, professional, and well-structured ones.

Interaction rules:
1. Politely ask the user once for:
   - The main context or background (if any)
   - The preferred output style (choose between "short" or "detailed")
2. If the user says they have no specific context, continue without re-asking.
3. Based on the user's chosen style:
   - Use `ShortPromptRefiner` for short outputs (≤40 words)
   - Use `DetailedPromptRefiner` for detailed outputs (≤100 words)
4. Return your final answer **as a plain text JSON-like object**, like this:
   {"improved_prompt": "Final refined prompt text here"}
5. Do not use Markdown formatting, code blocks, or commentary.
""",
    model=model,
    tools=[
        ShortPromptRefiner,
        DetailedPromptRefiner
    ],
)


    Ultimate_Prompt_Refiner_as_tool = Ultimate_Prompt_Refiner.as_tool(
        tool_name="ultimate_prompt_refiner_tool",
        tool_description="Transforms vague prompts into either short or detailed professional prompts based on user choice."
    )

    # =========================
    # Session + Streaming Loop
    # =========================
    session = SQLiteSession("user_123", "prompt_stream.db")

    print("=== Promptify By-Team_SAS ===")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        combined_input = f"User prompt: {user_input}\nAsk for context and preferred style, then refine using the appropriate short or detailed agent."

        print("\n✨ Improved Prompt:\n")
        result = Runner.run_streamed(Ultimate_Prompt_Refiner, input=combined_input, session=session)
        full_output = ""
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)
                full_output += event.data.delta

        print("\n")
        store_in_supabase("user_123", combined_input, full_output.strip())

if __name__ == "__main__":
    asyncio.run(main())
