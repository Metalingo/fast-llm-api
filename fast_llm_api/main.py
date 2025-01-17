from fastapi import FastAPI
from fast_llm_api.routes import additional_analysis, content_rank, random

app = FastAPI()

# Include the route groups
app.include_router(content_rank.router, prefix="/content-rank")
app.include_router(additional_analysis.router, prefix="/additional-analysis")
app.include_router(random.router, prefix="/random")


@app.get("/")
async def root():
    return {"message": "Welcome to the Fast-LLM API!"}
