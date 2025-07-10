# Copyright (c) 2025 Sumi Somangili
# All rights reserved.
import os
import json
import streamlit as st
from dotenv import load_dotenv
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

Clinical Notes (analyze these):
{json.dumps(medical_data['medical_notes'], indent=2)}

Return valid JSON ONLY:"""

def parse_llm_response(response: str) -> tuple:
    """Extracts answer from the content field of the response"""
    try:
        # Handle different response formats
        if hasattr(response, 'content'):  # If it's an LLM response object
            content = response.content
        elif isinstance(response, str):
            content = response
        else:
            content = str(response)
        
        # Clean the content string
        content = content.strip().replace("'", '"')  # Fix single quotes
        
        # Parse the JSON
        result = json.loads(content)
        return (
            result.get("Answer", "unknown").lower(),
            result.get("Reason", "No reason provided"),
            result.get("Evidence", []),
            float(result.get("Confidence", 0))
        )
    except Exception as e:
        print(f"Failed to parse response: {e}")
        print(f"Raw response content: {content if 'content' in locals() else response}")
        return "error", f"Parse error: {str(e)}", [], 0
    except Exception as e:
        print(f"Failed to parse response: {e}")
        print(f"Raw response content: {content if 'content' in locals() else response}")
        return "error", f"Parse error: {str(e)}", [], 0



def main():
    st.set_page_config(page_title="Medical Extraction", layout="wide")
    st.title("🩺 Medical Condition Extraction Tool")

    # Initialize session state variables
    if 'medical_data' not in st.session_state:
        st.session_state.medical_data = None
    if 'disabled' not in st.session_state:
        st.session_state.disabled = False

    # --- Sidebar Configuration ---
    with st.sidebar:
        st.header("LLM Configuration")

        # Provider selection
        llm_provider = st.selectbox(
            "LLM Provider",
            ["ollama", "openai", "mock"],
            index=0
        )

        # Provider-specific settings
        api_key = None
        if llm_provider == "openai":
            env_key = os.getenv("OPENAI_API_KEY")
            if not env_key:
                st.text_input(
                    "OpenAI API Key",
                    key="openai_key",
                    type="password",
                    help="Get yours from https://platform.openai.com/api-keys"
                )
                api_key = st.session_state.get("openai_key")
            else:
                api_key = env_key
                st.success("Using OpenAI key from .env")

        elif llm_provider == "ollama":
            st.info("Ensure Ollama is running locally")
            if st.button("Check Ollama Connection"):
                try:
                    import ollama
                    ollama.list()
                    st.success("Ollama connected!")
                except Exception as e:
                    st.error(f"Ollama error: {str(e)}")

        # Model selection
        default_models = {
            "ollama": "llama3",
            "openai": "gpt-3.5-turbo",
            "mock": "mock"
        }
        llm_model = st.text_input(
            "Model Name",
            value=default_models[llm_provider],
            help=f"Examples: {default_models[llm_provider]} for {llm_provider}"
        )

    # --- Main UI ---
    col1, col2 = st.columns(2)

    with col1:
        st.header("1. Data Input")
        if st.button("✨ Generate Test Data"):
            st.session_state.medical_data = generate_test_data()
            st.success("Test data generated!")

        if st.session_state.medical_data:
            st.subheader("Current Data")
            st.json(st.session_state.medical_data, expanded=False)

    with col2:
        st.header("2. Analysis")
        if st.session_state.medical_data:
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
                    
                    prompt = create_medical_prompt(st.session_state.medical_data, question)
                    response = llm.invoke(prompt)
                    
                    # Debug view - show raw response structure
                    # with st.expander("🔧 Raw Response Structure"):
                    #     st.write("Type:", type(response))
                    #     st.json(vars(response))  # Show all attributes
                    
                    # Debug view - show content field
                    with st.expander("📄 Response Content"):
                        st.code(response.content, language='json')
                    
                    # Parse and display
                    answer, reason, evidence, confidence = parse_llm_response(response)
                    
                    # Display results
                    st.subheader("Clinical Analysis")
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        if answer == "yes":
                            st.success("✅ Yes")
                        elif answer == "no":
                            st.error("❌ No")
                        else:
                            st.warning("⚠️ Unknown")
                        st.metric("Confidence", f"{confidence*100:.0f}%")
                    
                    with col2:
                        st.info(f"**Clinical Reasoning:**\n{reason}")
                        
                        if evidence:
                            st.markdown("**Supporting Evidence:**")
                            for item in evidence:
                                st.write(f"- {item}")
                        else:
                            st.warning("No specific evidence cited")

                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
                    with st.expander("Technical Details"):
                        st.exception(e)
if __name__ == "__main__":
    main()
