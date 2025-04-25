import os
import time
import uuid
import gradio as gr
from typing import Dict, List, Any, Optional, Tuple
import yaml
import dotenv
from pathlib import Path

# Import our utility modules
from utils.llm_manager import LLMManager
from utils.chat_history import ChatHistory
from utils.file_handler import FileHandler

# Load environment variables
dotenv.load_dotenv()

# Initialize our managers
llm_manager = LLMManager()
chat_history = ChatHistory()
file_handler = FileHandler()

# Get UI configuration
ui_config = llm_manager.config.get("ui", {})
title = ui_config.get("title", "AI Chatbot")
title_css = ui_config.get("title_css", ".title-container { text-align: center; font-size: 5rem; }")
welcome_message = ui_config.get("welcome_message", "Welcome to the Multi-Provider AI Chatbot!")

# Get providers, models, and personas
providers = llm_manager.get_providers()
default_provider_id = providers[0]["id"] if providers else None
default_models = llm_manager.get_models(default_provider_id) if default_provider_id else []
default_model_id = default_models[0]["id"] if default_models else None
personas = llm_manager.get_personas()
default_persona_id = personas[0]["id"] if personas else None

# File handling variables
file_handling_config = llm_manager.config.get("file_handling", {})
file_handler = FileHandler(config=file_handling_config)

# Chat History Management
def list_chat_options():
    chats = chat_history.list_chats()
    return [(f"{c['timestamp']} - {c['provider']}/{c['model']} ({c['persona']})", c["chat_id"]) for c in chats]

def load_selected_chat(chat_id: str, chat_id_state: str):
    chat_data = chat_history.load_chat(chat_id)
    if not chat_data:
        return [], "Failed to load chat.", chat_id_state
    history = []
    msgs = chat_data.get("messages", [])
    for i in range(0, len(msgs), 2):
        user_msg = msgs[i]["content"] if i < len(msgs) else ""
        bot_msg = msgs[i + 1]["content"] if i + 1 < len(msgs) else None
        history.append([user_msg, bot_msg])
    return history, f"Loaded chat from {chat_data.get('timestamp')}", chat_id

def delete_selected_chat(chat_id: str):
    success = chat_history.delete_chat(chat_id)
    return gr.update(choices=list_chat_options(), value=None), f"{'Deleted' if success else 'Failed to delete'} chat {chat_id}"

def update_models(provider_id: str, provider_state: str):
    """Update the models dropdown based on selected provider."""
    models = llm_manager.get_models(provider_id)
    model_choices = [(model["name"], model["id"]) for model in models] if models else []
    
    return gr.Dropdown(choices=model_choices, value=model_choices[0][1] if model_choices else None), provider_id

def update_model_selection(model_id: str, model_state: str):
    """Update the current model selection."""
    return model_id

def update_persona_selection(persona_id: str, persona_state: str):
    """Update the current persona selection."""
    return persona_id

def handle_file_upload(files, files_state):
    """Process uploaded files."""
    # Reset the uploaded files list based on what's actually in the UI
    uploaded_files = []
    
    if not files:
        return "No files uploaded.", uploaded_files
        
    file_messages = []
    for file in files:
        file_info = file_handler.process_file(file)
        
        if "error" in file_info:
            filename = file_info.get("filename", 
                      getattr(file, "name", str(file)) if hasattr(file, "name") else str(file))
            file_messages.append(f"Error with {filename}: {file_info['error']}")
        else:
            uploaded_files.append(file_info)
            file_type = "text" if file_info.get("is_text") else "binary"
            file_messages.append(f"Uploaded {file_info['filename']} ({file_type}, {file_info['size']/1024:.1f} KB)")
    
    return "\n".join(file_messages), uploaded_files

def update_file_list(files, files_state):
    """Update the list of uploaded files when a file is removed."""
    # Save the previous list to compare
    previous_files = set(f["filename"] for f in files_state)
    
    # Reset uploaded files
    uploaded_files = []
    
    if not files:
        return "All files have been removed.", uploaded_files
    
    # Process the remaining files
    for file in files:
        file_info = file_handler.process_file(file)
        if "error" not in file_info:
            uploaded_files.append(file_info)
    
    # Find removed files
    current_files = set(f["filename"] for f in uploaded_files)
    removed = previous_files - current_files
    
    if removed:
        return f"Removed: {', '.join(removed)}. {len(uploaded_files)} file(s) remaining.", uploaded_files
    else:
        return f"{len(uploaded_files)} file(s) currently attached.", uploaded_files

def clear_files(files_state):
    """Clear uploaded files."""
    return "All uploaded files cleared.", None, []

def user(message, history):
    """Add user message to history."""
    return "", history + [[message, None]]

def bot(history, provider_state, model_state, persona_state, files_state, chat_id_state):
    """Generate bot response."""
    # Format messages for the LLM
    messages = []
    for human_msg, ai_msg in history:
        messages.append({"role": "user", "content": human_msg})
        if ai_msg is not None:
            messages.append({"role": "assistant", "content": ai_msg})
    
    # Generate response
    response_text, metadata = llm_manager.chat_completion(
        provider_id=provider_state,
        model_id=model_state,
        persona_id=persona_state,
        messages=messages,
        files=files_state
    )
    
    # Update history
    history[-1][1] = response_text
    
    # Save chat history
    current_chat_id = chat_id_state
    if not current_chat_id:
        current_chat_id = str(uuid.uuid4())
    
    provider_name = next((p["name"] for p in providers if p["id"] == provider_state), provider_state)
    model_name = next((m["name"] for m in llm_manager.get_models(provider_state) if m["id"] == model_state), model_state)
    persona_name = next((p["name"] for p in personas if p["id"] == persona_state), persona_state)
    
    chat_history.save_chat(
        chat_id=current_chat_id,
        messages=messages + [{"role": "assistant", "content": response_text}],
        provider=provider_name,
        model=model_name,
        persona=persona_name
    )
    
    return history, current_chat_id

def create_chatbot_ui():
    with gr.Blocks(css=title_css) as demo:
        # Create session state variables
        chat_id_state = gr.State(value=None)
        provider_state = gr.State(value=default_provider_id)
        model_state = gr.State(value=default_model_id)
        persona_state = gr.State(value=default_persona_id)
        files_state = gr.State(value=[])
        
        gr.HTML(f"<div class='title-container'><span>{title}</span></div>")
        
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Group():
                    provider_dropdown = gr.Dropdown(
                        choices=[(p["name"], p["id"]) for p in providers],
                        value=default_provider_id,
                        label="Provider"
                    )
                    model_dropdown = gr.Dropdown(
                        choices=[(m["name"], m["id"]) for m in default_models] if default_models else [],
                        value=default_model_id,
                        label="Model"
                    )
                    persona_dropdown = gr.Dropdown(
                        choices=[(p["name"], p["id"]) for p in personas],
                        value=default_persona_id,
                        label="Persona"
                    )

                with gr.Group():
                    gr.Markdown("### Chat History")
                    chat_selector = gr.Dropdown(label="Select a chat", choices=list_chat_options())
                    load_chat_btn = gr.Button("Load Selected Chat")
                    delete_chat_btn = gr.Button("Delete Selected Chat")
                    chat_status = gr.Textbox(label="Chat Status", interactive=False)

                with gr.Group():
                    gr.Markdown("### File Attachments")
                    file_upload = gr.Files(label="Upload Files", file_count="multiple")
                    file_status = gr.Textbox(label="File Status", lines=5, interactive=False)
                    clear_files_btn = gr.Button("Clear Files")

            with gr.Column(scale=2):
                chatbot = gr.Chatbot([], elem_id="chatbot", height=600, avatar_images=(None, "🤖"))
                msg = gr.Textbox(placeholder="Type your message here...", label="Message", lines=2)
                with gr.Row():
                    submit_btn = gr.Button("Send")
                    clear_btn = gr.Button("Clear Chat")

        # Setup event handlers with state management
        provider_dropdown.change(
            fn=update_models, 
            inputs=[provider_dropdown, provider_state], 
            outputs=[model_dropdown, provider_state]
        )
        
        model_dropdown.change(
            fn=update_model_selection, 
            inputs=[model_dropdown, model_state], 
            outputs=model_state
        )
        
        persona_dropdown.change(
            fn=update_persona_selection, 
            inputs=[persona_dropdown, persona_state], 
            outputs=persona_state
        )
        
        # File handling events
        file_upload.upload(
            fn=handle_file_upload, 
            inputs=[file_upload, files_state], 
            outputs=[file_status, files_state]
        )
        
        file_upload.change(
            fn=update_file_list, 
            inputs=[file_upload, files_state], 
            outputs=[file_status, files_state]
        )
        
        clear_files_btn.click(
            fn=clear_files, 
            inputs=[files_state], 
            outputs=[file_status, file_upload, files_state]
        )
        
        # Chat events
        msg.submit(
            fn=user, 
            inputs=[msg, chatbot], 
            outputs=[msg, chatbot], 
            queue=False
        ).then(
            fn=bot, 
            inputs=[chatbot, provider_state, model_state, persona_state, files_state, chat_id_state], 
            outputs=[chatbot, chat_id_state]
        )
        
        submit_btn.click(
            fn=user, 
            inputs=[msg, chatbot], 
            outputs=[msg, chatbot], 
            queue=False
        ).then(
            fn=bot, 
            inputs=[chatbot, provider_state, model_state, persona_state, files_state, chat_id_state], 
            outputs=[chatbot, chat_id_state]
        )
        
        clear_btn.click(lambda: None, None, chatbot, queue=False)

        # Chat history actions
        load_chat_btn.click(
            fn=load_selected_chat, 
            inputs=[chat_selector, chat_id_state], 
            outputs=[chatbot, chat_status, chat_id_state]
        ).then(
            fn=lambda: gr.update(choices=list_chat_options()), 
            inputs=None, 
            outputs=chat_selector
        )
        
        delete_chat_btn.click(
            fn=delete_selected_chat, 
            inputs=chat_selector, 
            outputs=[chat_selector, chat_status]
        ).then(
            fn=lambda: gr.update(choices=list_chat_options(), value=None), 
            inputs=None, 
            outputs=chat_selector
        )

        gr.Markdown(f"### {welcome_message}")
    
    return demo

if __name__ == "__main__":
    demo = create_chatbot_ui()
    demo.launch()