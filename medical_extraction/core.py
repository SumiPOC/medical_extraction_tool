# medical_extraction/core.py
import json
import re
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, ValidationError
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MedicalExtractor:
    """Specialized LLM processor for medical data extraction from clinical notes"""

    PROMPT_TEMPLATE = """As a medical expert, analyze these clinical notes and extract the following:
    
**Patient Context:**
- ID: {patient_id}
- Age: {age}
- Conditions: {conditions}
- Allergies: {allergies}

**Task:**
1. Answer: {question}
2. Extract all relevant clinical findings
3. Identify supporting evidence

**Response Format (JSON ONLY):**
{{
  "answer": "yes|no|unknown",
  "confidence": 0.0-1.0,
  "reason": "clinical justification",
  "evidence": [
    {{
      "text": "exact note excerpt",
      "page": "note reference",
      "relevance": 0.0-1.0
    }}
  ],
  "extracted_data": {{
    "medications": [],
    "diagnoses": [],
    "procedures": [],
    "symptoms": []
  }}
}}

**Clinical Notes:**
{notes}

Return ONLY valid JSON with NO additional text:"""

    def __init__(self, llm_provider):
        self.llm = self._init_llm(llm_provider)
        self.retry_attempts = 3

    def _init_llm(self, provider):
        """Initialize the LLM with proper error handling"""
        try:
            from .llm_integration import get_llm
            return get_llm(provider)
        except ImportError as e:
            logger.error(f"LLM initialization failed: {str(e)}")
            raise

    def _calculate_age(self, dob: str) -> int:
        """Helper to calculate age from date of birth"""
        from datetime import datetime
        birth_date = datetime.strptime(dob, "%Y-%m-%d")
        age = datetime.now().year - birth_date.year
        return age

    def _preprocess_notes(self, notes: List[Dict]) -> str:
        """Format clinical notes for the prompt"""
        return "\n".join(
            f"[Note {idx+1} - {note['date']} by {note['doctor']}]:\n{note['note']}"
            for idx, note in enumerate(notes)
        )

    def _extract_from_response(self, response: str) -> Dict:
        """Robust JSON extraction with multiple fallback strategies"""
        # Strategy 1: Direct JSON parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract JSON from markdown
        json_match = re.search(r'```json\n?(.+?)\n?```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Strategy 3: Find innermost JSON
        try:
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1:
                return json.loads(response[start:end+1])
        except json.JSONDecodeError:
            pass

        # Final fallback: Manual field extraction
        return {
            "answer": self._extract_field(response, "answer"),
            "confidence": float(self._extract_field(response, "confidence", "0")),
            "reason": self._extract_field(response, "reason"),
            "evidence": [],
            "extracted_data": {
                "medications": [],
                "diagnoses": [],
                "procedures": [],
                "symptoms": []
            }
        }

    def _extract_field(self, text: str, field: str, default: str = "") -> str:
        """Extract specific field using regex fallback"""
        pattern = f'"{field}"\\s*:\\s*"([^"]+)"'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else default

    def extract(self, medical_data: Dict, question: str) -> Dict:
        """
        Main extraction method with retry logic and validation

        Args:
            medical_data: Dictionary containing patient medical records
            question: Specific clinical question to answer

        Returns:
            Dictionary with extracted medical information
        """
        # Prepare context
        age = self._calculate_age(medical_data["date_of_birth"])
        formatted_notes = self._preprocess_notes(medical_data["medical_notes"])

        prompt = self.PROMPT_TEMPLATE.format(
            patient_id=medical_data["patient_id"],
            age=age,
            conditions=", ".join(medical_data.get("chronic_conditions", [])),
            allergies=", ".join(medical_data.get("allergies", [])),
            question=question,
            notes=formatted_notes
        )

        # Try multiple attempts
        for attempt in range(self.retry_attempts):
            try:
                response = str(self.llm.invoke(prompt))
                logger.debug(f"Attempt {attempt+1} Response: {response}")

                result = self._extract_from_response(response)

                # Validate minimum required fields
                if not all(k in result for k in ["answer", "reason"]):
                    raise ValueError("Missing required fields in response")

                return {
                    "success": True,
                    "data": result,
                    "raw_response": response
                }

            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed: {str(e)}")
                if attempt == self.retry_attempts - 1:
                    return {
                        "success": False,
                        "error": str(e),
                        "raw_response": response
                    }

    def batch_extract(self, medical_records: List[Dict], questions: List[str]) -> List[Dict]:
        """Process multiple records/questions in bulk"""
        return [self.extract(record, q) for record, q in zip(medical_records, questions)]
