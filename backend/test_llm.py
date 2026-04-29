import os
from dotenv import load_dotenv
load_dotenv()
from services.llm_service import get_llm_response

prompt = "Hello, say hi!"
print(f"Testing LLM with prompt: {prompt}")
res = get_llm_response(prompt, schema=None)
print(f"Response: {res}")
