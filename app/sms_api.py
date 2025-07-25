from fastapi import APIRouter, Request, HTTPException
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from dotenv import load_dotenv

from app.agent import run_categorizer

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
    raise ValueError("Twilio environment variables (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER) not set.")

router = APIRouter()
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@router.post("/sms_webhook")
async def sms_webhook(request: Request):
    try:
        form_data = await request.form()
        from_number = form_data.get("From")
        message_body = form_data.get("Body")

        if not message_body:
            raise HTTPException(status_code=400, detail="No message body received.")

        # Use the existing categorization logic
        # For SMS, we'll use the 'From' number as a pseudo user_id
        result = run_categorizer(message_body, user_id=from_number)

        category = result.get("category", "Unknown")
        reasoning = result.get("reasoning", "No reasoning provided.")
        confidence = result.get("confidence_score", 0.0)

        response_text = (
            f"Category: {category}\n"
            f"Reasoning: {reasoning}\n"
            f"Confidence: {confidence:.2f}"
        )

        # Create TwiML response
        resp = MessagingResponse()
        resp.message(response_text)
        
        return resp.to_xml()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMS webhook error: {e}")