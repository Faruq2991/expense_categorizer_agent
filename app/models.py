from pydantic import BaseModel
from typing import Optional

class CategorizeRequest(BaseModel):
    input_text: str

class CategorizeResponse(BaseModel):
    category: str
    reasoning: Optional[str]
