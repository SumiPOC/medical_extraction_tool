# Copyright (c) 2025 Sumi Somangili
# All rights reserved.
    
import random
from datetime import datetime, timedelta

def generate_test_data(condition="h. pylori"):
    test_types = {
        "h. pylori": ["Stool Antigen Test", "Urea Breath Test", "Endoscopy"],
        "diabetes": ["HbA1c", "Fasting Glucose", "OGTT"]
    }
    
    return {
        "patient_id": f"PT{random.randint(100000, 999999)}",
        "patient_name": f"Patient_{random.randint(1, 100)}",
        "date_of_birth": f"{random.randint(1960, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
        "medical_notes": [
            {
                "date": (datetime.now() - timedelta(days=random.randint(1, 365)))
                    .strftime("%Y-%m-%d"),
                "doctor": f"Dr. {random.choice(['Smith', 'Lee'])}",
                "note": f"{random.choice(test_types[condition])} result: {random.choice(['Positive', 'Negative'])}" 
                if i == 0 else  # First note is always a test result
                f"Follow-up for {condition}"
            } for i in range(3)
        ]
    }