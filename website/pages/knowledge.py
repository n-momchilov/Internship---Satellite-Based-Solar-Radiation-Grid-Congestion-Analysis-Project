import streamlit as st

def render():
    tab1, tab2 = st.tabs(["SIS Knowledge", "Grid Knowledge"])

    with tab1:
        from pages.basics import render as render_basics
        render_basics()

    with tab2:
        from pages.grid_knowledge import render as render_grid_knowledge
        render_grid_knowledge()
