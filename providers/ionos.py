import os
import json
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
    """Generate a chat completion using IONOS API.
    
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
    api_key = os.environ.get("IONOS_API_KEY")
    if not api_key:
        return "Error: IONOS_API_KEY not found in environment variables", {}
    
    max_tokens = model_config.get("max_tokens", 2048)
    
    # Format messages for IONOS API
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
        formatted_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Prepare the API request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_id,
        "messages": formatted_messages,
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    
    try:
        # Make the API request
        response = requests.post(
            f"{endpoint}/chat/completions",
            headers=headers,
            json=payload
        )
        
        # Parse the response
        if response.status_code == 200:
            response_data = response.json()
            response_text = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Return response text and metadata
            usage = response_data.get("usage", {})
            return response_text, {
                "model": model_id,
                "usage": {
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                },
                "finish_reason": response_data.get("choices", [{}])[0].get("finish_reason", "stop")
            }
        else:
            error_msg = f"Error: IONOS API returned status code {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg += f" - {error_data['error'].get('message', '')}"
            except:
                pass
            
            return error_msg, {"error": error_msg}
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}", {"error": str(e)}