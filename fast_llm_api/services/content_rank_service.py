from fastapi import APIRouter
from fast_llm_api.services.llm_helper import call_openai, call_anthropic
from fast_llm_api.services.models import ToBeRankedTextList

router = APIRouter()

def full_rank(text_list: ToBeRankedTextList):
    
    return text_list  # Return a string instead of a coroutine
