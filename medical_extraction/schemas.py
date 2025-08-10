from datetime import date
from typing import Dict, List, Literal, Optional, Union, Annotated
from pydantic import BaseModel, Field, StringConstraints, field_validator
from typing_extensions import TypedDict

# ======================
# Type Aliases
# ======================

ICD10Code = Annotated[str, StringConstraints(pattern=r'^[A-Z]\d{2}(\.\d{1,2})?$')]
ICD10PCSCode = Annotated[str, StringConstraints(pattern=r'^\d[A-Z]\d{2}[A-Z0-9]{2}[A-Z]$')]
PatientID = Annotated[str, StringConstraints(pattern=r'^PT\d{3,6}$')]
FollowUpTime = Annotated[str, StringConstraints(pattern=r'^\d+\s(weeks|months)$')]

# ======================
# Core Data Types
# ======================

class DemographicData(BaseModel):
    """Patient demographic information"""
    name: str = Field(..., min_length=1, description="Full patient name")
    dob: date = Field(..., description="Date of birth in YYYY-MM-DD format")
    gender: Literal["M", "F", "Other"] = Field(..., description="Biological sex")
    race: Literal["White", "Black", "Asian", "Hispanic", "Other"] = Field(..., description="Self-reported race")
    language: str = Field(..., description="Primary language spoken")

class LabResult(BaseModel):
    """Laboratory test result with reference ranges"""
    value: Union[float, str] = Field(..., description="Numeric value or qualitative result")
    unit: Optional[str] = Field(None, description="Measurement units if applicable")

class MedicationChange(TypedDict):
    """Structure for medication changes"""
    continued: List[str]
    new: Optional[str]

# ======================
# Timeline Event Types  
# ======================

class InitialAssessment(BaseModel):
    """Baseline patient evaluation"""
    conditions: Dict[str, ICD10Code] = Field(..., description="Map of condition names to ICD-10 codes")
    allergies: List[str] = Field(..., description="List of allergy substances")
    baseline_labs: Dict[str, Dict[str, LabResult]] = Field(
        ..., 
        description="Condition-specific baseline lab results"
    )

class OfficeVisit(BaseModel):
    """Outpatient clinical encounter"""
    condition: str = Field(..., description="Primary condition addressed")
    icd10: ICD10Code = Field(..., description="ICD-10 diagnosis code")
    labs: Dict[str, LabResult] = Field(..., description="Lab results for this visit")
    medications: MedicationChange = Field(..., description="Medication changes")
    note: str = Field(..., min_length=50, description="Clinical narrative")

class HospitalAdmission(BaseModel):
    """Inpatient hospitalization record"""
    condition: str = Field(..., description="Primary admission diagnosis")
    icd10: ICD10Code = Field(..., description="ICD-10 code")
    labs: Dict[str, LabResult] = Field(..., description="Admission labs")
    note: str = Field(..., min_length=30, description="Admission summary")

class DischargeSummary(BaseModel):
    """Hospital discharge documentation"""
    condition: str = Field(..., description="Primary discharge diagnosis")
    procedure: Optional[str] = Field(None, description="Performed procedure if applicable")
    procedure_icd10: Optional[ICD10PCSCode] = Field(None, description="ICD-10-PCS procedure code")
    disposition: Literal["Home", "Rehab", "SNF", "Hospice"] = Field(..., description="Discharge destination")
    follow_up: FollowUpTime = Field(..., description="Follow-up timing")
    note: str = Field(..., min_length=100, description="Discharge instructions")

# ======================
# Timeline Event Wrappers
# ======================

class InitialAssessmentEvent(BaseModel):
    type: Literal["initial_assessment"]
    date: date
    content: InitialAssessment

class OfficeVisitEvent(BaseModel):
    type: Literal["office_visit"]
    date: date
    content: OfficeVisit

class HospitalAdmissionEvent(BaseModel):
    type: Literal["hospital_admission"]
    date: date
    content: HospitalAdmission

class DischargeSummaryEvent(BaseModel):
    type: Literal["discharge_summary"]
    date: date
    content: DischargeSummary

TimelineEvent = Union[
    InitialAssessmentEvent,
    OfficeVisitEvent,
    HospitalAdmissionEvent,
    DischargeSummaryEvent
]

# ======================
# Top-Level Patient Record
# ======================

class PatientRecord(BaseModel):
    """Complete longitudinal patient record"""
    patient_id: PatientID = Field(..., description="Unique patient identifier")
    demographics: DemographicData
    timeline: List[TimelineEvent] = Field(
        ...,
        min_length=1,
        description="Chronological sequence of clinical events"
    )

    @field_validator('timeline')
    def validate_timeline_order(cls, v: List[TimelineEvent]) -> List[TimelineEvent]:
        """Ensure timeline events are in chronological order"""
        dates = [event.date for event in v]
        if dates != sorted(dates):
            raise ValueError("Timeline events must be in chronological order")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "PT001",
                "demographics": {
                    "name": "John Doe",
                    "dob": "1980-01-15",
                    "gender": "M",
                    "race": "White",
                    "language": "English"
                },
                "timeline": [
                    {
                        "type": "initial_assessment",
                        "date": "2023-01-01",
                        "content": {
                            "conditions": {"Hypertension": "I10"},
                            "allergies": ["Penicillin"],
                            "baseline_labs": {
                                "Hypertension": {
                                    "BP": {"value": "140/90"},
                                    "Cr": {"value": 1.2, "unit": "mg/dL"}
                                }
                            }
                        }
                    }
                ]
            }
        }

# ======================
# Helper Functions
# ======================

def validate_patient_data(data: Dict) -> PatientRecord:
    """Validate raw patient data against the schema"""
    return PatientRecord.model_validate(data)

def generate_schema_docs() -> str:
    """Generate Markdown documentation for the schema"""
    return PatientRecord.model_json_schema()