"""
Build Status Component
Displays Agni build progress and results
"""

import streamlit as st
import json
from pathlib import Path
import plotly.graph_objects as go

def render_build_status():
    """Render build status and results"""
    
    st.subheader("🔥 Build & Containerization Status")
    
    # Check if we have build artifacts
    artifacts_dir = Path("artifacts")
    build_files = list(artifacts_dir.glob("build_artifacts_*.json"))
    
    if not build_files:
        st.info("No build artifacts found. Run a project analysis first.")
        return
    
    # Load latest build artifacts
    latest_build = max(build_files, key=lambda x: x.stat().st_mtime)
    
    with open(latest_build, 'r') as f:
        build_data = json.load(f)
    
    # Build overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Build Status",
            "Success" if build_data.get('build_time', 0) > 0 else "Failed",
            delta="Completed" if build_data.get('build_time', 0) > 0 else "Error"
        )
    
    with col2:
        build_time = build_data.get('build_time', 0)
        st.metric(
            "Build Time",
            f"{build_time:.1f}s" if build_time > 0 else "N/A"
        )
    
    with col3:
        image_size = build_data.get('image_size', 0)
        if image_size > 0:
            size_mb = image_size / (1024 * 1024)
            st.metric("Image Size", f"{size_mb:.1f} MB")
        else:
            st.metric("Image Size", "N/A")
    
    with col4:
        st.metric(
            "Multi-Stage",
            "Yes" if build_data.get('multi_stage', False) else "No"
        )
    
    st.divider()
    
    # Build details tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Overview", "🐳 Docker", "☸️ Kubernetes", "📊 Optimization"])
    
    with tab1:
        render_build_overview(build_data)
    
    with tab2:
        render_docker_details(build_data)
    
    with tab3:
        render_kubernetes_details(build_data)
    
    with tab4:
        render_optimization_notes(build_data)

def render_build_overview(build_data: dict):
    """Render build overview"""
    
    st.subheader("🏗️ Build Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Image Information:**")
        st.write(f"- **Name:** {build_data.get('image_name', 'Unknown')}")
        st.write(f"- **Tag:** {build_data.get('image_tag', 'latest')}")
        st.write(f"- **Build Type:** {'Multi-stage' if build_data.get('multi_stage') else 'Single-stage'}")
        
        if build_data.get('build_timestamp'):
            st.write(f"- **Built:** {build_data['build_timestamp']}")
    
    with col2:
        st.write("**Generated Files:**")
        
        if build_data.get('dockerfile_path'):
            st.write("✅ Dockerfile")
        
        if build_data.get('docker_compose_path'):
            st.write("✅ docker-compose.yml")
        
        k8s_manifests = build_data.get('kubernetes_manifests', {})
        if k8s_manifests:
            st.write(f"✅ Kubernetes manifests ({len(k8s_manifests)} files)")
    
    # Build logs
    if build_data.get('build_logs'):
        st.subheader("📝 Build Logs")
        
        with st.expander("View Build Logs", expanded=False):
            logs = build_data['build_logs']
            if isinstance(logs, list):
                for log in logs[-20:]:  # Show last 20 log entries
                    st.code(log, language=None)
            else:
                st.code(str(logs), language=None)

def render_docker_details(build_data: dict):
    """Render Docker-specific details"""
    
    st.subheader("🐳 Docker Configuration")
    
    # Show Dockerfile if available
    dockerfile_path = Path("artifacts/Dockerfile")
    if dockerfile_path.exists():
        st.subheader("📄 Generated Dockerfile")
        
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()
        
        st.code(dockerfile_content, language='dockerfile')
    
    # Show docker-compose if available
    compose_path = Path("artifacts/docker-compose.yml")
    if compose_path.exists():
        st.subheader("🐙 Docker Compose Configuration")
        
        with open(compose_path, 'r') as f:
            compose_content = f.read()
        
        st.code(compose_content, language='yaml')
        
        st.info("💡 Use `docker-compose up -d` to start all services")
    
    # Docker commands
    st.subheader("🚀 Quick Start Commands")
    
    image_name = build_data.get('image_name', 'app')
    image_tag = build_data.get('image_tag', 'latest')
    
    st.code(f"""
# Build the image
docker build -t {image_name}:{image_tag} .

# Run the container
docker run -p 8000:8000 {image_name}:{image_tag}

# Run with docker-compose (if available)
docker-compose up -d
    """, language='bash')

def render_kubernetes_details(build_data: dict):
    """Render Kubernetes deployment details"""
    
    st.subheader("☸️ Kubernetes Deployment")
    
    k8s_manifests = build_data.get('kubernetes_manifests', {})
    
    if not k8s_manifests:
        st.info("No Kubernetes manifests generated")
        return
    
    # Show available manifests
    st.write("**Generated Manifests:**")
    for manifest_type in k8s_manifests.keys():
        st.write(f"- {manifest_type}.yaml")
    
    # Show manifest contents
    manifest_tabs = st.tabs([name.title() for name in k8s_manifests.keys()])
    
    for i, (manifest_type, _) in enumerate(k8s_manifests.items()):
        with manifest_tabs[i]:
            manifest_path = Path(f"artifacts/k8s/{manifest_type}.yaml")
            
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifest_content = f.read()
                
                st.code(manifest_content, language='yaml')
    
    # Deployment commands
    st.subheader("🚀 Deployment Commands")
    
    st.code("""
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n <project>-ns

# Get service URL
kubectl get svc -n <project>-ns

# View logs
kubectl logs -f deployment/<project>-deployment -n <project>-ns
    """, language='bash')

def render_optimization_notes(build_data: dict):
    """Render optimization recommendations"""
    
    st.subheader("💡 Optimization Recommendations")
    
    optimization_notes = build_data.get('optimization_notes', [])
    
    if not optimization_notes:
        st.info("No optimization notes available")
        return
    
    # Categorize recommendations
    security_notes = []
    performance_notes = []
    size_notes = []
    general_notes = []
    
    for note in optimization_notes:
        note_lower = note.lower()
        if any(word in note_lower for word in ['security', 'user', 'root', 'vulnerabilit']):
            security_notes.append(note)
        elif any(word in note_lower for word in ['performance', 'cache', 'speed', 'fast']):
            performance_notes.append(note)
        elif any(word in note_lower for word in ['size', 'image', 'alpine', 'slim']):
            size_notes.append(note)
        else:
            general_notes.append(note)
    
    # Display categorized recommendations
    if security_notes:
        st.subheader("🔒 Security Recommendations")
        for note in security_notes:
            st.warning(f"🛡️ {note}")
    
    if performance_notes:
        st.subheader("⚡ Performance Recommendations")
        for note in performance_notes:
            st.info(f"🚀 {note}")
    
    if size_notes:
        st.subheader("📦 Size Optimization")
        for note in size_notes:
            st.info(f"📉 {note}")
    
    if general_notes:
        st.subheader("🔧 General Recommendations")
        for note in general_notes:
            st.info(f"💡 {note}")
    
    # Build metrics visualization
    if build_data.get('image_size', 0) > 0:
        st.subheader("📊 Build Metrics")
        
        # Create a simple metrics chart
        metrics = {
            'Build Time (s)': build_data.get('build_time', 0),
            'Image Size (MB)': build_data.get('image_size', 0) / (1024 * 1024),
            'Optimization Score': min(100, max(0, 100 - len(optimization_notes) * 10))
        }
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(metrics.keys()),
                y=list(metrics.values()),
                marker_color=['#1f77b4', '#ff7f0e', '#2ca02c']
            )
        ])
        
        fig.update_layout(
            title="Build Performance Metrics",
            yaxis_title="Value",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
