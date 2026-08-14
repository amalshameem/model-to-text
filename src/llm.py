import requests
import streamlit as st
import time
from openai import OpenAI

@st.cache_data(ttl=300, show_spinner=False)
def fetch_models(provider, endpoint, api_key):
    """
    Fetches available models dynamically based on the selected LLM provider.
    Results are cached for 5 minutes to prevent Streamlit UI selection glitches.
    """
    models = []
    try:
        headers = {}
        if provider == "LM Studio":
            base_url = endpoint.rstrip('/') if endpoint else "http://localhost:1234/v1"
            url = f"{base_url}/models"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model["id"] for model in data.get("data", [])]
            else:
                models = [f"Error: {response.status_code}"]
                
        elif provider == "Ollama":
            base_url = endpoint.rstrip('/') if endpoint else "https://ollama.com"
            if api_key:
                headers = {"Authorization": f"Bearer {api_key}"}
                
            models = []
            # 1. Try native Ollama endpoint
            if base_url.endswith("/api"):
                native_url = f"{base_url}/tags"
            else:
                native_url = f"{base_url}/api/tags"
            native_response = None
            try:
                native_response = requests.get(native_url, headers=headers, timeout=5)
                if native_response.status_code == 200:
                    data = native_response.json()
                    models = [model["name"] for model in data.get("models", [])]
            except Exception:
                pass
                
            # 2. If native failed, try OpenAI-compatible endpoint
            if not models:
                openai_url = f"{base_url}/models" if base_url.endswith("/v1") else f"{base_url}/v1/models"
                try:
                    openai_response = requests.get(openai_url, headers=headers, timeout=5)
                    if openai_response.status_code == 200:
                        data = openai_response.json()
                        models = [model["id"] for model in data.get("data", [])]
                    else:
                        # Combine errors to help user debug
                        err1 = native_response.status_code if native_response else "Timeout/DNS"
                        err2 = openai_response.status_code
                        models = [f"Failed to connect (Native: {err1}, OpenAI: {err2})"]
                except Exception as e:
                    models = [f"Connection Failed. Check URL. ({str(e)[:40]})"]
    except Exception as e:
        models = [f"Connection Failed: {str(e)}"]
        
    if models:
        # Sort alphabetically to guarantee stable UI ordering in Streamlit
        models.sort()
        return models
    else:
        return ["No models found"]

def generate_text(prompt: str, endpoint: str, api_key: str, model_name: str) -> str:
    client = OpenAI(
        base_url=endpoint,
        api_key=api_key if api_key else "not-needed-for-local"
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that explains BPMN models perfectly, grammatically, and completely without missing a single detail."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Generation error: {e}. Retrying... ({attempt+1}/{max_retries})")
            time.sleep(1.0 * (attempt + 1))
    return f"Failed to generate text after {max_retries} retries."

def get_model_explanation(parsed_json: str, endpoint: str, api_key: str, model_name: str) -> str:
    """
    Wraps the parsed JSON in the prompt template.
    """
    prompt = f"""[CONTEXT] You are an expert enterprise business analyst translating technical process models for non-technical stakeholders.
[AUDIENCE STYLE] Target: Business Stakeholder. Use plain language without jargon.
[DATA INJECTION]
{parsed_json}
[RESTRICTIONS] Do not invent any new actors or steps. Base narrative strictly on the JSON file."""
    
    explanation = generate_text(prompt, endpoint, api_key, model_name)
    return explanation
