import streamlit as st
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from utils.llm_config import LLMConfigManager
from utils.orchestrator import VedOpsOrchestrator
from utils.database import DatabaseManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="VedOps - AI-Powered DevSecOps Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for futuristic theme
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .agent-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        color: white;
    }
    .status-success { color: #00ff00; }
    .status-error { color: #ff4444; }
    .status-warning { color: #ffaa00; }
    .status-info { color: #00aaff; }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'llm_config' not in st.session_state:
        st.session_state.llm_config = None
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = None
    if 'pipeline_running' not in st.session_state:
        st.session_state.pipeline_running = False
    if 'pipeline_results' not in st.session_state:
        st.session_state.pipeline_results = {}

def main():
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 VedOps</h1>
        <h3>AI-Powered DevSecOps Platform</h3>
        <p>Autonomous agents for complete software delivery lifecycle</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # LLM Configuration Section
        st.subheader("🤖 LLM Configuration")
        llm_config_manager = LLMConfigManager()
        
        # Provider selection
        provider = st.selectbox(
            "Select LLM Provider",
            [
                "OpenAI", "Anthropic", "Google", "Ollama (Local)", "Azure OpenAI",
                "Groq", "Mistral", "Together AI", "OpenRouter", "Perplexity",
                "Fireworks AI", "xAI (Grok)", "DeepSeek", "Custom API"
            ],
            help="Choose your preferred LLM provider"
        )
        
        # Model selection based on provider (includes free-tier friendly options like Groq, Gemini Flash)
        if provider == "OpenAI":
            model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "o3-mini", "o4-mini", "gpt-3.5-turbo"])
            api_key = st.text_input("OpenAI API Key", type="password")
        elif provider == "Anthropic":
            model = st.selectbox("Model", ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-3.5-sonnet"])
            api_key = st.text_input("Anthropic API Key", type="password")
        elif provider == "Google":
            model = st.selectbox("Model", ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"])
            api_key = st.text_input("Google API Key", type="password")
        elif provider == "Ollama (Local)":
            model = st.selectbox("Model", [
                "llama3:8b", "llama3.1:8b", "llama2", "codellama", "mistral", "mixtral:8x7b",
                "neural-chat", "phi3", "qwen2:7b", "gemma:7b", "llava:13b"
            ])
            api_key = None
            ollama_url = st.text_input("Ollama URL", value="http://localhost:11434")
        elif provider == "Azure OpenAI":
            model = st.text_input("Deployment Name")
            api_key = st.text_input("Azure OpenAI API Key", type="password")
            endpoint = st.text_input("Azure OpenAI Endpoint")
        elif provider == "Groq":
            model = st.selectbox("Model", ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768", "gemma-7b-it"])
            api_key = st.text_input("Groq API Key", type="password")
            endpoint = st.text_input("Groq Endpoint", value="https://api.groq.com/openai/v1")
        elif provider == "Mistral":
            model = st.selectbox("Model", ["mistral-tiny", "mistral-small", "mistral-medium", "open-mixtral-8x7b"])
            api_key = st.text_input("Mistral API Key", type="password")
            endpoint = st.text_input("Mistral Endpoint", value="https://api.mistral.ai/v1")
        elif provider == "Together AI":
            model = st.selectbox("Model", ["meta-llama/Meta-Llama-3-70B-Instruct", "mistralai/Mixtral-8x7B-Instruct-v0.1"])
            api_key = st.text_input("Together AI Key", type="password")
            endpoint = st.text_input("Together Endpoint", value="https://api.together.xyz/v1")
        elif provider == "OpenRouter":
            model = st.selectbox("Model", ["openrouter/auto", "anthropic/claude-3.5-sonnet", "meta-llama/llama-3.1-70b-instruct"])
            api_key = st.text_input("OpenRouter API Key", type="password")
            endpoint = st.text_input("OpenRouter Endpoint", value="https://openrouter.ai/api/v1")
        elif provider == "Perplexity":
            model = st.selectbox("Model", ["sonar-small-online", "sonar-medium-online", "sonar-large-online"])
            api_key = st.text_input("Perplexity API Key", type="password")
            endpoint = st.text_input("Perplexity Endpoint", value="https://api.perplexity.ai")
        elif provider == "Fireworks AI":
            model = st.selectbox("Model", ["accounts/fireworks/models/llama-v3-70b-instruct", "accounts/fireworks/models/mixtral-8x7b-instruct"])
            api_key = st.text_input("Fireworks API Key", type="password")
            endpoint = st.text_input("Fireworks Endpoint", value="https://api.fireworks.ai/inference/v1")
        elif provider == "xAI (Grok)":
            model = st.selectbox("Model", ["grok-beta"])
            api_key = st.text_input("xAI API Key", type="password")
            endpoint = st.text_input("xAI Endpoint", value="https://api.x.ai/v1")
        elif provider == "DeepSeek":
            model = st.selectbox("Model", ["deepseek-chat", "deepseek-coder"])
            api_key = st.text_input("DeepSeek API Key", type="password")
            endpoint = st.text_input("DeepSeek Endpoint", value="https://api.deepseek.com")
        else:  # Custom API
            model = st.text_input("Model Name")
            api_key = st.text_input("API Key", type="password")
            endpoint = st.text_input("API Endpoint")
        
        # Cloud credentials (infra)
        st.subheader("🔐 Cloud Credentials (for provisioning)")
        cloud_creds = {}
        cloud_provider_for_infra = st.selectbox("Cloud for Infrastructure", ["None", "AWS", "Azure", "GCP", "DigitalOcean"])
        if cloud_provider_for_infra == "AWS":
            cloud_creds["AWS_ACCESS_KEY_ID"] = st.text_input("AWS Access Key ID")
            cloud_creds["AWS_SECRET_ACCESS_KEY"] = st.text_input("AWS Secret Access Key", type="password")
            cloud_creds["AWS_DEFAULT_REGION"] = st.text_input("AWS Region", value="us-east-1")
        elif cloud_provider_for_infra == "Azure":
            cloud_creds["ARM_CLIENT_ID"] = st.text_input("Azure Client ID")
            cloud_creds["ARM_CLIENT_SECRET"] = st.text_input("Azure Client Secret", type="password")
            cloud_creds["ARM_TENANT_ID"] = st.text_input("Azure Tenant ID")
            cloud_creds["ARM_SUBSCRIPTION_ID"] = st.text_input("Azure Subscription ID")
        elif cloud_provider_for_infra == "GCP":
            cloud_creds["GOOGLE_APPLICATION_CREDENTIALS_JSON"] = st.text_area("GCP Service Account JSON")
        elif cloud_provider_for_infra == "DigitalOcean":
            cloud_creds["DO_TOKEN"] = st.text_input("DigitalOcean API Token", type="password")

        # Save configuration
        if st.button("💾 Save LLM Configuration"):
            # Do not persist API keys in the config file; read from environment at runtime
            config = {
                "provider": provider,
                "model": model,
                "timestamp": datetime.now().isoformat()
            }
            
            if provider == "Ollama (Local)":
                config["ollama_url"] = ollama_url
            elif provider in [
                "Azure OpenAI", "Groq", "Mistral", "Together AI", "OpenRouter",
                "Perplexity", "Fireworks AI", "xAI (Grok)", "DeepSeek", "Custom API"
            ]:
                config["endpoint"] = endpoint
            
            if llm_config_manager.save_config(config):
                st.success("✅ LLM Configuration saved successfully!")
                st.session_state.llm_config = config
                st.session_state.cloud_credentials = cloud_creds
            else:
                st.error("❌ Failed to save configuration")
        
        # Load existing configuration
        if st.button("📂 Load Configuration"):
            config = llm_config_manager.load_config()
            if config:
                st.session_state.llm_config = config
                st.success("✅ Configuration loaded successfully!")
            else:
                st.warning("⚠️ No saved configuration found")
        
        st.divider()
        
        # Pipeline Configuration
        st.subheader("🔧 Pipeline Settings")
        
        parallel_execution = st.checkbox("Enable Parallel Execution", value=True)
        auto_rollback = st.checkbox("Auto Rollback on Failure", value=True)
        notification_webhook = st.text_input("Notification Webhook URL", placeholder="https://hooks.slack.com/...")
        
        # Environment Selection
        target_env = st.selectbox(
            "Target Environment",
            ["Local", "Development", "Staging", "Production"],
            help="Select deployment target"
        )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📋 Project Input")
        
        # Project input methods
        input_method = st.radio(
            "Choose input method:",
            ["Upload ZIP", "Git Repository", "Local Folder"],
            horizontal=True
        )
        
        project_data = None
        
        if input_method == "Upload ZIP":
            uploaded_file = st.file_uploader(
                "Upload your project ZIP file",
                type=['zip'],
                help="Upload a ZIP file containing your source code"
            )
            if uploaded_file:
                project_data = {"type": "zip", "file": uploaded_file}
        
        elif input_method == "Git Repository":
            repo_url = st.text_input(
                "Repository URL",
                placeholder="https://github.com/username/repo.git"
            )
            branch = st.text_input("Branch", value="main")
            if repo_url:
                project_data = {"type": "git", "url": repo_url, "branch": branch}
        
        else:  # Local Folder
            folder_path = st.text_input(
                "Local Folder Path",
                placeholder="/path/to/your/project"
            )
            if folder_path and os.path.exists(folder_path):
                project_data = {"type": "local", "path": folder_path}
        
        # Infrastructure requirements
        st.subheader("🏗️ Infrastructure Requirements")
        
        col_infra1, col_infra2 = st.columns(2)
        
        with col_infra1:
            expected_traffic = st.selectbox(
                "Expected Traffic",
                ["Low (< 1K requests/day)", "Medium (1K-10K requests/day)", 
                 "High (10K-100K requests/day)", "Very High (> 100K requests/day)"]
            )
            
            scaling_type = st.selectbox(
                "Scaling Strategy",
                ["Manual", "Auto-scaling", "Predictive Scaling"]
            )
        
        with col_infra2:
            cloud_provider = st.selectbox(
                "Cloud Provider",
                ["Local/On-Premise", "AWS", "Azure", "Google Cloud", "DigitalOcean"]
            )
            
            resource_tier = st.selectbox(
                "Resource Tier",
                ["Minimal", "Standard", "High Performance", "Enterprise"]
            )
        
        # Start pipeline button
        if st.button("🚀 Start DevSecOps Pipeline", type="primary", disabled=st.session_state.pipeline_running):
            if not st.session_state.llm_config:
                st.error("❌ Please configure LLM settings first!")
            elif not project_data:
                st.error("❌ Please provide project input!")
            else:
                start_pipeline(project_data, {
                    "traffic": expected_traffic,
                    "scaling": scaling_type,
                    "cloud": cloud_provider,
                    "resources": resource_tier,
                    "parallel": parallel_execution,
                    "auto_rollback": auto_rollback,
                    "webhook": notification_webhook,
                    "environment": target_env,
                    "cloud_credentials": st.session_state.get('cloud_credentials', {})
                })
    
    with col2:
        st.header("📊 Pipeline Status")
        
        if st.session_state.pipeline_running:
            display_pipeline_progress()
        else:
            st.info("Pipeline ready to start")
        
        # Agent status
        st.subheader("🤖 Agent Status")
        agents = [
            "Varuna (Code Analysis)",
            "Agni (Build & Docker)",
            "Yama (Security)",
            "Vayu (Deployment)",
            "Hanuman (Testing)",
            "Krishna (Governance)",
            "Observability Agent",
            "Optimization Agent"
        ]
        
        for agent in agents:
            status = get_agent_status(agent)
            st.markdown(f"**{agent}**: <span class='status-{status['type']}'>{status['message']}</span>", 
                       unsafe_allow_html=True)
    
    # Results section
    if st.session_state.pipeline_results:
        st.header("📈 Pipeline Results")
        display_pipeline_results()

    # Krishna principal DevSecOps consultant chat (anchor)
    st.markdown("<a id='krishna'></a>", unsafe_allow_html=True)
    render_krishna_chat()

def start_pipeline(project_data: Dict[str, Any], config: Dict[str, Any]):
    """Start the DevSecOps pipeline"""
    try:
        st.session_state.pipeline_running = True
        
        # Initialize orchestrator with LLM config
        orchestrator = VedOpsOrchestrator(
            llm_config=st.session_state.llm_config,
            pipeline_config=config
        )
        
        st.session_state.orchestrator = orchestrator
        
        # Start pipeline execution
        with st.spinner("Initializing pipeline..."):
            results = orchestrator.execute_pipeline(project_data)
            st.session_state.pipeline_results = results
        
        st.success("✅ Pipeline completed successfully!")
        
    except Exception as e:
        st.error(f"❌ Pipeline failed: {str(e)}")
        logger.error(f"Pipeline execution failed: {e}")
    finally:
        st.session_state.pipeline_running = False

def display_pipeline_progress():
    """Display real-time pipeline progress"""
    if st.session_state.orchestrator:
        progress = st.session_state.orchestrator.get_progress()
        
        # Progress bar
        progress_bar = st.progress(progress['percentage'] / 100)
        st.write(f"Progress: {progress['percentage']:.1f}%")
        
        # Current stage
        st.write(f"**Current Stage**: {progress['current_stage']}")
        
        # Live logs
        st.subheader("📝 Live Logs")
        log_container = st.container()
        
        with log_container:
            for log_entry in progress.get('logs', []):
                timestamp = log_entry.get('timestamp', '')
                level = log_entry.get('level', 'INFO')
                message = log_entry.get('message', '')
                
                if level == 'ERROR':
                    st.error(f"[{timestamp}] {message}")
                elif level == 'WARNING':
                    st.warning(f"[{timestamp}] {message}")
                else:
                    st.info(f"[{timestamp}] {message}")

def get_agent_status(agent_name: str) -> Dict[str, str]:
    """Get current status of an agent"""
    if st.session_state.orchestrator:
        return st.session_state.orchestrator.get_agent_status(agent_name)
    return {"type": "info", "message": "Idle"}

def display_pipeline_results():
    """Display comprehensive pipeline results"""
    results = st.session_state.pipeline_results
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Security Score", f"{results.get('security_score', 0)}/100")
    with col2:
        st.metric("Build Time", f"{results.get('build_time', 0)}s")
    with col3:
        st.metric("Test Coverage", f"{results.get('test_coverage', 0)}%")
    with col4:
        st.metric("Performance Score", f"{results.get('performance_score', 0)}/100")
    # Show endpoint URL if available
    endpoint_url = (
        results.get('provision', {}).get('endpoint_url')
        or (results.get('deployment', {}).get('deployment', {}).get('endpoints', [{}])[0].get('url')
            if isinstance(results.get('deployment', {}).get('deployment', {}), dict) else None)
    )
    if endpoint_url:
        st.success(f"🌐 Endpoint URL: {endpoint_url}")
    
    # Detailed results tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Analysis", "🔒 Security", "🚀 Deployment", "📊 Reports"])
    
    with tab1:
        st.subheader("Code Analysis Results")
        if 'analysis' in results:
            st.json(results['analysis'])
    
    with tab2:
        st.subheader("Security Scan Results")
        if 'security' in results:
            st.json(results['security'])
    
    with tab3:
        st.subheader("Deployment Status")
        if 'deployment' in results:
            st.json(results['deployment'])
    
    with tab4:
        st.subheader("Generated Reports")
        if 'reports' in results:
            for report_name, report_data in results['reports'].items():
                st.download_button(
                    f"Download {report_name}",
                    data=json.dumps(report_data, indent=2),
                    file_name=f"{report_name}.json",
                    mime="application/json"
                )

def render_krishna_chat():
    """Floating-style Krishna chatbot section using Streamlit chat API."""
    st.subheader("💬 Krishna – Principal DevSecOps Consultant")
    st.caption("Ask about security, compliance, infra, CI/CD, testing, observability, costs, and SRE best practices.")

    if 'krishna_messages' not in st.session_state:
        st.session_state.krishna_messages = [
            {"role": "system", "content": (
                "You are Krishna, a principal DevSecOps consultant. Provide concise, actionable, "
                "production-grade guidance spanning code, build, containerization, security, compliance, "
                "infrastructure (Kubernetes/Terraform/cloud), CI/CD, testing, observability, cost, and SRE. "
                "When helpful, include specific commands and configuration snippets."
            )}
        ]

    # Display history (excluding system)
    for msg in st.session_state.krishna_messages:
        if msg["role"] == "system":
            continue
        with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask Krishna about your DevSecOps needs…", key="krishna_input")
    if user_input:
        st.session_state.krishna_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        try:
            # Use configured LLM client
            llm_config_manager = LLMConfigManager()
            llm_cfg = st.session_state.get('llm_config') or llm_config_manager.load_config()
            llm_client = llm_config_manager.get_llm_client(llm_cfg)

            # Build conversation prompt
            history = "\n\n".join([
                ("User: " + m["content"]) if m["role"] == "user" else ("Assistant: " + m["content"]) 
                for m in st.session_state.krishna_messages if m["role"] != "system"
            ])
            system = st.session_state.krishna_messages[0]["content"]
            prompt = f"{system}\n\n{history}\n\nAssistant:"

            response = llm_client.invoke(prompt)
            text = getattr(response, 'content', None) or str(response)
        except Exception as e:
            text = f"Sorry, I encountered an error: {e}"

        st.session_state.krishna_messages.append({"role": "assistant", "content": text})
        with st.chat_message("assistant"):
            st.markdown(text)

if __name__ == "__main__":
    main()
