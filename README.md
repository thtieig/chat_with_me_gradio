# Multi-Provider AI Chatbot

A feature-rich Gradio-based chatbot application that supports multiple LLM providers, models, and personas.

## Features

- **Multiple LLM Providers**: IONOS, Google, Anthropic, and Ollama support
- **Model Selection**: Choose from various models offered by each provider
- **Persona System**: Customize the chatbot's behavior with different personas
- **File Upload**: Attach files to provide context for your questions
- **Folder Processing**: Load entire directories of files
- **Chat History**: Persistent conversations
- **Clean, Modern UI**: Rainbow-themed interface

## Installation

1. Clone this repository:
    ```bash
    git clone https://thtieig@bitbucket.org/thtieig/chat_with_me_gradio.git
    cd chat_with_me_gradio
    ```

2.  Create a virtual environment (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  
    ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your API keys in the `.env` file:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key
   GOOGLE_API_KEY=your_google_api_key
   IONOS_API_KEY=your_ionos_api_key
   OLLAMA_API_BASE=http://localhost:11434
   ```

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to `http://localhost:7860`

3. Select your preferred provider, model, and persona from the dropdown menus

4. Start chatting!

## File Structure

```
📦 multi_provider_chatbot/
 ┣ 📂 config/
 ┃ ┗ 📜 config.yaml      # Configuration for providers, models, personas
 ┣ 📂 utils/
 ┃ ┣ 📜 chat_history.py  # Chat history management
 ┃ ┣ 📜 file_handler.py  # File and folder handling utilities
 ┃ ┗ 📜 llm_manager.py   # LLM integration handling
 ┣ 📂 providers/
 ┃ ┣ 📜 anthropic.py     # Anthropic API integration
 ┃ ┣ 📜 google.py        # Google API integration
 ┃ ┣ 📜 ionos.py         # IONOS API integration
 ┃ ┗ 📜 ollama.py        # Ollama API integration
 ┣ 📜 .env               # Environment variables for API keys
 ┣ 📜 app.py             # Main Gradio application
 ┣ 📜 requirements.txt   # Project dependencies
 ┗ 📜 README.md          # Project documentation
```

## Customization

In the `config` folder, create a copy of the `config.yaml.example` template to create your own `config.yaml` 

### Adding New Providers

1. Create a new provider module in the `providers` directory
2. Implement the `chat()` function as seen in the existing provider modules
3. Add the provider configuration to `config.yaml`

### Adding New Personas

Add new persona entries to the `personas` list in `config.yaml`.

### Modifying the UI

The UI components are defined in the `create_chatbot_ui()` function in `app.py`.

## License

MIT