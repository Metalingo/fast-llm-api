import os
from dotenv import load_dotenv
import openai
import anthropic

# Load environment variables from .env file
load_dotenv()

# Access the API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Set OpenAI API key globally
openai.api_key = OPENAI_API_KEY

# Set Anthropic API key globally in the client (can also create a global client here)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
