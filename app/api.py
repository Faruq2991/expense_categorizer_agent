from fastapi import APIRouter
from app.models import CategorizationRequest, CategorizationResponse
from app.agent import run_categorizer

router = APIRouter()

@router.post("/categorize", response_model=CategorizationResponse)
def categorize(req: CategorizationRequest):
    result = run_categorizer(req.description)
    return CategorizationResponse(
        category=result["category"],
        reasoning=result.get("reasoning")
    )
