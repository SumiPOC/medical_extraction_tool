# Copyright (c) 2025 Sumi Somangili
# All rights reserved.
import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI  # Updated import
from medical_extraction.llm_integration import get_llm
from medical_extraction.utils.data_generator import generate_test_data
from medical_extraction.schemas import MedicalRecord, ExtractionResult

# Initialize environment and session state
load_dotenv()


def create_medical_prompt(medical_data: dict, question: str) -> str:
    """Creates a prompt that forces valid JSON output with clinical analysis"""
    return f"""You are a medical analyst. Return JSON with:
1. Clear yes/no answer
2. Clinical reasoning
3. Supporting evidence

Format MUST be:
{{
  "Answer": "yes|no",
  "Reason": "string",
  "Evidence": ["string"],
  "Confidence": 0-1
}}

Patient Data:
- ID: {medical_data['patient_id']}
- Conditions: {', '.join(medical_data.get('chronic_conditions', ['None']))}

Question: {question}

Clinical Notes (analyze these, pay very close attention to the note field):
{json.dumps(medical_data['medical_notes'], indent=2)}

Return valid JSON ONLY:"""


def parse_llm_response(response: str) -> tuple:
    """Robustly extracts answer from LLM response with comprehensive error handling"""
    try:
        # Extract content from different response types
        content = ""
        if hasattr(response, 'content'):  # LLM response object
            content = response.content
        elif isinstance(response, str):
            content = response
        else:
            content = str(response)

        # Debug: Print raw response before cleaning
        print(f"Raw response received:\n{content}")

        # Common LLM JSON response cleaning
        content = content.strip()
        
        # Remove markdown code fences if present
        if content.startswith("```json"):
            content = content[7:].strip()
        if content.startswith("```"):
            content = content[3:].strip()
        if content.endswith("```"):
            content = content[:-3].strip()
        
        # Remove leading/trailing quotes and whitespace
        content = content.strip('"\' \n')

        # Handle cases where LLM adds explanations before/after JSON
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start != -1 and json_end != 0:
            content = content[json_start:json_end]

        # Fix common JSON issues
        content = (content
                   .replace('\\"', '"')  # Unescape quotes
                   .replace('\\n', ' ')  # Newlines in strings
                   .replace("'", '"'))    # Single to double quotes

        # Debug: Print cleaned content
        print(f"Cleaned content:\n{content}")

        # Parse JSON with detailed error reporting
        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            # Try adding quotes around unquoted fields if needed
            if 'Expecting property name enclosed in double quotes' in str(e):
                content = re.sub(r'(\w+):', r'"\1":', content)
                result = json.loads(content)
            else:
                raise

        # Validate required fields
        if not all(key in result for key in ['Answer', 'Reason']):
            raise ValueError("Missing required fields in JSON response")

        return (
            str(result.get("Answer", "unknown")).lower().strip(),
            str(result.get("Reason", "No reason provided")),
            list(result.get("Evidence", [])),
            float(result.get("Confidence", 0)))
        
    except json.JSONDecodeError as e:
        error_msg = f"JSON Parse Error: {str(e)}\nProblematic content:\n{content[:200]}..."
        print(error_msg)
        return "error", error_msg, [], 0
        
    except Exception as e:
        error_msg = f"Unexpected error: {type(e).__name__}: {str(e)}"
        print(error_msg)
        return "error", error_msg, [], 0
        
def check_model_access(api_key: str, model: str) -> bool:
    """Check if a specific model is available"""
    try:
        client = OpenAI(api_key=api_key)
        client.models.retrieve(model)
        return True
    except:
        return False


def main():
    st.set_page_config(page_title="Medical Extraction", layout="wide")
    st.title("🩺 Medical Condition Extraction Tool")

    # Initialize all session state variables
    if 'medical_data' not in st.session_state:
        st.session_state.medical_data = None
    if 'edited_data' not in st.session_state:
        st.session_state.edited_data = None
    if 'disabled' not in st.session_state:
        st.session_state.disabled = False

    # --- Sidebar Configuration ---
    with st.sidebar:
        st.header("LLM Configuration")

        # Provider selection
        llm_provider = st.selectbox(
            "LLM Provider",
            ["openai", "ollama", "mock"],
            index=0
        )

        # Model selection with clear labels
        if llm_provider == "openai":
            # Get API key first
            env_key = os.getenv("OPENAI_API_KEY")or st.secrets.get("OPENAI_API_KEY") or st.secrets.get("openai", {}).get("api_key")
            env_key="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"
            if not env_key:
                api_key = st.text_input(
                    "OpenAI API Key",
                    type="password",
                    help="Get yours from https://platform.openai.com/api-keys"
                )
            else:
                api_key = env_key

            # Check model availability
            # In the OpenAI model selection section of your code:
            if api_key:
                gpt4_available = check_model_access(
                    api_key, "gpt-4-turbo-preview")

                if gpt4_available:
                    model_options = [
                        ("GPT-4 Turbo", "gpt-4-turbo-preview"),
                        ("GPT-3.5 Turbo", "gpt-3.5-turbo-0125")
                    ]
                    llm_model = st.selectbox(
                        "OpenAI Model",
                        options=model_options,
                        format_func=lambda x: x[0],
                        index=0
                    )
                    llm_model = llm_model[1]  # Get the actual model ID
                else:
                    # When GPT-4 is not available, don't show the selectbox
                    # and directly set the model to GPT-3.5
                    llm_model = "gpt-3.5-turbo-0125"
                    st.warning("GPT-4 not available - defaulting to GPT-3.5")

        elif llm_provider == "ollama":
            model_options = [
                ("Llama 3 (70B)", "llama3:70b"),
                ("Llama 3 (8B)", "llama3:8b"),
                ("Mistral (7B)", "mistral")
            ]
            selected_model = st.selectbox(
                "Ollama Model",
                options=model_options,
                format_func=lambda x: x[0],
                index=1
            )
            llm_model = selected_model[1]

            if st.button("Check Ollama Connection"):
                try:
                    import ollama
                    ollama.list()
                    st.success("Ollama connected!")
                except Exception as e:
                    st.error(f"Ollama error: {str(e)}")

        else:  # mock provider
            llm_model = "mock"
            st.info("Using mock responses for testing")

    # --- Main UI ---
    col1, col2 = st.columns(2)

    with col1:
        st.header("1. Data Input")

        if st.button("✨ Generate Test Data"):
            st.session_state.medical_data = generate_test_data()
            st.session_state.edited_data = json.dumps(
                st.session_state.medical_data, indent=2)
            st.success("Test data generated!")

        if st.session_state.get('medical_data'):
            st.subheader("Current Data")

            # Editable JSON text area
            edited_json = st.text_area(
                "Edit JSON (make changes below):",
                value=st.session_state.get('edited_data', json.dumps(
                    st.session_state.medical_data, indent=2)),
                height=400,
                key="json_editor"
            )

            # Update button
            if st.button("🔄 Update Data"):
                try:
                    st.session_state.medical_data = json.loads(edited_json)
                    st.session_state.edited_data = edited_json
                    st.success("Data updated successfully!")
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON: {str(e)}")

            # Validation expander
            with st.expander("🔍 Validate Structure"):
                try:
                    MedicalRecord(**st.session_state.medical_data)
                    st.success("✅ Valid medical record structure")
                except Exception as e:
                    st.error(f"❌ Validation error: {str(e)}")
                    st.json(MedicalRecord.schema(), expanded=False)

    with col2:
        st.header("2. Analysis")
        if st.session_state.get('medical_data'):
            question = st.text_input(
                "Enter your medical question:",
                "Did the patient have H. pylori?"
            )

            if st.button("🔍 Analyze"):
                with st.spinner("Processing..."):
                    try:
                        llm = get_llm(
                            provider=llm_provider,
                            model=llm_model,
                            openai_api_key=api_key if llm_provider == "openai" else None
                        )

                        prompt = create_medical_prompt(
                            st.session_state.medical_data, question)
                        response = llm.invoke(prompt)

                        # Debug view - show content field
                        with st.expander("📄 Response Content"):
                            st.code(response.content, language='json')

                        # Parse and display
                        answer, reason, evidence, confidence = parse_llm_response(
                            response)

                        # Display results
                        st.subheader("Clinical Analysis")
                        col_a, col_b = st.columns([1, 3])

                        with col_a:
                            if answer == "yes":
                                st.success("✅ Yes")
                            elif answer == "no":
                                st.error("❌ No")
                            else:
                                st.warning("⚠️ Unknown")
                            st.metric("Confidence", f"{confidence*100:.0f}%")

                        with col_b:
                            st.info(f"**Clinical Reasoning:**\n{reason}")

                            if evidence:
                                st.markdown("**Supporting Evidence:**")
                                for item in evidence:
                                    st.write(f"- {item}")
                            else:
                                st.warning("No specific evidence cited")

                    except Exception as e:
                        error_msg = str(e)
                        if "model_not_found" in error_msg:
                            st.error("""
                            **Model Access Error**  
                            The selected model is not available.  
                            Possible solutions:  
                            - Try GPT-3.5 instead  
                            - [Check your OpenAI access](https://platform.openai.com/account/org-settings)  
                            - [Upgrade your plan](https://openai.com/pricing)  
                            """)
                        else:
                            st.error(f"Analysis failed: {error_msg}")
                        with st.expander("Technical Details"):
                            st.exception(e)


if __name__ == "__main__":
    main()
