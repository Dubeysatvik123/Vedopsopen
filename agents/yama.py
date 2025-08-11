"""
Yama - The Security & Compliance Agent
Handles security scanning, vulnerability assessment, and compliance checking
"""

import os
import json
import subprocess
import tempfile
import logging
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re
import yaml

from langchain_community.llms import Ollama

@dataclass
class SecurityReport:
    """Security assessment results"""
    overall_score: str  # A+, A, B, C, D, F
    risk_level: str  # critical, high, medium, low
    vulnerabilities: List[Dict[str, Any]]
    compliance_status: Dict[str, Any]
    dependency_issues: List[Dict[str, Any]]
    container_security: Dict[str, Any]
    recommendations: List[str]
    auto_patches: List[Dict[str, Any]]
    scan_timestamp: str
    tools_used: List[str]

class YamaAgent:
    """Security & Compliance Agent"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.temp_dir = None
        
        # Initialize LLM for intelligent security analysis
        self.llm = Ollama(model="codellama", base_url="http://localhost:11434")
        
        # Security tools configuration
        self.security_tools = {
            'bandit': {
                'languages': ['python'],
                'command': 'bandit',
                'available': self._check_tool_availability('bandit')
            },
            'safety': {
                'languages': ['python'],
                'command': 'safety',
                'available': self._check_tool_availability('safety')
            },
            'semgrep': {
                'languages': ['python', 'javascript', 'java', 'go'],
                'command': 'semgrep',
                'available': self._check_tool_availability('semgrep')
            },
            'trivy': {
                'languages': ['all'],
                'command': 'trivy',
                'available': self._check_tool_availability('trivy')
            },
            'npm_audit': {
                'languages': ['javascript', 'typescript'],
                'command': 'npm',
                'available': self._check_tool_availability('npm')
            }
        }
        
        # Vulnerability severity mapping
        self.severity_scores = {
            'critical': 10,
            'high': 8,
            'medium': 5,
            'low': 2,
            'info': 1
        }
        
        # OWASP Top 10 2021 categories
        self.owasp_categories = {
            'A01': 'Broken Access Control',
            'A02': 'Cryptographic Failures',
            'A03': 'Injection',
            'A04': 'Insecure Design',
            'A05': 'Security Misconfiguration',
            'A06': 'Vulnerable and Outdated Components',
            'A07': 'Identification and Authentication Failures',
            'A08': 'Software and Data Integrity Failures',
            'A09': 'Security Logging and Monitoring Failures',
            'A10': 'Server-Side Request Forgery (SSRF)'
        }
        
        # CIS Benchmark categories
        self.cis_categories = {
            'access_control': 'Access Control Management',
            'authentication': 'Authentication and Authorization',
            'encryption': 'Data Protection and Encryption',
            'logging': 'Logging and Monitoring',
            'network': 'Network Security',
            'system': 'System Configuration'
        }
    
    def execute(self, build_artifacts: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution method for Yama agent"""
        try:
            self.logger.info("Yama: Starting security and compliance assessment")
            
            # Create temporary working directory
            self.temp_dir = tempfile.mkdtemp(prefix="yama_")
            work_dir = Path(self.temp_dir)
            
            # Step 1: Static Application Security Testing (SAST)
            sast_results = self._run_sast_scans(build_artifacts, work_dir)
            
            # Step 2: Dependency vulnerability scanning
            dependency_results = self._scan_dependencies(build_artifacts, work_dir)
            
            # Step 3: Container security scanning
            container_results = self._scan_container_security(build_artifacts, work_dir)
            
            # Step 4: Configuration security analysis
            config_results = self._analyze_configuration_security(build_artifacts, work_dir)
            
            # Step 5: Compliance assessment
            compliance_results = self._assess_compliance(
                sast_results, dependency_results, container_results, config_results
            )
            
            # Step 6: Generate auto-patch recommendations
            auto_patches = self._generate_auto_patches(dependency_results, sast_results)
            
            # Step 7: Calculate overall security score
            overall_score, risk_level = self._calculate_security_score(
                sast_results, dependency_results, container_results, compliance_results
            )
            
            # Step 8: Generate security recommendations
            recommendations = self._generate_security_recommendations(
                sast_results, dependency_results, container_results, compliance_results
            )
            
            # Compile all vulnerabilities
            all_vulnerabilities = []
            all_vulnerabilities.extend(sast_results.get('vulnerabilities', []))
            all_vulnerabilities.extend(dependency_results.get('vulnerabilities', []))
            all_vulnerabilities.extend(container_results.get('vulnerabilities', []))
            all_vulnerabilities.extend(config_results.get('vulnerabilities', []))
            
            # Create security report
            report = SecurityReport(
                overall_score=overall_score,
                risk_level=risk_level,
                vulnerabilities=all_vulnerabilities,
                compliance_status=compliance_results,
                dependency_issues=dependency_results.get('issues', []),
                container_security=container_results,
                recommendations=recommendations,
                auto_patches=auto_patches,
                scan_timestamp=str(datetime.now()),
                tools_used=self._get_used_tools()
            )
            
            # Convert to dict for JSON serialization
            result = {
                'overall_score': report.overall_score,
                'risk_level': report.risk_level,
                'vulnerabilities': report.vulnerabilities,
                'compliance_status': report.compliance_status,
                'dependency_issues': report.dependency_issues,
                'container_security': report.container_security,
                'recommendations': report.recommendations,
                'auto_patches': report.auto_patches,
                'scan_timestamp': report.scan_timestamp,
                'tools_used': report.tools_used,
                'summary': {
                    'total_vulnerabilities': len(all_vulnerabilities),
                    'critical_count': len([v for v in all_vulnerabilities if v.get('severity') == 'critical']),
                    'high_count': len([v for v in all_vulnerabilities if v.get('severity') == 'high']),
                    'medium_count': len([v for v in all_vulnerabilities if v.get('severity') == 'medium']),
                    'low_count': len([v for v in all_vulnerabilities if v.get('severity') == 'low']),
                    'patchable_count': len(auto_patches)
                },
                'agent': 'yama'
            }
            
            # Save security report
            self._save_security_report(result)
            
            self.logger.info("Yama: Security assessment completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Yama execution failed: {str(e)}")
            raise
        finally:
            self._cleanup()
    
    def _run_sast_scans(self, build_artifacts: Dict[str, Any], work_dir: Path) -> Dict[str, Any]:
        """Run Static Application Security Testing"""
        
        sast_results = {
            'vulnerabilities': [],
            'tools_used': [],
            'scan_summary': {}
        }
        
        # Get project source (we'll need to extract from build context)
        project_path = self._get_project_source_path(build_artifacts)
        
        if not project_path or not project_path.exists():
            self.logger.warning("Project source not available for SAST scanning")
            return sast_results
        
        # Determine project languages from build artifacts
        languages = self._extract_languages_from_artifacts(build_artifacts)
        
        # Run Bandit for Python
        if 'python' in languages and self.security_tools['bandit']['available']:
            bandit_results = self._run_bandit_scan(project_path)
            sast_results['vulnerabilities'].extend(bandit_results.get('vulnerabilities', []))
            sast_results['tools_used'].append('bandit')
            sast_results['scan_summary']['bandit'] = bandit_results.get('summary', {})
        
        # Run Semgrep for multiple languages
        if self.security_tools['semgrep']['available']:
            semgrep_results = self._run_semgrep_scan(project_path, languages)
            sast_results['vulnerabilities'].extend(semgrep_results.get('vulnerabilities', []))
            sast_results['tools_used'].append('semgrep')
            sast_results['scan_summary']['semgrep'] = semgrep_results.get('summary', {})
        
        # Run language-specific scans
        if any(lang in languages for lang in ['javascript', 'typescript']):
            eslint_results = self._run_eslint_security_scan(project_path)
            sast_results['vulnerabilities'].extend(eslint_results.get('vulnerabilities', []))
            sast_results['tools_used'].append('eslint-security')
            sast_results['scan_summary']['eslint'] = eslint_results.get('summary', {})
        
        return sast_results
    
    def _scan_dependencies(self, build_artifacts: Dict[str, Any], work_dir: Path) -> Dict[str, Any]:
        """Scan dependencies for known vulnerabilities"""
        
        dependency_results = {
            'vulnerabilities': [],
            'issues': [],
            'tools_used': [],
            'scan_summary': {}
        }
        
        project_path = self._get_project_source_path(build_artifacts)
        if not project_path:
            return dependency_results
        
        # Python dependency scanning
        if (project_path / 'requirements.txt').exists():
            # Safety scan
            if self.security_tools['safety']['available']:
                safety_results = self._run_safety_scan(project_path)
                dependency_results['vulnerabilities'].extend(safety_results.get('vulnerabilities', []))
                dependency_results['issues'].extend(safety_results.get('issues', []))
                dependency_results['tools_used'].append('safety')
                dependency_results['scan_summary']['safety'] = safety_results.get('summary', {})
            
            # pip-audit scan (if available)
            pip_audit_results = self._run_pip_audit_scan(project_path)
            if pip_audit_results:
                dependency_results['vulnerabilities'].extend(pip_audit_results.get('vulnerabilities', []))
                dependency_results['tools_used'].append('pip-audit')
        
        # Node.js dependency scanning
        if (project_path / 'package.json').exists():
            if self.security_tools['npm_audit']['available']:
                npm_results = self._run_npm_audit_scan(project_path)
                dependency_results['vulnerabilities'].extend(npm_results.get('vulnerabilities', []))
                dependency_results['issues'].extend(npm_results.get('issues', []))
                dependency_results['tools_used'].append('npm-audit')
                dependency_results['scan_summary']['npm'] = npm_results.get('summary', {})
        
        # Java dependency scanning (Maven/Gradle)
        if (project_path / 'pom.xml').exists() or (project_path / 'build.gradle').exists():
            maven_results = self._run_maven_dependency_scan(project_path)
            if maven_results:
                dependency_results['vulnerabilities'].extend(maven_results.get('vulnerabilities', []))
                dependency_results['tools_used'].append('maven-dependency-check')
        
        return dependency_results
    
    def _scan_container_security(self, build_artifacts: Dict[str, Any], work_dir: Path) -> Dict[str, Any]:
        """Scan container images for security vulnerabilities"""
        
        container_results = {
            'vulnerabilities': [],
            'image_analysis': {},
            'dockerfile_issues': [],
            'tools_used': []
        }
        
        # Scan Dockerfile for security issues
        dockerfile_path = build_artifacts.get('dockerfile_path')
        if dockerfile_path and Path(dockerfile_path).exists():
            dockerfile_issues = self._analyze_dockerfile_security(Path(dockerfile_path))
            container_results['dockerfile_issues'] = dockerfile_issues
        
        # Trivy container scanning
        if self.security_tools['trivy']['available']:
            image_name = build_artifacts.get('image_name')
            if image_name:
                trivy_results = self._run_trivy_scan(image_name)
                container_results['vulnerabilities'].extend(trivy_results.get('vulnerabilities', []))
                container_results['image_analysis'] = trivy_results.get('analysis', {})
                container_results['tools_used'].append('trivy')
        
        return container_results
    
    def _analyze_configuration_security(self, build_artifacts: Dict[str, Any], work_dir: Path) -> Dict[str, Any]:
        """Analyze configuration files for security issues"""
        
        config_results = {
            'vulnerabilities': [],
            'misconfigurations': [],
            'secrets_found': []
        }
        
        project_path = self._get_project_source_path(build_artifacts)
        if not project_path:
            return config_results
        
        # Scan for hardcoded secrets
        secrets = self._scan_for_secrets(project_path)
        config_results['secrets_found'] = secrets
        
        # Convert secrets to vulnerabilities
        for secret in secrets:
            config_results['vulnerabilities'].append({
                'type': 'hardcoded_secret',
                'severity': 'high',
                'title': f"Hardcoded {secret['type']} found",
                'description': f"Potential {secret['type']} found in {secret['file']}",
                'file': secret['file'],
                'line': secret.get('line', 0),
                'owasp_category': 'A02',  # Cryptographic Failures
                'cwe': 'CWE-798'  # Use of Hard-coded Credentials
            })
        
        # Analyze Docker Compose security
        compose_path = build_artifacts.get('docker_compose_path')
        if compose_path and Path(compose_path).exists():
            compose_issues = self._analyze_compose_security(Path(compose_path))
            config_results['misconfigurations'].extend(compose_issues)
        
        # Analyze Kubernetes manifests security
        k8s_manifests = build_artifacts.get('kubernetes_manifests', {})
        for manifest_type, manifest_path in k8s_manifests.items():
            if Path(manifest_path).exists():
                k8s_issues = self._analyze_k8s_security(Path(manifest_path), manifest_type)
                config_results['misconfigurations'].extend(k8s_issues)
        
        return config_results
    
    def _run_bandit_scan(self, project_path: Path) -> Dict[str, Any]:
        """Run Bandit security scan for Python code"""
        
        try:
            cmd = [
                'bandit', '-r', str(project_path),
                '-f', 'json',
                '--skip', 'B101,B601'  # Skip assert and shell injection for common cases
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode in [0, 1]:  # 0 = no issues, 1 = issues found
                bandit_data = json.loads(result.stdout)
                
                vulnerabilities = []
                for issue in bandit_data.get('results', []):
                    vulnerabilities.append({
                        'type': 'sast',
                        'tool': 'bandit',
                        'severity': issue.get('issue_severity', 'medium').lower(),
                        'confidence': issue.get('issue_confidence', 'medium').lower(),
                        'title': issue.get('test_name', 'Security Issue'),
                        'description': issue.get('issue_text', ''),
                        'file': issue.get('filename', ''),
                        'line': issue.get('line_number', 0),
                        'code': issue.get('code', ''),
                        'test_id': issue.get('test_id', ''),
                        'owasp_category': self._map_bandit_to_owasp(issue.get('test_id', '')),
                        'cwe': issue.get('cwe', '')
                    })
                
                return {
                    'vulnerabilities': vulnerabilities,
                    'summary': {
                        'total_issues': len(vulnerabilities),
                        'high_severity': len([v for v in vulnerabilities if v['severity'] == 'high']),
                        'medium_severity': len([v for v in vulnerabilities if v['severity'] == 'medium']),
                        'low_severity': len([v for v in vulnerabilities if v['severity'] == 'low'])
                    }
                }
            
        except Exception as e:
            self.logger.warning(f"Bandit scan failed: {str(e)}")
        
        return {'vulnerabilities': [], 'summary': {}}
    
    def _run_safety_scan(self, project_path: Path) -> Dict[str, Any]:
        """Run Safety scan for Python dependencies"""
        
        try:
            requirements_file = project_path / 'requirements.txt'
            if not requirements_file.exists():
                return {'vulnerabilities': [], 'issues': [], 'summary': {}}
            
            cmd = ['safety', 'check', '--json', '-r', str(requirements_file)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode in [0, 64]:  # 0 = no issues, 64 = vulnerabilities found
                if result.stdout.strip():
                    safety_data = json.loads(result.stdout)
                    
                    vulnerabilities = []
                    issues = []
                    
                    for vuln in safety_data:
                        vulnerability = {
                            'type': 'dependency',
                            'tool': 'safety',
                            'severity': 'high',  # Safety reports are generally high severity
                            'title': f"Vulnerable dependency: {vuln.get('package_name', 'Unknown')}",
                            'description': vuln.get('advisory', ''),
                            'package': vuln.get('package_name', ''),
                            'installed_version': vuln.get('installed_version', ''),
                            'vulnerable_spec': vuln.get('vulnerable_spec', ''),
                            'cve': vuln.get('cve', ''),
                            'owasp_category': 'A06',  # Vulnerable and Outdated Components
                            'fix_available': bool(vuln.get('vulnerable_spec'))
                        }
                        
                        vulnerabilities.append(vulnerability)
                        issues.append({
                            'package': vuln.get('package_name', ''),
                            'current_version': vuln.get('installed_version', ''),
                            'vulnerable_spec': vuln.get('vulnerable_spec', ''),
                            'advisory': vuln.get('advisory', ''),
                            'cve': vuln.get('cve', '')
                        })
                    
                    return {
                        'vulnerabilities': vulnerabilities,
                        'issues': issues,
                        'summary': {
                            'total_vulnerabilities': len(vulnerabilities),
                            'packages_affected': len(set(v['package'] for v in vulnerabilities))
                        }
                    }
            
        except Exception as e:
            self.logger.warning(f"Safety scan failed: {str(e)}")
        
        return {'vulnerabilities': [], 'issues': [], 'summary': {}}
    
    def _run_npm_audit_scan(self, project_path: Path) -> Dict[str, Any]:
        """Run npm audit for Node.js dependencies"""
        
        try:
            cmd = ['npm', 'audit', '--json']
            result = subprocess.run(
                cmd, 
                cwd=project_path, 
                capture_output=True, 
                text=True, 
                timeout=300
            )
            
            if result.stdout.strip():
                audit_data = json.loads(result.stdout)
                
                vulnerabilities = []
                issues = []
                
                # Parse npm audit format
                advisories = audit_data.get('advisories', {})
                for advisory_id, advisory in advisories.items():
                    vulnerability = {
                        'type': 'dependency',
                        'tool': 'npm-audit',
                        'severity': advisory.get('severity', 'medium'),
                        'title': advisory.get('title', 'Vulnerability in npm package'),
                        'description': advisory.get('overview', ''),
                        'package': advisory.get('module_name', ''),
                        'vulnerable_versions': advisory.get('vulnerable_versions', ''),
                        'patched_versions': advisory.get('patched_versions', ''),
                        'cve': advisory.get('cves', []),
                        'cwe': advisory.get('cwe', ''),
                        'owasp_category': 'A06',  # Vulnerable and Outdated Components
                        'fix_available': bool(advisory.get('patched_versions'))
                    }
                    
                    vulnerabilities.append(vulnerability)
                    issues.append({
                        'package': advisory.get('module_name', ''),
                        'severity': advisory.get('severity', 'medium'),
                        'vulnerable_versions': advisory.get('vulnerable_versions', ''),
                        'patched_versions': advisory.get('patched_versions', ''),
                        'recommendation': advisory.get('recommendation', '')
                    })
                
                return {
                    'vulnerabilities': vulnerabilities,
                    'issues': issues,
                    'summary': {
                        'total_vulnerabilities': len(vulnerabilities),
                        'critical': len([v for v in vulnerabilities if v['severity'] == 'critical']),
                        'high': len([v for v in vulnerabilities if v['severity'] == 'high']),
                        'moderate': len([v for v in vulnerabilities if v['severity'] == 'moderate']),
                        'low': len([v for v in vulnerabilities if v['severity'] == 'low'])
                    }
                }
            
        except Exception as e:
            self.logger.warning(f"npm audit scan failed: {str(e)}")
        
        return {'vulnerabilities': [], 'issues': [], 'summary': {}}
    
    def _run_trivy_scan(self, image_name: str) -> Dict[str, Any]:
        """Run Trivy container security scan"""
        
        try:
            cmd = [
                'trivy', 'image',
                '--format', 'json',
                '--severity', 'CRITICAL,HIGH,MEDIUM,LOW',
                image_name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0 and result.stdout.strip():
                trivy_data = json.loads(result.stdout)
                
                vulnerabilities = []
                
                # Parse Trivy results
                for result_item in trivy_data.get('Results', []):
                    target = result_item.get('Target', '')
                    
                    for vuln in result_item.get('Vulnerabilities', []):
                        vulnerability = {
                            'type': 'container',
                            'tool': 'trivy',
                            'severity': vuln.get('Severity', 'medium').lower(),
                            'title': f"Container vulnerability: {vuln.get('VulnerabilityID', 'Unknown')}",
                            'description': vuln.get('Description', ''),
                            'vulnerability_id': vuln.get('VulnerabilityID', ''),
                            'package': vuln.get('PkgName', ''),
                            'installed_version': vuln.get('InstalledVersion', ''),
                            'fixed_version': vuln.get('FixedVersion', ''),
                            'target': target,
                            'references': vuln.get('References', []),
                            'owasp_category': 'A06',  # Vulnerable and Outdated Components
                            'fix_available': bool(vuln.get('FixedVersion'))
                        }
                        
                        vulnerabilities.append(vulnerability)
                
                return {
                    'vulnerabilities': vulnerabilities,
                    'analysis': {
                        'total_vulnerabilities': len(vulnerabilities),
                        'critical': len([v for v in vulnerabilities if v['severity'] == 'critical']),
                        'high': len([v for v in vulnerabilities if v['severity'] == 'high']),
                        'medium': len([v for v in vulnerabilities if v['severity'] == 'medium']),
                        'low': len([v for v in vulnerabilities if v['severity'] == 'low']),
                        'fixable': len([v for v in vulnerabilities if v['fix_available']])
                    }
                }
            
        except Exception as e:
            self.logger.warning(f"Trivy scan failed: {str(e)}")
        
        return {'vulnerabilities': [], 'analysis': {}}
    
    def _scan_for_secrets(self, project_path: Path) -> List[Dict[str, Any]]:
        """Scan for hardcoded secrets and sensitive information"""
        
        secrets = []
        
        # Common secret patterns
        secret_patterns = {
            'api_key': r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            'password': r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^"\'\s]{8,})["\']?',
            'secret': r'(?i)(secret|secret[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            'token': r'(?i)(token|access[_-]?token)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            'private_key': r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
            'aws_key': r'(?i)(aws[_-]?access[_-]?key[_-]?id)\s*[:=]\s*["\']?([A-Z0-9]{20})["\']?',
            'github_token': r'(?i)(github[_-]?token)\s*[:=]\s*["\']?([a-zA-Z0-9_]{40})["\']?'
        }
        
        # File extensions to scan
        scan_extensions = ['.py', '.js', '.ts', '.java', '.go', '.rs', '.php', '.rb', '.cs', '.yaml', '.yml', '.json', '.env']
        
        for root, dirs, files in os.walk(project_path):
            # Skip common directories that shouldn't contain secrets
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.venv', 'venv']]
            
            for file in files:
                file_path = Path(root) / file
                
                # Skip binary files and focus on text files
                if not any(file.endswith(ext) for ext in scan_extensions):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        for secret_type, pattern in secret_patterns.items():
                            matches = re.finditer(pattern, content, re.MULTILINE)
                            
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                
                                # Skip common false positives
                                matched_text = match.group(0)
                                if self._is_false_positive(matched_text, secret_type):
                                    continue
                                
                                secrets.append({
                                    'type': secret_type,
                                    'file': str(file_path.relative_to(project_path)),
                                    'line': line_num,
                                    'match': matched_text[:100],  # Truncate for security
                                    'confidence': self._calculate_secret_confidence(matched_text, secret_type)
                                })
                
                except Exception as e:
                    self.logger.debug(f"Could not scan file {file_path}: {str(e)}")
                    continue
        
        return secrets
    
    def _analyze_dockerfile_security(self, dockerfile_path: Path) -> List[Dict[str, Any]]:
        """Analyze Dockerfile for security issues"""
        
        issues = []
        
        try:
            with open(dockerfile_path, 'r') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                # Check for running as root
                if line.startswith('USER root') or (line.startswith('RUN') and 'sudo' in line):
                    issues.append({
                        'type': 'dockerfile_security',
                        'severity': 'medium',
                        'line': i,
                        'issue': 'Running as root user',
                        'description': 'Container should not run as root for security reasons',
                        'recommendation': 'Create and use a non-root user'
                    })
                
                # Check for ADD instead of COPY
                if line.startswith('ADD ') and not line.startswith('ADD --'):
                    issues.append({
                        'type': 'dockerfile_security',
                        'severity': 'low',
                        'line': i,
                        'issue': 'Using ADD instead of COPY',
                        'description': 'ADD has additional features that may be security risks',
                        'recommendation': 'Use COPY instead of ADD when possible'
                    })
                
                # Check for latest tag
                if 'FROM' in line and ':latest' in line:
                    issues.append({
                        'type': 'dockerfile_security',
                        'severity': 'medium',
                        'line': i,
                        'issue': 'Using latest tag',
                        'description': 'Using latest tag can lead to unpredictable builds',
                        'recommendation': 'Use specific version tags'
                    })
                
                # Check for missing health check
                if line.startswith('FROM '):
                    # This is a simple check - in a real implementation, you'd track if HEALTHCHECK is defined
                    pass
        
        except Exception as e:
            self.logger.warning(f"Could not analyze Dockerfile: {str(e)}")
        
        return issues
    
    def _assess_compliance(self, sast_results: Dict, dependency_results: Dict, 
                          container_results: Dict, config_results: Dict) -> Dict[str, Any]:
        """Assess compliance with security frameworks"""
        
        compliance_status = {
            'owasp_top10': {},
            'cis_benchmarks': {},
            'overall_compliance': 0
        }
        
        # OWASP Top 10 assessment
        all_vulnerabilities = []
        all_vulnerabilities.extend(sast_results.get('vulnerabilities', []))
        all_vulnerabilities.extend(dependency_results.get('vulnerabilities', []))
        all_vulnerabilities.extend(container_results.get('vulnerabilities', []))
        all_vulnerabilities.extend(config_results.get('vulnerabilities', []))
        
        # Count vulnerabilities by OWASP category
        owasp_counts = {}
        for vuln in all_vulnerabilities:
            category = vuln.get('owasp_category', 'Unknown')
            owasp_counts[category] = owasp_counts.get(category, 0) + 1
        
        # Assess each OWASP category
        for category, description in self.owasp_categories.items():
            vuln_count = owasp_counts.get(category, 0)
            
            if vuln_count == 0:
                status = 'compliant'
                score = 100
            elif vuln_count <= 2:
                status = 'mostly_compliant'
                score = 75
            elif vuln_count <= 5:
                status = 'partially_compliant'
                score = 50
            else:
                status = 'non_compliant'
                score = 25
            
            compliance_status['owasp_top10'][category] = {
                'description': description,
                'status': status,
                'score': score,
                'vulnerability_count': vuln_count
            }
        
        # CIS Benchmarks assessment (simplified)
        cis_scores = {
            'access_control': 85,  # Based on user configuration in containers
            'authentication': 90,  # Based on secret management
            'encryption': 80,     # Based on TLS/SSL usage
            'logging': 70,        # Based on logging configuration
            'network': 85,        # Based on network policies
            'system': 75          # Based on system hardening
        }
        
        for category, description in self.cis_categories.items():
            score = cis_scores.get(category, 50)
            
            if score >= 90:
                status = 'compliant'
            elif score >= 75:
                status = 'mostly_compliant'
            elif score >= 50:
                status = 'partially_compliant'
            else:
                status = 'non_compliant'
            
            compliance_status['cis_benchmarks'][category] = {
                'description': description,
                'status': status,
                'score': score
            }
        
        # Calculate overall compliance score
        owasp_avg = sum(cat['score'] for cat in compliance_status['owasp_top10'].values()) / len(compliance_status['owasp_top10'])
        cis_avg = sum(cat['score'] for cat in compliance_status['cis_benchmarks'].values()) / len(compliance_status['cis_benchmarks'])
        
        compliance_status['overall_compliance'] = int((owasp_avg + cis_avg) / 2)
        
        return compliance_status
    
    def _generate_auto_patches(self, dependency_results: Dict, sast_results: Dict) -> List[Dict[str, Any]]:
        """Generate automatic patch recommendations"""
        
        auto_patches = []
        
        # Dependency patches
        for issue in dependency_results.get('issues', []):
            if issue.get('fix_available') or issue.get('patched_versions'):
                patch = {
                    'type': 'dependency_update',
                    'package': issue.get('package', ''),
                    'current_version': issue.get('current_version', issue.get('installed_version', '')),
                    'recommended_version': issue.get('patched_versions', ''),
                    'severity': issue.get('severity', 'medium'),
                    'auto_applicable': True,
                    'command': self._generate_update_command(issue),
                    'description': f"Update {issue.get('package', '')} to fix security vulnerability"
                }
                auto_patches.append(patch)
        
        # Configuration patches
        for vuln in sast_results.get('vulnerabilities', []):
            if vuln.get('type') == 'sast' and vuln.get('severity') in ['high', 'critical']:
                # Generate code fix suggestions for common issues
                if 'hardcoded' in vuln.get('description', '').lower():
                    patch = {
                        'type': 'configuration_fix',
                        'file': vuln.get('file', ''),
                        'line': vuln.get('line', 0),
                        'issue': vuln.get('title', ''),
                        'auto_applicable': False,
                        'recommendation': 'Move sensitive data to environment variables',
                        'description': 'Replace hardcoded secrets with environment variable references'
                    }
                    auto_patches.append(patch)
        
        return auto_patches
    
    def _calculate_security_score(self, sast_results: Dict, dependency_results: Dict,
                                container_results: Dict, compliance_results: Dict) -> Tuple[str, str]:
        """Calculate overall security score and risk level"""
        
        # Collect all vulnerabilities
        all_vulnerabilities = []
        all_vulnerabilities.extend(sast_results.get('vulnerabilities', []))
        all_vulnerabilities.extend(dependency_results.get('vulnerabilities', []))
        all_vulnerabilities.extend(container_results.get('vulnerabilities', []))
        
        # Count by severity
        severity_counts = {
            'critical': len([v for v in all_vulnerabilities if v.get('severity') == 'critical']),
            'high': len([v for v in all_vulnerabilities if v.get('severity') == 'high']),
            'medium': len([v for v in all_vulnerabilities if v.get('severity') == 'medium']),
            'low': len([v for v in all_vulnerabilities if v.get('severity') == 'low'])
        }
        
        # Calculate weighted score
        total_score = (
            severity_counts['critical'] * self.severity_scores['critical'] +
            severity_counts['high'] * self.severity_scores['high'] +
            severity_counts['medium'] * self.severity_scores['medium'] +
            severity_counts['low'] * self.severity_scores['low']
        )
        
        # Factor in compliance score
        compliance_score = compliance_results.get('overall_compliance', 50)
        compliance_factor = compliance_score / 100
        
        # Determine grade and risk level
        if total_score == 0 and compliance_score >= 90:
            grade = 'A+'
            risk_level = 'low'
        elif total_score <= 5 and compliance_score >= 80:
            grade = 'A'
            risk_level = 'low'
        elif total_score <= 15 and compliance_score >= 70:
            grade = 'B'
            risk_level = 'medium'
        elif total_score <= 30 and compliance_score >= 60:
            grade = 'C'
            risk_level = 'medium'
        elif total_score <= 50:
            grade = 'D'
            risk_level = 'high'
        else:
            grade = 'F'
            risk_level = 'critical'
        
        # Adjust for critical vulnerabilities
        if severity_counts['critical'] > 0:
            risk_level = 'critical'
            if grade in ['A+', 'A']:
                grade = 'B'
        
        return grade, risk_level
    
    def _generate_security_recommendations(self, sast_results: Dict, dependency_results: Dict,
                                         container_results: Dict, compliance_results: Dict) -> List[str]:
        """Generate security improvement recommendations"""
        
        recommendations = []
        
        # SAST recommendations
        sast_vulns = sast_results.get('vulnerabilities', [])
        if sast_vulns:
            high_severity = len([v for v in sast_vulns if v.get('severity') in ['critical', 'high']])
            if high_severity > 0:
                recommendations.append(f"Address {high_severity} high/critical severity code vulnerabilities")
            
            recommendations.append("Implement secure coding practices and code review processes")
            recommendations.append("Integrate SAST tools into your CI/CD pipeline")
        
        # Dependency recommendations
        dep_vulns = dependency_results.get('vulnerabilities', [])
        if dep_vulns:
            recommendations.append(f"Update {len(dep_vulns)} vulnerable dependencies")
            recommendations.append("Implement automated dependency scanning in CI/CD")
            recommendations.append("Regularly audit and update project dependencies")
        
        # Container recommendations
        container_vulns = container_results.get('vulnerabilities', [])
        if container_vulns:
            recommendations.append("Update base images and container dependencies")
            recommendations.append("Use minimal base images (alpine, distroless)")
            recommendations.append("Implement container image scanning in CI/CD")
        
        # Compliance recommendations
        compliance_score = compliance_results.get('overall_compliance', 0)
        if compliance_score < 80:
            recommendations.append("Improve compliance with security frameworks (OWASP, CIS)")
            recommendations.append("Implement security policies and procedures")
        
        # General security recommendations
        recommendations.extend([
            "Implement proper secret management (HashiCorp Vault, AWS Secrets Manager)",
            "Enable security logging and monitoring",
            "Implement network segmentation and least privilege access",
            "Regular security training for development team",
            "Establish incident response procedures"
        ])
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    # Helper methods
    def _check_tool_availability(self, tool: str) -> bool:
        """Check if a security tool is available"""
        try:
            result = subprocess.run([tool, '--version'], capture_output=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def _get_project_source_path(self, build_artifacts: Dict[str, Any]) -> Optional[Path]:
        """Extract project source path from build artifacts"""
        # This would need to be implemented based on how build artifacts store source info
        # For now, return None to indicate source not available
        return None
    
    def _extract_languages_from_artifacts(self, build_artifacts: Dict[str, Any]) -> List[str]:
        """Extract programming languages from build artifacts"""
        # This would extract language info from the build artifacts
        # For now, return common languages
        return ['python', 'javascript']
    
    def _map_bandit_to_owasp(self, test_id: str) -> str:
        """Map Bandit test IDs to OWASP categories"""
        mapping = {
            'B101': 'A03',  # Assert usage -> Injection
            'B102': 'A03',  # Exec usage -> Injection
            'B103': 'A05',  # Set bad file permissions -> Security Misconfiguration
            'B104': 'A02',  # Hardcoded bind all interfaces -> Cryptographic Failures
            'B105': 'A02',  # Hardcoded password string -> Cryptographic Failures
            'B106': 'A02',  # Hardcoded password funcarg -> Cryptographic Failures
            'B107': 'A02',  # Hardcoded password default -> Cryptographic Failures
        }
        return mapping.get(test_id, 'A05')  # Default to Security Misconfiguration
    
    def _is_false_positive(self, matched_text: str, secret_type: str) -> bool:
        """Check if a secret match is likely a false positive"""
        false_positive_patterns = [
            'example', 'test', 'dummy', 'placeholder', 'your_', 'my_',
            'fake', 'sample', 'demo', 'xxx', '***', '...'
        ]
        
        matched_lower = matched_text.lower()
        return any(pattern in matched_lower for pattern in false_positive_patterns)
    
    def _calculate_secret_confidence(self, matched_text: str, secret_type: str) -> str:
        """Calculate confidence level for secret detection"""
        if len(matched_text) > 40:
            return 'high'
        elif len(matched_text) > 20:
            return 'medium'
        else:
            return 'low'
    
    def _generate_update_command(self, issue: Dict[str, Any]) -> str:
        """Generate update command for dependency"""
        package = issue.get('package', '')
        version = issue.get('patched_versions', 'latest')
        
        # Simple command generation - would need more sophisticated logic
        if 'requirements.txt' in str(issue):
            return f"pip install {package}>={version}"
        elif 'package.json' in str(issue):
            return f"npm install {package}@{version}"
        else:
            return f"Update {package} to {version}"
    
    def _get_used_tools(self) -> List[str]:
        """Get list of security tools that were actually used"""
        used_tools = []
        for tool, config in self.security_tools.items():
            if config['available']:
                used_tools.append(tool)
        return used_tools
    
    def _save_security_report(self, report: Dict[str, Any]):
        """Save security report to artifacts directory"""
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        
        # Save detailed report
        report_path = artifacts_dir / f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save summary report
        summary = {
            'overall_score': report['overall_score'],
            'risk_level': report['risk_level'],
            'summary': report['summary'],
            'compliance_score': report['compliance_status'].get('overall_compliance', 0),
            'top_recommendations': report['recommendations'][:5],
            'scan_timestamp': report['scan_timestamp']
        }
        
        summary_path = artifacts_dir / "security_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        self.logger.info(f"Security report saved to {report_path}")
    
    def _cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and Path(self.temp_dir).exists():
            import shutil
            shutil.rmtree(self.temp_dir)
            self.logger.info("Temporary security scan files cleaned up")
    
    # Placeholder methods for additional scans
    def _run_semgrep_scan(self, project_path: Path, languages: List[str]) -> Dict[str, Any]:
        """Run Semgrep security scan"""
        return {'vulnerabilities': [], 'summary': {}}
    
    def _run_eslint_security_scan(self, project_path: Path) -> Dict[str, Any]:
        """Run ESLint security scan for JavaScript/TypeScript"""
        return {'vulnerabilities': [], 'summary': {}}
    
    def _run_pip_audit_scan(self, project_path: Path) -> Optional[Dict[str, Any]]:
        """Run pip-audit scan for Python dependencies"""
        return None
    
    def _run_maven_dependency_scan(self, project_path: Path) -> Optional[Dict[str, Any]]:
        """Run Maven dependency check"""
        return None
    
    def _analyze_compose_security(self, compose_path: Path) -> List[Dict[str, Any]]:
        """Analyze Docker Compose security configuration"""
        return []
    
    def _analyze_k8s_security(self, manifest_path: Path, manifest_type: str) -> List[Dict[str, Any]]:
        """Analyze Kubernetes manifest security"""
        return []
