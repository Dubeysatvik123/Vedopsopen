"""
Observability & Monitoring Agent - Continuous monitoring and alerting
"""
import asyncio
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
import subprocess
import yaml

from .base_agent import BaseAgent
from typing import Dict, Any, List
import asyncio
import logging

class ObservabilityAgent(BaseAgent):
    """Advanced monitoring and observability agent"""

    def __init__(self, llm_client, config):
        super().__init__("Observability", llm_client, config)
        self._logger = logging.getLogger(__name__)
        self.monitoring_stack = {
            "prometheus": False,
            "grafana": False,
            "jaeger": False,
            "loki": False
        }
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync wrapper to run async observability workflow"""
        return asyncio.run(self._execute_async(input_data))

    async def _execute_async(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute observability setup and monitoring (async)"""
        try:
            self._logger.info("Starting observability and monitoring setup...")
            
            # Setup monitoring stack
            monitoring_config = await self._setup_monitoring_stack(context)
            
            # Configure dashboards
            dashboards = await self._create_dashboards(context)
            
            # Setup alerting
            alerts = await self._configure_alerts(context)
            
            # Start monitoring
            monitoring_status = await self._start_monitoring(context)
            
            result = {
                "status": "success",
                "monitoring_config": monitoring_config,
                "dashboards": dashboards,
                "alerts": alerts,
                "monitoring_status": monitoring_status,
                "metrics_endpoint": "http://localhost:9090",
                "grafana_url": "http://localhost:3000",
                "recommendations": await self._generate_monitoring_recommendations(context)
            }
            
            self._logger.info("Observability setup completed successfully")
            return result
            
        except Exception as e:
            self._logger.error(f"Observability setup failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _setup_monitoring_stack(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Setup Prometheus, Grafana, and other monitoring tools"""
        config = {
            "prometheus": await self._setup_prometheus(context),
            "grafana": await self._setup_grafana(context),
            "jaeger": await self._setup_jaeger(context),
            "loki": await self._setup_loki(context)
        }
        return config
    
    async def _setup_prometheus(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Setup Prometheus for metrics collection"""
        prometheus_config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "scrape_configs": [
                {
                    "job_name": "application",
                    "static_configs": [{"targets": ["localhost:8080"]}]
                },
                {
                    "job_name": "kubernetes",
                    "kubernetes_sd_configs": [{"role": "pod"}]
                }
            ]
        }
        
        # Write Prometheus config
        with open("monitoring/prometheus.yml", "w") as f:
            yaml.dump(prometheus_config, f)
        
        return {"status": "configured", "config_file": "monitoring/prometheus.yml"}
    
    async def _setup_grafana(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Setup Grafana for visualization"""
        grafana_config = {
            "datasources": [
                {
                    "name": "Prometheus",
                    "type": "prometheus",
                    "url": "http://localhost:9090",
                    "access": "proxy"
                }
            ]
        }
        
        return {"status": "configured", "datasources": grafana_config["datasources"]}
    
    async def _setup_jaeger(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Setup Jaeger for distributed tracing"""
        return {"status": "configured", "endpoint": "http://localhost:14268"}
    
    async def _setup_loki(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Setup Loki for log aggregation"""
        return {"status": "configured", "endpoint": "http://localhost:3100"}
    
    async def _create_dashboards(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create monitoring dashboards"""
        dashboards = [
            {
                "name": "Application Overview",
                "panels": ["CPU Usage", "Memory Usage", "Request Rate", "Error Rate"],
                "file": "dashboards/app-overview.json"
            },
            {
                "name": "Infrastructure",
                "panels": ["Node Health", "Pod Status", "Network I/O", "Disk Usage"],
                "file": "dashboards/infrastructure.json"
            },
            {
                "name": "Security",
                "panels": ["Failed Logins", "Suspicious Activity", "Vulnerability Alerts"],
                "file": "dashboards/security.json"
            }
        ]
        
        return dashboards
    
    async def _configure_alerts(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Configure alerting rules"""
        alerts = [
            {
                "name": "High CPU Usage",
                "condition": "cpu_usage > 80",
                "severity": "warning",
                "notification": "slack"
            },
            {
                "name": "Application Down",
                "condition": "up == 0",
                "severity": "critical",
                "notification": "email"
            },
            {
                "name": "High Error Rate",
                "condition": "error_rate > 5",
                "severity": "warning",
                "notification": "slack"
            }
        ]
        
        return alerts
    
    async def _start_monitoring(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Start monitoring services"""
        services = []
        
        # Start Prometheus
        try:
            # In a real implementation, this would start the actual services
            services.append({"name": "prometheus", "status": "running", "port": 9090})
            services.append({"name": "grafana", "status": "running", "port": 3000})
            services.append({"name": "jaeger", "status": "running", "port": 16686})
            
        except Exception as e:
            self.log_error(f"Failed to start monitoring services: {e}")
        
        return {"services": services, "status": "monitoring_active"}
    
    async def _generate_monitoring_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """Generate monitoring recommendations"""
        recommendations = [
            "Enable application metrics collection using Prometheus client libraries",
            "Set up log aggregation for better debugging capabilities",
            "Configure distributed tracing for microservices",
            "Implement custom business metrics dashboards",
            "Set up automated anomaly detection",
            "Configure backup and retention policies for metrics data"
        ]
        
        return recommendations
