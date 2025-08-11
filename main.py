"""
VedOps - Local-First AI-Powered DevSecOps Platform
Main Streamlit application entry point
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ui.dashboard import render_dashboard
from core.orchestrator import AgentOrchestrator
from core.state_manager import StateManager
from utils.config import load_config

def main():
    """Main application entry point"""
    
    # Configure Streamlit page
    st.set_page_config(
        page_title="VedOps - AI DevSecOps Platform",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS
    load_custom_css()
    
    # Initialize core components
    if 'state_manager' not in st.session_state:
        st.session_state.state_manager = StateManager()
    
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = AgentOrchestrator(st.session_state.state_manager)
    
    # Render main dashboard
    render_dashboard()

def load_custom_css():
    """Load custom CSS for futuristic theme"""
    css_file = Path(__file__).parent / "ui" / "styles.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
