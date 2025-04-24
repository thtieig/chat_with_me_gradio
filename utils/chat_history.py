import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class ChatHistory:
    def __init__(self, history_dir: str = "chat_histories"):
        """Initialize the chat history manager.
        
        Args:
            history_dir: Directory to store chat histories
        """
        self.history_dir = history_dir
        os.makedirs(self.history_dir, exist_ok=True)
    
    def save_chat(self, chat_id: str, messages: List[Dict[str, Any]], 
                  provider: str, model: str, persona: str) -> str:
        """Save the current chat history to a file.
        
        Args:
            chat_id: Unique identifier for the chat
            messages: List of message dictionaries
            provider: LLM provider name
            model: Model name
            persona: Persona name
            
        Returns:
            Path to the saved file
        """
        if not chat_id:
            chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        chat_data = {
            "chat_id": chat_id,
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "model": model,
            "persona": persona,
            "messages": messages
        }
        
        filename = f"{chat_id}.json"
        filepath = os.path.join(self.history_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def load_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Load a chat history from file.
        
        Args:
            chat_id: Unique identifier for the chat to load
            
        Returns:
            Dictionary with chat data or None if not found
        """
        filepath = os.path.join(self.history_dir, f"{chat_id}.json")
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading chat history: {e}")
            return None
    
    def list_chats(self) -> List[Dict[str, Any]]:
        """List all available chat histories with metadata.
        
        Returns:
            List of chat metadata dictionaries
        """
        chats = []
        
        for filename in os.listdir(self.history_dir):
            if filename.endswith(".json"):
                try:
                    filepath = os.path.join(self.history_dir, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        chats.append({
                            "chat_id": data.get("chat_id"),
                            "timestamp": data.get("timestamp"),
                            "provider": data.get("provider"),
                            "model": data.get("model"),
                            "persona": data.get("persona")
                        })
                except Exception as e:
                    print(f"Error reading chat file {filename}: {e}")
        
        # Sort by timestamp (newest first)
        chats.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return chats
    
    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat history file.
        
        Args:
            chat_id: Unique identifier for the chat to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        filepath = os.path.join(self.history_dir, f"{chat_id}.json")
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except Exception as e:
                print(f"Error deleting chat history: {e}")
                return False
        return False