"""
PRO ANALYST — AI-Powered Financial Intelligence Dashboard
Entry point for Streamlit application
"""

import streamlit as st
st.set_page_config(
    page_title="PRO ANALYST | Financial Intelligence",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/yourusername/pro-analyst-dashboard",
        "Report a bug": "https://github.com/yourusername/pro-analyst-dashboard/issues",
        "About": "PRO ANALYST — Institutional-grade financial analysis powered by AI"
    }
)

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pages.main_dashboard import render_dashboard

def main():
    # Global CSS
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] {
            font-family: 'DM Sans', sans-serif;
        }

        .stApp {
            background-color: #0a0e1a;
            color: #ffffff;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #0f1320;
            border-right: 1px solid rgba(255,255,255,0.07);
        }

        /* Cards */
        .metric-card {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 16px 20px;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background-color: transparent;
            gap: 4px;
        }

        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            color: rgba(255,255,255,0.4);
            border: none;
            font-size: 13px;
            font-weight: 500;
        }

        .stTabs [aria-selected="true"] {
            color: #00d4aa !important;
            border-bottom: 2px solid #00d4aa !important;
            background-color: transparent !important;
        }

        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, rgba(0,212,170,0.15), rgba(99,102,241,0.15));
            border: 1px solid rgba(0,212,170,0.3);
            color: #00d4aa;
            border-radius: 8px;
            font-weight: 600;
            font-size: 13px;
            transition: all 0.2s;
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, rgba(0,212,170,0.25), rgba(99,102,241,0.25));
            border-color: #00d4aa;
        }

        /* Select boxes */
        .stSelectbox > div > div {
            background-color: rgba(255,255,255,0.05) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            color: white !important;
        }

        /* File uploader */
        .stFileUploader {
            background: rgba(255,255,255,0.03);
            border: 1px dashed rgba(0,212,170,0.3);
            border-radius: 12px;
        }

        /* Dividers */
        hr {
            border-color: rgba(255,255,255,0.07);
        }

        /* Risk high */
        .risk-high { color: #ef4444; }
        .risk-medium { color: #f97316; }
        .risk-low { color: #facc15; }

        /* Score colors */
        .score-excellent { color: #00d4aa; }
        .score-strong { color: #4ade80; }
        .score-moderate { color: #facc15; }
        .score-weak { color: #f97316; }
        .score-concern { color: #ef4444; }

        /* Table styling */
        .dataframe {
            background: transparent !important;
            color: white !important;
        }

        /* Hide Streamlit branding */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        .stDeployButton { display: none; }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); }
        ::-webkit-scrollbar-thumb { background: rgba(0,212,170,0.3); border-radius: 2px; }
    </style>
    """, unsafe_allow_html=True)

    render_dashboard()

if __name__ == "__main__":
    main()
