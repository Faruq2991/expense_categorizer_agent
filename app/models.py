from pydantic import BaseModel
from typing import Optional

class CategorizeRequest(BaseModel):
    input_text: str

class CategorizeResponse(BaseModel):
    category: str
    reasoning: Optional[str]
    confidence_score: Optional[float]
    matching_method: Optional[str]

class FeedbackRequest(BaseModel):
    input_text: str
    predicted_category: str
    corrected_category: str
    reasoning: Optional[str]
    confidence_score: Optional[float]
