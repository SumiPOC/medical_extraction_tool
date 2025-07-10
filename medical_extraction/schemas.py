from typing import List, Dict, Optional
from pydantic import BaseModel

class Treatment(BaseModel):
    date: str
    medications: List[str]
    facility: Optional[str] = None
    doctor: Optional[str] = None

class TestResult(BaseModel):
    date: str
    test_type: str
    result: str
    facility: Optional[str] = None

class MedicalNote(BaseModel):
    date: str
    doctor: str
    note: str

class MedicalRecord(BaseModel):
    patient_id: str
    patient_name: str
    date_of_birth: str
    medical_notes: List[MedicalNote]
    allergies: List[str] = []
    chronic_conditions: List[str] = []

class ExtractionResult(BaseModel):
    patient_info: Dict[str, str]
    condition: str
    treatments: List[Treatment]
    tests: List[TestResult]
    symptoms: List[Dict[str, str]]
    has_condition: bool
    was_treated: bool
    error: Optional[str] = None