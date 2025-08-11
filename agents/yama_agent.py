"""
Yama - The Security & Compliance Agent
Handles security scanning, vulnerability assessment, and compliance checking
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
import hashlib

from langchain.tools import BaseTool, tool

from .base_agent import BaseAgent

class SecurityScanTool(BaseTool):
    """Tool for running security scans"""
    name: str = "security_scan"
    description: str = "Run comprehensive security scans on code and containers"
    
    def _run(self, project_path: str, languages: List[str]) -> Dict[str, Any]:
        """Run security scans on the project"""
        project_dir = Path(project_path)
        
        scan_results = {
            "sast_results": {},
            "dependency_scan": {},
            "secrets_scan": {},
            "compliance_check": {},
            "risk_score": 0,
            "critical_issues": [],
            "recommendations": []
        }
        
        # Run SAST (Static Application Security Testing)
        scan_results["sast_results"] = self._run_sast_scan(project_dir, languages)
        
        # Run dependency vulnerability scan
        scan_results["dependency_scan"] = self._run_dependency_scan(project_dir, languages)
        
        # Run secrets detection
        scan_results["secrets_scan"] = self._run_secrets_scan(project_dir)
        
        # Run compliance checks
        scan_results["compliance_check"] = self._run_compliance_check(project_dir)
        
        # Calculate risk score
        scan_results["risk_score"] = self._calculate_risk_score(scan_results)
        
        # Generate recommendations
        scan_results["recommendations"] = self._generate_security_recommendations(scan_results)
        
        return scan_results
    
    def _run_sast_scan(self, project_dir: Path, languages: List[str]) -> Dict[str, Any]:
        """Run Static Application Security Testing"""
        sast_results = {
            "total_issues": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "issues": []
        }
        
        # Python security scan (simulate Bandit)
        if "Python" in languages:
            python_issues = self._scan_python_security(project_dir)
            sast_results["issues"].extend(python_issues)
        
        # JavaScript security scan
        if "JavaScript" in languages or "TypeScript" in languages:
            js_issues = self._scan_javascript_security(project_dir)
            sast_results["issues"].extend(js_issues)
        
        # Count issues by severity
        for issue in sast_results["issues"]:
            severity = issue.get("severity", "low").lower()
            if severity in sast_results:
                sast_results[severity] += 1
            sast_results["total_issues"] += 1
        
        return sast_results
    
    def _scan_python_security(self, project_dir: Path) -> List[Dict[str, Any]]:
        """Scan Python files for security issues"""
        issues = []
        
        for py_file in project_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for common security issues
                # SQL Injection patterns
                if re.search(r'execute\s*\(\s*["\'].*%.*["\']', content):
                    issues.append({
                        "file": str(py_file.relative_to(project_dir)),
                        "line": 1,
                        "severity": "high",
                        "issue": "Possible SQL injection vulnerability",
                        "description": "String formatting in SQL queries can lead to injection attacks"
                    })
                
                # Hardcoded secrets
                secret_patterns = [
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'secret\s*=\s*["\'][^"\']+["\']',
                    r'api_key\s*=\s*["\'][^"\']+["\']',
                    r'token\s*=\s*["\'][^"\']+["\']'
                ]
                
                for pattern in secret_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        issues.append({
                            "file": str(py_file.relative_to(project_dir)),
                            "line": 1,
                            "severity": "critical",
                            "issue": "Hardcoded secret detected",
                            "description": "Secrets should be stored in environment variables"
                        })
                
                # Unsafe deserialization
                if re.search(r'pickle\.loads?\s*\(', content):
                    issues.append({
                        "file": str(py_file.relative_to(project_dir)),
                        "line": 1,
                        "severity": "high",
                        "issue": "Unsafe deserialization",
                        "description": "pickle.loads can execute arbitrary code"
                    })
                
                # Debug mode in production
                if re.search(r'debug\s*=\s*True', content):
                    issues.append({
                        "file": str(py_file.relative_to(project_dir)),
                        "line": 1,
                        "severity": "medium",
                        "issue": "Debug mode enabled",
                        "description": "Debug mode should be disabled in production"
                    })
                
            except Exception:
                continue
        
        return issues
    
    def _scan_javascript_security(self, project_dir: Path) -> List[Dict[str, Any]]:
        """Scan JavaScript/TypeScript files for security issues"""
        issues = []
        
        js_extensions = ["*.js", "*.ts", "*.jsx", "*.tsx"]
        
        for ext in js_extensions:
            for js_file in project_dir.rglob(ext):
                try:
                    with open(js_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for eval usage
                    if re.search(r'\beval\s*\(', content):
                        issues.append({
                            "file": str(js_file.relative_to(project_dir)),
                            "line": 1,
                            "severity": "high",
                            "issue": "Use of eval() function",
                            "description": "eval() can execute arbitrary code and is dangerous"
                        })
                    
                    # Check for innerHTML usage
                    if re.search(r'\.innerHTML\s*=', content):
                        issues.append({
                            "file": str(js_file.relative_to(project_dir)),
                            "line": 1,
                            "severity": "medium",
                            "issue": "Use of innerHTML",
                            "description": "innerHTML can lead to XSS vulnerabilities"
                        })
                    
                    # Check for hardcoded API keys
                    if re.search(r'["\'][A-Za-z0-9]{20,}["\']', content):
                        issues.append({
                            "file": str(js_file.relative_to(project_dir)),
                            "line": 1,
                            "severity": "medium",
                            "issue": "Possible hardcoded API key",
                            "description": "API keys should be stored securely"
                        })
                
                except Exception:
                    continue
        
        return issues
    
    def _run_dependency_scan(self, project_dir: Path, languages: List[str]) -> Dict[str, Any]:
        """Scan dependencies for known vulnerabilities"""
        dep_results = {
            "total_vulnerabilities": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "vulnerable_packages": []
        }
        
        # Python dependencies
        if "Python" in languages:
            requirements_file = project_dir / "requirements.txt"
            if requirements_file.exists():
                python_vulns = self._scan_python_dependencies(requirements_file)
                dep_results["vulnerable_packages"].extend(python_vulns)
        
        # Node.js dependencies
        if "JavaScript" in languages or "TypeScript" in languages:
            package_json = project_dir / "package.json"
            if package_json.exists():
                node_vulns = self._scan_node_dependencies(package_json)
                dep_results["vulnerable_packages"].extend(node_vulns)
        
        # Count vulnerabilities by severity
        for vuln in dep_results["vulnerable_packages"]:
            severity = vuln.get("severity", "low").lower()
            if severity in dep_results:
                dep_results[severity] += 1
            dep_results["total_vulnerabilities"] += 1
        
        return dep_results
    
    def _scan_python_dependencies(self, requirements_file: Path) -> List[Dict[str, Any]]:
        """Scan Python dependencies for vulnerabilities"""
        vulnerabilities = []
        
        # Simulate vulnerability database lookup
        known_vulns = {
            "django": {"version": "<3.2.0", "severity": "high", "cve": "CVE-2021-31542"},
            "flask": {"version": "<2.0.0", "severity": "medium", "cve": "CVE-2021-23385"},
            "requests": {"version": "<2.25.0", "severity": "medium", "cve": "CVE-2021-33503"},
            "pillow": {"version": "<8.2.0", "severity": "high", "cve": "CVE-2021-25287"}
        }
        
        try:
            with open(requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        package_name = line.split('==')[0].split('>=')[0].split('<=')[0].lower()
                        
                        if package_name in known_vulns:
                            vuln_info = known_vulns[package_name]
                            vulnerabilities.append({
                                "package": package_name,
                                "current_version": line,
                                "vulnerable_version": vuln_info["version"],
                                "severity": vuln_info["severity"],
                                "cve": vuln_info["cve"],
                                "description": f"Known vulnerability in {package_name}"
                            })
        except Exception:
            pass
        
        return vulnerabilities
    
    def _scan_node_dependencies(self, package_json: Path) -> List[Dict[str, Any]]:
        """Scan Node.js dependencies for vulnerabilities"""
        vulnerabilities = []
        
        # Simulate npm audit results
        known_vulns = {
            "lodash": {"version": "<4.17.21", "severity": "high", "cve": "CVE-2021-23337"},
            "axios": {"version": "<0.21.2", "severity": "medium", "cve": "CVE-2021-3749"},
            "express": {"version": "<4.17.3", "severity": "medium", "cve": "CVE-2022-24999"}
        }
        
        try:
            with open(package_json, 'r') as f:
                package_data = json.load(f)
                
                all_deps = {
                    **package_data.get("dependencies", {}),
                    **package_data.get("devDependencies", {})
                }
                
                for package_name, version in all_deps.items():
                    if package_name in known_vulns:
                        vuln_info = known_vulns[package_name]
                        vulnerabilities.append({
                            "package": package_name,
                            "current_version": version,
                            "vulnerable_version": vuln_info["version"],
                            "severity": vuln_info["severity"],
                            "cve": vuln_info["cve"],
                            "description": f"Known vulnerability in {package_name}"
                        })
        except Exception:
            pass
        
        return vulnerabilities
    
    def _run_secrets_scan(self, project_dir: Path) -> Dict[str, Any]:
        """Scan for exposed secrets and credentials"""
        secrets_results = {
            "total_secrets": 0,
            "secrets_found": []
        }
        
        # Common secret patterns
        secret_patterns = {
            "AWS Access Key": r'AKIA[0-9A-Z]{16}',
            "AWS Secret Key": r'[0-9a-zA-Z/+]{40}',
            "GitHub Token": r'ghp_[0-9a-zA-Z]{36}',
            "API Key": r'[aA][pP][iI]_?[kK][eE][yY].*[\'|"][0-9a-zA-Z]{32,45}[\'|"]',
            "Private Key": r'-----BEGIN PRIVATE KEY-----',
            "Database URL": r'(mongodb|mysql|postgres)://[^\s]+',
        }
        
        for file_path in project_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.py', '.js', '.ts', '.json', '.yaml', '.yml', '.env']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for secret_type, pattern in secret_patterns.items():
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            secrets_results["secrets_found"].append({
                                "file": str(file_path.relative_to(project_dir)),
                                "type": secret_type,
                                "line": content[:match.start()].count('\n') + 1,
                                "severity": "critical"
                            })
                            secrets_results["total_secrets"] += 1
                
                except Exception:
                    continue
        
        return secrets_results
    
    def _run_compliance_check(self, project_dir: Path) -> Dict[str, Any]:
        """Run compliance checks against security standards"""
        compliance_results = {
            "owasp_top10": {"score": 0, "issues": []},
            "cis_benchmarks": {"score": 0, "issues": []},
            "pci_dss": {"score": 0, "issues": []},
            "overall_compliance": 0
        }
        
        # OWASP Top 10 checks
        owasp_score = 85  # Simulated score
        owasp_issues = [
            "A03:2021 – Injection: Potential SQL injection vulnerabilities found",
            "A07:2021 – Identification and Authentication Failures: Weak password policies detected"
        ]
        
        compliance_results["owasp_top10"] = {
            "score": owasp_score,
            "issues": owasp_issues
        }
        
        # CIS Benchmarks
        cis_score = 78
        cis_issues = [
            "CIS 5.1: Ensure secure configurations for containers",
            "CIS 5.7: Ensure secrets are not stored in container images"
        ]
        
        compliance_results["cis_benchmarks"] = {
            "score": cis_score,
            "issues": cis_issues
        }
        
        # Overall compliance score
        compliance_results["overall_compliance"] = (owasp_score + cis_score) / 2
        
        return compliance_results
    
    def _calculate_risk_score(self, scan_results: Dict[str, Any]) -> int:
        """Calculate overall risk score (0-100, lower is better)"""
        risk_score = 0
        
        # SAST results impact
        sast = scan_results.get("sast_results", {})
        risk_score += sast.get("critical", 0) * 20
        risk_score += sast.get("high", 0) * 10
        risk_score += sast.get("medium", 0) * 5
        risk_score += sast.get("low", 0) * 1
        
        # Dependency vulnerabilities impact
        deps = scan_results.get("dependency_scan", {})
        risk_score += deps.get("critical", 0) * 15
        risk_score += deps.get("high", 0) * 8
        risk_score += deps.get("medium", 0) * 4
        
        # Secrets impact
        secrets = scan_results.get("secrets_scan", {})
        risk_score += secrets.get("total_secrets", 0) * 25
        
        # Compliance impact
        compliance = scan_results.get("compliance_check", {})
        compliance_score = compliance.get("overall_compliance", 100)
        risk_score += (100 - compliance_score) * 0.5
        
        return min(risk_score, 100)
    
    def _generate_security_recommendations(self, scan_results: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on scan results"""
        recommendations = []
        
        # SAST recommendations
        sast = scan_results.get("sast_results", {})
        if sast.get("critical", 0) > 0:
            recommendations.append("Address critical security vulnerabilities immediately")
        if sast.get("high", 0) > 0:
            recommendations.append("Fix high-severity security issues before deployment")
        
        # Dependency recommendations
        deps = scan_results.get("dependency_scan", {})
        if deps.get("total_vulnerabilities", 0) > 0:
            recommendations.append("Update vulnerable dependencies to secure versions")
        
        # Secrets recommendations
        secrets = scan_results.get("secrets_scan", {})
        if secrets.get("total_secrets", 0) > 0:
            recommendations.append("Remove hardcoded secrets and use environment variables")
            recommendations.append("Implement proper secrets management solution")
        
        # Compliance recommendations
        compliance = scan_results.get("compliance_check", {})
        if compliance.get("overall_compliance", 100) < 80:
            recommendations.append("Improve security compliance to meet industry standards")
        
        # General recommendations
        recommendations.extend([
            "Implement automated security testing in CI/CD pipeline",
            "Enable security headers in web applications",
            "Use HTTPS for all communications",
            "Implement proper input validation and sanitization",
            "Enable security logging and monitoring"
        ])
        
        return recommendations

class YamaAgent(BaseAgent):
    """Security & Compliance Agent"""

    def __init__(self, llm_client, config):
        super().__init__("Yama", llm_client, config)
    
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize Yama-specific tools"""
        return [
            SecurityScanTool()
        ]
    
    def _get_system_prompt(self) -> str:
        """Get Yama's system prompt"""
        return """You are Yama, the Security & Compliance Agent in the VedOps DevSecOps platform.

Your responsibilities:
1. Perform comprehensive security scans (SAST, DAST, dependency analysis)
2. Detect secrets, credentials, and sensitive data exposure
3. Assess compliance with security standards (OWASP Top 10, CIS Benchmarks, PCI-DSS)
4. Calculate risk scores and prioritize security issues
5. Generate actionable security recommendations
6. Automatically patch vulnerabilities where possible

You have expertise in:
- Static and Dynamic Application Security Testing
- Vulnerability assessment and penetration testing
- Security compliance frameworks and standards
- Container and infrastructure security
- Secrets management and data protection
- Security automation and DevSecOps practices

Your security assessments should be:
- Comprehensive (covering all attack vectors)
- Accurate (minimal false positives)
- Actionable (clear remediation steps)
- Risk-based (prioritized by business impact)
- Compliant (meeting regulatory requirements)

Security principles you enforce:
- Defense in depth
- Principle of least privilege
- Fail securely
- Security by design
- Continuous monitoring
- Zero trust architecture

Always provide clear, prioritized recommendations with specific remediation steps."""
    
    def _prepare_input(self, input_data: Dict[str, Any]) -> str:
        """Prepare input for Yama"""
        project_data = input_data.get("project_data", {})
        varuna_result = input_data.get("agent_results", {}).get("varuna", {})
        agni_result = input_data.get("agent_results", {}).get("agni", {})
        
        build_plan = varuna_result.get("build_plan", {}) if varuna_result else {}
        
        input_text = f"""
Perform comprehensive security assessment for:

Project: {project_data.get('name', 'Unknown')}
Languages: {build_plan.get('languages', [])}
Frameworks: {build_plan.get('frameworks', [])}
Source Path: {project_data.get('source_path', '')}

Previous Analysis:
- Varuna detected: {len(build_plan.get('languages', []))} languages
- Agni created: Docker containers and K8s manifests

Please perform:
1. Static Application Security Testing (SAST)
2. Dependency vulnerability scanning
3. Secrets and credential detection
4. Compliance assessment (OWASP Top 10, CIS Benchmarks)
5. Container security analysis
6. Risk scoring and prioritization
7. Automated patching recommendations

Focus on:
- Critical and high-severity vulnerabilities
- Compliance with security standards
- Production readiness from security perspective
- Actionable remediation steps
"""
        
        return input_text
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute security scan and produce deployment decision"""
        # Determine project path and languages from previous stages
        project_path = input_data.get("project_path") or input_data.get("source_path", "")
        tech_stack = input_data.get("tech_stack", {})
        languages = []
        if isinstance(tech_stack.get("languages"), dict):
            languages = list(tech_stack.get("languages", {}).keys())
        elif isinstance(tech_stack.get("languages"), list):
            languages = tech_stack.get("languages", [])

        security_tool = SecurityScanTool()
        security_results = security_tool._run(project_path or "", languages)

        risk_score = security_results.get("risk_score", 0)
        deployment_approved = risk_score < 50

        result = {
            "status": "completed",
            "agent_name": "Yama",
            "security_scan": security_results,
            "deployment_decision": {
                "approved": deployment_approved,
                "risk_score": risk_score,
                "risk_level": self._get_risk_level(risk_score),
                "blocking_issues": self._get_blocking_issues(security_results),
                "required_fixes": self._get_required_fixes(security_results)
            },
            "compliance_status": {
                "owasp_compliant": security_results.get("compliance_check", {}).get("owasp_top10", {}).get("score", 0) >= 80,
                "cis_compliant": security_results.get("compliance_check", {}).get("cis_benchmarks", {}).get("score", 0) >= 80,
                "overall_score": security_results.get("compliance_check", {}).get("overall_compliance", 0)
            },
            "recommendations": security_results.get("recommendations", []),
            "next_agent": "Vayu" if deployment_approved else "Krishna",
            "timestamp": input_data.get("timestamp")
        }

        return result
    
    def _get_risk_level(self, risk_score: int) -> str:
        """Get risk level based on score"""
        if risk_score >= 80:
            return "CRITICAL"
        elif risk_score >= 60:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        elif risk_score >= 20:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _get_blocking_issues(self, security_results: Dict[str, Any]) -> List[str]:
        """Get issues that block deployment"""
        blocking_issues = []
        
        # Critical SAST issues
        sast = security_results.get("sast_results", {})
        if sast.get("critical", 0) > 0:
            blocking_issues.append(f"{sast['critical']} critical security vulnerabilities")
        
        # Exposed secrets
        secrets = security_results.get("secrets_scan", {})
        if secrets.get("total_secrets", 0) > 0:
            blocking_issues.append(f"{secrets['total_secrets']} exposed secrets/credentials")
        
        # Critical dependency vulnerabilities
        deps = security_results.get("dependency_scan", {})
        if deps.get("critical", 0) > 0:
            blocking_issues.append(f"{deps['critical']} critical dependency vulnerabilities")
        
        return blocking_issues
    
    def _get_required_fixes(self, security_results: Dict[str, Any]) -> List[str]:
        """Get required fixes before deployment"""
        required_fixes = []
        
        # High priority fixes
        sast = security_results.get("sast_results", {})
        if sast.get("high", 0) > 0:
            required_fixes.append("Fix high-severity code vulnerabilities")
        
        deps = security_results.get("dependency_scan", {})
        if deps.get("high", 0) > 0:
            required_fixes.append("Update high-risk dependencies")
        
        # Compliance fixes
        compliance = security_results.get("compliance_check", {})
        if compliance.get("overall_compliance", 100) < 70:
            required_fixes.append("Address security compliance gaps")
        
        return required_fixes
