from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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

class Session(BaseModel):
    session_id: str
    start_time: datetime
    last_active_time: datetime
    user_id: Optional[str]
    metadata: Optional[str]

class Interaction(BaseModel):
    interaction_id: Optional[int]
    session_id: str
    timestamp: datetime
    interaction_type: str
    input_data: Optional[str]
    output_data: Optional[str]

class CategorizedExpense(BaseModel):
    expense_id: Optional[int]
    session_id: str
    timestamp: datetime
    description: str
    amount: Optional[float]
    category: str
    confidence_score: Optional[float]
    raw_input: Optional[str]
