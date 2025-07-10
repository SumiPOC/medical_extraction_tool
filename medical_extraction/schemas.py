# Copyright (c) 2025 Sumi Somangili
# All rights reserved.
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import date

class Treatment(BaseModel):
    date: str
    medications: List[str]
    facility: Optional[str] = None
    doctor: Optional[str] = None

class TestResult(BaseModel):  # <-- The missing class
    date: str
    test_type: str
    result: str
    facility: Optional[str] = None
    reference_range: Optional[str] = None

class MedicalNote(BaseModel):
    date: str
    doctor: str
    note: str

class MedicalRecord(BaseModel):
    patient_id: str
    patient_name: str
    date_of_birth: str
    medical_notes: List[MedicalNote]

class ExtractionResult(BaseModel):
    patient_info: Dict[str, str]  # Includes id, name, dob
    condition: str
    treatments: List[Treatment]
    tests: List[TestResult]  # <-- Now properly defined
    symptoms: List[Dict[str, str]]
    has_condition: bool
    was_treated: bool