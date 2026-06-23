import streamlit as st

def header():
    st.markdown("<div class='app-title'>Solar Radiation — Demo</div>", unsafe_allow_html=True)
    st.caption("CAMS (point) • SARAH-3 (grid) • HGBR baseline (no leakage)")

def confirm_box(nm, la, lo):
    st.markdown(
        f"""
        <div class="confirm-box">
          <div class="confirm-title">Confirm location</div>
          <div class="confirm-text">
            Use <b>{nm}</b> for analysis?<br>
            <span class="confirm-sub">({la:.4f}, {lo:.4f})</span>
          </div>
        </div>""", unsafe_allow_html=True)
