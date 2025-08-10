import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

class ClinicalDataGenerator:
    def __init__(self):
        self.ALLERGY_GROUPS = [
            ["Penicillin"],
            ["Sulfa", "NSAIDs"],
            ["Latex", "Iodine"],
            ["Shellfish"],
            ["None"]
        ]
        
        self.CONDITIONS = {
            "Hypertension": {
                "icd10": "I10",
                "labs": {
                    "BP": lambda: f"{random.randint(110,180)}/{random.randint(70,120)}",
                    "Cr": lambda: round(random.uniform(0.6, 2.5), 1)
                },
                "meds": ["Lisinopril", "Amlodipine", "HCTZ"]
            },
            "Diabetes": {
                "icd10": "E11.9",
                "labs": {
                    "HbA1c": lambda: round(random.uniform(5.0, 12.0), 1),
                    "Glucose": lambda: random.randint(80, 350)
                },
                "meds": ["Metformin", "Glipizide", "Insulin glargine"]
            },
            "COPD": {
                "icd10": "J44.9",
                "labs": {
                    "FEV1": lambda: f"{random.randint(30,80)}%",
                    "O2 Sat": lambda: f"{random.randint(88,100)}%"
                },
                "meds": ["Tiotropium", "Albuterol", "Prednisone"]
            },
            "CHF": {
                "icd10": "I50.9",
                "labs": {
                    "BNP": lambda: random.randint(100, 2000),
                    "EF": lambda: f"{random.randint(20,55)}%"
                },
                "meds": ["Furosemide", "Carvedilol", "Spironolactone"]
            }
        }
        
        self.PROCEDURES = {
            "Colonoscopy": {"icd10": "0DJ08ZZ", "recovery_days": 3},
            "Knee Replacement": {"icd10": "0SRD0JZ", "recovery_days": 60},
            "Cardiac Cath": {"icd10": "4A023N7", "recovery_days": 7}
        }

    def generate_patient(self, patient_id: str) -> Dict:
        """Generate complete 1-year record for a patient"""
        conditions = random.sample(
            list(self.CONDITIONS.keys()), 
            k=random.randint(1, 3)
        )
        allergies = random.choice(self.ALLERGY_GROUPS)
        
        start_date = datetime.now() - timedelta(days=365)
        timeline = []
        
        # Generate baseline health data
        baseline = {
            "date": start_date.strftime("%Y-%m-%d"),
            "type": "initial_assessment",
            "content": {
                "conditions": {cond: self.CONDITIONS[cond]["icd10"] for cond in conditions},
                "allergies": allergies,
                "baseline_labs": {
                    cond: {test: fn() for test, fn in self.CONDITIONS[cond]["labs"].items()}
                    for cond in conditions
                }
            }
        }
        timeline.append(baseline)
        
        # Generate regular visits (every 4-12 weeks)
        current_date = start_date
        while current_date < datetime.now():
            current_date += timedelta(days=random.randint(28, 84))
            
            # 15% chance of hospitalization
            if random.random() < 0.15:
                timeline.extend(self._generate_hospitalization(current_date, conditions))
                current_date += timedelta(days=random.randint(3, 14))
            else:
                timeline.append(self._generate_office_visit(current_date, conditions, allergies))
        
        return {
            "patient_id": patient_id,
            "demographics": self._generate_demographics(),
            "timeline": timeline
        }

    def _generate_office_visit(self, date: datetime, conditions: List[str], allergies: List[str]) -> Dict:
        """Generate outpatient visit note"""
        condition = random.choice(conditions)
        cond_data = self.CONDITIONS[condition]
        
        return {
            "date": date.strftime("%Y-%m-%d"),
            "type": "office_visit",
            "content": {
                "condition": condition,
                "icd10": cond_data["icd10"],
                "labs": {test: fn() for test, fn in cond_data["labs"].items()},
                "medications": {
                    "continued": random.sample(cond_data["meds"], k=random.randint(1, 2)),
                    "new": random.choice(cond_data["meds"]) if random.random() > 0.7 else None
                },
                "note": self._generate_clinical_note("office", condition, allergies)
            }
        }

    def _generate_hospitalization(self, admit_date: datetime, conditions: List[str]) -> List[Dict]:
        """Generate hospital admission with discharge summary"""
        condition = random.choice(conditions)
        procedure = random.choice(list(self.PROCEDURES.keys())) if random.random() > 0.5 else None
        
        admission = {
            "date": admit_date.strftime("%Y-%m-%d"),
            "type": "hospital_admission",
            "content": {
                "condition": condition,
                "icd10": self.CONDITIONS[condition]["icd10"],
                "labs": {test: fn() for test, fn in self.CONDITIONS[condition]["labs"].items()},
                "note": f"Admitted for acute exacerbation of {condition}"
            }
        }
        
        discharge_date = admit_date + timedelta(days=random.randint(3, 14))
        discharge = {
            "date": discharge_date.strftime("%Y-%m-%d"),
            "type": "discharge_summary",
            "content": {
                "condition": condition,
                "procedure": procedure,
                "procedure_icd10": self.PROCEDURES[procedure]["icd10"] if procedure else None,
                "disposition": random.choice(["Home", "Rehab", "SNF"]),
                "follow_up": f"{random.randint(1,4)} weeks",
                "note": self._generate_clinical_note("discharge", condition, [])
            }
        }
        
        return [admission, discharge]

    def _generate_clinical_note(self, note_type: str, condition: str, allergies: List[str]) -> str:
        """Generate realistic clinical note text"""
        templates = {
            "office": (
                f"Patient presents for follow-up of {condition}. "
                f"Reports {random.choice(['improved', 'stable', 'worsening'])} symptoms. "
                f"Allergies: {', '.join(allergies) if allergies else 'None known'}. "
                f"Assessment: {condition} {random.choice(['well controlled', 'suboptimally controlled'])}. "
                f"Plan: {random.choice(['Continue current regimen', 'Adjust medications', 'Refer to specialist'])}."
            ),
            "discharge": (
                f"Patient hospitalized for {condition} management. "
                f"{'Underwent ' + random.choice(list(self.PROCEDURES.keys())) + ' procedure. ' if random.random() > 0.5 else ''}"
                f"Discharge condition: {random.choice(['Improved', 'Stable', 'Guarded'])}. "
                f"Follow-up in {random.randint(1,4)} weeks with {random.choice(['PCP', 'specialist'])}."
            )
        }
        return templates[note_type]

    def _generate_demographics(self) -> Dict:
        """Generate realistic patient demographics"""
        gender = random.choice(["M", "F"])
        first_names = {
            "M": ["James", "John", "Robert", "Michael"],
            "F": ["Mary", "Jennifer", "Linda", "Elizabeth"]
        }
        return {
            "name": f"{random.choice(first_names[gender])} {random.choice(['Smith', 'Johnson', 'Williams'])}",
            "dob": f"{random.randint(1940, 2000)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "gender": gender,
            "race": random.choice(["White", "Black", "Asian", "Hispanic"]),
            "language": random.choice(["English", "Spanish", "Mandarin"])
        }
        
def generate_test_data():
        """Generate a list of synthetic patient data for testing"""
        generator = ClinicalDataGenerator()
        patients = []
        
        for i in range(10):  # Generate 10 patients
            patient_id = f"PT{i+1:03d}"
            patient_data = generator.generate_patient(patient_id)
            patients.append(patient_data)
        return patients    

# Example usage
if __name__ == "__main__":
    generator = ClinicalDataGenerator()
    
    # Generate 10 patients with 1-year records
    patients = [generator.generate_patient(f"PT{1000+i}") for i in range(10)]
    
    # Save to JSON file
    with open("synthetic_patients.json", "w") as f:
        json.dump(patients, f, indent=2)
    
    print(f"Generated {len(patients)} patients with full 1-year timelines ")