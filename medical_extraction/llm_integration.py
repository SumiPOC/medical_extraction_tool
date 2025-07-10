# Copyright (c) 2025 Sumi Somangili
# All rights reserved.
from typing import Literal
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI
import json
import os
from dotenv import load_dotenv

# Load environment variables first thing
load_dotenv() 

LLM_Provider = Literal["ollama", "openai", "mock"]

def get_llm(
    provider: LLM_Provider = "ollama",
    model: str = None,
    **kwargs
):
    """Factory function for LLMs with auto-fallback"""
    if provider == "mock":
        return _get_mock_llm()
    
    try:
        if provider == "openai":
            return _get_openai_llm(model or "gpt-3.5-turbo", **kwargs)
        else:
            return _get_ollama_llm(model or "llama3", **kwargs)
    except ImportError:
        print(f"Warning: {provider} not available, using mock LLM")
        return _get_mock_llm()

def _get_mock_llm():
    class MockLLM:
        def invoke(self, prompt):
            return json.dumps({
                "treatments": [{
                    "medications": ["amoxicillin"],
                    "facility": "Mock Hospital"
                }],
                "has_condition": True
            })
    return MockLLM()

def _get_openai_llm(model: str, **kwargs):
    # Use API key from .env if not passed explicitly
    api_key = kwargs.pop('openai_api_key', None) or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in .env or pass explicitly")
    
    return ChatOpenAI(
        model=model,
        api_key=api_key,  # Now properly sourced
        model_kwargs={
            "response_format": {"type": "json_object"}
        },
        **kwargs
    )

def _get_ollama_llm(model: str, **kwargs):
    return Ollama(
        model=model,
        format="json",  # Ensures JSON output
        **kwargs
    )