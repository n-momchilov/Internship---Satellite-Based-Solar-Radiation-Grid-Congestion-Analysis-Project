# app.py
import streamlit as st
from ui.layout import setup_page, load_styles, render_chrome, footer, get_active_page

setup_page()
load_styles(active_page=None)

active = get_active_page()
load_styles(active_page=active)
render_chrome(active)

# route
if active == "Home":
    from pages.home import render as render_home
    render_home()
elif active == "Radiation":
    from pages.radiation import render as render_radiation
    render_radiation()
elif active == "Basics":
    from pages.basics import render as render_basics
    render_basics()
elif active == "About":
    from pages.about import render as render_about
    render_about()
elif active == "Feedback":
    from pages.feedback import render as render_feedback
    render_feedback()
elif active == "Assistant":
    from pages.assistant import render as render_assistant
    render_assistant()

footer()

