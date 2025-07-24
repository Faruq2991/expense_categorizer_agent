from fastapi import FastAPI
from app.api import router

app = FastAPI(title="Expense Categorizer API")

app.include_router(router, prefix="/api", tags=["Categorization"])
