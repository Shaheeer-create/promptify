from agents import OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from decouple import config

GEMINI_API_KEY = config("GEMINI_API_KEY")
BASE_URL=config("BASE_URL")

client_provider=AsyncOpenAI(api_key=GEMINI_API_KEY,base_url=BASE_URL)

model=OpenAIChatCompletionsModel(model="gemini-2.5-flash",openai_client=client_provider)
