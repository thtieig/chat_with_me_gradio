import os
import requests
from typing import List, Dict, Any, Optional, Tuple
import google.generativeai as genai

def chat(
    endpoint: str,
    model_id: str,
    messages: List[Dict[str, str]],
    persona_description: str,
    model_config: Dict[str, Any],
    files: Optional[List[Dict[str, Any]]] = None
) -> Tuple[str, Dict[str, Any]]:
    """Generate a chat completion using Google's Gemini API.
    
    Args:
        endpoint: API endpoint (not used, Google client handles this)
        model_id: Model identifier
        messages: List of message dictionaries
        persona_description: Description of the persona
        model_config: Model configuration
        files: Optional list of file dictionaries
        
    Returns:
        Tuple of (response text, response metadata)
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "Error: GOOGLE_API_KEY not found in environment variables", {}
    
    genai.configure(api_key=api_key)
    max_tokens = model_config.get("max_tokens", 8192)
    
    # Create a chat session
    model = genai.GenerativeModel(model_name=model_id)
    chat = model.start_chat(history=[])
    
    # Add system message with persona description
    if persona_description:
        # Google uses the first user message with system instructions pattern
        system_msg = {"role": "user", "parts": [f"System instructions: {persona_description}\n\nPlease acknowledge these instructions."]}
        assistant_ack = {"role": "model", "parts": ["I'll follow these instructions in our conversation."]}
        chat.history.append(system_msg)
        chat.history.append(assistant_ack)
    
    # Process files if present
    file_content = ""
    if files:
        for file in files:
            if "error" in file or "warning" in file:
                continue
                
            if file.get("is_text") and file.get("content"):
                file_content += f"\nFile: {file.get('filename')}\n"
                file_content += f"```{file.get('extension', '').lstrip('.')}\n"
                file_content += file.get("content", "")
                file_content += "\n```\n\n"
    
    # Add user messages
    for msg in messages:
        content = msg["content"]
        role = msg["role"]
        
        # Add file content to first user message
        if role == "user" and file_content and msg == messages[0]:
            content = content + "\n\nAttached files:\n" + file_content
            file_content = ""  # Clear so we don't add it again
        
        if role == "user":
            chat.history.append({"role": "user", "parts": [content]})
        elif role == "assistant":
            chat.history.append({"role": "model", "parts": [content]})
    
    # Get response
    try:
        # If the last message is from the assistant, we need to add a user message
        last_role = messages[-1]["role"] if messages else None
        if last_role == "assistant" or not messages:
            response = chat.send_message("Please continue")
        else:
            # The last message added to the chat was from the user, so we can just get the response
            # We need to use the last user message for generation
            last_user_message = messages[-1]["content"]
            response = chat.send_message(last_user_message)
        
        response_text = response.text
        
        # Return response text and basic metadata (Google doesn't provide token counts like OpenAI)
        return response_text, {
            "model": model_id,
            "finish_reason": "stop"  # Google doesn't provide this info directly
        }
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}", {"error": str(e)}