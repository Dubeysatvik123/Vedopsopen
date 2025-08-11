"""
Sidebar Navigation Component
"""

import streamlit as st

def render_sidebar():
    """Render sidebar navigation"""
    
    with st.sidebar:
        st.markdown("### 🚀 VedOps Navigation")
        
        # Navigation menu
        page = st.radio(
            "Select Page:",
            [
                "Dashboard",
                "Upload", 
                "Pipeline",
                "Build Status",  # Added build status option
                "Security",  # Added security option
                "Agents",
                "Reports", 
                "Settings"
            ],
            index=0
        )
        
        st.divider()
        
        # Current pipeline status
        if hasattr(st.session_state, 'state_manager'):
            current_pipeline = st.session_state.state_manager.get_current_pipeline()
            
            if current_pipeline:
                st.markdown("### 📊 Current Pipeline")
                st.write(f"**Project:** {current_pipeline.get('project_name', 'Unknown')}")
                st.write(f"**Status:** {current_pipeline.get('status', 'Unknown').title()}")
                
                progress = current_pipeline.get('progress', 0)
                st.progress(progress / 100)
                st.write(f"Progress: {progress}%")
        
        st.divider()
        
        # System status
        st.markdown("### 🔧 System Status")
        st.success("🟢 VedOps Online")
        st.info("🐳 Docker Available")
        st.info("🤖 Ollama Ready")
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.rerun()
        
        if st.button("🧹 Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared!")
    
    return page
