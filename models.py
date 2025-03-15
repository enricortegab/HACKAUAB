# models.py
from datetime import datetime

from pydantic import BaseModel
from typing import List, Optional

class MedicalEncounter(BaseModel):
    symptoms: List[str]
    diagnosis: Optional[str] = None
    recommendations: List[str]
    locations: List[dict]
    timestamp: str = datetime.now().isoformat()
