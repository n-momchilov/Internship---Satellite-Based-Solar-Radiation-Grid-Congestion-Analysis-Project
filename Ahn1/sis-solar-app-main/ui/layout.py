from pathlib import Path
import base64
import streamlit as st

CSS_BASE_ORDER = [
    "00-tokens.css",
    "01-host-overrides.css",
    "02-layout.css",
    "03-typography.css",
    "04-theme.css",
    "components/nav.css",
    "components/footer.css",
    "components/panels.css",
    "components/forms.css",
    "utilities.css",
]

def load_styles(active_page: str | None = None, base_dir: str = "styles"):
    base = Path(base_dir)
    parts = []
    for rel in CSS_BASE_ORDER:
        p = base / rel
        if p.is_file():
            parts.append(p.read_text(encoding="utf-8"))
    if active_page:  # page-specific override last
        p = base / "pages" / (active_page.lower() + ".css")
        if p.is_file():
            parts.append(p.read_text(encoding="utf-8"))
    st.markdown("<style>" + "\n\n".join(parts) + "</style>", unsafe_allow_html=True)
    
# Resolve logo path relative to this file
FONTYS_LOGO = (Path(__file__).parent / "static" / "fontys.png").resolve()

def setup_page():
    st.set_page_config(page_title="Solar Radiation Demo",
                       layout="wide", initial_sidebar_state="collapsed")

def get_active_page():
    qp = st.query_params
    return qp.get("page", "Home")

def _nav_link(page, label, active):
    cls = "nav-link active" if active == page else "nav-link"
    return f'<a class="{cls}" href="?page={page}" target="_self">{label}</a>'

def render_chrome(active: str):
    st.markdown(
        f"""
<div class="site-bar">
  <div class="site-bar-inner">
    <div class="brand">
      <div class="site-title">SIS</div> 
    </div>
    <nav class="topnav">
      {_nav_link("Home", "🏠 Home", active)}
      {_nav_link("Radiation", "☀️ Radiation", active)}
      {_nav_link("Basics", "📚 Knowledge", active)}
      {_nav_link("About", "👥 About Us", active)}
      {_nav_link("Feedback", "📝 Feedback", active)}
      {_nav_link("Assistant", "🤖 Chatbot", active)}
    </nav>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

def _img_data_uri(path: Path) -> str:
    try:
        if not path.is_file():
            return ""
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        mime = "image/svg+xml" if path.suffix.lower() == ".svg" else "image/png"
        return f"data:{mime};base64,{b64}"
    except Exception:
        return ""
    
def footer():
    data_uri = _img_data_uri(FONTYS_LOGO)
    logo_html = f'<img src="{data_uri}" alt="Fontys" class="brandmark">' if data_uri else ""
    if logo_html:
        logo_html = f'<span class="logo-wrap">{logo_html}</span>'

    st.markdown(
        '''
<div class="footer-wrap">
  <footer class="site-footer">
    <div class="site-footer-inner">
      <span>© 2025 SIS Project</span>
      ''' + logo_html + '''
      <span>Sustainable Data & AI Applications Research Group</span>
    </div>
  </footer>
</div>
''',
        unsafe_allow_html=True,
    )
