import streamlit as st
from core.chatbot import ask_chatbot

def render_chat_widget():
    """
    Floating SIS chatbot:
    - Round launcher at bottom-right of the screen
    - Floating panel above it that stays fixed while scrolling
    - Uses your existing ask_chatbot() function
    """

    # ---------- Session state ----------
    if "sis_chat_open" not in st.session_state:
        st.session_state.sis_chat_open = False

    if "mini_chat_history" not in st.session_state:
        st.session_state.mini_chat_history = []

    if "mini_chat_history" not in st.session_state:
        st.session_state.mini_chat_history = []

    # ---------- CSS for everything ----------
    st.markdown(
        """
        <style>
        /* Hide default Streamlit elements in chat */
        div[data-testid="stVerticalBlock"] > div:has(.sis-chat-marker) {
            position: fixed !important;
            bottom: 90px !important;
            right: 22px !important;
            z-index: 999998 !important;
            width: 360px !important;
            max-width: calc(100vw - 44px) !important;
        }
        
        .sis-chat-header {
            padding: 12px 16px;
            background: linear-gradient(135deg, #0f172a, #1d4ed8);
            color: #e5e7eb;
            display: flex;
            align-items: center;
            gap: 10px;
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
        
        .sis-chat-title {
            font-weight: 600;
            font-size: 15px;
        }
        
        .sis-chat-subtitle {
            font-size: 11px;
            opacity: 0.85;
        }
        
        .sis-chat-body {
            padding: 12px 16px;
            max-height: 350px;
            overflow-y: auto;
            background: #f8fafc;
        }
        
        .sis-message {
            margin-bottom: 8px;
            padding: 8px 12px;
            border-radius: 12px;
            font-size: 13px;
        }
        
        .sis-message.user {
            background: #2563eb;
            color: white;
            margin-left: 20%;
        }
        
        .sis-message.assistant {
            background: white;
            color: #111827;
            margin-right: 10%;
            border: 1px solid #e2e8f0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ---------- Toggle button ----------
    if st.button("💬 SIS chat", key="sis_chat_toggle"):
        st.session_state.sis_chat_open = not st.session_state.sis_chat_open
        st.rerun()
    st.markdown(
        """
        <style>
        /* Style the actual button - small and round */
        button[kind="secondary"] {
            background: #f97316 !important;
            color: white !important;
            border: none !important;
            border-radius: 999px !important;
            padding: 12px 20px !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            cursor: pointer !important;
            box-shadow: 0 8px 20px rgba(0,0,0,0.35) !important;
            transition: transform 0.2s, box-shadow 0.2s !important;
            width: auto !important;
            min-width: auto !important;
        }
        
        button[kind="secondary"]:hover {
            transform: scale(1.05) !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.45) !important;
        }
        
        /* Chat panel styling */
        .sis-chat-panel-fixed {
            position: fixed !important;
            bottom: 80px !important;
            right: 22px !important;
            z-index: 999998 !important;
            width: 360px !important;
            max-width: calc(100vw - 44px) !important;
            background: white;
            border-radius: 16px;
            box-shadow: 0 18px 45px rgba(15,23,42,0.55);
            overflow: hidden;
        }
        
        .sis-chat-header {
            padding: 12px 16px;
            background: linear-gradient(135deg, #0f172a, #1d4ed8);
            color: #e5e7eb;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .sis-chat-header-left {
            display: flex;
            align-items: center;
            gap: 10px;
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
        
        .sis-chat-title {
            font-weight: 600;
            font-size: 15px;
        }
        
        .sis-chat-subtitle {
            font-size: 11px;
            opacity: 0.85;
        }
        
        .sis-chat-body {
            padding: 12px 16px;
            max-height: 400px;
            overflow-y: auto;
            background: #f8fafc;
        }
        
        .sis-suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 12px;
        }
        
        .sis-suggestions button {
            background: white !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 999px !important;
            padding: 6px 12px !important;
            font-size: 12px !important;
            cursor: pointer !important;
        }
        
        .sis-messages {
            margin-top: 12px;
        }
        
        .sis-message {
            margin-bottom: 8px;
            padding: 8px 12px;
            border-radius: 12px;
            font-size: 13px;
        }
        
        .sis-message.user {
            background: #2563eb;
            color: white;
            margin-left: auto;
            max-width: 80%;
            text-align: right;
        }
        
        .sis-message.assistant {
            background: white;
            color: #111827;
            margin-right: auto;
            max-width: 85%;
            border: 1px solid #e2e8f0;
        }
        
        .sis-input-area {
            padding: 12px 16px;
            border-top: 1px solid #cbd5e1;
            background: #e5e7eb;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Check if user sent a message via query params
    query_params = st.query_params
    if "sis_msg" in query_params:
        message_to_send = query_params.get("sis_msg", "").strip()
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
            except Exception as e:
                friendly = (
                    "Sorry, the SIS chatbot cannot answer right now. "
                    "This usually happens when the OpenAI API key has no quota left."
                )
                st.session_state.mini_chat_history.append(
                    {"role": "assistant", "content": friendly}
                )
            else:
                st.session_state.mini_chat_history.append(
                    {"role": "assistant", "content": answer}
                )
            
            st.query_params.clear()
            st.rerun()
    
    # If chat is open, render it as pure HTML overlay
    if st.session_state.sis_chat_open:
        # Build messages HTML
        messages_html = ""
        for msg in st.session_state.mini_chat_history:
            role_class = "user" if msg["role"] == "user" else "assistant"
            # Escape HTML but keep newlines as <br>
            content = msg["content"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            messages_html += f'<div class="sis-message {role_class}">{content}</div>'
        
        if not messages_html:
            messages_html = '<div class="sis-message assistant">Hi! Ask me anything about solar radiation and satellite imagery.</div>'
        
        # Complete chat panel HTML - use components.html to render properly
        components.html(
            f"""
            <div class="sis-chat-panel-fixed">
                <div class="sis-chat-header">
                  <div class="sis-chat-header-left">
                    <div class="sis-chat-avatar">S</div>
                    <div>
                      <div class="sis-chat-title">SIS Research Chatbot</div>
                      <div class="sis-chat-subtitle">Ask about satellite imagery and solar radiation</div>
                    </div>
                  </div>
                </div>
                <div class="sis-chat-body">
                  <div class="sis-messages">
                    {messages_html}
                  </div>
                </div>
                <div class="sis-input-area">
                  <form id="sis-chat-form" method="get" onsubmit="return false;">
                    <input type="text" name="sis_msg" id="sis-chat-input" 
                           placeholder="Ask about solar radiation..." 
                           style="flex:1; padding:8px 12px; border:1px solid #cbd5e1; border-radius:8px; font-size:13px;" />
                    <button type="button" id="sis-send-btn" style="padding:8px 16px; background:#2563eb; color:white; border:none; border-radius:8px; font-size:13px; cursor:pointer; font-weight:600;">
                      Send
                    </button>
                  </form>
                </div>
            </div>
            
            <style>
            .sis-chat-panel-fixed {{
                position: fixed !important;
                bottom: 80px !important;
                right: 22px !important;
                z-index: 999998 !important;
                width: 360px !important;
                max-width: calc(100vw - 44px) !important;
                background: white;
                border-radius: 16px;
                box-shadow: 0 18px 45px rgba(15,23,42,0.55);
                overflow: hidden;
            }}
            
            .sis-chat-header {{
                padding: 12px 16px;
                background: linear-gradient(135deg, #0f172a, #1d4ed8);
                color: #e5e7eb;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}
            
            .sis-chat-header-left {{
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .sis-chat-avatar {{
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: #f97316;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
            }}
            
            .sis-chat-title {{
                font-weight: 600;
                font-size: 15px;
            }}
            
            .sis-chat-subtitle {{
                font-size: 11px;
                opacity: 0.85;
            }}
            
            .sis-chat-body {{
                padding: 12px 16px;
                max-height: 400px;
                overflow-y: auto;
                background: #f8fafc;
            }}
            
            .sis-messages {{
                display: flex;
                flex-direction: column;
                gap: 8px;
            }}
            
            .sis-message {{
                padding: 8px 12px;
                border-radius: 12px;
                font-size: 13px;
                max-width: 85%;
            }}
            
            .sis-message.user {{
                background: #2563eb;
                color: white;
                margin-left: auto;
                text-align: right;
            }}
            
            .sis-message.assistant {{
                background: white;
                color: #111827;
                margin-right: auto;
                border: 1px solid #e2e8f0;
            }}
            
            .sis-input-area {{
                padding: 12px 16px;
                border-top: 1px solid #cbd5e1;
                background: white;
            }}
            
            #sis-chat-form {{
                display: flex;
                gap: 8px;
                align-items: center;
            }}
            </style>
            
            <script>
            (function() {{
                var parentDoc = window.parent.document;
                
                function setupSendHandler() {{
                    var sendBtn = document.getElementById('sis-send-btn');
                    var input = document.getElementById('sis-chat-input');
                    
                    if (sendBtn && input) {{
                        sendBtn.onclick = function() {{
                            var msg = input.value.trim();
                            if (msg) {{
                                console.log('Sending message:', msg);
                                var currentUrl = new URL(window.parent.location.href);
                                currentUrl.searchParams.set('sis_msg', msg);
                                window.parent.location.href = currentUrl.toString();
                            }}
                        }};
                        
                        input.onkeypress = function(e) {{
                            if (e.key === 'Enter') {{
                                e.preventDefault();
                                sendBtn.click();
                            }}
                        }};
                        
                        console.log('Chat input handlers attached');
                    }}
                }}
                
                setTimeout(setupSendHandler, 100);
            }})();
            </script>
            """,
            height=500,
        )
