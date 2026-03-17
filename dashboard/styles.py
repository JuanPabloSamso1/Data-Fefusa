"""Inyeccion de CSS para el dashboard Streamlit."""

import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {
        --bg-app: #07111f;
        --bg-surface: #0f1b2b;
        --bg-surface-soft: #13233a;
        --bg-card: #102033;
        --bg-card-2: #142844;
        --border-1: #21344d;
        --border-2: #335077;
        --text-1: #eef4fb;
        --text-2: #9fb1c7;
        --text-3: #70839b;
        --brand-1: #78b8ff;
        --brand-2: #3d8cff;
        --accent-1: #45d39c;
        --warn-1: #f3c96b;
        --danger-1: #ff7272;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at top right, rgba(120, 184, 255, 0.14), transparent 28%),
            radial-gradient(circle at top left, rgba(69, 211, 156, 0.09), transparent 24%),
            linear-gradient(180deg, #09121f 0%, #07111f 100%);
        color: var(--text-1);
    }

    .block-container {
        padding-top: 1.35rem;
        padding-bottom: 1.2rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1422 0%, #09111c 100%);
        border-right: 1px solid rgba(120, 184, 255, 0.12);
    }

    [data-testid="stSidebar"] div.stButton > button {
        min-height: 0;
        border-radius: 10px;
        border: 1px solid var(--border-1);
        background: var(--bg-surface-soft);
        color: var(--text-1);
        font-weight: 600;
    }

    .main-header {
        background:
            linear-gradient(130deg, rgba(13, 29, 49, 0.96) 0%, rgba(16, 32, 51, 0.96) 55%, rgba(21, 44, 73, 0.96) 100%);
        border: 1px solid rgba(120, 184, 255, 0.18);
        border-radius: 22px;
        padding: 28px 30px;
        margin-bottom: 22px;
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
    }

    .main-header .eyebrow {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        border: 1px solid rgba(120, 184, 255, 0.22);
        color: var(--brand-1);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 12px;
        background: rgba(61, 140, 255, 0.10);
    }

    .main-header h1 {
        margin: 0;
        font-size: 2.05rem;
        line-height: 1.05;
        font-weight: 800;
        color: var(--text-1);
    }

    .main-header p {
        color: var(--text-2);
        margin: 8px 0 0;
        font-size: 0.98rem;
    }

    .context-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 14px;
    }

    .context-pill {
        display: inline-flex;
        align-items: center;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid rgba(159, 177, 199, 0.18);
        background: rgba(255, 255, 255, 0.03);
        color: var(--text-2);
        font-size: 0.82rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.9rem;
        background: linear-gradient(180deg, rgba(11, 20, 34, 0.98) 0%, rgba(13, 22, 35, 0.98) 100%);
        padding: 0.6rem;
        border: 1px solid rgba(120, 184, 255, 0.12);
        border-radius: 16px;
        margin-bottom: 1rem;
    }

    .stTabs [data-baseweb="tab"] {
        min-height: 56px;
        border-radius: 13px;
        padding: 0.55rem 1.1rem;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(112, 131, 155, 0.20);
        color: var(--text-2);
        font-weight: 700;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #78b8ff 0%, #45d39c 100%);
        border-color: rgba(255, 255, 255, 0.22);
        color: #06101f;
        box-shadow: 0 12px 28px rgba(61, 140, 255, 0.25);
    }

    .stTabs [data-baseweb="tab-highlight"] {
        background: transparent;
    }

    section.main div.stButton > button {
        min-height: 78px;
        border-radius: 16px;
        border: 1px solid rgba(120, 184, 255, 0.18);
        background: linear-gradient(180deg, rgba(15, 27, 43, 0.96) 0%, rgba(18, 35, 58, 0.96) 100%);
        color: var(--text-1);
        font-weight: 700;
        font-size: 0.98rem;
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.16);
    }

    section.main div.stButton > button:hover {
        border-color: rgba(120, 184, 255, 0.40);
        transform: translateY(-1px);
    }

    section.main div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, rgba(61, 140, 255, 0.28) 0%, rgba(69, 211, 156, 0.22) 100%);
        border-color: rgba(120, 184, 255, 0.45);
        box-shadow: 0 14px 32px rgba(61, 140, 255, 0.18);
    }

    .view-card-sub {
        margin: 6px 2px 18px;
        color: var(--text-3);
        font-size: 0.79rem;
        min-height: 34px;
    }

    .section-title {
        font-size: 1rem;
        font-weight: 800;
        color: var(--text-1);
        margin: 0 0 0.2rem 0;
    }

    .section-subtitle {
        color: var(--text-2);
        font-size: 0.9rem;
        margin: 0 0 1rem 0;
    }

    .panel-card {
        background: linear-gradient(180deg, rgba(16, 32, 51, 0.95) 0%, rgba(18, 40, 68, 0.92) 100%);
        border: 1px solid rgba(120, 184, 255, 0.12);
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.16);
    }

    .panel-card + .panel-card {
        margin-top: 12px;
    }

    .metric-card {
        background: linear-gradient(180deg, rgba(16, 32, 51, 0.98) 0%, rgba(15, 27, 43, 0.98) 100%);
        border: 1px solid rgba(120, 184, 255, 0.14);
        border-radius: 18px;
        padding: 18px 18px 16px;
        min-height: 126px;
    }

    .metric-kicker {
        color: var(--text-3);
        font-size: 0.75rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-weight: 700;
    }

    .metric-value {
        margin-top: 10px;
        color: var(--text-1);
        font-size: 1.95rem;
        line-height: 1;
        font-weight: 800;
    }

    .metric-label {
        margin-top: 6px;
        color: var(--text-2);
        font-size: 0.88rem;
        font-weight: 600;
    }

    .metric-note {
        margin-top: 8px;
        color: var(--text-3);
        font-size: 0.76rem;
    }

    .info-card {
        background: rgba(69, 211, 156, 0.08);
        border: 1px solid rgba(69, 211, 156, 0.18);
        border-radius: 16px;
        padding: 14px 16px;
        color: #dffaf0;
        font-size: 0.9rem;
    }

    .score-card {
        background: linear-gradient(135deg, rgba(11, 20, 34, 0.98) 0%, rgba(15, 27, 43, 0.98) 100%);
        border: 1px solid rgba(120, 184, 255, 0.16);
        border-radius: 20px;
        padding: 18px 20px;
        text-align: center;
    }

    .score-teams {
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        gap: 16px;
        align-items: center;
        color: var(--text-1);
        font-weight: 700;
    }

    .score-value {
        font-size: 2.25rem;
        font-weight: 800;
        color: var(--brand-1);
    }

    .score-meta {
        margin-top: 10px;
        color: var(--text-2);
        font-size: 0.86rem;
    }

    .badge-risk {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 4px 9px;
        font-size: 0.76rem;
        font-weight: 700;
        border: 1px solid transparent;
    }

    .badge-risk.bajo {
        color: #b8f3dc;
        background: rgba(69, 211, 156, 0.10);
        border-color: rgba(69, 211, 156, 0.22);
    }

    .badge-risk.medio {
        color: #f8e2a8;
        background: rgba(243, 201, 107, 0.10);
        border-color: rgba(243, 201, 107, 0.24);
    }

    .badge-risk.alto {
        color: #ffd2d2;
        background: rgba(255, 114, 114, 0.10);
        border-color: rgba(255, 114, 114, 0.24);
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(120, 184, 255, 0.12);
        border-radius: 16px;
        overflow: hidden;
    }

    div[data-testid="stDataFrame"] div[role="gridcell"] {
        font-size: 0.9rem;
    }

    @media (max-width: 900px) {
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }

        .main-header {
            padding: 22px 20px;
            border-radius: 18px;
            margin-bottom: 18px;
        }

        .main-header h1 {
            font-size: 1.72rem;
        }

        .main-header p {
            font-size: 0.92rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.55rem;
            padding: 0.45rem;
            overflow-x: auto;
            overflow-y: hidden;
            flex-wrap: nowrap;
            scrollbar-width: none;
            -ms-overflow-style: none;
        }

        .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
            display: none;
        }

        .stTabs [data-baseweb="tab"] {
            min-height: 48px;
            padding: 0.45rem 0.9rem;
            font-size: 0.88rem;
            flex: 0 0 auto;
            white-space: nowrap;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: 0.85rem;
        }

        .score-card {
            padding: 16px 16px;
        }

        .score-value {
            font-size: 2rem;
        }
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: 0.8rem;
            padding-bottom: 0.9rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }

        .main-header {
            padding: 18px 16px;
            border-radius: 16px;
            margin-bottom: 16px;
        }

        .main-header .eyebrow {
            font-size: 0.72rem;
            margin-bottom: 10px;
        }

        .main-header h1 {
            font-size: 1.45rem;
            line-height: 1.12;
        }

        .main-header p {
            font-size: 0.88rem;
            line-height: 1.4;
        }

        .context-row {
            gap: 6px;
            margin-top: 12px;
        }

        .context-pill {
            font-size: 0.75rem;
            padding: 5px 9px;
            max-width: 100%;
        }

        section.main div.stButton > button {
            min-height: 60px;
            border-radius: 14px;
            font-size: 0.92rem;
        }

        .section-title {
            font-size: 0.96rem;
        }

        .section-subtitle {
            font-size: 0.84rem;
            margin-bottom: 0.85rem;
        }

        div[data-testid="stHorizontalBlock"] {
            flex-direction: column;
        }

        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }

        .metric-card {
            min-height: 0;
            padding: 16px 16px 14px;
            border-radius: 16px;
        }

        .metric-kicker {
            font-size: 0.7rem;
        }

        .metric-value {
            font-size: 1.6rem;
        }

        .metric-label {
            font-size: 0.84rem;
        }

        .metric-note {
            font-size: 0.72rem;
        }

        .info-card,
        .panel-card {
            border-radius: 14px;
            padding: 14px 14px;
        }

        .score-card {
            border-radius: 16px;
            padding: 14px 14px;
        }

        .score-teams {
            grid-template-columns: 1fr;
            gap: 8px;
        }

        .score-teams > div {
            text-align: center;
            justify-self: center;
        }

        .score-value {
            font-size: 1.85rem;
        }

        .score-meta {
            margin-top: 8px;
            font-size: 0.8rem;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 14px;
        }

        div[data-testid="stDataFrame"] div[role="gridcell"] {
            font-size: 0.82rem;
        }

        .footer-line {
            font-size: 0.74rem;
            padding: 10px 0 6px;
        }
    }

    @media (max-width: 480px) {
        .main-header h1 {
            font-size: 1.28rem;
        }

        .main-header p {
            font-size: 0.83rem;
        }

        .context-pill {
            font-size: 0.72rem;
        }

        .stTabs [data-baseweb="tab"] {
            min-height: 44px;
            padding: 0.4rem 0.78rem;
            font-size: 0.82rem;
        }

        .metric-value {
            font-size: 1.45rem;
        }

        .score-value {
            font-size: 1.7rem;
        }
    }

    .footer-line {
        text-align: center;
        color: var(--text-3);
        font-size: 0.8rem;
        padding: 8px 0 2px;
    }
</style>
        """,
        unsafe_allow_html=True,
    )
