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
    .block-container {padding-top: 1.4rem; padding-bottom: 1.2rem;}

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
        margin: 22px 0 12px 0;
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
        gap: 0.9rem;
        background: linear-gradient(180deg, #10161f 0%, #0d1117 100%);
        padding: 0.65rem;
        border: 1px solid #2b3440;
        border-radius: 14px;
        margin-bottom: 1rem;
        box-shadow: inset 0 0 0 1px rgba(88,166,255,0.08);
    }
    .stTabs [data-baseweb="tab"] {
        min-height: 58px;
        border-radius: 12px;
        padding: 0.55rem 1.15rem;
        background: #161b22;
        border: 1px solid #36404d;
        color: #c9d1d9;
        font-weight: 700;
        letter-spacing: 0.01em;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: #1f2937;
        border-color: #6ea8ff;
        color: #ffffff;
        transform: translateY(-1px);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #58a6ff 0%, #9cc9ff 100%);
        border-color: #ffffff;
        color: #06101f;
        box-shadow: 0 8px 22px rgba(88,166,255,0.4);
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background: transparent;
    }



    .insight-banner {
        background: linear-gradient(135deg, rgba(31,111,235,0.22) 0%, rgba(88,166,255,0.12) 100%);
        border: 1px solid #2f81f7;
        border-radius: 10px;
        padding: 12px 16px;
        margin: 10px 0 16px 0;
        color: #dbeafe;
        font-weight: 500;
    }

    div[data-testid="stDataFrame"] div[role="gridcell"] {
        font-size: 0.92rem;
    }

    hr { border-color: #21262d; margin: 24px 0; }
</style>
""", unsafe_allow_html=True)
