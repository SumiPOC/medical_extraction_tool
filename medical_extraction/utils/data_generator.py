# Copyright (c) 2025 Sumi Somangili
# All rights reserved.
import random
from datetime import datetime, timedelta

def generate_test_data():
    # Define allergy groups that commonly occur together
    ALLERGY_GROUPS = [
        ["Penicillin"],
        ["Sulfa", "NSAIDs"],
        ["Latex", "Iodine"],
        ["None"]
    ]
    
    CONDITION_NOTES = {
        "Hypertension": ["BP {}/{}".format(random.randint(110,160), random.randint(70,100))],
        "Diabetes": ["HbA1c {}%".format(round(random.uniform(5.0, 10.0), 1))],
        "Asthma": ["Peak flow {}".format(random.randint(200,500))],
        "Hyperlipidemia": ["LDL {} mg/dL".format(random.randint(100,200))]
    }
    
    allergies = random.choice(ALLERGY_GROUPS)
    chronic_conditions = random.sample(
        ["Hypertension", "Diabetes", "Asthma", "Hyperlipidemia"], 
        k=random.randint(1, 2)
    )
    
    return {
        "patient_id": f"PT{random.randint(100000, 999999)}",
        "patient_name": f"Patient_{random.randint(1, 100)}",
        "date_of_birth": f"{random.randint(1960, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
        "allergies": allergies,
        "chronic_conditions": chronic_conditions,
        "medical_notes": [
            {
                "date": (datetime.now() - timedelta(days=random.randint(1, 365)))
                    .strftime("%Y-%m-%d"),
                "doctor": f"Dr. {random.choice(['Smith', 'Lee'])}",
                "note": (
                    f"Managing {cond}. "
                    f"{random.choice(CONDITION_NOTES[cond])}. "
                    f"Allergies: {', '.join(allergies)}. "
                    f"Assessment: {random.choice(['Improved', 'Stable', 'Worsening'])}. "
                    f"Plan: {random.choice(['Continue', 'Adjust', 'Refer'])}."
                )
            } 
            for cond in chronic_conditions
            for _ in range(2)  # 2 notes per condition
        ]
    }