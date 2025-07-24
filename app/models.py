from pydantic import BaseModel
from typing import Optional

class CategorizationRequest(BaseModel):
    description: str

class CategorizationResponse(BaseModel):
    category: str
    reasoning: Optional[str]
