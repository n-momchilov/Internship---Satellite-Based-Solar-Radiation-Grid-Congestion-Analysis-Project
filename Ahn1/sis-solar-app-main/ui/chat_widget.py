import streamlit as st
from core.chatbot import ask_chatbot


def render_chat_widget():
    """
    Floating SIS chatbot:
    - Round launcher at bottom-right of the screen
    - Floating panel above it that stays fixed while scrolling
    - Bubble-style messages + quick topic buttons
    """

    # ---------- Session state ----------
    if "sis_chat_open" not in st.session_state:
        st.session_state.sis_chat_open = False

    if "mini_chat_history" not in st.session_state:
        st.session_state.mini_chat_history = []  # [{"role": "user"|"assistant", "content": "..."}]

    # ---------- CSS (purely visual) ----------
    st.markdown(
        """
        <style>
        /* ============================
           Floating launcher button
           ============================ */
        .sis-chat-launcher-wrapper {
            position: fixed !important;
            bottom: 1.6rem !important;
            right: 1.6rem !important;
            z-index: 9999 !important;
        }

        .sis-chat-launcher-wrapper .stButton>button {
            border-radius: 999px !important;
            padding: 0.65rem 1.2rem !important;
            font-size: 0.9rem !important;
            font-weight: 600 !important;
            box-shadow: 0 10px 24px rgba(15,23,42,0.35) !important;
            background: #f97316 !important;  /* orange */
            color: #ffffff !important;
            border: none !important;
        }

        /* ============================
           Floating chat panel
           ============================ */
        .sis-chat-panel-wrapper {
            position: fixed !important;
            bottom: 5.4rem !important;         /* sits above launcher */
            right: 1.6rem !important;
            z-index: 9998 !important;
            width: 360px;
            max-height: 560px;
            display: none;
        }

        .sis-chat-panel-wrapper.open {
            display: block !important;
        }

        .sis-chat-panel {
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 18px 45px rgba(15,23,42,0.55);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            font-size: 0.9rem;
            border: 1px solid rgba(148,163,184,0.4);
        }

        /* Header (Thermo-Fisher-style) */
        .sis-chat-header {
            padding: 0.75rem 0.95rem;
            background: linear-gradient(135deg, #0f172a, #1d4ed8);
            color: #e5e7eb;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .sis-chat-header-left {
            display: flex;
            align-items: center;
            gap: 0.55rem;
        }

        .sis-chat-avatar {
            width: 30px;
            height: 30px;
            border-radius: 999px;
            background: #f97316;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
            font-weight: 700;
        }

        .sis-chat-header-title {
            font-weight: 600;
            font-size: 0.9rem;
        }

        .sis-chat-header-sub {
            font-size: 0.72rem;
            opacity: 0.85;
        }

        .sis-chat-header-close {
            font-size: 0.8rem;
            opacity: 0.85;
        }

        /* Body background */
        .sis-chat-body {
            padding: 0.6rem 0.85rem 0.5rem 0.85rem;
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
            background: #f8fafc;
        }

        /* Suggestions row */
        .sis-chat-suggestions-label {
            font-size: 0.75rem;
            font-weight: 500;
            color: #0f172a;
            margin-bottom: 0.2rem;
        }

        .sis-chat-suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 0.25rem;
            margin-bottom: 0.25rem;
        }

        .sis-chat-suggestions .stButton>button {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border-radius: 999px !important;
            border: 1px solid rgba(148,163,184,0.8) !important;
            font-size: 0.72rem !important;
            padding: 0.12rem 0.7rem !important;
            box-shadow: 0 1px 4px rgba(15,23,42,0.12) !important;
            white-space: nowrap;
        }

        /* Messages area with subtle scroll */


        .sis-bubble-row {
            display: flex;
            margin-bottom: 0.35rem;
        }

        .sis-bubble-user {
            margin-left: auto;
            max-width: 80%;
            background: #2563eb;
            color: #eff6ff;
            padding: 0.35rem 0.65rem;
            border-radius: 14px 14px 2px 14px;
            font-size: 0.82rem;
        }

        .sis-bubble-bot {
            margin-right: auto;
            max-width: 85%;
            background: #ffffff;
            color: #111827;
            padding: 0.35rem 0.65rem;
            border-radius: 14px 14px 14px 2px;
            font-size: 0.82rem;
            box-shadow: 0 1px 3px rgba(15,23,42,0.16);
            border: 1px solid rgba(226,232,240,0.8);
        }

        .sis-bubble-label {
            font-size: 0.7rem;
            opacity: 0.75;
            margin-bottom: 0.12rem;
        }

        /* Input area */
        .sis-chat-input-area {
            padding: 0.45rem 0.85rem 0.6rem 0.85rem;
            border-top: 1px solid rgba(203,213,225,0.9);
            background: #e5e7eb;
        }

        .sis-chat-input-area .stTextInput>div>div>input {
            font-size: 0.83rem !important;
            padding-top: 0.25rem !important;
            padding-bottom: 0.25rem !important;
            border-radius: 999px !important;
        }

        .sis-chat-send-btn .stButton>button {
            border-radius: 999px !important;
            padding: 0.25rem 0.9rem !important;
            font-size: 0.8rem !important;
            font-weight: 500 !important;
            background: #0f172a !important;
            color: #f9fafb !important;
            border: none !important;
        }
        
        /* Position the actual Streamlit toggle button */
        div[data-testid="column"]:has(button[key="sis_chat_button"]) {
            position: fixed !important;
            bottom: 22px !important;
            right: 22px !important;
            z-index: 999999 !important;
            width: auto !important;
        }
        
        button[key="sis_chat_button"] {
            background: #f97316 !important;
            color: white !important;
            border: none !important;
            border-radius: 999px !important;
            padding: 12px 20px !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            box-shadow: 0 8px 20px rgba(0,0,0,0.35) !important;
            transition: transform 0.2s !important;
        }
        
        button[key="sis_chat_button"]:hover {
            transform: scale(1.05) !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.45) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ---------- Chat toggle button ----------
    if st.button("💬 SIS chat", key="sis_chat_button"):
        st.session_state.sis_chat_open = not st.session_state.sis_chat_open

    # If closed, stop here (launcher still visible)
    if not st.session_state.sis_chat_open:
        return

    # Show the chat panel when open
    st.markdown('<div class="sis-chat-panel-wrapper open">', unsafe_allow_html=True)
    st.markdown('<div class="sis-chat-panel">', unsafe_allow_html=True)

    # Header
    st.markdown(
        """
        <div class="sis-chat-header">
          <div class="sis-chat-header-left">
            <div class="sis-chat-avatar">S</div>
            <div>
              <div class="sis-chat-header-title">SIS Research Chatbot</div>
              <div class="sis-chat-header-sub">
                Ask about the SIS project, satellite imagery, and solar radiation.
              </div>
            </div>
          </div>
          <div class="sis-chat-header-close">● ● ●</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Body
    st.markdown('<div class="sis-chat-body">', unsafe_allow_html=True)

    # Suggestions
    st.markdown(
        '<div class="sis-chat-suggestions-label">Try a topic:</div>',
        unsafe_allow_html=True,
    )
    suggestions = [
        "SIS project overview",
        "Satellite imagery basics",
        "Solar radiation concepts",
        "Research group mission",
        "Common challenges",
    ]
    chosen_suggestion = None
    st.markdown('<div class="sis-chat-suggestions">', unsafe_allow_html=True)
    sugg_cols = st.columns(len(suggestions))
    for i, label in enumerate(suggestions):
        if sugg_cols[i].button(label, key=f"sis_suggestion_{i}"):
            chosen_suggestion = label
    st.markdown("</div>", unsafe_allow_html=True)

    # Messages (bubbles)
    for msg in st.session_state.mini_chat_history:
        if msg["role"] == "user":
            st.markdown(
                f"""
                <div class="sis-bubble-row" style="justify-content: flex-end;">
                    <div class="sis-bubble-user">
                        <div class="sis-bubble-label">You</div>
                        <div>{msg["content"]}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="sis-bubble-row" style="justify-content: flex-start;">
                    <div class="sis-bubble-bot">
                        <div class="sis-bubble-label">SIS bot</div>
                        <div>{msg["content"]}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)  # messages
    st.markdown("</div>", unsafe_allow_html=True)  # body

    # ----- Input area -----
    st.markdown('<div class="sis-chat-input-area">', unsafe_allow_html=True)
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        user_msg = st.text_input(
            "Type your question here",
            key="mini_chat_input",
            label_visibility="collapsed",
            placeholder="E.g. Solar radiation concepts",
        )
    with col_btn:
        st.markdown('<div class="sis-chat-send-btn">', unsafe_allow_html=True)
        send_clicked = st.button("Send", key="mini_chat_send")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)  # input area

    # Close panel wrappers
    st.markdown("</div>", unsafe_allow_html=True)  # .sis-chat-panel
    st.markdown("</div>", unsafe_allow_html=True)  # .sis-chat-panel-wrapper

    # ---------- Decide what to send ----------
    message_to_send = None
    if chosen_suggestion is not None:
        message_to_send = chosen_suggestion
    elif send_clicked and user_msg.strip():
        message_to_send = user_msg.strip()

    # ---------- Handle send ----------
    if message_to_send is not None:
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
                "This usually happens when the OpenAI API key has no quota "
                "left or there is a temporary connection problem."
            )
            if "insufficient_quota" in str(e) or "RateLimitError" in type(e).__name__:
                friendly = (
                    "The SIS chatbot is temporarily unavailable because the "
                    "OpenAI API key has **no remaining quota**. "
                    "Please update the API key or add credits, then try again."
                )

            st.session_state.mini_chat_history.append(
                {"role": "assistant", "content": friendly}
            )
            st.error(str(e))
        else:
            st.session_state.mini_chat_history.append(
                {"role": "assistant", "content": answer}
            )

        st.rerun()
