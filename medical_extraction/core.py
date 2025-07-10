# Copyright (c) 2025 Sumi Somangili
# All rights reserved.
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Any, Optional
import json
from datetime import datetime
from medical_extraction.schemas import ExtractionResult, MedicalRecord

class MedicalExtractor:
    def __init__(self, llm):
        self.llm = llm
    
    def extract(self, medical_data: Dict[str, Any], question: str) -> ExtractionResult:
        """
        Processes medical records and extracts structured information.
        
        Args:
            medical_data: Dictionary containing:
                - patient_id: str
                - patient_name: str
                - date_of_birth: str
                - medical_notes: List[Dict]
            question: Natural language query about the medical condition
            
        Returns:
            ExtractionResult containing structured data
        """
        # Validate input
        if not isinstance(medical_data, dict):
            raise ValueError("medical_data must be a dictionary")
        if "patient_id" not in medical_data:
            raise ValueError("medical_data must contain patient_id")
        
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a medical data extraction system. 
            Return ONLY valid JSON with this exact structure:
            {
                "patient_info": {
                    "id": "string",
                    "name": "string",
                    "dob": "string"
                },
                "condition": "string",
                "treatments": [{
                    "date": "string",
                    "medications": ["string"],
                    "facility": "string",
                    "doctor": "string"
                }],
                "tests": [{
                    "date": "string",
                    "test_type": "string",
                    "result": "string",
                    "facility": "string"
                }],
                "symptoms": [{
                    "date": "string",
                    "description": "string"
                }],
                "has_condition": boolean,
                "was_treated": boolean
            }"""),
            
            HumanMessage(content=f"""Analyze these medical notes for {question}:
            
            Patient ID: {medical_data['patient_id']}
            Name: {medical_data['patient_name']}
            DOB: {medical_data.get('date_of_birth', 'Unknown')}
            
            Medical Notes:
            {json.dumps(medical_data['medical_notes'], indent=2)}""")
        ])
        
        # Create and invoke the chain
        chain = prompt | self.llm
        response = chain.invoke({
            "question": question,
            "medical_data": medical_data
        })
        
        # Parse and validate response
        try:
            response_content = response.content if hasattr(response, 'content') else response
            result = json.loads(response_content)
            
            # Convert to ExtractionResult
            return ExtractionResult(
                patient_info={
                    "id": medical_data["patient_id"],
                    "name": medical_data["patient_name"],
                    "dob": medical_data.get("date_of_birth", "Unknown")
                },
                condition=result.get("condition", question),
                treatments=result.get("treatments", []),
                tests=result.get("tests", []),
                symptoms=result.get("symptoms", []),
                has_condition=result.get("has_condition", False),
                was_treated=result.get("was_treated", False)
            )
            
        except json.JSONDecodeError as e:
            return ExtractionResult(
                patient_info={
                    "id": medical_data["patient_id"],
                    "name": medical_data["patient_name"],
                    "dob": medical_data.get("date_of_birth", "Unknown")
                },
                condition=question,
                treatments=[],
                tests=[],
                symptoms=[],
                has_condition=False,
                was_treated=False,
                error=f"JSON parsing failed: {str(e)}",
                raw_response=str(response)
            )

    @staticmethod
    def test_extractor():
        """Test the extractor with mock data"""
        from medical_extraction.llm_integration import get_llm
        from medical_extraction.utils.data_generator import generate_test_data
        
        # Setup
        llm = get_llm("mock")
        extractor = MedicalExtractor(llm)
        test_data = generate_test_data("h. pylori")
        
        # Test
        result = extractor.extract(test_data, "Does the patient have H. pylori?")
        
        print("\nTest Results:")
        print(f"Patient ID: {result.patient_info['id']}")
        print(f"Condition: {result.condition}")
        print(f"Tests Found: {len(result.tests)}")
        print(f"Treatments Found: {len(result.treatments)}")
        print(f"Has Condition: {result.has_condition}")

if __name__ == "__main__":
    MedicalExtractor.test_extractor()