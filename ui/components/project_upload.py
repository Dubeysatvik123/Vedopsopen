"""
Project Upload Component
Handles code ingestion UI for Varuna agent
"""

import streamlit as st
import tempfile
import zipfile
from pathlib import Path
import asyncio
import json

def render_project_upload():
    """Render project upload interface"""
    
    st.subheader("📁 Project Upload & Analysis")
    st.write("Upload your project for AI-powered DevSecOps analysis")
    
    # Upload method selection
    upload_method = st.radio(
        "Select upload method:",
        ["ZIP Upload", "Git Repository", "Local Directory"],
        horizontal=True
    )
    
    project_data = {}
    
    if upload_method == "ZIP Upload":
        uploaded_file = st.file_uploader(
            "Choose a ZIP file",
            type=['zip'],
            help="Upload a ZIP file containing your project source code"
        )
        
        if uploaded_file:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                project_data = {
                    'source_type': 'zip',
                    'zip_path': tmp_file.name,
                    'project_name': uploaded_file.name.replace('.zip', '')
                }
    
    elif upload_method == "Git Repository":
        git_url = st.text_input(
            "Git Repository URL",
            placeholder="https://github.com/username/repository.git",
            help="Enter the URL of your Git repository"
        )
        
        project_name = st.text_input(
            "Project Name",
            placeholder="my-awesome-project",
            help="Enter a name for your project"
        )
        
        if git_url and project_name:
            project_data = {
                'source_type': 'git',
                'git_url': git_url,
                'project_name': project_name
            }
    
    elif upload_method == "Local Directory":
        local_path = st.text_input(
            "Local Directory Path",
            placeholder="/path/to/your/project",
            help="Enter the full path to your local project directory"
        )
        
        project_name = st.text_input(
            "Project Name",
            placeholder="my-local-project",
            help="Enter a name for your project"
        )
        
        if local_path and project_name:
            if Path(local_path).exists():
                project_data = {
                    'source_type': 'local',
                    'local_path': local_path,
                    'project_name': project_name
                }
            else:
                st.error("Directory does not exist!")
    
    # Deployment preferences
    if project_data:
        st.divider()
        st.subheader("🚀 Deployment Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            target_env = st.selectbox(
                "Target Environment",
                ["Local Development", "Staging", "Production"],
                help="Select the target deployment environment"
            )
            
            expected_traffic = st.selectbox(
                "Expected Traffic",
                ["Low (< 1K users)", "Medium (1K-10K users)", "High (10K+ users)"],
                help="Estimate your expected user traffic"
            )
        
        with col2:
            cloud_provider = st.selectbox(
                "Cloud Provider (Optional)",
                ["None (Local Only)", "AWS", "Azure", "GCP", "On-Premises"],
                help="Select cloud provider for deployment"
            )
            
            auto_deploy = st.checkbox(
                "Auto-deploy after successful pipeline",
                value=False,
                help="Automatically deploy if all checks pass"
            )
        
        # Add preferences to project data
        project_data.update({
            'target_env': target_env,
            'expected_traffic': expected_traffic,
            'cloud_provider': cloud_provider,
            'auto_deploy': auto_deploy
        })
        
        # Start analysis button
        st.divider()
        
        if st.button("🔍 Start Analysis", type="primary", use_container_width=True):
            start_analysis(project_data)

def start_analysis(project_data: dict):
    """Start the DevSecOps pipeline analysis"""
    
    # Initialize progress tracking
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    with progress_placeholder.container():
        st.info("🚀 Starting VedOps pipeline analysis...")
        progress_bar = st.progress(0)
        
        # Start pipeline
        pipeline_id = st.session_state.state_manager.start_pipeline(
            project_data['project_name'], 
            project_data
        )
        
        # Update session state
        st.session_state.current_pipeline_id = pipeline_id
        st.session_state.analysis_started = True
        
        # Show initial progress
        progress_bar.progress(10)
        
        with status_placeholder.container():
            st.success("✅ Pipeline started successfully!")
            st.write(f"**Pipeline ID:** {pipeline_id}")
            st.write(f"**Project:** {project_data['project_name']}")
            st.write("**Status:** Initializing Varuna agent...")
            
            # Execute Varuna analysis
            try:
                from agents.varuna import VarunaAgent
                varuna = VarunaAgent()
                
                with st.spinner("🌊 Varuna is analyzing your project..."):
                    result = varuna.execute(project_data)
                
                progress_bar.progress(100)
                
                # Display results
                display_analysis_results(result)
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")
                st.session_state.state_manager.current_pipeline['status'] = 'failed'

def display_analysis_results(result: dict):
    """Display Varuna analysis results"""
    
    st.success("🎉 Project analysis completed!")
    
    # Project overview
    st.subheader("📊 Project Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Languages Detected", len(result['languages']))
    
    with col2:
        st.metric("Dependencies", sum(len(deps) for deps in result['dependencies'].values()))
    
    with col3:
        st.metric("Complexity", result['estimated_complexity'].title())
    
    with col4:
        st.metric("Est. Build Time", f"{result['build_time_estimate']} min")
    
    # Tech stack
    st.subheader("🛠️ Technology Stack")
    tech_cols = st.columns(min(len(result['tech_stack']), 5))
    for i, tech in enumerate(result['tech_stack'][:5]):
        with tech_cols[i % 5]:
            st.info(f"**{tech.title()}**")
    
    # Languages breakdown
    if result['languages']:
        st.subheader("💻 Language Distribution")
        lang_data = result['languages']
        
        # Create a simple bar chart representation
        for lang, percentage in sorted(lang_data.items(), key=lambda x: x[1], reverse=True):
            st.write(f"**{lang.title()}:** {percentage:.1f}%")
            st.progress(percentage / 100)
    
    # Dependencies
    if result['dependencies']:
        st.subheader("📦 Dependencies")
        for pkg_manager, deps in result['dependencies'].items():
            with st.expander(f"{pkg_manager.title()} ({len(deps)} packages)"):
                st.write(", ".join(deps[:20]))  # Show first 20 dependencies
                if len(deps) > 20:
                    st.write(f"... and {len(deps) - 20} more")
    
    # Security notes
    if result['security_notes']:
        st.subheader("🔒 Security Considerations")
        for note in result['security_notes']:
            st.warning(note)
    
    # Recommendations
    if result['recommendations']:
        st.subheader("💡 Recommendations")
        for rec in result['recommendations']:
            st.info(rec)
    
    # Architecture info
    st.subheader("🏗️ Architecture Analysis")
    arch = result['architecture']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Type:** {arch['type'].replace('_', ' ').title()}")
        if arch['entry_points']:
            st.write(f"**Entry Points:** {', '.join(arch['entry_points'])}")
    
    with col2:
        if arch['patterns']:
            st.write(f"**Patterns:** {', '.join(arch['patterns'])}")
        if arch['test_directories']:
            st.write(f"**Tests:** {', '.join(arch['test_directories'])}")
    
    # Build configuration
    st.subheader("⚙️ Build Configuration")
    build_config = result['build_config']
    
    st.code(f"""
Build Tool: {build_config['build_tool']}
Port: {build_config['port']}
Health Check: {build_config.get('health_check', 'Not configured')}

Dependencies Install:
{chr(10).join(f"  - {cmd}" for cmd in build_config['dependencies_install'])}

Build Commands:
{chr(10).join(f"  - {cmd}" for cmd in build_config['build_commands']) if build_config['build_commands'] else "  - No build commands needed"}

Test Commands:
{chr(10).join(f"  - {cmd}" for cmd in build_config['test_commands']) if build_config['test_commands'] else "  - No test commands configured"}
    """)
    
    # Next steps
    st.divider()
    st.subheader("🚀 Next Steps")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔥 Continue to Build (Agni)", type="primary", use_container_width=True):
            st.info("Agni agent will be available in the next update!")
    
    with col2:
        if st.button("📋 View Full Report", use_container_width=True):
            st.json(result)
