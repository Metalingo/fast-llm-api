from fastapi import APIRouter
from fast_llm_api.services.content_rank_service import full_rank
from fast_llm_api.services.models import ToBeRankedTextList

router = APIRouter()

@router.post("/full-rank")
async def concat_and_send(text_list: ToBeRankedTextList):
   
    response = full_rank(text_list)
    return {"response": response}