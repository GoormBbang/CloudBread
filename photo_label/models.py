from pydantic import BaseModel
from typing import Optional


class PhotoLabelRequest(BaseModel):
    photoAnalysisId: int
    imageUrl: str


class PhotoLabelResult(BaseModel):
    label: str
    confidence: float


class PhotoLabelResponse(BaseModel):
    success: bool
    photoAnalysisId: int
    label: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None

