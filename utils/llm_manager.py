import os
import importlib
from typing import Dict, List, Any, Optional, Tuple
import yaml
import dotenv
from pathlib import Path

# Load environment variables
dotenv.load_dotenv()

class LLMManager:
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the LLM Manager.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config = self._load_config(config_path)
        self.provider_modules = {}
        self._load_provider_modules()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to the YAML configuration file
            
        Returns:
            Dictionary with configuration
        """
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {
                "providers": {},
                "personas": [],
                "generic_settings": "",
                "ui": {"title": "AI Chatbot", "title_color": "blue"}
            }
    
    def _load_provider_modules(self):
        """Load provider modules dynamically."""
        for provider_id in self.config.get("providers", {}):
            try:
                module_name = provider_id.lower()
                module = importlib.import_module(f"providers.{module_name}")
                self.provider_modules[provider_id] = module
            except Exception as e:
                print(f"Failed to load provider module {provider_id}: {e}")
    
    def get_providers(self) -> List[Dict[str, str]]:
        """Get list of available providers.
        
        Returns:
            List of provider dictionaries with id and name
        """
        return [
            {"id": provider_id, "name": provider_info.get("name", provider_id)}
            for provider_id, provider_info in self.config.get("providers", {}).items()
        ]
    
    def get_models(self, provider_id: str) -> List[Dict[str, str]]:
        """Get list of models for a specific provider.
        
        Args:
            provider_id: Provider identifier
            
        Returns:
            List of model dictionaries with id and name
        """
        provider_info = self.config.get("providers", {}).get(provider_id, {})
        return provider_info.get("models", [])
    
    def get_personas(self) -> List[Dict[str, str]]:
        """Get list of available personas.
        
        Returns:
            List of persona dictionaries with id and name
        """
        return self.config.get("personas", [])
    
    def get_persona_description(self, persona_id: str) -> str:
        """Get the description for a specific persona.
        
        Args:
            persona_id: Persona identifier
            
        Returns:
            Persona description with generic settings appended
        """
        personas = self.config.get("personas", [])
        generic_settings = self.config.get("generic_settings", "")
        
        for persona in personas:
            if persona.get("id") == persona_id:
                description = persona.get("description", "")
                if generic_settings:
                    description = f"{description}\n\n{generic_settings}"
                return description
        
        return generic_settings
    
    def chat_completion(self, 
                       provider_id: str, 
                       model_id: str, 
                       persona_id: str, 
                       messages: List[Dict[str, str]],
                       files: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, Dict[str, Any]]:
        """Generate a chat completion using the specified provider and model.
        
        Args:
            provider_id: Provider identifier
            model_id: Model identifier
            persona_id: Persona identifier
            messages: List of message dictionaries
            files: Optional list of file dictionaries
            
        Returns:
            Tuple of (response text, response metadata)
        """
        if provider_id not in self.provider_modules:
            return f"Error: Provider {provider_id} not available", {}
        
        persona_description = self.get_persona_description(persona_id)
        provider_module = self.provider_modules[provider_id]
        
        # Get provider-specific parameters
        provider_config = self.config.get("providers", {}).get(provider_id, {})
        endpoint = provider_config.get("endpoint", "")
        
        # Replace environment variables in endpoint
        if "${" in endpoint:
            for env_var in os.environ:
                placeholder = f"${{{env_var}}}"
                if placeholder in endpoint:
                    endpoint = endpoint.replace(placeholder, os.environ[env_var])
        
        # Get model-specific parameters
        model_config = {}
        for model in provider_config.get("models", []):
            if model.get("id") == model_id:
                model_config = model
                break
        
        try:
            # Call the provider-specific chat function
            if hasattr(provider_module, "chat"):
                return provider_module.chat(
                    endpoint=endpoint,
                    model_id=model_id,
                    messages=messages,
                    persona_description=persona_description,
                    model_config=model_config,
                    files=files
                )
            else:
                return f"Error: Provider {provider_id} does not implement chat function", {}
        except Exception as e:
            return f"Error calling {provider_id} API: {str(e)}", {"error": str(e)}