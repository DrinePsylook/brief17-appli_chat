from pydantic import BaseModel
from typing import Optional

class VerificationResponse(BaseModel):
    status: str
    match: bool
    message: Optional[str] = None

class IdentificationResponse(BaseModel):
    status: str
    user_id: Optional[str]
    confidence: Optional[float]
    message: Optional[str] = None

class StandardResponse(BaseModel):
    status: str
    message: Optional[str] = None