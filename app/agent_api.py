from fastapi import APIRouter
from app.models import CategorizeRequest, CategorizeResponse
from app.agent import run_categorizer

router = APIRouter()

@router.post("/categorize", response_model=CategorizeResponse)
def categorize_expense(req: CategorizeRequest):
    result = run_categorizer(req.input_text)

    return CategorizeResponse(
        category=result["category"] or "Unknown",
        reasoning=result["reasoning"] or "No reasoning provided"
    )

@router.get("/categorize")
def categorize_example():
    return {"message": "Send a POST request with input_text to categorize."}
