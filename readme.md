# Model to Text
## Features
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
