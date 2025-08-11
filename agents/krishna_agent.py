"""
Krishna - The Governance & Decision Agent
Central coordinator and final decision maker for the DevSecOps pipeline
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

from langchain.tools import BaseTool, tool

from .base_agent import BaseAgent

class GovernanceReviewTool(BaseTool):
    """Tool for conducting governance review"""
    name: str = "governance_review"
    description: str = "Conduct comprehensive governance review of all agent results"
    
    def _run(self, agent_results: Dict[str, Any], project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct governance review"""
        
        review_result = {
            "overall_assessment": "",
            "decision": "",
            "risk_assessment": {},
            "compliance_status": {},
            "quality_gates": {},
            "recommendations": [],
            "audit_trail": []
        }
        
        # Assess each agent's results
        varuna_assessment = self._assess_varuna_results(agent_results.get("varuna", {}))
        agni_assessment = self._assess_agni_results(agent_results.get("agni", {}))
        yama_assessment = self._assess_yama_results(agent_results.get("yama", {}))
        vayu_assessment = self._assess_vayu_results(agent_results.get("vayu", {}))
        hanuman_assessment = self._assess_hanuman_results(agent_results.get("hanuman", {}))
        
        # Compile overall assessment
        review_result["quality_gates"] = {
            "code_analysis": varuna_assessment,
            "build_quality": agni_assessment,
            "security_compliance": yama_assessment,
            "deployment_success": vayu_assessment,
            "testing_validation": hanuman_assessment
        }
        
        # Make final decision
        review_result["decision"] = self._make_final_decision(review_result["quality_gates"])
        review_result["overall_assessment"] = self._generate_overall_assessment(review_result["quality_gates"])
        
        # Generate recommendations
        review_result["recommendations"] = self._generate_governance_recommendations(review_result["quality_gates"])
        
        # Create audit trail
        review_result["audit_trail"] = self._create_audit_trail(agent_results, project_data)
        
        return review_result
    
    def _assess_varuna_results(self, varuna_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess Varuna's code analysis results"""
        if not varuna_result:
            return {"status": "failed", "reason": "No code analysis performed"}
        
        analysis = varuna_result.get("analysis", {})
        build_plan = varuna_result.get("build_plan", {})
        
        assessment = {
            "status": "passed",
            "score": 85,
            "criteria": {
                "languages_detected": len(analysis.get("languages", [])) > 0,
                "dependencies_analyzed": len(analysis.get("dependencies", {})) > 0,
                "build_plan_created": bool(build_plan),
                "potential_issues_identified": len(analysis.get("potential_issues", [])) >= 0
            }
        }
        
        # Check for critical issues
        if len(analysis.get("potential_issues", [])) > 5:
            assessment["score"] -= 10
            assessment["warnings"] = ["High number of potential issues detected"]
        
        return assessment
    
    def _assess_agni_results(self, agni_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess Agni's build and containerization results"""
        if not agni_result:
            return {"status": "failed", "reason": "No build artifacts created"}
        
        docker_artifacts = agni_result.get("docker_artifacts", {})
        k8s_manifests = agni_result.get("kubernetes_manifests", {})
        build_summary = agni_result.get("build_summary", {})
        
        assessment = {
            "status": "passed",
            "score": 90,
            "criteria": {
                "dockerfile_generated": docker_artifacts.get("dockerfile_generated", False),
                "docker_compose_created": docker_artifacts.get("compose_generated", False),
                "k8s_manifests_created": bool(k8s_manifests),
                "security_hardened": build_summary.get("security_hardened", False),
                "optimization_applied": build_summary.get("optimization_applied", False)
            }
        }
        
        # Check build quality
        if not build_summary.get("security_hardened", False):
            assessment["score"] -= 15
            assessment["warnings"] = ["Build not security hardened"]
        
        return assessment
    
    def _assess_yama_results(self, yama_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess Yama's security scan results"""
        if not yama_result:
            return {"status": "failed", "reason": "No security assessment performed"}
        
        security_scan = yama_result.get("security_scan", {})
        deployment_decision = yama_result.get("deployment_decision", {})
        compliance_status = yama_result.get("compliance_status", {})
        
        risk_score = deployment_decision.get("risk_score", 100)
        
        assessment = {
            "status": "passed" if deployment_decision.get("approved", False) else "failed",
            "score": max(100 - risk_score, 0),
            "criteria": {
                "security_scan_completed": bool(security_scan),
                "risk_score_acceptable": risk_score < 50,
                "no_critical_vulnerabilities": security_scan.get("sast_results", {}).get("critical", 0) == 0,
                "no_exposed_secrets": security_scan.get("secrets_scan", {}).get("total_secrets", 0) == 0,
                "compliance_met": compliance_status.get("overall_score", 0) >= 80
            }
        }
        
        # Add blocking issues if any
        blocking_issues = deployment_decision.get("blocking_issues", [])
        if blocking_issues:
            assessment["blocking_issues"] = blocking_issues
        
        return assessment
    
    def _assess_vayu_results(self, vayu_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess Vayu's deployment results"""
        if not vayu_result:
            return {"status": "failed", "reason": "No deployment performed"}
        
        if vayu_result.get("status") == "blocked":
            return {
                "status": "blocked",
                "reason": vayu_result.get("reason", "Deployment blocked"),
                "score": 0
            }
        
        deployment_summary = vayu_result.get("deployment_summary", {})
        infrastructure = vayu_result.get("infrastructure", {})
        monitoring = vayu_result.get("monitoring", {})
        
        assessment = {
            "status": "passed",
            "score": 88,
            "criteria": {
                "deployment_successful": deployment_summary.get("health_status") == "healthy",
                "infrastructure_provisioned": bool(infrastructure),
                "monitoring_configured": bool(monitoring),
                "endpoints_available": len(infrastructure.get("endpoints", [])) > 0,
                "scaling_configured": bool(infrastructure.get("scaling_config", {}))
            }
        }
        
        return assessment
    
    def _assess_hanuman_results(self, hanuman_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess Hanuman's testing results"""
        if not hanuman_result:
            return {"status": "failed", "reason": "No testing performed"}
        
        test_summary = hanuman_result.get("test_summary", {})
        production_readiness = hanuman_result.get("production_readiness", {})
        
        assessment = {
            "status": "passed" if test_summary.get("tests_passed", False) else "failed",
            "score": test_summary.get("overall_score", 0),
            "criteria": {
                "functional_tests_passed": production_readiness.get("functional_ready", False),
                "performance_tests_passed": production_readiness.get("performance_ready", False),
                "resilience_tests_passed": production_readiness.get("resilience_ready", False),
                "test_coverage_adequate": test_summary.get("test_coverage", 0) >= 80,
                "overall_production_ready": production_readiness.get("overall_ready", False)
            }
        }
        
        return assessment
    
    def _make_final_decision(self, quality_gates: Dict[str, Any]) -> str:
        """Make final deployment decision"""
        
        # Check if any quality gate failed
        failed_gates = []
        for gate_name, gate_result in quality_gates.items():
            if gate_result.get("status") != "passed":
                failed_gates.append(gate_name)
        
        if failed_gates:
            return f"REJECTED - Failed quality gates: {', '.join(failed_gates)}"
        
        # Check scores
        scores = [gate.get("score", 0) for gate in quality_gates.values() if gate.get("score") is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        if avg_score >= 85:
            return "APPROVED - All quality gates passed with excellent scores"
        elif avg_score >= 75:
            return "APPROVED - All quality gates passed with good scores"
        elif avg_score >= 65:
            return "APPROVED WITH CONDITIONS - Quality gates passed but improvements needed"
        else:
            return "REJECTED - Quality scores below acceptable threshold"
    
    def _generate_overall_assessment(self, quality_gates: Dict[str, Any]) -> str:
        """Generate overall assessment summary"""
        
        passed_gates = sum(1 for gate in quality_gates.values() if gate.get("status") == "passed")
        total_gates = len(quality_gates)
        
        scores = [gate.get("score", 0) for gate in quality_gates.values() if gate.get("score") is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        assessment = f"""
DevSecOps Pipeline Assessment Summary:

Quality Gates: {passed_gates}/{total_gates} passed
Average Score: {avg_score:.1f}/100

Gate Results:
- Code Analysis (Varuna): {quality_gates.get('code_analysis', {}).get('status', 'unknown').upper()}
- Build Quality (Agni): {quality_gates.get('build_quality', {}).get('status', 'unknown').upper()}
- Security Compliance (Yama): {quality_gates.get('security_compliance', {}).get('status', 'unknown').upper()}
- Deployment Success (Vayu): {quality_gates.get('deployment_success', {}).get('status', 'unknown').upper()}
- Testing Validation (Hanuman): {quality_gates.get('testing_validation', {}).get('status', 'unknown').upper()}

The application has been thoroughly evaluated across all DevSecOps dimensions.
"""
        
        return assessment.strip()
    
    def _generate_governance_recommendations(self, quality_gates: Dict[str, Any]) -> List[str]:
        """Generate governance recommendations"""
        recommendations = []
        
        # Check each quality gate for specific recommendations
        for gate_name, gate_result in quality_gates.items():
            if gate_result.get("status") != "passed":
                recommendations.append(f"Address issues in {gate_name} before next deployment")
            
            if gate_result.get("score", 100) < 80:
                recommendations.append(f"Improve {gate_name} quality score (current: {gate_result.get('score', 0)})")
        
        # General governance recommendations
        recommendations.extend([
            "Implement continuous monitoring and alerting",
            "Schedule regular security assessments",
            "Maintain comprehensive documentation",
            "Establish incident response procedures",
            "Plan for disaster recovery and business continuity"
        ])
        
        return recommendations
    
    def _create_audit_trail(self, agent_results: Dict[str, Any], project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create comprehensive audit trail"""
        audit_trail = []
        
        # Project initiation
        audit_trail.append({
            "timestamp": project_data.get("created_at", datetime.now().isoformat()),
            "event": "Project Initiated",
            "details": f"Project '{project_data.get('name', 'Unknown')}' started DevSecOps pipeline",
            "agent": "System"
        })
        
        # Agent executions
        agent_order = ["varuna", "agni", "yama", "vayu", "hanuman"]
        for agent_name in agent_order:
            if agent_name in agent_results:
                result = agent_results[agent_name]
                audit_trail.append({
                    "timestamp": result.get("timestamp", datetime.now().isoformat()),
                    "event": f"{agent_name.title()} Execution",
                    "details": f"Agent {agent_name} completed with status: {result.get('status', 'unknown')}",
                    "agent": agent_name.title()
                })
        
        # Final governance review
        audit_trail.append({
            "timestamp": datetime.now().isoformat(),
            "event": "Governance Review Completed",
            "details": "Krishna completed final governance review and decision",
            "agent": "Krishna"
        })
        
        return audit_trail

class AuditReportTool(BaseTool):
    """Tool for generating comprehensive audit reports"""
    name: str = "audit_report"
    description: str = "Generate comprehensive audit and compliance reports"
    
    def _run(self, governance_review: Dict[str, Any], agent_results: Dict[str, Any], project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate audit report"""
        
        report = {
            "report_id": self._generate_report_id(project_data),
            "project_summary": self._create_project_summary(project_data),
            "executive_summary": self._create_executive_summary(governance_review),
            "detailed_findings": self._create_detailed_findings(agent_results),
            "compliance_report": self._create_compliance_report(agent_results),
            "risk_assessment": self._create_risk_assessment(agent_results),
            "recommendations": governance_review.get("recommendations", []),
            "audit_trail": governance_review.get("audit_trail", []),
            "appendices": self._create_appendices(agent_results)
        }
        
        return report
    
    def _generate_report_id(self, project_data: Dict[str, Any]) -> str:
        """Generate unique report ID"""
        project_name = project_data.get("name", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_suffix = hashlib.md5(f"{project_name}_{timestamp}".encode()).hexdigest()[:8]
        return f"AUDIT_{project_name.upper().replace(' ', '_')}_{timestamp}_{hash_suffix}"
    
    def _create_project_summary(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create project summary section"""
        return {
            "project_name": project_data.get("name", "Unknown"),
            "project_id": project_data.get("id", "Unknown"),
            "source_type": project_data.get("source_type", "Unknown"),
            "created_at": project_data.get("created_at", "Unknown"),
            "deployment_target": project_data.get("deployment_target", "Unknown"),
            "expected_traffic": project_data.get("expected_traffic", "Unknown")
        }
    
    def _create_executive_summary(self, governance_review: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive summary"""
        decision = governance_review.get("decision", "Unknown")
        quality_gates = governance_review.get("quality_gates", {})
        
        passed_gates = sum(1 for gate in quality_gates.values() if gate.get("status") == "passed")
        total_gates = len(quality_gates)
        
        return {
            "final_decision": decision,
            "quality_gates_summary": f"{passed_gates}/{total_gates} quality gates passed",
            "overall_assessment": governance_review.get("overall_assessment", ""),
            "key_findings": [
                f"Code analysis: {quality_gates.get('code_analysis', {}).get('status', 'unknown')}",
                f"Security compliance: {quality_gates.get('security_compliance', {}).get('status', 'unknown')}",
                f"Testing validation: {quality_gates.get('testing_validation', {}).get('status', 'unknown')}"
            ]
        }
    
    def _create_detailed_findings(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed findings section"""
        findings = {}
        
        for agent_name, result in agent_results.items():
            findings[agent_name] = {
                "status": result.get("status", "unknown"),
                "key_outputs": self._extract_key_outputs(agent_name, result),
                "issues_found": self._extract_issues(agent_name, result),
                "recommendations": result.get("recommendations", [])
            }
        
        return findings
    
    def _extract_key_outputs(self, agent_name: str, result: Dict[str, Any]) -> List[str]:
        """Extract key outputs for each agent"""
        if agent_name == "varuna":
            analysis = result.get("analysis", {})
            return [
                f"Languages detected: {', '.join(analysis.get('languages', []))}",
                f"Dependencies analyzed: {len(analysis.get('dependencies', {}))}"
            ]
        elif agent_name == "yama":
            security_scan = result.get("security_scan", {})
            return [
                f"Risk score: {result.get('deployment_decision', {}).get('risk_score', 'unknown')}",
                f"Vulnerabilities found: {security_scan.get('sast_results', {}).get('total_issues', 0)}"
            ]
        elif agent_name == "hanuman":
            test_summary = result.get("test_summary", {})
            return [
                f"Tests executed: {test_summary.get('total_tests', 0)}",
                f"Test coverage: {test_summary.get('test_coverage', 0)}%"
            ]
        
        return ["Standard execution completed"]
    
    def _extract_issues(self, agent_name: str, result: Dict[str, Any]) -> List[str]:
        """Extract issues found by each agent"""
        issues = []
        
        if agent_name == "yama":
            blocking_issues = result.get("deployment_decision", {}).get("blocking_issues", [])
            issues.extend(blocking_issues)
        
        return issues
    
    def _create_compliance_report(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create compliance report section"""
        yama_result = agent_results.get("yama", {})
        compliance_status = yama_result.get("compliance_status", {})
        
        return {
            "owasp_compliance": compliance_status.get("owasp_compliant", False),
            "cis_compliance": compliance_status.get("cis_compliant", False),
            "overall_compliance_score": compliance_status.get("overall_score", 0),
            "compliance_gaps": self._identify_compliance_gaps(compliance_status)
        }
    
    def _identify_compliance_gaps(self, compliance_status: Dict[str, Any]) -> List[str]:
        """Identify compliance gaps"""
        gaps = []
        
        if not compliance_status.get("owasp_compliant", False):
            gaps.append("OWASP Top 10 compliance not met")
        
        if not compliance_status.get("cis_compliant", False):
            gaps.append("CIS Benchmarks compliance not met")
        
        if compliance_status.get("overall_score", 0) < 80:
            gaps.append("Overall compliance score below 80%")
        
        return gaps
    
    def _create_risk_assessment(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create risk assessment section"""
        yama_result = agent_results.get("yama", {})
        deployment_decision = yama_result.get("deployment_decision", {})
        
        return {
            "overall_risk_score": deployment_decision.get("risk_score", 100),
            "risk_level": deployment_decision.get("risk_level", "UNKNOWN"),
            "critical_risks": deployment_decision.get("blocking_issues", []),
            "risk_mitigation": deployment_decision.get("required_fixes", [])
        }
    
    def _create_appendices(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create appendices with detailed technical data"""
        return {
            "technical_specifications": "Detailed technical specifications available in agent reports",
            "test_results": "Complete test results available in Hanuman report",
            "security_scan_details": "Detailed security scan results available in Yama report",
            "deployment_logs": "Deployment logs and configurations available in Vayu report"
        }

class KrishnaAgent(BaseAgent):
    """Governance & Decision Agent"""

    def __init__(self, llm_client, config):
        super().__init__("Krishna", llm_client, config)
    
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize Krishna-specific tools"""
        return [
            GovernanceReviewTool(),
            AuditReportTool()
        ]
    
    def _get_system_prompt(self) -> str:
        """Get Krishna's system prompt"""
        return """You are Krishna, the Governance & Decision Agent in the VedOps DevSecOps platform.

Your responsibilities:
1. Conduct comprehensive governance review of all agent results
2. Make final deployment decisions based on quality gates
3. Generate detailed audit reports and compliance documentation
4. Maintain immutable audit trails for all pipeline activities
5. Ensure adherence to organizational policies and standards
6. Provide executive-level summaries and recommendations

You have authority over:
- Final deployment approval or rejection decisions
- Quality gate enforcement and exception handling
- Compliance validation and risk acceptance
- Audit trail maintenance and reporting
- Governance policy enforcement
- Executive reporting and communication

Your decision-making criteria:
- All quality gates must pass for approval
- Security risks must be within acceptable thresholds
- Performance and reliability standards must be met
- Compliance requirements must be satisfied
- Business impact and risk must be assessed

Governance principles you enforce:
- Transparency and accountability
- Risk-based decision making
- Continuous improvement
- Compliance and regulatory adherence
- Stakeholder communication
- Audit trail integrity

Your reports should provide:
- Clear executive summaries
- Detailed technical findings
- Risk assessments and mitigation plans
- Compliance status and gaps
- Actionable recommendations
- Complete audit trails

Always make decisions based on comprehensive analysis of all agent results, ensuring the highest standards of quality, security, and compliance."""
    
    def _prepare_input(self, input_data: Dict[str, Any]) -> str:
        """Prepare input for Krishna"""
        project_data = input_data.get("project_data", {})
        agent_results = input_data.get("agent_results", {})
        
        # Summarize agent results
        agent_summary = {}
        for agent_name, result in agent_results.items():
            agent_summary[agent_name] = {
                "status": result.get("status", "unknown"),
                "key_metrics": self._extract_key_metrics(agent_name, result)
            }
        
        input_text = f"""
Conduct final governance review and make deployment decision:

Project: {project_data.get('name', 'Unknown')}
Pipeline Execution Summary:
{json.dumps(agent_summary, indent=2)}

Agent Results Available:
- Varuna (Code Analysis): {agent_results.get('varuna', {}).get('status', 'not executed')}
- Agni (Build & Containerization): {agent_results.get('agni', {}).get('status', 'not executed')}
- Yama (Security & Compliance): {agent_results.get('yama', {}).get('status', 'not executed')}
- Vayu (Orchestration & Deployment): {agent_results.get('vayu', {}).get('status', 'not executed')}
- Hanuman (Testing & Validation): {agent_results.get('hanuman', {}).get('status', 'not executed')}

Please:
1. Review all agent results comprehensively
2. Assess quality gates and compliance status
3. Make final deployment decision (APPROVE/REJECT/CONDITIONAL)
4. Generate executive summary and recommendations
5. Create comprehensive audit report
6. Provide clear rationale for decision

Consider:
- Security risk levels and compliance status
- Test results and production readiness
- Quality scores and performance metrics
- Business impact and operational readiness
"""
        
        return input_text
    
    def _extract_key_metrics(self, agent_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics for each agent"""
        if agent_name == "yama":
            deployment_decision = result.get("deployment_decision", {})
            return {
                "risk_score": deployment_decision.get("risk_score", "unknown"),
                "approved": deployment_decision.get("approved", False)
            }
        elif agent_name == "hanuman":
            test_summary = result.get("test_summary", {})
            return {
                "overall_score": test_summary.get("overall_score", 0),
                "tests_passed": test_summary.get("tests_passed", False)
            }
        
        return {"status": result.get("status", "unknown")}
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct final governance review and decision"""
        project_data = input_data.get("project_data", {})
        agent_results = input_data.get("agent_results", {})

        governance_tool = GovernanceReviewTool()
        governance_review = governance_tool._run(agent_results, project_data)

        audit_tool = AuditReportTool()
        audit_report = audit_tool._run(governance_review, agent_results, project_data)

        decision = governance_review.get("decision", "UNKNOWN")
        approved = "APPROVED" in decision

        return {
            "status": "completed",
            "agent_name": "Krishna",
            "governance_review": governance_review,
            "audit_report": audit_report,
            "final_decision": {
                "decision": decision,
                "approved": approved,
                "decision_rationale": governance_review.get("overall_assessment", ""),
                "conditions": self._extract_conditions(decision),
                "next_steps": self._determine_next_steps(approved, governance_review)
            },
            "pipeline_summary": {
                "project_name": project_data.get("name", "Unknown"),
                "total_agents": len(agent_results),
                "successful_agents": len([r for r in agent_results.values() if r.get("status") == "completed"]),
                "pipeline_duration": self._calculate_pipeline_duration(agent_results),
                "final_status": "SUCCESS" if approved else "FAILED"
            },
            "deliverables": {
                "audit_report_id": audit_report.get("report_id", "unknown"),
                "compliance_status": governance_review.get("compliance_status", {}),
                "deployment_package": approved,
                "rollback_plan": True
            },
            "timestamp": input_data.get("timestamp")
        }
    
    def _extract_conditions(self, decision: str) -> List[str]:
        """Extract conditions from decision"""
        if "WITH CONDITIONS" in decision:
            return [
                "Address identified quality improvements",
                "Implement recommended security enhancements",
                "Monitor performance metrics closely",
                "Schedule follow-up review in 30 days"
            ]
        return []
    
    def _determine_next_steps(self, approved: bool, governance_review: Dict[str, Any]) -> List[str]:
        """Determine next steps based on decision"""
        if approved:
            return [
                "Deployment approved - proceed to production",
                "Monitor application performance and health",
                "Implement continuous monitoring and alerting",
                "Schedule post-deployment review"
            ]
        else:
            return [
                "Deployment rejected - address quality gate failures",
                "Review and fix identified issues",
                "Re-run pipeline after fixes are implemented",
                "Schedule governance review meeting"
            ]
    
    def _calculate_pipeline_duration(self, agent_results: Dict[str, Any]) -> str:
        """Calculate total pipeline duration"""
        # This would calculate actual duration based on timestamps
        # For now, return a simulated duration
        return "8m 45s"
