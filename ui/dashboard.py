"""
Main Streamlit Dashboard UI
Renders the primary interface for VedOps platform
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import asyncio
import time

from ui.components.sidebar import render_sidebar
from ui.components.pipeline_view import render_pipeline_view
from ui.components.agent_status import render_agent_status
from ui.components.project_upload import render_project_upload
from ui.components.reports_viewer import render_reports_viewer

def render_dashboard():
    """Main dashboard rendering function"""
    
    # Custom header with futuristic styling
    st.markdown("""
        <div class="header-container">
            <h1 class="main-title">🚀 VedOps</h1>
            <p class="subtitle">AI-Powered DevSecOps Platform</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    page = render_sidebar()
    
    # Main content area
    if page == "Dashboard":
        render_main_dashboard()
    elif page == "Pipeline":
        render_pipeline_view()
    elif page == "Agents":
        render_agent_status()
    elif page == "Upload":
        render_project_upload()
    elif page == "Build Status":
        from ui.components.build_status import render_build_status
        render_build_status()
    elif page == "Security":  # Added security dashboard page
        from ui.components.security_dashboard import render_security_dashboard
        render_security_dashboard()
    elif page == "Reports":
        render_reports_viewer()
    elif page == "Settings":
        render_settings()

    # Floating Krishna chatbot button
    inject_krishna_chatbot()

def render_main_dashboard():
    """Render main dashboard overview"""
    
    # Status metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🔄 Active Pipelines",
            value="1",
            delta="0"
        )
    
    with col2:
        st.metric(
            label="✅ Success Rate",
            value="94.7%",
            delta="2.3%"
        )
    
    with col3:
        st.metric(
            label="⚡ Avg Build Time",
            value="4.2 min",
            delta="-0.8 min"
        )
    
    with col4:
        st.metric(
            label="🛡️ Security Score",
            value="A+",
            delta="Improved"
        )
    
    st.divider()
    
    # Current pipeline status
    current_pipeline = st.session_state.state_manager.get_current_pipeline()
    
    if current_pipeline:
        st.subheader("🔄 Current Pipeline Status")
        
        # Progress bar
        progress = current_pipeline.get('progress', 0)
        st.progress(progress / 100)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Project:** {current_pipeline.get('project_name', 'Unknown')}")
            st.write(f"**Status:** {current_pipeline.get('status', 'Unknown').title()}")
        
        with col2:
            st.write(f"**Current Step:** {current_pipeline.get('current_step', 'Unknown').title()}")
            st.write(f"**Progress:** {progress}%")
    
    else:
        st.info("No active pipeline. Upload a project to get started!")
    
    st.divider()
    
    # Recent activity and system health
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 System Health")
        render_system_health_chart()
    
    with col2:
        st.subheader("📈 Pipeline History")
        render_pipeline_history_chart()

    st.divider()
    st.subheader("🖥️ System Monitoring")
    st.button("Open Monitoring Panel", key="open_monitoring", help="View CPU, RAM, and service health", on_click=open_monitoring)

def render_system_health_chart():
    """Render system health metrics chart"""
    
    # Mock system health data
    metrics = {
        'CPU Usage': 67,
        'Memory': 45,
        'GPU': 89,
        'Network': 23,
        'Storage': 34
    }
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(metrics.keys()),
            y=list(metrics.values()),
            marker_color=['#00ff88' if v < 70 else '#ff6b6b' if v > 85 else '#ffd93d' for v in metrics.values()]
        )
    ])
    
    fig.update_layout(
        title="Resource Utilization",
        yaxis_title="Usage %",
        showlegend=False,
        height=300,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def open_monitoring():
    st.session_state["show_monitoring_panel"] = True

def inject_krishna_chatbot():
    """Adds a floating chatbot button and container in the bottom-right corner."""
    st.markdown(
        """
        <style>
        .krishna-fab { position: fixed; bottom: 24px; right: 24px; z-index: 1000; }
        .krishna-panel { position: fixed; bottom: 90px; right: 24px; width: 360px; height: 480px; background: #111827; color: white; border-radius: 12px; border: 1px solid #374151; box-shadow: 0 8px 24px rgba(0,0,0,0.3); display: none; z-index: 1001; }
        .krishna-panel.show { display: block; }
        </style>
        <button class="krishna-fab" onclick="const p=document.getElementById('krishna-panel'); p.classList.toggle('show');">💬</button>
        <div id="krishna-panel" class="krishna-panel">
            <iframe srcdoc="<html><body style='margin:0;background:#111;color:#fff;font-family:sans-serif'>
            <div style='padding:10px;background:#1f2937;border-bottom:1px solid #374151'>Krishna - Principal DevSecOps Consultant</div>
            <div id='chat' style='height:392px;overflow:auto;padding:10px'></div>
            <div style='display:flex'><input id='msg' style='flex:1;padding:8px;background:#111;border:1px solid #374151;color:#fff'><button onclick=\"parent.postMessage({type:'krishna_msg',text:document.getElementById('msg').value},'*');document.getElementById('msg').value=''\" style='padding:8px;background:#2563eb;color:#fff;border:none'>Send</button></div>
            </body></html>" style="width:100%;height:100%;border:0"></iframe>
        </div>
        <script>
        window.addEventListener('message', (e)=>{
          if(e.data && e.data.type==='krishna_msg'){
            const text = e.data.text || '';
            const payload = {text};
            fetch('/krishna_chat', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)}).catch(()=>{});
          }
        });
        </script>
        """,
        unsafe_allow_html=True,
    )

def render_pipeline_history_chart():
    """Render pipeline execution history"""
    
    # Mock pipeline history data
    history = st.session_state.state_manager.get_pipeline_history(limit=10)
    
    if not history:
        st.info("No pipeline history available")
        return
    
    # Create timeline chart
    fig = px.timeline(
        history,
        x_start="start_time",
        x_end="end_time", 
        y="project_name",
        color="status",
        title="Recent Pipeline Executions"
    )
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

def render_settings():
    """Render settings page"""
    st.subheader("⚙️ Platform Settings")
    
    # Local/Cloud mode toggle
    st.subheader("🌐 Execution Mode")
    mode = st.radio(
        "Select execution mode:",
        ["Local Only", "Hybrid (Local + Cloud)", "Cloud Enhanced"],
        help="Local mode uses only local resources. Hybrid allows optional cloud services. Cloud Enhanced uses cloud AI models."
    )
    
    if mode != "Local Only":
        st.subheader("☁️ Cloud Configuration")
        
        cloud_provider = st.selectbox(
            "Cloud Provider",
            ["AWS", "Azure", "GCP", "On-Premises"]
        )
        
        if cloud_provider != "On-Premises":
            st.text_input("API Key", type="password")
            st.text_input("Region", value="us-east-1")
    
    # AI Model settings
    st.subheader("🤖 AI Model Configuration")
    
    local_model = st.selectbox(
        "Local LLM (via Ollama)",
        [
            "llama3:8b", "llama3.1:8b", "llama2", "codellama", "mistral", "mixtral:8x7b",
            "neural-chat", "phi3", "qwen2:7b", "gemma:7b", "llava:13b"
        ]
    )
    
    if mode != "Local Only":
        provider = st.selectbox(
            "Cloud Provider",
            [
                "OpenAI", "Anthropic", "Google (Gemini)", "Azure OpenAI", "Groq",
                "Mistral", "Cohere", "Together AI", "OpenRouter", "Perplexity",
                "Fireworks AI", "xAI (Grok)", "DeepSeek", "Custom API"
            ]
        )

        model_options = {
            "OpenAI": [
                "gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "o3-mini", "o4-mini", "gpt-3.5-turbo"
            ],
            "Anthropic": [
                "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-3.5-sonnet"
            ],
            "Google (Gemini)": [
                "gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"
            ],
            "Azure OpenAI": [
                "your-deployment-name"
            ],
            "Groq": [
                "llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768", "gemma-7b-it"
            ],
            "Mistral": [
                "mistral-tiny", "mistral-small", "mistral-medium", "open-mixtral-8x7b"
            ],
            "Cohere": [
                "command", "command-r", "command-r-plus"
            ],
            "Together AI": [
                "meta-llama/Meta-Llama-3-70B-Instruct", "mistralai/Mixtral-8x7B-Instruct-v0.1"
            ],
            "OpenRouter": [
                "openrouter/auto", "anthropic/claude-3.5-sonnet", "meta-llama/llama-3.1-70b-instruct"
            ],
            "Perplexity": [
                "sonar-small-online", "sonar-medium-online", "sonar-large-online"
            ],
            "Fireworks AI": [
                "accounts/fireworks/models/llama-v3-70b-instruct", "accounts/fireworks/models/mixtral-8x7b-instruct"
            ],
            "xAI (Grok)": [
                "grok-beta"
            ],
            "DeepSeek": [
                "deepseek-chat", "deepseek-coder"
            ],
            "Custom API": [
                "model-name"
            ]
        }

        cloud_model = st.selectbox(
            "Cloud AI Model",
            model_options.get(provider, ["model-name"])
        )
        st.caption("Tip: For Custom API and some providers, set the endpoint in Settings or config.")
    
    # Security settings
    st.subheader("🔒 Security Configuration")
    
    st.checkbox("Enable vulnerability auto-patching", value=True)
    st.checkbox("Strict compliance mode", value=False)
    st.checkbox("Enable audit logging", value=True)
    
    # Save settings
    if st.button("💾 Save Settings", type="primary"):
        st.success("Settings saved successfully!")
