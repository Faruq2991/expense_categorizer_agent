from fastapi import FastAPI
from app.agent_api import router as agent_router
from app.telegram_api import router as telegram_router
from app.sms_api import router as sms_router

app = FastAPI(title="Expense Categorizer API")

app.include_router(agent_router, prefix="/api", tags=["Categorization", "Sessions", "Analytics"])
app.include_router(telegram_router, prefix="/telegram", tags=["Telegram Bot"])
app.include_router(sms_router, prefix="/sms", tags=["SMS Integration"])

@app.get("/")
def root():
    return {"message": "Expense Categorizer API is running"}
