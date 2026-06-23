from pathlib import Path
from typing import List, Dict, Any

import streamlit as st
from openai import OpenAI

# ==============================
# OpenAI client
# ==============================
# API key comes from .streamlit/secrets.toml:
# OPENAI_API_KEY = "sk-..."
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


# ==============================
# Research context loading
# ==============================

def load_research_context() -> str:
    """
    Load SIS/kb/research_context.txt in a very explicit way.

    Expected path:
      C:/Users/Student/Desktop/SIS/kb/research_context.txt
    """
    # project_root = .../SIS
    project_root = Path(__file__).resolve().parents[1]
    kb_path = project_root / "kb" / "research_context.txt"

    # Debug info in terminal and sidebar
    print("🔎 Looking for research_context.txt at:", kb_path)
    if kb_path.is_file():
        try:
            text = kb_path.read_text(encoding="utf-8")
            print("✅ Loaded research_context.txt, length:", len(text))
            # Small hint in sidebar for you (not for users)
            try:
                st.sidebar.info(f"Loaded SIS research context from:\n{kb_path}")
            except Exception:
                # Sidebar may not exist during early import – ignore
                pass
            return text.strip()
        except Exception as e:
            print("❌ Error reading research_context.txt:", e)
            try:
                st.sidebar.error(f"Error reading research_context.txt: {e}")
            except Exception:
                pass
            return ""
    else:
        print("❌ research_context.txt NOT FOUND at:", kb_path)
        try:
            st.sidebar.warning(
                "Could not find 'kb/research_context.txt'.\n"
                f"Tried path:\n{kb_path}"
            )
        except Exception:
            pass
        return ""


RESEARCH_CONTEXT = load_research_context()


# ==============================
# System prompt
# ==============================

BASE_SYSTEM_PROMPT = f"""
You are the SIS Research Chatbot.

Your job is to answer questions using ONLY the SIS research context below.

Rules:
- Base your answers on this context whenever possible.
- You may rephrase and summarise the context, but do not add new facts.
- If you truly cannot find anything related in the context, reply with:
  "I’m not sure about that based on the current SIS research information."
- Keep answers short, clear, and student-friendly (2–5 sentences).

Helpful mapping between user topics and sections:
- "SIS project overview" → [SIS Project Overview]
- "Solar radiation concepts" → [Key Solar Radiation Concepts] + [Why Solar Radiation Matters]
- "Satellite imagery basics" / "what is satellite image" → [Satellite Imagery Basics]
- "Research group mission" → [About the Sustainable Data & AI Applications Research Group]
- "Common challenges" → [Common Challenges]
- "Eindhoven sunlight" / "city example" → [SIS Radiation Workflow in Eindhoven]
- "Scenario vs forecast" / "typical pattern vs prediction" → [Scenario Thinking vs Weather Forecasting]
- "Explainable AI" / "why this map looks like this" → [Explainable AI in Simple Terms] + [How to Read the SIS Maps]
- "Grid congestion" / "grid risk" → [Basic Grid Congestion Awareness]
- "Ethics" / "responsible use" → [Ethics and Responsible Interpretation]

[RESEARCH CONTEXT START]
{RESEARCH_CONTEXT}
[RESEARCH CONTEXT END]
"""


# ==============================
# Chat logic
# ==============================

def build_messages(
    user_message: str,
    history: List[Dict[str, Any]] | None = None
) -> List[Dict[str, str]]:
    """
    Prepare the messages list for the OpenAI chat completion.
    """
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": BASE_SYSTEM_PROMPT},
    ]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": user_message})
    return messages


def ask_chatbot(
    user_message: str,
    history: List[Dict[str, str]] | None = None,
    model: str = "gpt-4.1-mini",
) -> str:
    """
    Main entry point for the rest of your app.

    Returns: assistant reply as plain text.
    """

    # 🔴 If context is still empty, tell *you* clearly
    if not RESEARCH_CONTEXT:
        return (
            "The SIS research context file could not be loaded.\n\n"
            "Please check that this file exists and is a plain text file:\n"
            "SIS/kb/research_context.txt"
        )

    messages = build_messages(user_message, history)

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()
