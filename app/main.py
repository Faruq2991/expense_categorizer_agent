from fastapi import FastAPI
from app.agent_api import router

app = FastAPI(title="Expense Categorizer API")

app.include_router(router, prefix="/api", tags=["Categorization", "Sessions", "Analytics"])

@app.get("/")
def root():
    return {"message": "Expense Categorizer API is running"}
