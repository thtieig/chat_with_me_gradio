import os
import requests
from typing import List, Dict, Any, Optional, Tuple

def chat(
    endpoint: str,
    model_id: str,
    messages: List[Dict[str, str]],
    persona_description: str,
    model_config: Dict[str, Any],
    files: Optional[List[Dict[str, Any]]] = None
) -> Tuple[str, Dict[str, Any]]:
    """Generate a chat completion using Ollama API.
    
    Args:
        endpoint: API endpoint
        model_id: Model identifier
        messages: List of message dictionaries
        persona_description: Description of the persona
        model_config: Model configuration
        files: Optional list of file dictionaries
        
    Returns:
        Tuple of (response text, response metadata)
    """
    if not endpoint:
        endpoint = "http://localhost:11434"
    
    # Format messages for Ollama API
    formatted_messages = []
    
    # Add system message with persona description
    if persona_description:
        formatted_messages.append({
            "role": "system",
            "content": persona_description
        })
    
    # Add file contents to the first user message if files are provided
    if files and len(messages) > 0 and messages[0]["role"] == "user":
        file_content = ""
        for file in files:
            if "error" in file or "warning" in file:
                continue
                
            if file.get("is_text") and file.get("content"):
                file_content += f"\nFile: {file.get('filename')}\n"
                file_content += f"```{file.get('extension', '').lstrip('.')}\n"
                file_content += file.get("content", "")
                file_content += "\n```\n\n"
        
        if file_content:
            first_msg = messages[0]["content"]
            messages[0]["content"] = first_msg + "\n\nAttached files:\n" + file_content
    
    # Add user and assistant messages
    for msg in messages:
        role = msg["role"]
        # Ollama uses "assistant" for assistant messages
        if role == "assistant":
            ollama_role = "assistant"
        elif role == "system":
            ollama_role = "system"
        else:
            ollama_role = "user"
            
        formatted_messages.append({
            "role": ollama_role,
            "content": msg["content"]
        })
    
    # Prepare the API request
    payload = {
        "model": model_id,
        "messages": formatted_messages,
        "stream": False,
        "options": {
            "temperature": 0.7
        }
    }
    
    try:
        # Make the API request
        response = requests.post(
            f"{endpoint}/api/chat",
            json=payload
        )
        
        # Parse the response
        if response.status_code == 200:
            response_data = response.json()
            response_text = response_data.get("message", {}).get("content", "")
            
            # Return response text and metadata
            return response_text, {
                "model": model_id,
                "total_tokens": response_data.get("total_tokens", 0)
            }
        else:
            error_msg = f"Error: Ollama API returned status code {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg += f" - {error_data['error']}"
            except:
                pass
            
            return error_msg, {"error": error_msg}
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}", {"error": str(e)}