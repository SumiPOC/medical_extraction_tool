from typing import Literal
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI
import json
import os
from dotenv import load_dotenv

load_dotenv()

LLM_Provider = Literal["ollama", "openai", "mock"]

def get_llm(provider: LLM_Provider = "ollama", model: str = None, **kwargs):
    if provider == "mock":
        return _get_mock_llm()
    try:
        if provider == "openai":
            return _get_openai_llm(model or "gpt-3.5-turbo", **kwargs)
        return _get_ollama_llm(model or "llama3", **kwargs)
    except ImportError:
        print(f"Warning: {provider} not available, using mock LLM")
        return _get_mock_llm()

def _get_mock_llm():
    class MockLLM:
        def invoke(self, prompt):
            return json.dumps({
                "Answer": random.choice(["yes", "no"]),
                "Reason": "Mock response",
                "Evidence": ["Sample evidence 1", "Sample evidence 2"]
            })
    return MockLLM()

def _get_openai_llm(model: str, **kwargs):
    api_key = kwargs.pop('openai_api_key', None) or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found in .env or arguments")

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        model_kwargs={
            "response_format": {"type": "json_object"}
        },
        **kwargs
    )

def _get_ollama_llm(model: str, **kwargs):
    return Ollama(
        model=model,
        format="json",
        **kwargs
    )