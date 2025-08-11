"""
Security Dashboard Component
Displays Yama security scan results and compliance status
"""

import streamlit as st
import json
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import pandas as pd

def render_security_dashboard():
    """Render security assessment dashboard"""
    
    st.subheader("🛡️ Security & Compliance Dashboard")
    
    # Check if we have security reports
    artifacts_dir = Path("artifacts")
    security_files = list(artifacts_dir.glob("security_report_*.json"))
    
    if not security_files:
        st.info("No security reports found. Run a security scan first.")
        return
    
    # Load latest security report
    latest_report = max(security_files, key=lambda x: x.stat().st_mtime)
    
    with open(latest_report, 'r') as f:
        security_data = json.load(f)
    
    # Security overview metrics
    render_security_overview(security_data)
    
    st.divider()
    
    # Detailed tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Vulnerabilities", 
        "📦 Dependencies", 
        "🐳 Container Security", 
        "📋 Compliance", 
        "🔧 Recommendations"
    ])
    
    with tab1:
        render_vulnerabilities_tab(security_data)
    
    with tab2:
        render_dependencies_tab(security_data)
    
    with tab3:
        render_container_security_tab(security_data)
    
    with tab4:
        render_compliance_tab(security_data)
    
    with tab5:
        render_recommendations_tab(security_data)

def render_security_overview(security_data: dict):
    """Render security overview metrics"""
    
    summary = security_data.get('summary', {})
    
    # Main metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        score = security_data.get('overall_score', 'Unknown')
        risk_level = security_data.get('risk_level', 'unknown')
        
        # Color based on score
        if score in ['A+', 'A']:
            delta_color = "normal"
        elif score in ['B', 'C']:
            delta_color = "off"
        else:
            delta_color = "inverse"
        
        st.metric(
            "Security Score",
            score,
            delta=risk_level.title(),
            delta_color=delta_color
        )
    
    with col2:
        total_vulns = summary.get('total_vulnerabilities', 0)
        st.metric(
            "Total Issues",
            total_vulns,
            delta=f"{summary.get('critical_count', 0)} Critical"
        )
    
    with col3:
        compliance_score = security_data.get('compliance_status', {}).get('overall_compliance', 0)
        st.metric(
            "Compliance",
            f"{compliance_score}%",
            delta="OWASP + CIS"
        )
    
    with col4:
        patchable = summary.get('patchable_count', 0)
        st.metric(
            "Auto-Fixable",
            patchable,
            delta=f"{len(security_data.get('auto_patches', []))} patches"
        )
    
    with col5:
        tools_used = len(security_data.get('tools_used', []))
        st.metric(
            "Scan Tools",
            tools_used,
            delta="Active"
        )
    
    # Vulnerability distribution chart
    if summary.get('total_vulnerabilities', 0) > 0:
        st.subheader("📊 Vulnerability Distribution")
        
        severity_data = {
            'Critical': summary.get('critical_count', 0),
            'High': summary.get('high_count', 0),
            'Medium': summary.get('medium_count', 0),
            'Low': summary.get('low_count', 0)
        }
        
        # Remove zero values
        severity_data = {k: v for k, v in severity_data.items() if v > 0}
        
        if severity_data:
            fig = go.Figure(data=[
                go.Pie(
                    labels=list(severity_data.keys()),
                    values=list(severity_data.values()),
                    marker_colors=['#ff4444', '#ff8800', '#ffaa00', '#44aa44']
                )
            ])
            
            fig.update_layout(
                title="Vulnerabilities by Severity",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)

def render_vulnerabilities_tab(security_data: dict):
    """Render vulnerabilities details"""
    
    vulnerabilities = security_data.get('vulnerabilities', [])
    
    if not vulnerabilities:
        st.info("No vulnerabilities found! 🎉")
        return
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        severity_filter = st.selectbox(
            "Filter by Severity",
            ["All", "Critical", "High", "Medium", "Low"]
        )
    
    with col2:
        type_filter = st.selectbox(
            "Filter by Type",
            ["All", "SAST", "Dependency", "Container", "Configuration"]
        )
    
    with col3:
        tool_filter = st.selectbox(
            "Filter by Tool",
            ["All"] + list(set(v.get('tool', 'Unknown') for v in vulnerabilities))
        )
    
    # Apply filters
    filtered_vulns = vulnerabilities
    
    if severity_filter != "All":
        filtered_vulns = [v for v in filtered_vulns if v.get('severity', '').lower() == severity_filter.lower()]
    
    if type_filter != "All":
        filtered_vulns = [v for v in filtered_vulns if v.get('type', '').lower() == type_filter.lower()]
    
    if tool_filter != "All":
        filtered_vulns = [v for v in filtered_vulns if v.get('tool', '') == tool_filter]
    
    st.write(f"**Showing {len(filtered_vulns)} of {len(vulnerabilities)} vulnerabilities**")
    
    # Display vulnerabilities
    for i, vuln in enumerate(filtered_vulns[:20]):  # Limit to 20 for performance
        with st.expander(f"🚨 {vuln.get('title', 'Security Issue')} ({vuln.get('severity', 'unknown').title()})"):
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Type:** {vuln.get('type', 'Unknown').title()}")
                st.write(f"**Tool:** {vuln.get('tool', 'Unknown')}")
                st.write(f"**Severity:** {vuln.get('severity', 'Unknown').title()}")
                
                if vuln.get('owasp_category'):
                    st.write(f"**OWASP:** {vuln.get('owasp_category')}")
                
                if vuln.get('cwe'):
                    st.write(f"**CWE:** {vuln.get('cwe')}")
            
            with col2:
                if vuln.get('file'):
                    st.write(f"**File:** {vuln.get('file')}")
                
                if vuln.get('line'):
                    st.write(f"**Line:** {vuln.get('line')}")
                
                if vuln.get('package'):
                    st.write(f"**Package:** {vuln.get('package')}")
                
                if vuln.get('fix_available'):
                    st.success("✅ Fix Available")
            
            if vuln.get('description'):
                st.write("**Description:**")
                st.write(vuln.get('description'))
            
            if vuln.get('code'):
                st.write("**Code:**")
                st.code(vuln.get('code'), language='python')

def render_dependencies_tab(security_data: dict):
    """Render dependency security details"""
    
    dependency_issues = security_data.get('dependency_issues', [])
    
    if not dependency_issues:
        st.success("No dependency vulnerabilities found! 🎉")
        return
    
    st.write(f"**Found {len(dependency_issues)} dependency issues**")
    
    # Group by package
    packages = {}
    for issue in dependency_issues:
        pkg_name = issue.get('package', 'Unknown')
        if pkg_name not in packages:
            packages[pkg_name] = []
        packages[pkg_name].append(issue)
    
    # Display by package
    for package, issues in packages.items():
        with st.expander(f"📦 {package} ({len(issues)} issues)"):
            
            for issue in issues:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Current Version:** {issue.get('current_version', 'Unknown')}")
                    st.write(f"**Severity:** {issue.get('severity', 'Unknown').title()}")
                    
                    if issue.get('cve'):
                        cves = issue.get('cve', [])
                        if isinstance(cves, list):
                            st.write(f"**CVEs:** {', '.join(cves)}")
                        else:
                            st.write(f"**CVE:** {cves}")
                
                with col2:
                    if issue.get('patched_versions'):
                        st.write(f"**Fixed In:** {issue.get('patched_versions')}")
                        st.success("✅ Update Available")
                    
                    if issue.get('vulnerable_spec'):
                        st.write(f"**Vulnerable:** {issue.get('vulnerable_spec')}")
                
                if issue.get('advisory'):
                    st.write("**Advisory:**")
                    st.write(issue.get('advisory'))
                
                if issue.get('recommendation'):
                    st.info(f"💡 **Recommendation:** {issue.get('recommendation')}")
                
                st.divider()

def render_container_security_tab(security_data: dict):
    """Render container security details"""
    
    container_security = security_data.get('container_security', {})
    
    # Container vulnerabilities
    container_vulns = [v for v in security_data.get('vulnerabilities', []) if v.get('type') == 'container']
    
    if container_vulns:
        st.subheader("🐳 Container Image Vulnerabilities")
        
        # Summary
        analysis = container_security.get('image_analysis', {})
        if analysis:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total", analysis.get('total_vulnerabilities', 0))
            with col2:
                st.metric("Critical", analysis.get('critical', 0))
            with col3:
                st.metric("High", analysis.get('high', 0))
            with col4:
                st.metric("Fixable", analysis.get('fixable', 0))
        
        # Vulnerability list
        for vuln in container_vulns[:10]:  # Limit display
            with st.expander(f"🔍 {vuln.get('vulnerability_id', 'Unknown')} - {vuln.get('package', 'Unknown')}"):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Package:** {vuln.get('package', 'Unknown')}")
                    st.write(f"**Installed:** {vuln.get('installed_version', 'Unknown')}")
                    st.write(f"**Severity:** {vuln.get('severity', 'Unknown').title()}")
                
                with col2:
                    if vuln.get('fixed_version'):
                        st.write(f"**Fixed In:** {vuln.get('fixed_version')}")
                        st.success("✅ Update Available")
                    
                    st.write(f"**Target:** {vuln.get('target', 'Unknown')}")
                
                if vuln.get('description'):
                    st.write("**Description:**")
                    st.write(vuln.get('description'))
    
    # Dockerfile issues
    dockerfile_issues = container_security.get('dockerfile_issues', [])
    if dockerfile_issues:
        st.subheader("📄 Dockerfile Security Issues")
        
        for issue in dockerfile_issues:
            severity = issue.get('severity', 'medium')
            
            if severity == 'high':
                st.error(f"**Line {issue.get('line', 0)}:** {issue.get('issue', 'Unknown issue')}")
            elif severity == 'medium':
                st.warning(f"**Line {issue.get('line', 0)}:** {issue.get('issue', 'Unknown issue')}")
            else:
                st.info(f"**Line {issue.get('line', 0)}:** {issue.get('issue', 'Unknown issue')}")
            
            if issue.get('recommendation'):
                st.write(f"💡 {issue.get('recommendation')}")
    
    if not container_vulns and not dockerfile_issues:
        st.success("No container security issues found! 🎉")

def render_compliance_tab(security_data: dict):
    """Render compliance assessment"""
    
    compliance_status = security_data.get('compliance_status', {})
    
    # Overall compliance score
    overall_score = compliance_status.get('overall_compliance', 0)
    
    col1, col2, col3 = st.columns(3)
    with col2:
        st.metric(
            "Overall Compliance Score",
            f"{overall_score}%",
            delta="OWASP Top 10 + CIS Benchmarks"
        )
    
    st.divider()
    
    # OWASP Top 10 compliance
    st.subheader("🔟 OWASP Top 10 Compliance")
    
    owasp_status = compliance_status.get('owasp_top10', {})
    
    if owasp_status:
        owasp_df = []
        for category, details in owasp_status.items():
            owasp_df.append({
                'Category': category,
                'Description': details.get('description', ''),
                'Status': details.get('status', 'unknown').replace('_', ' ').title(),
                'Score': details.get('score', 0),
                'Issues': details.get('vulnerability_count', 0)
            })
        
        df = pd.DataFrame(owasp_df)
        
        # Color code the status
        def color_status(val):
            if val == 'Compliant':
                return 'background-color: #d4edda'
            elif val == 'Mostly Compliant':
                return 'background-color: #fff3cd'
            elif val == 'Partially Compliant':
                return 'background-color: #f8d7da'
            else:
                return 'background-color: #f5c6cb'
        
        styled_df = df.style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True)
    
    st.divider()
    
    # CIS Benchmarks compliance
    st.subheader("🛡️ CIS Benchmarks Compliance")
    
    cis_status = compliance_status.get('cis_benchmarks', {})
    
    if cis_status:
        cis_df = []
        for category, details in cis_status.items():
            cis_df.append({
                'Category': category.replace('_', ' ').title(),
                'Description': details.get('description', ''),
                'Status': details.get('status', 'unknown').replace('_', ' ').title(),
                'Score': details.get('score', 0)
            })
        
        df = pd.DataFrame(cis_df)
        styled_df = df.style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True)

def render_recommendations_tab(security_data: dict):
    """Render security recommendations and auto-patches"""
    
    recommendations = security_data.get('recommendations', [])
    auto_patches = security_data.get('auto_patches', [])
    
    # Auto-patches section
    if auto_patches:
        st.subheader("🔧 Automatic Fixes Available")
        
        st.write(f"**{len(auto_patches)} automatic fixes can be applied:**")
        
        for patch in auto_patches:
            patch_type = patch.get('type', 'unknown')
            
            if patch_type == 'dependency_update':
                with st.expander(f"📦 Update {patch.get('package', 'Unknown')} ({patch.get('severity', 'medium').title()})"):
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Package:** {patch.get('package', 'Unknown')}")
                        st.write(f"**Current:** {patch.get('current_version', 'Unknown')}")
                        st.write(f"**Recommended:** {patch.get('recommended_version', 'Latest')}")
                    
                    with col2:
                        st.write(f"**Severity:** {patch.get('severity', 'Medium').title()}")
                        if patch.get('auto_applicable'):
                            st.success("✅ Auto-applicable")
                        else:
                            st.warning("⚠️ Manual review required")
                    
                    if patch.get('command'):
                        st.write("**Command:**")
                        st.code(patch.get('command'), language='bash')
                    
                    if patch.get('description'):
                        st.write(f"**Description:** {patch.get('description')}")
            
            elif patch_type == 'configuration_fix':
                with st.expander(f"⚙️ Fix {patch.get('issue', 'Configuration Issue')}"):
                    
                    st.write(f"**File:** {patch.get('file', 'Unknown')}")
                    st.write(f"**Line:** {patch.get('line', 0)}")
                    st.write(f"**Issue:** {patch.get('issue', 'Unknown')}")
                    
                    if patch.get('recommendation'):
                        st.info(f"💡 **Recommendation:** {patch.get('recommendation')}")
                    
                    if not patch.get('auto_applicable', True):
                        st.warning("⚠️ Manual review and implementation required")
    
    # General recommendations
    if recommendations:
        st.subheader("💡 Security Recommendations")
        
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")
    
    # Security best practices
    st.subheader("📚 Security Best Practices")
    
    best_practices = [
        "Implement security scanning in your CI/CD pipeline",
        "Regular security training for development team",
        "Use infrastructure as code for consistent deployments",
        "Implement proper logging and monitoring",
        "Regular security audits and penetration testing",
        "Keep all dependencies and base images up to date",
        "Use least privilege principle for all access controls",
        "Implement proper secret management practices"
    ]
    
    for practice in best_practices:
        st.info(f"🔒 {practice}")
