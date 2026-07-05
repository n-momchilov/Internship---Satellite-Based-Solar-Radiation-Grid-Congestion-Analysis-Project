import streamlit as st
import streamlit.components.v1 as components

def render():
    # Wrapper for safe bottom padding on phones
    st.markdown("<div class='page-pad'>", unsafe_allow_html=True)

    st.title("Company & Team")

    # -----------------------------
    # Company Section (same as before)
    # -----------------------------
    st.subheader("The Company – Sustainable Data & AI Applications Research Group")

    st.markdown(
        """
The **Sustainable Data & AI Applications** research group at **Fontys University of Applied Sciences** focuses on developing and applying responsible, transparent and practical AI solutions that contribute to a sustainable and inclusive society.  

Artificial Intelligence (AI) is considered a key enabling technology - a driver of transformation that influences not only ICT innovation but also industries, healthcare, nature conservation and society as a whole. Although AI is becoming increasingly visible in our daily lives, the technology itself is still evolving. The research group aims to bridge that gap by making AI mature, explainable and beneficial for people and the planet.
        """
    )

    st.markdown("### Our Mission")
    st.markdown(
        """
We aim to accelerate the practical applicability of AI by conducting applied research, exploring new possibilities with data and algorithms and guiding the transition from data-driven AI toward smart and sustainable technology.  

Our work emphasizes:
- Turning data into actionable insights that address real societal and environmental challenges.  
- Making AI systems more transparent, ethical and explainable.  
- Collaborating with students, teachers and industry partners to design AI that truly serves human and ecological well-being.
        """
    )

    st.markdown("### Focus Areas")
    st.markdown(
        """
1. **AI for People & Planet**  
   Exploring and implementing AI solutions that have a positive and measurable impact on humans and the natural environment.  
   Examples include projects related to biodiversity monitoring, wildlife management, healthcare innovation and energy sustainability.  

2. **AI Engineering**  
   Developing AI as a mature engineering discipline, focusing on structure, reliability and lifecycle management.  
   This includes automated model retraining, data governance, performance monitoring and ethical integration of AI within organizations.
        """
    )

    st.markdown("### Research Vision and Challenges")
    st.markdown(
        """
The research group explores the next generation of AI technologies that move beyond brute-force data processing toward intelligent, efficient and human-aligned systems.  
Current research topics include:
- **Explainable AI (XAI)** - ensuring transparency in AI decisions.  
- **Causal AI** - enabling AI to reason with less data by understanding cause and effect.  
- **Ethical and Responsible AI** - aligning algorithms with human values, privacy, and fairness.  
- **AI Process Engineering** - moving from experimental prototypes to well-defined, repeatable AI development processes.  

The group’s ambition is to make AI trustworthy, sustainable and accessible - supporting organizations and society in using AI responsibly and effectively.
        """
    )

    st.markdown("### Collaboration & Education")
    st.markdown(
        """
At Fontys, sustainability and openness are key. The research group operates within the Centre of Expertise AI for Society (CoE AI),  
where knowledge and experience in AI are shared to foster innovation and collaboration in the Brainport region.  

Through public-private partnerships, student involvement and interdisciplinary cooperation, the group contributes to both education and applied innovation - helping to prepare the next generation of AI professionals who design with purpose and responsibility.
        """
    )

    st.markdown(
        """
<div style='margin-top:10px; margin-bottom:22px;'>
    🔗 <a href='https://www.fontys.nl/Onderzoek/AI-en-big-data.htm' target='_blank' style='color:#4FC3F7; font-weight:600; text-decoration:none;'>
        Visit the official Fontys Sustainable Data & AI Applications page
    </a>
</div>
""",
        unsafe_allow_html=True
    )

    st.markdown(
        """
By connecting technology, sustainability, and education, **Sustainable Data & AI Applications** actively supports the Brainport region’s transition toward a data-driven and environmentally responsible future.  
Its applied research not only strengthens industry collaboration but also helps society adopt AI innovations that are ethical, transparent and sustainable.
        """
    )

    # -----------------------------
    # Team Section (improved version with avatar + LinkedIn)
    # -----------------------------
    st.markdown("<h3 style='font-family: Tahoma, sans-serif; margin-top:26px;'>The Team</h3>", unsafe_allow_html=True)

    team_html = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1" />
<style>
  :root { --gap: 22px; }
  body { margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
  .team {
    display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:var(--gap);
    max-width:1080px; margin:20px auto 0; padding:0 12px;
  }
  .card {
    background:#ffffff; border-radius:16px; padding:28px;
    box-shadow:0 6px 16px rgba(0,0,0,0.15);
    min-width:0; text-align:center; transition:transform .2s ease;
  }
  .card:hover { transform: translateY(-4px); }
  .avatar {
    width:90px; height:90px; border-radius:50%; display:flex; align-items:center; justify-content:center;
    font-size:34px; color:white; font-weight:700; margin:0 auto 14px;
  }
  .anh { background:#4CAF50; }
  .nikola { background:#7C3AED; }
  .priyanka { background:#2196F3; }
  .card h3 { font-size:22px; margin:8px 0 10px; font-weight:800; }
  .card p { font-size:17px; margin:0 0 10px; line-height:1.55; color:#333; }
  .linkedin {
    display:inline-flex; align-items:center; gap:6px; margin-top:8px;
    text-decoration:none; color:#0077b5; font-weight:600; font-size:16px;
  }
  .linkedin:hover { text-decoration:underline; }

  @media (max-width: 820px){
    .team { grid-template-columns:1fr; max-width:420px; }
  }

  @media (max-width: 600px){
    .team { gap:16px; }
    .card { padding:22px; }
    .avatar { width:72px; height:72px; font-size:28px; margin-bottom:10px; }
    .card h3 { font-size:20px; }
    .card p  { font-size:15px; line-height:1.45; }
  }
</style>
</head>
<body>
  <div class="team">
    <div class="card">
      <div class="avatar anh">AH</div>
      <h3>Anh Huynh</h3>
      <p>Student of Software Engineering, currently specializing in AI at Fontys University of Applied Sciences</p>
      <a class="linkedin" href="https://www.linkedin.com/in/anh-huynh-a69645348/" target="_blank">
        <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" width="20" height="20" alt="LinkedIn"/> LinkedIn
      </a>
    </div>
    <div class="card">
      <div class="avatar nikola">N</div>
      <h3>Nikola</h3>
      <p>Student of Software Engineering, currently specializing in AI at Fontys University of Applied Sciences</p>
      <a class="linkedin" href="https://www.linkedin.com/in/nikola-momchilov/" target="_blank">
        <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" width="20" height="20" alt="LinkedIn"/> LinkedIn
      </a>
    </div>
    <div class="card">
      <div class="avatar priyanka">PD</div>
      <h3>Priyanka Darbari</h3>
      <p>Company Mentor guiding the project at Fontys University of Applied Sciences.</p>
      <a class="linkedin" href="https://www.linkedin.com/in/priyanka-darbari-ba480078/" target="_blank">
        <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" width="20" height="20" alt="LinkedIn"/> LinkedIn
      </a>
    </div>
  </div>
</body>
</html>
"""
    components.html(team_html, height=760, scrolling=False)

    # Safety spacer for mobile
    st.markdown("<div class='mobile-bottom-spacer'></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
