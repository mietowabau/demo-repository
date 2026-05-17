#1. Współdzielone modele (models.py)
#Plik zawiera struktury danych używane zarówno przez API, jak i Workera.

from pydantic import BaseModel
from typing import Optional, Dict
from enum import Enum

class FileStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSED = "PROCESSED"
    PROCESSED_BY_ML = "PROCESSED_BY_ML"
    PENDING_HUMAN_REVIEW = "PENDING_HUMAN_REVIEW"
    PROCESSED_MANUALLY = "PROCESSED_MANUALLY"

class FileMetadata(BaseModel):
    id: int
    filename: str
    status: FileStatus
    uploaded_by: str
    ml_suggestions: Optional[Dict[str, str]] = None

# Zdefiniowany, docelowy schemat pliku CSV
class TargetCsvSchema(BaseModel):
    first_name: str
    last_name: str
    email: str
    age: int