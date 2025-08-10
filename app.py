# Copyright (c) 2025 Sumi Somangili
# All rights reserved.
import os
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

# Add light theme CSS
light_theme = """
<style>
    /* Light theme colors */
    :root {
        --primary: #f0f2f6;
        --background: white;
        --secondary: #f0f2f6;
        --text: black;
    }
    
    /* Remove all icons */
    [data-testid="stDecoration"],
    .st-emotion-cache-1v0mbdj e115fcil1 {
        display: none !important;
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #f0f2f6;
        color: black;
        border: 1px solid #d6d6d6;
        border-radius: 4px;
        padding: 0.5rem 1rem;
    }
    
    .stButton>button:hover {
        background-color: #e1e4eb;
    }
    
    /* Input fields */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>select {
        background-color: white;
        color: black;
        border: 1px solid #d6d6d6;
    }
    
    /* Success/error messages */
    .stAlert {
        border-left: none;
    }
    
    /* Remove expander icons */
    .st-emotion-cache-1hynsf2 {
        display: none;
    }
</style>
"""

# Apply light theme
st.markdown(light_theme, unsafe_allow_html=True)

# Add project root to Python path
sys.path.append(str(Path(__file__).parent))

try:
    from medical_extraction.schemas import PatientRecord, validate_patient_data
    from medical_extraction.utils.clinical_notes_generator import generate_test_data
    from medical_extraction.llm_integration import get_llm
except ImportError as e:
    st.error(f"Import error: {str(e)}")
    # Fallback implementations
    def validate_patient_data(data: Dict) -> Dict:
        return data
    
    # Mock implementations
    class PatientRecord:
        pass
    
    def generate_test_data():
        return {
            "patient_id": "PT000",
            "demographics": {
                "name": "Test Patient",
                "dob": "2000-01-01",
                "gender": "M",
                "race": "Other",
                "language": "English"
            },
            "timeline": []
        }
    
    def get_llm(*args, **kwargs):
        class MockLLM:
            def invoke(self, prompt):
                return {
                    "content": json.dumps({
                        "Answer": "yes",
                        "Reason": "Mock response",
                        "Evidence": ["Test evidence"],
                        "Confidence": 0.95
                    })
                }
        return MockLLM()

# Initialize environment and session state
load_dotenv()

def safe_date_parse(date_str: str) -> datetime:
    """Safely parse date strings with multiple formats"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        try:
            return datetime.strptime(date_str.split('T')[0], '%Y-%m-%d')
        except:
            return datetime.now()

def create_medical_prompt(medical_data: Dict, question: str) -> str:
    """Creates a prompt that forces valid JSON output with clinical analysis"""
    try:
        # Safely calculate age from DOB
        dob = medical_data['demographics']['dob']
        birth_date = safe_date_parse(dob)
        age = (datetime.now() - birth_date).days // 365
        
        # Extract conditions from timeline
        conditions = set()
        for event in medical_data['timeline']:
            content = event.get('content', {})
            if 'condition' in content:
                conditions.add(content['condition'])
        
        patient_info = (
            f"Patient ID: {medical_data.get('patient_id', 'N/A')}\n"
            f"Name: {medical_data['demographics'].get('name', 'Unknown')}\n"
            f"Age: {age} years\n"
            f"Gender: {medical_data['demographics'].get('gender', 'Unknown')}\n"
            f"Race: {medical_data['demographics'].get('race', 'Unknown')}\n"
            f"Conditions: {', '.join(conditions) if conditions else 'None'}\n"
        )
        
        # Get the 3 most recent notes
        recent_notes = [
            event['content']['note'] for event in medical_data['timeline'] 
            if 'note' in event.get('content', {})
        ][-3:]
        
        # Build the prompt in parts
        prompt_parts = [
            "You are a medical analyst. Return JSON with:",
            "1. Clear yes/no answer",
            "2. Clinical reasoning",
            "3. Supporting evidence from timeline",
            "",
            "Format MUST be:",
            '{',
            '  "Answer": "yes|no",',
            '  "Reason": "string",',
            '  "Evidence": ["string"],',
            '  "Confidence": 0-1',
            '}',
            "",
            "Patient Information:",
            patient_info,
            "",
            f"Question: {question}",
            "",
            "Recent Clinical Notes (analyze these chronologically):",
            '\n\n'.join(recent_notes),
            "",
            "Full Timeline (reference as needed):",
            json.dumps(medical_data['timeline'], indent=2),
            "",
            "Return valid JSON ONLY:"
        ]
        
        return '\n'.join(prompt_parts)
    except Exception as e:
        st.error(f"Error creating prompt: {str(e)}")
        return ""

def parse_llm_response(response: str) -> tuple:
    """Robustly extracts answer from LLM response"""
    try:
        content = response.content if hasattr(response, 'content') else str(response)
        content = content.strip()
        
        # Clean JSON response
        if content.startswith("```json"):
            content = content[7:].strip()
        if content.startswith("```"):
            content = content[3:].strip()
        if content.endswith("```"):
            content = content[:-3].strip()
        
        # Parse JSON
        result = json.loads(content)
        return (
            str(result.get("Answer", "unknown")).lower(),
            str(result.get("Reason", "No reason provided")),
            list(result.get("Evidence", [])),
            float(result.get("Confidence", 0)))
    except Exception as e:
        return "error", f"Analysis error: {str(e)}", [], 0

def check_model_access(api_key: str, model: str) -> bool:
    """Check if model is available"""
    try:
        client = OpenAI(api_key=api_key)
        client.models.retrieve(model)
        return True
    except:
        return False

def display_timeline(timeline: List[Dict]) -> None:
    """Display timeline visually"""
    with st.expander("Patient Timeline"):
        for event in timeline:
            col1, col2 = st.columns([1, 4])
            with col1:
                st.write(f"**{event['date']}**")
                st.caption(event['type'].replace('_', ' ').title())
            with col2:
                content = event.get('content', {})
                if 'condition' in content:
                    st.write(f"**Condition:** {content['condition']}")
                if 'note' in content:
                    st.write(content['note'])
                if 'labs' in content:
                    st.json(content['labs'])

def validate_patient_json(json_data: str) -> Optional[Dict]:
    """Validate patient JSON data"""
    try:
        data = json.loads(json_data)
        return validate_patient_data(data).model_dump()
    except Exception as e:
        st.error(f"Validation error: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="Medical Timeline Analysis", layout="wide")
    st.title("Medical Timeline Analysis Tool")

    # Initialize session state
    if 'medical_data' not in st.session_state:
        st.session_state.medical_data = None
    if 'edited_data' not in st.session_state:
        st.session_state.edited_data = None

    # Sidebar Configuration
    with st.sidebar:
        st.header("LLM Configuration")
        llm_provider = st.selectbox("LLM Provider", ["openai", "ollama", "mock"])
        
        api_key = None
        llm_model = "mock"
        
        if llm_provider == "openai":
            api_key = st.text_input("OpenAI API Key", type="password")
            if api_key:
                llm_model = st.selectbox("Model", ["gpt-4-turbo-preview", "gpt-3.5-turbo-0125"])
        
        elif llm_provider == "ollama":
            llm_model = st.selectbox("Model", ["llama3:70b", "llama3:8b", "mistral"])

    # Main UI
    col1, col2 = st.columns(2)

    with col1:
        st.header("1. Patient Data")
        if st.button("Generate Test Patient"):
            try:
                patients = generate_test_data()
                if isinstance(patients, list):
                    st.session_state.medical_data = patients[0]
                else:
                    st.session_state.medical_data = patients
                st.session_state.edited_data = json.dumps(st.session_state.medical_data, indent=2)
                st.success("Test patient data generated!")
            except Exception as e:
                st.error(f"Error generating data: {str(e)}")

        if st.session_state.get('medical_data'):
            st.subheader("Current Patient Record")
            demographics = st.session_state.medical_data.get('demographics', {})
            st.write(f"**Name:** {demographics.get('name', 'Unknown')}")
            
            if 'dob' in demographics:
                age = (datetime.now() - safe_date_parse(demographics['dob'])).days // 365
                st.write(f"**Age:** {age} years")
            
            st.write(f"**Gender:** {demographics.get('gender', 'Unknown')}")
            
            edited_json = st.text_area(
                "Edit JSON:",
                value=st.session_state.get('edited_data', ""),
                height=400
            )
            
            if st.button("Update Data"):
                validated = validate_patient_json(edited_json)
                if validated:
                    st.session_state.medical_data = validated
                    st.success("Data updated!")
            
            if 'timeline' in st.session_state.medical_data:
                display_timeline(st.session_state.medical_data['timeline'])

    with col2:
        st.header("2. Clinical Analysis")
        if st.session_state.get('medical_data'):
            question = st.selectbox(
                "Select question:",
                [
                    "Does the patient have uncontrolled hypertension?",
                    "Has the patient been hospitalized recently?",
                    "Is the patient on multiple medications?",
                    "Custom question..."
                ]
            )
            
            if question == "Custom question...":
                question = st.text_input("Enter question:")
            
            if st.button("Analyze") and question:
                with st.spinner("Analyzing..."):
                    try:
                        llm = get_llm(
                            provider=llm_provider,
                            model=llm_model,
                            openai_api_key=api_key
                        )
                        
                        prompt = create_medical_prompt(
                            st.session_state.medical_data, 
                            question
                        )
                        
                        response = llm.invoke(prompt)
                        answer, reason, evidence, confidence = parse_llm_response(response)
                        
                        st.subheader("Results")
                        if answer == "yes":
                            st.success("Yes")
                        elif answer == "no":
                            st.error("No")
                        else:
                            st.warning("Unknown")
                            
                        st.metric("Confidence", f"{confidence*100:.1f}%")
                        st.info(f"**Reasoning:** {reason}")
                        
                        if evidence:
                            st.write("**Evidence:**")
                            for item in evidence:
                                st.write(f"- {item}")
                        
                        with st.expander("View Raw Response"):
                            st.code(response.content if hasattr(response, 'content') else str(response))
                    
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    main()