# Copyright (c) 2025 Sumi Somangili
# All rights reserved.
import os
import streamlit as st
from dotenv import load_dotenv
from medical_extraction.llm_integration import get_llm
from medical_extraction.utils.data_generator import generate_test_data

# Initialize environment and session state
load_dotenv()

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
            if st.button("🔍 Analyze", disabled=st.session_state.disabled):
                with st.spinner("Processing..."):
                    try:
                        llm = get_llm(
                            provider=llm_provider,
                            model=llm_model,
                            openai_api_key=api_key if llm_provider == "openai" else None
                        )
                        
                        # Use the extractor properly
                        from medical_extraction.core import MedicalExtractor
                        extractor = MedicalExtractor(llm)
                        
                        result = extractor.extract(
                            st.session_state.medical_data,
                            question
                        )
                        
                        st.subheader("Results")
                        st.json(result)
                        
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")
                        st.error("Full error details:", e)
                
            
                        

if __name__ == "__main__":
    main()