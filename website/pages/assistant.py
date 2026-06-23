import streamlit as st
from core.chatbot import ask_chatbot


def _init_state():
    if "assistant_chat_history" not in st.session_state:
        # Each message: {"role": "user" | "assistant", "content": "..."}
        st.session_state.assistant_chat_history = [
            {
                "role": "assistant",
                "content": (
                    "Hi, I’m the SIS Research Chatbot. 👋\n\n"
                    "You can ask me about the SIS project, satellite imagery, "
                    "solar radiation concepts, scenario thinking, explainable AI, "
                    "or basic grid congestion awareness. I’ll answer based on the "
                    "current SIS research context."
                ),
            }
        ]
    # You can keep this if you ever go back to query-param based suggestions,
    # but it's no longer used in this version:
    if "last_assistant_suggestion" not in st.session_state:
        st.session_state.last_assistant_suggestion = None


def render():
    _init_state()

    # ====== PAGE SHELL + HERO ======
    st.markdown(
        """
        <div class="sis-chat-page">
          <header class="sis-chat-hero">
            <div class="sis-chat-hero-icon">🤖</div>
            <div>
              <h1 class="sis-chat-title">SIS Research Chatbot</h1>
              <p class="sis-chat-subtitle">
                Ask questions about the SIS project, satellite imagery, solar radiation,
                and basic grid congestion awareness.
                The chatbot answers using the SIS research context only.
              </p>
            </div>
          </header>
        """,
        unsafe_allow_html=True,
    )

    # ====== MOBILE / PERFORMANCE DISCLAIMER ======
    st.markdown(
        """
        <div class="sis-warning"
             style="
                margin: 18px 0 10px 0;
                padding: 12px 16px;
                background: rgba(245, 158, 11, 0.15);
                border-left: 4px solid #f59e0b;
                border-radius: 8px;
                font-size: 0.95rem;
                color: #fcd34d;
                line-height: 1.45;
                box-shadow: 0 6px 20px rgba(0,0,0,0.25);
             ">
            ⚠️ <strong>Mobile experience notice</strong><br>
            The chatbot is still under development. On some mobile devices responses can be slow
            or may not always appear. For the most reliable experience, please try using a laptop
            or desktop browser.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ====== CHAT CARD ======
    st.markdown('<div class="sis-chat-card">', unsafe_allow_html=True)

    history = st.session_state.assistant_chat_history

    # --- First bot message (greeting) ---
    first_msg = history[0]
    st.markdown(
        f"""
        <div class="sis-chat-row sis-chat-row-bot">
          <div class="sis-bubble sis-bubble-bot">
            <div class="sis-bubble-label">SIS bot</div>
            <div class="sis-bubble-text">{first_msg["content"]}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Suggestions directly under greeting (Streamlit buttons again) ---
    suggestions = [
        "SIS project overview",
        "Satellite imagery basics",
        "Solar radiation concepts",
        "Explainable AI in SIS",
        "Grid congestion basics",
        "Common challenges",
        "Research group mission",
    ]

    st.markdown(
        """
        <div class="sis-chat-suggestion-area">
          <span>Some suggestions to get you started, or you can type your own question in the input field:</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sugg_cols = st.columns(3)
    chosen_suggestion = None
    for i, label in enumerate(suggestions):
        with sugg_cols[i % 3]:
            if st.button(label, key=f"inside_sugg_{i}"):
                chosen_suggestion = label

    # --- Rest of the conversation (skip first message already rendered) ---
    for msg in history[1:]:
        if msg["role"] == "user":
            st.markdown(
                f"""
                <div class="sis-chat-row sis-chat-row-user">
                  <div class="sis-bubble sis-bubble-user">
                    <div class="sis-bubble-label">You</div>
                    <div class="sis-bubble-text">{msg["content"]}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="sis-chat-row sis-chat-row-bot">
                  <div class="sis-bubble sis-bubble-bot">
                    <div class="sis-bubble-label">SIS bot</div>
                    <div class="sis-bubble-text">{msg["content"]}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # close messages wrapper
    st.markdown("</div>", unsafe_allow_html=True)

    # ====== INPUT AREA ======
    st.markdown('<div class="sis-chat-input">', unsafe_allow_html=True)
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_text = st.text_input(
            "Ask the SIS chatbot something...",
            key="assistant_input",
            label_visibility="collapsed",
            placeholder="Ask about SIS, satellite imagery, radiation, scenarios, or grid congestion…",
        )
    with col_btn:
        send_clicked = st.button("Send", key="assistant_send")
    st.markdown("</div>", unsafe_allow_html=True)  # end .sis-chat-input

    st.markdown("</div>", unsafe_allow_html=True)  # end .sis-chat-card
    st.markdown("</div>", unsafe_allow_html=True)  # end .sis-chat-page

    # ====== MESSAGE TO SEND ======
    message_to_send = None

    # 1) Suggestion click
    if chosen_suggestion is not None:
        message_to_send = chosen_suggestion

    # 2) Manual user input
    elif send_clicked and user_text.strip():
        message_to_send = user_text.strip()

    # ====== HANDLE SEND ======
    if message_to_send is not None:
        st.session_state.assistant_chat_history.append(
            {"role": "user", "content": message_to_send}
        )

        try:
            history_before_last = st.session_state.assistant_chat_history[:-1]
            answer = ask_chatbot(
                user_message=message_to_send,
                history=history_before_last,
            )
        except Exception as e:
            friendly = (
                "Sorry, the SIS chatbot cannot answer right now. "
                "This usually happens when the OpenAI API key has no quota left "
                "or there is a temporary connection problem."
            )
            if "insufficient_quota" in str(e) or "RateLimitError" in type(e).__name__:
                friendly = (
                    "The SIS chatbot is temporarily unavailable because the "
                    "OpenAI API key has **no remaining quota**. "
                    "Please update the API key or add credits, then try again."
                )

            st.session_state.assistant_chat_history.append(
                {"role": "assistant", "content": friendly}
            )
            st.error(str(e))
        else:
            st.session_state.assistant_chat_history.append(
                {"role": "assistant", "content": answer}
            )

        st.rerun()
