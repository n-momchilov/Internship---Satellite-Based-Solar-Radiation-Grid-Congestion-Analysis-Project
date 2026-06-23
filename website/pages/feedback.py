# pages/feedback.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime

import csv
import streamlit as st

# ============================================================
# Config: where to store feedback
# ============================================================

# feedback.csv will be stored in:  <project_root>/data/feedback.csv
FEEDBACK_CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "feedback.csv"


def _ensure_feedback_file_exists() -> None:
    """
    Make sure the feedback CSV file (and folder) exist.
    If the file doesn't exist yet, create it with a header row.
    """
    FEEDBACK_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not FEEDBACK_CSV_PATH.is_file():
        with FEEDBACK_CSV_PATH.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp",
                    "rating",
                    "device",
                    "main_issue",
                    "like",
                    "improve",
                    "extra_comment",
                ]
            )


def _save_feedback(
    rating: int,
    device: str,
    main_issue: str,
    like: str,
    improve: str,
    extra_comment: str,
) -> None:
    """
    Append one feedback row to feedback.csv.
    """
    _ensure_feedback_file_exists()
    now_iso = datetime.utcnow().isoformat()

    with FEEDBACK_CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                now_iso,
                rating,
                device,
                main_issue,
                like,
                improve,
                extra_comment,
            ]
        )


# ============================================================
# Streamlit page
# ============================================================

def render():
    # ---- Session flag: was feedback just submitted? ----
    if "feedback_submitted" not in st.session_state:
        st.session_state.feedback_submitted = False

    # --------------- Inline CSS for nicer UI ---------------
    st.markdown(
        """
<style>
/* === Bright, clean, readable feedback UI (aligned with chatbot) === */

.sis-feedback-page {
  max-width: 900px;
  margin: 2.5rem auto 3rem auto;
  padding: 0 1.2rem;
  font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.sis-feedback-card {
  background: rgba(30,41,59,0.90);      /* lighter navy, similar to chatbot card */
  border-radius: 20px;
  border: 1px solid rgba(148,163,184,0.65);
  box-shadow: 0 20px 50px rgba(15,23,42,0.65);
  padding: 1.7rem 1.6rem 1.4rem 1.6rem;
  color: #f3f4f6;                       /* brighter text */
}

/* Titles */
.sis-feedback-title {
  font-size: 1.7rem;
  font-weight: 700;
  margin-bottom: 0.35rem;
  color: #ffffff;
}

.sis-feedback-subtitle {
  font-size: 1rem;
  color: #dbeafe;
  margin-bottom: 1.1rem;
}

/* Badge */
.sis-feedback-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.25rem 0.7rem;
  border-radius: 999px;
  background: rgba(59,130,246,0.25);
  border: 1px solid rgba(96,165,250,0.8);
  font-size: 0.8rem;
  font-weight: 600;
  color: #f0f9ff;
  margin-bottom: 0.7rem;
}

/* Sections */
.sis-feedback-section-title {
  font-size: 1.05rem;
  font-weight: 650;
  margin: 0.4rem 0 0.15rem 0;
  color: #f1f5f9;
}

.sis-feedback-hint {
  font-size: 0.9rem;
  color: #cbd5e1;
  margin-bottom: 0.35rem;
}

/* ===== GLOBAL overrides so widget texts are bright ===== */

/* Any plain markdown text inside Streamlit widgets
   (radio options, button text, etc.) */
[data-testid="stMarkdownContainer"] p {
  color: #f9fafb !important;
  font-size: 0.96rem;
}

/* Radio labels */
[data-testid="stRadio"] label {
  color: #f9fafb !important;
  font-size: 0.96rem;
}

/* Slider label / ticks */
[data-testid="stSlider"] label {
  color: #e5e7eb !important;
}

/* Generic widget labels */
label {
  color: #e5e7eb !important;
  font-size: 0.95rem;
}

/* Slider track & thumb */
.stSlider > div > div > div {
  background: #94a3b8 !important;
}
.stSlider > div[data-baseweb="slider"] span {
  background: #3b82f6 !important;
}

/* Text areas */
textarea {
  background: #ffffff !important;
  color: #0f172a !important;
  border-radius: 10px !important;
  border: 1px solid #cbd5e1 !important;
  padding: 0.6rem !important;
  font-size: 0.95rem !important;
}

/* Submit buttons (Submit feedback + Submit another response) */
.stButton > button {
  font-size: 1rem;
  font-weight: 650;
  border-radius: 999px;
  padding: 0.6rem 1.6rem;
  border: 1px solid rgba(148,163,184,0.8);
  background: #f8fafc !important;
  color: #0f172a !important;
  box-shadow: 0 8px 18px rgba(0,0,0,0.3);
  transition: 0.2s;
}

/* Ensure button text (which is markdown) is dark on light bg */
.stButton > button [data-testid="stMarkdownContainer"] p {
  color: #0f172a !important;
  font-weight: 650 !important;
  font-size: 1rem !important;
}

.stButton > button:hover {
  background: #e2e8f0 !important;
  transform: translateY(-1px);
}
</style>
        """,
        unsafe_allow_html=True,
    )

    # --------------- Page wrapper ---------------
    st.markdown('<div class="sis-feedback-page">', unsafe_allow_html=True)

    # --------------- Feedback card ---------------
    st.markdown('<div class="sis-feedback-card">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="sis-feedback-badge">🧪 Prototype • Short survey (1–2 min)</div>
        <div class="sis-feedback-title">Help us improve the SIS dashboard & chatbot</div>
        <div class="sis-feedback-subtitle">
          This dashboard and chatbot are still under development. Your quick feedback will help us a lot to
          decide what to fix and improve more in the best way. The survey is anonymous.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ===== If feedback was just submitted: show thank you and stop =====
    if st.session_state.feedback_submitted:
        st.success("Thank you! Your feedback has been recorded 🙌")
        st.info("You can close this page now or submit another response if you like.")

        if st.button("Submit another response"):
            st.session_state.feedback_submitted = False
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)  # close .sis-feedback-card
        st.markdown("</div>", unsafe_allow_html=True)  # close .sis-feedback-page
        return

    # --------------- 1. Overall experience rating ---------------
    st.markdown(
        """
        <div class="sis-feedback-section-title">
          1️⃣ Overall, how was your experience with the SIS dashboard & chatbot?
        </div>
        <div class="sis-feedback-hint">
          Think about ease of use, clarity and how useful the information was.
        </div>
        """,
        unsafe_allow_html=True,
    )

    rating = st.slider(
        "Overall experience rating (1–5)",
        min_value=1,
        max_value=5,
        value=4,
        step=1,
        help="1 = Very poor • 5 = Excellent",
        key="feedback_rating",
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------- 2. Device ---------------
    st.markdown(
        """
        <div class="sis-feedback-section-title">
          2️⃣ Which device did you use for this feedback?
        </div>
        """,
        unsafe_allow_html=True,
    )

    device = st.radio(
        "Device used",
        ["Laptop / Desktop", "Tablet", "Phone", "Other"],
        index=0,
        key="feedback_device",
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------- 3. Main experience / issue ---------------
    st.markdown(
        """
        <div class="sis-feedback-section-title">
          3️⃣ What best describes your experience?
        </div>
        <div class="sis-feedback-hint">
          Pick the option that is closest to how it felt.
        </div>
        """,
        unsafe_allow_html=True,
    )

    main_issue = st.radio(
        "Main experience",
        [
            "Everything worked well",
            "Mostly good, a bit slow",
            "Difficult to understand",
            "Too many technical issues (layout, buttons, chatbot, etc.)",
        ],
        index=0,
        key="feedback_main_issue",
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------- 4. One thing they like & one thing to improve ---------------
    st.markdown(
        """
        <div class="sis-feedback-section-title">
          4️⃣ Tell us one thing you liked and one thing we should improve
        </div>
        <div class="sis-feedback-hint">
          Short answers are perfect. This helps us see strengths & priorities.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_like, col_improve = st.columns(2)

    with col_like:
        like = st.text_area(
            "One thing you liked",
            placeholder="Example: “The dashboard layout is clear.”",
            key="feedback_like",
            height=70,
        )

    with col_improve:
        improve = st.text_area(
            "One thing to improve",
            placeholder="Example: “Navigation is confusing.”",
            key="feedback_improve",
            height=70,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------- 5. Optional extra comment ---------------
    st.markdown(
        """
        <div class="sis-feedback-section-title">
          5️⃣ Optional: Anything else we should know?
        </div>
        <div class="sis-feedback-hint">
          For example: specific bugs, ideas or situations where the dashboard didn’t help you.
        </div>
        """,
        unsafe_allow_html=True,
    )

    extra_comment = st.text_area(
        "Extra feedback",
        placeholder="Example: “I found a bug somewhere.”",
        key="feedback_comment",
        height=80,
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------- Submit button ---------------
    submit = st.button("Submit feedback")

    if submit:
        like_clean = like.strip()
        improve_clean = improve.strip()
        comment_clean = extra_comment.strip()

        # Save to CSV
        _save_feedback(
            rating=rating,
            device=device,
            main_issue=main_issue,
            like=like_clean,
            improve=improve_clean,
            extra_comment=comment_clean,
        )

        # Mark as submitted and rerun. Next render shows thank-you screen only.
        st.session_state.feedback_submitted = True
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)  # close .sis-feedback-card
    st.markdown("</div>", unsafe_allow_html=True)  # close .sis-feedback-page
