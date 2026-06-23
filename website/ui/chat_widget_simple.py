import streamlit as st
import streamlit.components.v1 as components
from core.chatbot import ask_chatbot


def render_chat_widget():
    """
    Floating SIS chatbot - fixed to bottom-right of viewport (like normal websites)
    """

    # ---------- Session state ----------
    if "sis_chat_open" not in st.session_state:
        st.session_state.sis_chat_open = False

    if "mini_chat_history" not in st.session_state:
        st.session_state.mini_chat_history = []

    # ---------- Inject fixed-position HTML via iframe ----------
    # This creates a truly fixed element that stays in corner while scrolling
    chat_button_html = """
    <div style="position: fixed; bottom: 24px; right: 24px; z-index: 999999;">
        <button onclick="parent.postMessage({type: 'streamlit:setComponentValue', data: {value: true}}, '*')" 
                style="background: #f97316; color: white; border: none; border-radius: 999px; 
                       padding: 12px 20px; font-size: 14px; font-weight: 600; 
                       box-shadow: 0 8px 20px rgba(0,0,0,0.35); cursor: pointer; 
                       transition: transform 0.2s;">
            💬 SIS chat
        </button>
    </div>
    """
    
    # Render the fixed button (height=0 so it doesn't take space)
    clicked = components.html(chat_button_html, height=0)
    
    if clicked:
        st.session_state.sis_chat_open = True
        st.rerun()

    # ---------- Chat panel as modal overlay ----------
    if st.session_state.sis_chat_open:
        # Full-screen overlay
        st.markdown(
            """
            <style>
            .sis-modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(15, 23, 42, 0.4);
                z-index: 999998;
                display: flex;
                align-items: flex-end;
                justify-content: flex-end;
                padding: 24px;
            }
            
            .sis-chat-panel {
                background: white;
                border-radius: 16px;
                box-shadow: 0 18px 45px rgba(15,23,42,0.55);
                width: 360px;
                max-width: 100%;
                max-height: 600px;
                display: flex;
                flex-direction: column;
                margin-bottom: 80px;
            }
            
            .sis-chat-header {
                padding: 12px 16px;
                background: linear-gradient(135deg, #0f172a, #1d4ed8);
                color: #e5e7eb;
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-radius: 16px 16px 0 0;
            }
            
            .sis-chat-avatar {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: #f97316;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
            }
            
            .sis-chat-body {
                padding: 12px 16px;
                max-height: 400px;
                overflow-y: auto;
                background: #f8fafc;
                flex: 1;
            }
            
            .sis-bubble-user {
                margin-left: auto;
                margin-bottom: 8px;
                max-width: 80%;
                background: #2563eb;
                color: white;
                padding: 8px 12px;
                border-radius: 14px 14px 2px 14px;
                font-size: 13px;
                width: fit-content;
                margin-left: auto;
                display: block;
            }
            
            .sis-bubble-bot {
                margin-right: auto;
                margin-bottom: 8px;
                max-width: 85%;
                background: white;
                color: #111827;
                padding: 8px 12px;
                border-radius: 14px 14px 14px 2px;
                font-size: 13px;
                box-shadow: 0 1px 3px rgba(15,23,42,0.16);
                border: 1px solid #e2e8f0;
                width: fit-content;
            }
            
            .sis-chat-input-area {
                padding: 12px 16px;
                border-top: 1px solid #e2e8f0;
                background: white;
                border-radius: 0 0 16px 16px;
            }
            
            .sis-close-btn {
                cursor: pointer;
                opacity: 0.8;
                font-size: 20px;
            }
            
            .sis-close-btn:hover {
                opacity: 1;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        
        # Modal overlay
        st.markdown('<div class="sis-modal-overlay" onclick="if(event.target === this) { /* close */ }">', unsafe_allow_html=True)
        st.markdown('<div class="sis-chat-panel">', unsafe_allow_html=True)
        
        # Header with close button
        col1, col2 = st.columns([10, 1])
        with col1:
            st.markdown(
                """
                <div class="sis-chat-header">
                  <div style="display: flex; align-items: center; gap: 10px;">
                    <div class="sis-chat-avatar">S</div>
                    <div>
                      <div style="font-weight: 600; font-size: 15px;">SIS Research Chatbot</div>
                      <div style="font-size: 11px; opacity: 0.85;">Ask about satellite imagery and solar radiation</div>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            if st.button("✕", key="close_chat"):
                st.session_state.sis_chat_open = False
                st.rerun()
        
        # Messages
        st.markdown('<div class="sis-chat-body">', unsafe_allow_html=True)
        
        # Quick suggestions
        if not st.session_state.mini_chat_history:
            st.markdown("**Try asking:**")
            suggestions = [
                "SIS project overview",
                "Satellite imagery basics", 
                "Solar radiation concepts",
            ]
            chosen = None
            for i, label in enumerate(suggestions):
                if st.button(label, key=f"sugg_{i}"):
                    chosen = label
        
        # Message bubbles
        for msg in st.session_state.mini_chat_history:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="sis-bubble-user">{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="sis-bubble-bot">{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Input area
        st.markdown('<div class="sis-chat-input-area">', unsafe_allow_html=True)
        col_input, col_send = st.columns([4, 1])
        with col_input:
            user_msg = st.text_input(
                "Message",
                key="chat_input",
                label_visibility="collapsed",
                placeholder="Ask about solar radiation...",
            )
        with col_send:
            send_clicked = st.button("Send", key="send_btn")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # panel
        st.markdown('</div>', unsafe_allow_html=True)  # overlay
        
        # Handle message sending
        message_to_send = None
        if 'chosen' in locals() and chosen:
            message_to_send = chosen
        elif send_clicked and user_msg and user_msg.strip():
            message_to_send = user_msg.strip()
        
        if message_to_send:
            st.session_state.mini_chat_history.append(
                {"role": "user", "content": message_to_send}
            )
            
            try:
                history_before_last = st.session_state.mini_chat_history[:-1]
                answer = ask_chatbot(
                    user_message=message_to_send,
                    history=history_before_last,
                )
                st.session_state.mini_chat_history.append(
                    {"role": "assistant", "content": answer}
                )
            except Exception as e:
                friendly = (
                    "Sorry, the SIS chatbot cannot answer right now. "
                    "This usually happens when the OpenAI API key has no quota left."
                )
                st.session_state.mini_chat_history.append(
                    {"role": "assistant", "content": friendly}
                )
            
            st.rerun()
