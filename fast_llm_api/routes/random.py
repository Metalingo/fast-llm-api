from fastapi import APIRouter
from fast_llm_api.services.random_service import consult
from starlette.concurrency import run_in_threadpool

router = APIRouter()

@router.get("/consult")
async def consult_route():
    # Run the synchronous consult() in a threadpool and await the result
    response = await run_in_threadpool(consult)
    return {"response": response}  # Return a proper JSON serializable object
