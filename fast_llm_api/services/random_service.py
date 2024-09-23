from fastapi import APIRouter
from fast_llm_api.helpers.basic_llm_callers import call_openai, call_anthropic

router = APIRouter()

def consult():
    prompt = "It's okay, we'll get through this together."

    # Get responses from OpenAI and Anthropic
    openai_response = call_openai(prompt)
    anthropic_response = call_anthropic(prompt)

    # Concatenate both responses
    combined_response = f"ChatGPT: {openai_response}\n\nClaude: {anthropic_response}"

    return combined_response  # Return a string instead of a coroutine
