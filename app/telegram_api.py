from fastapi import APIRouter, Request, HTTPException
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import os
from dotenv import load_dotenv

from app.agent import run_categorizer

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set.")

router = APIRouter()

# Initialize the bot application
application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

async def start(update: Update, context):
    await update.message.reply_text("Hi! I'm your Expense Categorizer bot. Send me an expense description to categorize.")

async def categorize_expense_telegram(update: Update, context):
    input_text = update.message.text
    user_id = str(update.effective_user.id)
    
    # Use the existing categorization logic
    result = run_categorizer(input_text, user_id=user_id)
    
    category = result.get("category", "Unknown")
    reasoning = result.get("reasoning", "No reasoning provided.")
    confidence = result.get("confidence_score", 0.0)
    
    response_text = (
        f"Category: {category}\n"
        f"Reasoning: {reasoning}\n"
        f"Confidence: {confidence:.2f}"
    )
    try:
        await update.message.reply_text(response_text)
    except Exception as e:
        # Log the error, but don't prevent the webhook from returning 200 OK
        print(f"ERROR: Failed to send Telegram response: {e}")

# Add handlers to the application
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, categorize_expense_telegram))

@router.post("/telegram_webhook")
async def telegram_webhook(request: Request):
    try:
        # Process the Telegram update
        update_json = await request.json()
        update = Update.de_json(update_json, application.bot)
        await application.initialize() # Initialize the application
        await application.process_update(update)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Telegram webhook error: {e}")
    return {"status": "ok"}