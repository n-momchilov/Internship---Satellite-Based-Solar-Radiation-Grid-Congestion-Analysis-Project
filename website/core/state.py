import streamlit as st
from .config import DEFAULT_PLACE, DEFAULT_CENTER, DEFAULT_ROI

def init():
    ss = st.session_state
    ss.setdefault("place", DEFAULT_PLACE)
    ss.setdefault("center_lat", DEFAULT_CENTER[0])
    ss.setdefault("center_lon", DEFAULT_CENTER[1])
    ss.setdefault("roi_bounds", DEFAULT_ROI)
    ss.setdefault("result", None)
    ss.setdefault("input_mode", "city")
    ss.setdefault("confirmed", True)
    ss.setdefault("pending_confirm", False)
    ss.setdefault("candidate", None)
    return ss
