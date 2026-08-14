# Model to Text
Turn enterprise process models (BPMN 2.0 or generic XML) into clear, natural language explanations using LLMs. Upload a model, watch it parsed into a structured intermediate format, and get a readable narrative generated for non-technical stakeholders, all inside a simple Streamlit app

## Features
-BPMN and XML parsing: reads BPMN 2.0 files (tasks, gateways, events, pools, lanes, data objects) and falls back to a generic XML parser for other model formats.

-Structured intermediate representation: every model is converted into a clean JSON schema before it ever reaches the LLM, so the language model only rephrases real facts instead of guessing at them.

-Ordered process sequencing: the app works out the correct step-by-step flow of the process on its own, even if the original file lists everything out of order.

-Local LLM integration: connects to LM Studio or Ollama, auto discovers available models, and standardizes all requests through a single OpenAI compatible client.

-Grounded prompt engineering: a persona based prompt keeps the generated text in plain business language and explicitly restricts the model from inventing actors, steps, or relationships not present in the source.

-Interactive diagram viewer: the original diagram is displayed as an interactive picture you can zoom and pan around, right next to the written explanation.

-Side by side inspection: tabs let you view the original file, the parsed JSON, and the generated explanation together for easy verification.

-Automatic evaluation logging: every generated explanation is appended to a CSV log with its source file and model name, ready for benchmarking.

## Installation

Follow these steps to get `model-to-text` up and running on your local machine.

### Prerequisites

Ensure you have Python 3.8+ installed.

### Manual Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/amalshameem/model-to-text.git
    cd model-to-text
    ```
    
2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create an .env file and add the API keys**:
    ```bash
    OLLAMA_API_KEY="<your_key_here>"
    ```

5.  **Usage**:
    ```bash
    streamlit run app.py
    ```

## Folder structurce
    model-to-text
    ├── .env
    ├── app.py
    └── src/
       ├── llm.py
       ├── parser.py
       └── visualizer.py
