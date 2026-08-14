import streamlit as st
import streamlit.components.v1 as components
import os
import json
from dotenv import load_dotenv

from src.parser import parse_model
from src.llm import fetch_models, get_model_explanation
from src.visualizer import render_bpmn

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Model Explainer", layout="wide")

# Initialize session state to store generated texts so they survive re-renders
if "generated_texts" not in st.session_state:
    st.session_state["generated_texts"] = {}

import csv

def save_to_csv(input_file, model_name, generated_text):
    """Automatically logs generated texts to the evaluation CSV."""
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluation", "sample_model_outputs.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    file_exists = os.path.exists(csv_path)
    
    # Prevent appending to the Apple Numbers zip file by checking the magic number
    is_valid_csv = True
    if file_exists:
        try:
            with open(csv_path, 'rb') as f:
                if f.read(2) == b'PK':
                    is_valid_csv = False
        except:
            pass

    # Overwrite if it's the Numbers file or missing, otherwise append
    mode = 'a' if (file_exists and is_valid_csv) else 'w'
    
    with open(csv_path, mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        if mode == 'w':
            writer.writerow(["Input_File", "Model_Name", "Generated_Text"])
        writer.writerow([input_file, model_name, generated_text])

st.title("Model to Text Explainer")
st.write("Upload a BPMN or XML file to generate process explanations.")

# Sidebar settings for LLM configuration
st.sidebar.header("LLM Settings")
provider = st.sidebar.selectbox("LLM Provider", ["LM Studio", "Ollama"])

endpoint = ""
if provider == "LM Studio":
    endpoint = "http://localhost:1234/v1"
elif provider == "Ollama":
    endpoint = "https://ollama.com/v1"
    
api_key = ""
if provider == "Ollama":
    api_key = os.getenv("OLLAMA_API_KEY", "")

with st.sidebar.spinner("Fetching models..."):
    available_models = fetch_models(provider, endpoint, api_key)
    
selected_model = st.sidebar.selectbox("Select Model", available_models)

# File uploader (Single file only)
uploaded_file = st.file_uploader("Upload Model File", type=["bpmn", "xml", "cml"], accept_multiple_files=False)

if uploaded_file:
    file_content = uploaded_file.getvalue().decode("utf-8")
    file_type = "cml" if uploaded_file.name.endswith(".cml") else "bpmn"
    parsed_json = parse_model(file_content, file_type=file_type)
    
    st.markdown(f"### 📄 {uploaded_file.name}")
    
    # Show Visual Diagram tab only if it's a BPMN file
    if file_type == "bpmn":
        tab_visual, tab_xml, tab_json, tab_text = st.tabs([
            "Visual Diagram", 
            "Original File (XML)", 
            "Parsed File (JSON)", 
            "Generated Text"
        ])
    else:
        # CML files don't render visually in bpmn-js
        tab_xml, tab_json, tab_text = st.tabs([
            "Original File (CML)", 
            "Parsed File (JSON)", 
            "Generated Text"
        ])
        
    if file_type == "bpmn":
        with tab_visual:
            st.info("Interactive Diagram: Scroll to zoom, click and drag to pan.")
            render_bpmn(file_content)
            
    with tab_xml:
        st.code(file_content, language="xml")
        
    with tab_json:
        st.code(parsed_json, language="json")
        
    with tab_text:
        if st.button("Generate Explanation", type="primary"):
            with st.spinner(f"Generating explanation using {selected_model}..."):
                explanation = get_model_explanation(parsed_json, endpoint, api_key, selected_model)
                st.session_state["generated_texts"][uploaded_file.name] = explanation
                
                # Automatically save to the CSV for evaluation
                save_to_csv(uploaded_file.name, selected_model, explanation)
                st.success(f"Generated text automatically saved to evaluation/sample_model_outputs.csv!")
                
        if uploaded_file.name in st.session_state["generated_texts"]:
            st.markdown("---")
            st.write(st.session_state["generated_texts"][uploaded_file.name])
