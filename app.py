import os
import uuid
import gradio as gr
from typing import List, Dict, Any, Optional
import dotenv

# your modules
from utils.llm_manager import LLMManager
from utils.chat_history import ChatHistory
from utils.file_handler import FileHandler

# load env and init managers
dotenv.load_dotenv()
llm_manager  = LLMManager()
chat_history = ChatHistory()
file_handler = FileHandler(config=llm_manager.config.get("file_handling", {}))

# ui config
ui = llm_manager.config.get("ui", {})
title           = ui.get("title", "AI Chatbot")
title_css       = ui.get("title_css", ".title-container { text-align: center; font-size: 5rem; }")
welcome_message = ui.get("welcome_message", "Welcome to the Multi-Provider AI Chatbot!")
chatbot_height = ui.get("chatbot_height", 600)
bot_avatar_img = ui.get("bot_avatar_img", "None")
human_avatar_img = ui.get("human_avatar_img", "None")

# initial pick-lists
providers       = llm_manager.get_providers()
default_pid     = providers[0]["id"] if providers else None
default_models  = llm_manager.get_models(default_pid) if default_pid else []
default_mid     = default_models[0]["id"] if default_models else None
personas        = llm_manager.get_personas()
default_persona = personas[0]["id"] if personas else None

# helper for chat-history dropdown
def list_chat_options():
    return [
        (f"{c['timestamp']} - {c['provider']}/{c['model']} ({c['persona']})", c["chat_id"])
        for c in chat_history.list_chats()
    ]

# load/delete chat
def load_selected_chat(chat_id, _state):
    data = chat_history.load_chat(chat_id) or {}
    msgs = data.get("messages", [])
    status = f"Loaded chat from {data.get('timestamp', 'unknown')}"
    return msgs, status, chat_id

def delete_selected_chat(chat_id):
    ok = chat_history.delete_chat(chat_id)
    label = "Deleted" if ok else "Failed to delete"
    return gr.update(choices=list_chat_options(), value=None), f"{label} chat {chat_id}"

# dropdown updaters
def update_models(pid, _state):
    models = llm_manager.get_models(pid)
    choices = [(m["name"], m["id"]) for m in models]
    return gr.Dropdown(choices=choices, value=(choices[0][1] if choices else None)), pid

def update_model_selection(mid, _state):   return mid
def update_persona_selection(per, _state): return per

# file handlers
def handle_file_upload(files, files_state):
    if not files:
        return "No files uploaded.", []
    infos, msgs = [], []
    for f in files:
        info = file_handler.process_file(f)
        if info.get("error"):
            msgs.append(f"Error: {info['error']} on {info.get('filename', getattr(f, 'name', str(f)))}")
        else:
            infos.append(info)
            kind = "text" if info.get("is_text") else "binary"
            size_kb = info["size"] / 1024
            msgs.append(f"Uploaded {info['filename']} ({kind}, {size_kb:.1f} KB)")
    return "\n".join(msgs), infos

def clear_files(_):
    return "All files cleared.", []

# user-bot glue
def user(msg, history):
    return "", history + [{"role": "user", "content": msg}]

def bot(
    history: List[Dict[str,Any]],
    pid, mid, per,
    files_state: List[Dict[str,Any]],
    chat_id_state: Optional[str]
):
    # if there are files, stick a system message at the top
    if files_state:
        file_block = file_handler.format_files_for_llm(files_state)
        history.insert(0, {"role":"system", "content": file_block})

    # ask LLM
    resp_text, _meta = llm_manager.chat_completion(
        provider_id=pid,
        model_id=   mid,
        persona_id= per,
        messages=   history,
        files=      files_state
    )
    history.append({"role":"assistant","content":resp_text})

    # save chat
    cid = chat_id_state or str(uuid.uuid4())
    pname = next((p["name"] for p in providers if p["id"]==pid), pid)
    mname = next((m["name"] for m in llm_manager.get_models(pid) if m["id"]==mid), mid)
    pername= next((p["name"] for p in personas     if p["id"]==per), per)

    chat_history.save_chat(
        chat_id=  cid,
        messages= history,
        provider= pname,
        model=    mname,
        persona=  pername
    )
    return history, cid

# build the UI
def create_chatbot_ui():
    with gr.Blocks(css=title_css) as demo:
        # states
        chat_id_state  = gr.State(None)
        provider_state = gr.State(default_pid)
        model_state    = gr.State(default_mid)
        persona_state  = gr.State(default_persona)
        files_state    = gr.State([])

        gr.HTML(f"<div class='title-container'><span>{title}</span></div>")

        with gr.Row():
            with gr.Column(scale=1):
                # pickers
                with gr.Group():
                    provider_dropdown = gr.Dropdown(
                        choices=[(p["name"],p["id"]) for p in providers],
                        value=default_pid, label="Provider"
                    )
                    model_dropdown = gr.Dropdown(
                        choices=[(m["name"],m["id"]) for m in default_models],
                        value=default_mid, label="Model"
                    )
                    persona_dropdown = gr.Dropdown(
                        choices=[(p["name"],p["id"]) for p in personas],
                        value=default_persona, label="Persona"
                    )

                # history
                with gr.Group():
                    gr.Markdown("### Chat History")
                    chat_selector = gr.Dropdown(label="Select a chat", choices=list_chat_options())
                    load_chat_btn = gr.Button("Load Selected Chat")
                    delete_chat_btn = gr.Button("Delete Selected Chat")
                    chat_status   = gr.Textbox(label="Status", interactive=False)

                # files
                with gr.Group():
                    gr.Markdown("### File Attachments")
                    upload_btn = gr.UploadButton("Upload Files", file_count="multiple")
                    file_status= gr.Textbox(label="File Status", lines=5, interactive=False)
                    clear_btn  = gr.Button("Clear Files")

                # wire file events
                upload_btn.upload(fn=handle_file_upload, inputs=[upload_btn, files_state],
                                                          outputs=[file_status, files_state])
                clear_btn.click(fn=clear_files, inputs=[files_state],
                                              outputs=[file_status, files_state])

            # chat panel
            with gr.Column(scale=2):
                chatbot = gr.Chatbot([],
                                     elem_id="chatbot", 
                                     height=chatbot_height, 
                                     avatar_images=(human_avatar_img, bot_avatar_img), 
                                     type="messages")
                msg = gr.Textbox(placeholder="Type your message here...", label="Message", lines=2)
                with gr.Row():
                    send_btn = gr.Button("Send")
                    wipe_btn = gr.Button("Clear Chat")

        # wire up dropdowns
        provider_dropdown.change(fn=update_models, inputs=[provider_dropdown, provider_state],
                                                      outputs=[model_dropdown, provider_state])
        model_dropdown.change(fn=update_model_selection, inputs=[model_dropdown, model_state],
                                                             outputs=model_state)
        persona_dropdown.change(fn=update_persona_selection, inputs=[persona_dropdown, persona_state],
                                                               outputs=persona_state)

        # wire chat
        msg.submit(fn=user, inputs=[msg, chatbot], outputs=[msg, chatbot], queue=False)\
           .then(fn=bot, inputs=[chatbot, provider_state, model_state, persona_state, files_state, chat_id_state],
                       outputs=[chatbot, chat_id_state])
        send_btn.click(fn=user, inputs=[msg, chatbot], outputs=[msg, chatbot], queue=False)\
                .then(fn=bot, inputs=[chatbot, provider_state, model_state, persona_state, files_state, chat_id_state],
                            outputs=[chatbot, chat_id_state])
        wipe_btn.click(lambda: None, None, chatbot, queue=False)

        # wire history buttons
        load_chat_btn.click(fn=load_selected_chat, inputs=[chat_selector, chat_id_state],
                            outputs=[chatbot, chat_status, chat_id_state])\
                       .then(fn=lambda: gr.update(choices=list_chat_options()), inputs=None, outputs=chat_selector)
        delete_chat_btn.click(fn=delete_selected_chat, inputs=[chat_selector],
                              outputs=[chat_selector, chat_status])\
                         .then(fn=lambda: gr.update(choices=list_chat_options(), value=None),
                               inputs=None, outputs=chat_selector)

        gr.Markdown(f"### {welcome_message}")

    return demo

if __name__=="__main__":
    demo = create_chatbot_ui()
    demo.launch(favicon_path='config/img/favicon.ico')
