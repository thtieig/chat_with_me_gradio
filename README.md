# Multi-Provider AI Chatbot

A feature-rich Gradio-based chatbot application that supports multiple LLM providers, models, and personas.

## Features

- **Multiple LLM Providers**: IONOS, Google, Anthropic, and Ollama support
- **Model Selection**: Choose from various models offered by each provider
- **Persona System**: Customize the chatbot's behavior with different personas
- **File Upload**: Attach files to provide context for your questions
- **Folder Processing**: Load entire directories of files
- **Chat History**: Persistent conversations
- **Clean, Modern UI**: Customizable interface

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
     
   NOTE. This app is based on [Gradio](https://www.gradio.app/). You can also set [environment variables for Gradio](https://www.gradio.app/guides/environment-variables) in this file.  
   For example, if you want to run your app on port `5001` and serve it from `https:\\mydomain.com/v2`, you can add the following:
   ```
   GRADIO_SERVER_PORT=5001
   GRADIO_SERVER_NAME="https:\\mydomain.com"
   GRADIO_ROOT_PATH="/v2"
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

In the `config` folder, create a copy of the `config.yaml.example` template to create your own `config.yaml`.   
The `config.yaml` file contains several configuration options, including:

### UI Configuration

The ui section in `config.yaml` allows you to customize the chatbot's UI. For example, you can modify the `title`, `welcome_message`, and t`itle_css` to give your chatbot a personalized touch. Try this CSS for a more colorful experience:
```css
title_css: |
  .title-container {
    text-align: center;
    margin: 0;
    padding: 0.1em;
    height: 6rem; 
    line-height: 6rem; 
    color: white; 
  }

  .title-container span {
    font-size: 3rem; /* size that fits the container */
    padding: 0.1em;
    background: linear-gradient(to right, #ff0000, #ffa500, #ffff00, #008000, #0000ff, #4b0082, #ee82ee, #ff69b4, #ff00ff, #800080);
    color: transparent;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
```
This will give your title a rainbow-colored gradient effect.  

### Adding New Providers

1. Create a new provider module in the `providers` directory
2. Implement the `chat()` function as seen in the existing provider modules
3. Add the provider configuration to `config.yaml`

### Adding New Personas

Add new persona entries to the `personas` list in `config.yaml`.

### File Handling Configuration

The file_handling section in `config.yaml` allows you to configure the file upload capabilities. You can modify the `allowed_extensions`, `max_file_size_mb`, and `max_files_per_upload` to suit your needs. For example:

```
file_handling:
  allowed_extensions: [".txt", ".py", ".js", ".html", ".css", ".json", ".md", ".csv", ".pdf"]
  max_file_size_mb: 10
  max_files_per_upload: 100
```
This configuration allows users to upload files with the specified extensions, with a maximum size of 10MB and a maximum of 100 files per upload.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).