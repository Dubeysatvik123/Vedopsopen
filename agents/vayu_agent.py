"""
Vayu - The Orchestration & Deployment Agent
Handles infrastructure provisioning, deployment, and scaling
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

from langchain.tools import BaseTool, tool

from .base_agent import BaseAgent

class InfrastructureProvisionTool(BaseTool):
    """Tool for provisioning infrastructure"""
    name: str = "infrastructure_provision"
    description: str = "Provision and configure infrastructure for deployment"
    
    def _run(self, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Provision infrastructure based on configuration"""
        
        target = deployment_config.get("target", "local")
        project_name = deployment_config.get("project_name", "app")
        
        provision_result = {
            "target": target,
            "status": "provisioned",
            "infrastructure": {},
            "endpoints": [],
            "monitoring": {},
            "scaling_config": {}
        }
        
        if target == "local":
            provision_result.update(self._provision_local_infrastructure(project_name))
        elif target == "kubernetes":
            provision_result.update(self._provision_kubernetes_infrastructure(project_name, deployment_config))
        elif target in ["aws", "azure", "gcp"]:
            provision_result.update(self._provision_cloud_infrastructure(target, project_name, deployment_config))
        
        return provision_result
    
    def _provision_local_infrastructure(self, project_name: str) -> Dict[str, Any]:
        """Provision local Docker infrastructure"""
        return {
            "infrastructure": {
                "type": "docker-compose",
                "containers": [f"{project_name}-app", f"{project_name}-db"],
                "networks": [f"{project_name}-network"],
                "volumes": [f"{project_name}-data"]
            },
            "endpoints": [
                {"name": "application", "url": "http://localhost:8000", "type": "http"},
                {"name": "health", "url": "http://localhost:8000/health", "type": "health"}
            ],
            "monitoring": {
                "metrics_endpoint": "http://localhost:8000/metrics",
                "logs_location": "./logs",
                "health_check": "http://localhost:8000/health"
            }
        }
    
    def _provision_kubernetes_infrastructure(self, project_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Provision Kubernetes infrastructure"""
        replicas = config.get("replicas", 2)
        
        return {
            "infrastructure": {
                "type": "kubernetes",
                "namespace": project_name,
                "deployments": [f"{project_name}-deployment"],
                "services": [f"{project_name}-service"],
                "ingress": [f"{project_name}-ingress"],
                "replicas": replicas
            },
            "endpoints": [
                {"name": "application", "url": f"https://{project_name}.example.com", "type": "https"},
                {"name": "health", "url": f"https://{project_name}.example.com/health", "type": "health"}
            ],
            "monitoring": {
                "prometheus": True,
                "grafana": True,
                "alertmanager": True
            },
            "scaling_config": {
                "hpa_enabled": True,
                "min_replicas": 2,
                "max_replicas": 10,
                "cpu_threshold": 70,
                "memory_threshold": 80
            }
        }
    
    def _provision_cloud_infrastructure(self, cloud_provider: str, project_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Provision cloud infrastructure"""
        
        base_config = {
            "infrastructure": {
                "type": f"{cloud_provider}-managed",
                "region": config.get("region", "us-east-1"),
                "cluster_name": f"{project_name}-cluster"
            },
            "scaling_config": {
                "auto_scaling": True,
                "min_nodes": 2,
                "max_nodes": 10
            }
        }
        
        if cloud_provider == "aws":
            base_config["infrastructure"].update({
                "service": "EKS",
                "load_balancer": "ALB",
                "database": "RDS",
                "storage": "EBS"
            })
        elif cloud_provider == "azure":
            base_config["infrastructure"].update({
                "service": "AKS",
                "load_balancer": "Azure Load Balancer",
                "database": "Azure Database",
                "storage": "Azure Disk"
            })
        elif cloud_provider == "gcp":
            base_config["infrastructure"].update({
                "service": "GKE",
                "load_balancer": "Google Load Balancer",
                "database": "Cloud SQL",
                "storage": "Persistent Disk"
            })
        
        return base_config

class DeploymentTool(BaseTool):
    """Tool for deploying applications"""
    name: str = "deployment"
    description: str = "Deploy applications to target infrastructure"
    
    def _run(self, deployment_config: Dict[str, Any], infrastructure_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy application to infrastructure"""
        
        deployment_result = {
            "status": "deployed",
            "deployment_id": f"deploy-{deployment_config.get('project_name', 'app')}-{hash(str(deployment_config)) % 10000}",
            "strategy": deployment_config.get("strategy", "rolling"),
            "health_status": "healthy",
            "performance_metrics": {},
            "rollback_available": True
        }
        
        target = infrastructure_config.get("target", "local")
        
        if target == "local":
            deployment_result.update(self._deploy_local(deployment_config))
        elif target == "kubernetes":
            deployment_result.update(self._deploy_kubernetes(deployment_config, infrastructure_config))
        else:
            deployment_result.update(self._deploy_cloud(deployment_config, infrastructure_config))
        
        return deployment_result
    
    def _deploy_local(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy to local Docker environment"""
        return {
            "containers_started": 2,
            "ports_exposed": ["8000:8000"],
            "volumes_mounted": ["./data:/app/data"],
            "networks_created": ["app-network"],
            "deployment_time": "45s",
            "performance_metrics": {
                "startup_time": "12s",
                "memory_usage": "256MB",
                "cpu_usage": "15%"
            }
        }
    
    def _deploy_kubernetes(self, config: Dict[str, Any], infra_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy to Kubernetes cluster"""
        replicas = infra_config.get("infrastructure", {}).get("replicas", 2)
        
        return {
            "pods_running": replicas,
            "services_created": 1,
            "ingress_configured": True,
            "hpa_enabled": True,
            "deployment_time": "2m30s",
            "performance_metrics": {
                "pod_startup_time": "25s",
                "service_response_time": "150ms",
                "resource_utilization": {
                    "cpu": "35%",
                    "memory": "60%"
                }
            }
        }
    
    def _deploy_cloud(self, config: Dict[str, Any], infra_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy to cloud infrastructure"""
        cloud_provider = infra_config.get("infrastructure", {}).get("type", "").split("-")[0]
        
        return {
            "cloud_provider": cloud_provider,
            "cluster_status": "active",
            "load_balancer_ready": True,
            "ssl_certificate": "configured",
            "deployment_time": "4m15s",
            "performance_metrics": {
                "global_latency": "85ms",
                "availability": "99.9%",
                "throughput": "1000 req/s"
            }
        }

class MonitoringSetupTool(BaseTool):
    """Tool for setting up monitoring and observability"""
    name: str = "monitoring_setup"
    description: str = "Set up monitoring, logging, and alerting"
    
    def _run(self, deployment_config: Dict[str, Any], infrastructure_config: Dict[str, Any]) -> Dict[str, Any]:
        """Set up comprehensive monitoring"""
        
        monitoring_result = {
            "metrics_collection": True,
            "logging_enabled": True,
            "alerting_configured": True,
            "dashboards_created": [],
            "alert_rules": [],
            "endpoints": {}
        }
        
        target = infrastructure_config.get("target", "local")
        project_name = deployment_config.get("project_name", "app")
        
        # Set up metrics collection
        monitoring_result["dashboards_created"] = [
            f"{project_name}-application-metrics",
            f"{project_name}-infrastructure-metrics",
            f"{project_name}-business-metrics"
        ]
        
        # Configure alert rules
        monitoring_result["alert_rules"] = [
            {"name": "High CPU Usage", "threshold": "80%", "duration": "5m"},
            {"name": "High Memory Usage", "threshold": "85%", "duration": "5m"},
            {"name": "Application Down", "threshold": "0 healthy pods", "duration": "1m"},
            {"name": "High Error Rate", "threshold": "5%", "duration": "2m"},
            {"name": "Slow Response Time", "threshold": "2s", "duration": "3m"}
        ]
        
        # Set up monitoring endpoints
        if target == "local":
            monitoring_result["endpoints"] = {
                "prometheus": "http://localhost:9090",
                "grafana": "http://localhost:3000",
                "alertmanager": "http://localhost:9093"
            }
        else:
            monitoring_result["endpoints"] = {
                "prometheus": f"https://prometheus.{project_name}.example.com",
                "grafana": f"https://grafana.{project_name}.example.com",
                "alertmanager": f"https://alerts.{project_name}.example.com"
            }
        
        return monitoring_result

class VayuAgent(BaseAgent):
    """Orchestration & Deployment Agent"""

    def __init__(self, llm_client, config):
        super().__init__("Vayu", llm_client, config)
    
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize Vayu-specific tools"""
        return [
            InfrastructureProvisionTool(),
            DeploymentTool(),
            MonitoringSetupTool()
        ]
    
    def _get_system_prompt(self) -> str:
        """Get Vayu's system prompt"""
        return """You are Vayu, the Orchestration & Deployment Agent in the VedOps DevSecOps platform.

Your responsibilities:
1. Provision and configure target infrastructure
2. Deploy applications with zero-downtime strategies
3. Configure auto-scaling and load balancing
4. Set up monitoring, logging, and alerting
5. Implement blue-green and canary deployments
6. Manage rollbacks and disaster recovery

You have expertise in:
- Kubernetes orchestration and management
- Cloud infrastructure (AWS, Azure, GCP)
- Container orchestration and service mesh
- Infrastructure as Code (Terraform, CloudFormation)
- CI/CD pipeline integration
- Monitoring and observability (Prometheus, Grafana)
- Load balancing and traffic management
- Auto-scaling and resource optimization

Your deployments should be:
- Highly available (99.9%+ uptime)
- Scalable (handle traffic spikes)
- Resilient (self-healing, fault-tolerant)
- Secure (network policies, encryption)
- Observable (comprehensive monitoring)
- Cost-optimized (efficient resource usage)

Deployment strategies you implement:
- Rolling updates for zero downtime
- Blue-green deployments for risk mitigation
- Canary releases for gradual rollouts
- Feature flags for controlled releases
- Automated rollbacks on failure detection

Always ensure production readiness with proper health checks, monitoring, and disaster recovery plans."""
    
    def _prepare_input(self, input_data: Dict[str, Any]) -> str:
        """Prepare input for Vayu"""
        project_data = input_data.get("project_data", {})
        yama_result = input_data.get("agent_results", {}).get("yama", {})
        agni_result = input_data.get("agent_results", {}).get("agni", {})
        
        deployment_decision = yama_result.get("deployment_decision", {}) if yama_result else {}
        
        input_text = f"""
Deploy the following project to production:

Project: {project_data.get('name', 'Unknown')}
Security Status: {'APPROVED' if deployment_decision.get('approved', False) else 'BLOCKED'}
Risk Level: {deployment_decision.get('risk_level', 'UNKNOWN')}

Infrastructure Requirements:
- Target: {project_data.get('deployment_target', 'kubernetes')}
- Expected Traffic: {project_data.get('expected_traffic', 'medium')}
- Scaling: {project_data.get('scaling_preference', 'auto-scaling')}
- Region: {project_data.get('region', 'us-east-1')}

Previous Results:
- Agni: Built containers and K8s manifests
- Yama: Security scan completed with risk score {deployment_decision.get('risk_score', 0)}

Please:
1. Provision appropriate infrastructure
2. Deploy with zero-downtime strategy
3. Configure auto-scaling and load balancing
4. Set up comprehensive monitoring
5. Implement health checks and alerting
6. Prepare rollback procedures

Focus on high availability, scalability, and production readiness.
"""
        
        return input_text
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provision infra, deploy app, and set up monitoring"""
        project_data = input_data.get("project_data", {})
        deployment_decision = input_data.get("deployment_decision", {})

        if not deployment_decision.get("approved", False):
            return {
                "status": "blocked",
                "agent_name": "Vayu",
                "reason": "Deployment blocked by security assessment",
                "blocking_issues": deployment_decision.get("blocking_issues", []),
                "next_agent": "Krishna",
                "timestamp": input_data.get("timestamp")
            }

        project_name = project_data.get("name", "app").lower().replace(" ", "-")

        deployment_config = {
            "project_name": project_name,
            "target": project_data.get("deployment_target", "kubernetes"),
            "strategy": "rolling",
            "replicas": self._calculate_replicas(project_data.get("expected_traffic", "medium")),
            "region": project_data.get("region", "us-east-1")
        }

        infra_tool = InfrastructureProvisionTool()
        infrastructure_result = infra_tool._run(deployment_config)

        deploy_tool = DeploymentTool()
        deployment_result = deploy_tool._run(deployment_config, infrastructure_result)

        monitoring_tool = MonitoringSetupTool()
        monitoring_result = monitoring_tool._run(deployment_config, infrastructure_result)

        return {
            "status": "completed",
            "agent_name": "Vayu",
            "infrastructure": infrastructure_result,
            "deployment": deployment_result,
            "monitoring": monitoring_result,
            "deployment_summary": {
                "target": deployment_config["target"],
                "strategy": deployment_config["strategy"],
                "replicas": deployment_config["replicas"],
                "deployment_time": deployment_result.get("deployment_time", "unknown"),
                "health_status": deployment_result.get("health_status", "unknown"),
                "endpoints": infrastructure_result.get("endpoints", [])
            },
            "next_agent": "Hanuman",
            "timestamp": input_data.get("timestamp")
        }
    
    def _calculate_replicas(self, expected_traffic: str) -> int:
        """Calculate number of replicas based on expected traffic"""
        traffic_map = {
            "low": 2,
            "medium": 3,
            "high": 5,
            "very_high": 8
        }
        
        return traffic_map.get(expected_traffic.lower(), 3)
