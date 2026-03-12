"""
Inyección de CSS personalizado para el tema oscuro del dashboard.
"""
import streamlit as st


def inject_css() -> None:
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp { background-color: #0d1117; color: #e6edf3; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
        border-right: 1px solid #21262d;
    }

    /* ── KPI Cards ── */
    .kpi-card {
        background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(88,166,255,0.15);
    }
    .kpi-value {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #58a6ff, #79c0ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1;
    }
    .kpi-label {
        font-size: 0.82rem;
        font-weight: 500;
        color: #8b949e;
        margin-top: 6px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .kpi-icon { font-size: 1.8rem; margin-bottom: 8px; }

    /* ── Section titles ── */
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #e6edf3;
        border-left: 4px solid #58a6ff;
        padding-left: 12px;
        margin: 28px 0 16px 0;
    }

    /* ── Header ── */
    .main-header {
        background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
        border: 1px solid #21262d;
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 24px;
    }
    .main-header h1 {
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(135deg, #58a6ff, #79c0ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .main-header p { color: #8b949e; margin: 6px 0 0; font-size: 0.95rem; }


    /* ── Tabs principales ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.75rem;
        background: #0d1117;
        padding: 0.4rem;
        border: 1px solid #21262d;
        border-radius: 12px;
        margin-bottom: 0.8rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 52px;
        border-radius: 10px;
        padding: 0 1rem;
        background: #161b22;
        border: 1px solid #30363d;
        color: #c9d1d9;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: #1f2937;
        border-color: #58a6ff;
        color: #e6edf3;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1f6feb 0%, #58a6ff 100%);
        border-color: #79c0ff;
        color: #ffffff;
        box-shadow: 0 6px 20px rgba(31, 111, 235, 0.35);
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background: transparent;
    }

    hr { border-color: #21262d; margin: 24px 0; }
</style>
""", unsafe_allow_html=True)
