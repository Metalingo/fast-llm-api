import openai
import anthropic
from fast_llm_api.config import anthropic_client

# Synchronous OpenAI function
def call_openai(prompt: str, model: str = "gpt-4o"):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        return response.choices[0].message['content'].strip()
    except openai.error.OpenAIError as e:
        return f"OpenAI API error: {e}"

# Synchronous Anthropic function
def call_anthropic(prompt: str, model: str = "claude-3-5-sonnet-20240620"):
    try:
        response = anthropic_client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        print("response", response)
        return response.content[0].text
    except anthropic.APIError as e:
        return f"Anthropic API error: {e}"
