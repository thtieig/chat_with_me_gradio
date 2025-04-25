import os
import requests
import json
from typing import List, Dict, Any, Optional, Tuple
import anthropic

def chat(
    endpoint: str,
    model_id: str,
    messages: List[Dict[str, str]],
    persona_description: str,
    model_config: Dict[str, Any],
    files: Optional[List[Dict[str, Any]]] = None
) -> Tuple[str, Dict[str, Any]]:
    """Generate a chat completion using Anthropic's Claude API.
    
    Args:
        endpoint: API endpoint (not used, Anthropic client handles this)
        model_id: Model identifier
        messages: List of message dictionaries
        persona_description: Description of the persona
        model_config: Model configuration
        files: Optional list of file dictionaries
        
    Returns:
        Tuple of (response text, response metadata)
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "Error: ANTHROPIC_API_KEY not found in environment variables", {}
    
    client = anthropic.Anthropic(api_key=api_key)
    max_tokens = model_config.get("max_tokens", 4096)
    
    # Format messages for Anthropic API
    anthropic_messages = []
    
    # Add system message with persona description
    if persona_description:
        anthropic_messages.append({
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
    
    # Convert message format to Anthropic format
    for msg in messages:
        role = msg["role"]
        # Map 'assistant' to 'assistant' and everything else to 'user'
        anthropic_role = role if role == "assistant" else "user"
        anthropic_messages.append({
            "role": anthropic_role,
            "content": msg["content"]
        })
    
    try:
        response = client.messages.create(
            model=model_id,
            messages=anthropic_messages,
            max_tokens=max_tokens
        )
        
        # Extract response text
        response_text = response.content[0].text
        
        # Return response text and metadata
        return response_text, {
            "model": model_id,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            "finish_reason": response.stop_reason
        }
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}", {"error": str(e)}