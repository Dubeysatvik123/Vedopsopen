"""
Observability & Incident Response Agent (OIRA)
Monitors application health and triggers auto-recovery if issues occur.
"""

import asyncio
import json
import logging
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import docker
import psutil
import requests
from prometheus_client import CollectorRegistry, Gauge, Counter, start_http_server

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class OIRAAgent(BaseAgent):
    """Observability & Incident Response Agent - Monitors and auto-heals applications"""
    
    def __init__(self):
        super().__init__("OIRA", "🔍")
        self.docker_client = docker.from_env()
        self.monitoring_active = False
        self.metrics_registry = CollectorRegistry()
        self.setup_metrics()
        
    def setup_metrics(self):
        """Initialize Prometheus metrics"""
        self.cpu_usage = Gauge('app_cpu_usage_percent', 'CPU usage percentage', registry=self.metrics_registry)
        self.memory_usage = Gauge('app_memory_usage_bytes', 'Memory usage in bytes', registry=self.metrics_registry)
        self.response_time = Gauge('app_response_time_seconds', 'Application response time', registry=self.metrics_registry)
        self.error_count = Counter('app_errors_total', 'Total application errors', registry=self.metrics_registry)
        
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute observability and monitoring setup"""
        try:
            self.log_info("🔍 Starting observability and incident response setup...")
            
            # Setup monitoring infrastructure
            monitoring_setup = await self._setup_monitoring_stack(context)
            
            # Configure alerting
            alerting_config = await self._configure_alerting(context)
            
            # Start health monitoring
            health_monitoring = await self._start_health_monitoring(context)
            
            # Setup auto-recovery mechanisms
            recovery_config = await self._setup_auto_recovery(context)
            
            result = {
                "status": "success",
                "monitoring_setup": monitoring_setup,
                "alerting_config": alerting_config,
                "health_monitoring": health_monitoring,
                "recovery_config": recovery_config,
                "dashboard_url": f"http://localhost:3000/grafana",
                "metrics_endpoint": "http://localhost:9090/metrics"
            }
            
            self.log_info("✅ Observability and monitoring setup completed successfully")
            return result
            
        except Exception as e:
            error_msg = f"❌ OIRA execution failed: {str(e)}"
            self.log_error(error_msg)
            return {"status": "error", "message": error_msg}
    
    async def _setup_monitoring_stack(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Setup Prometheus and Grafana monitoring stack"""
        try:
            # Create monitoring docker-compose
            monitoring_compose = {
                "version": "3.8",
                "services": {
                    "prometheus": {
                        "image": "prom/prometheus:latest",
                        "ports": ["9090:9090"],
                        "volumes": ["./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml"],
                        "command": [
                            "--config.file=/etc/prometheus/prometheus.yml",
                            "--storage.tsdb.path=/prometheus",
                            "--web.console.libraries=/etc/prometheus/console_libraries",
                            "--web.console.templates=/etc/prometheus/consoles",
                            "--web.enable-lifecycle"
                        ]
                    },
                    "grafana": {
                        "image": "grafana/grafana:latest",
                        "ports": ["3000:3000"],
                        "environment": {
                            "GF_SECURITY_ADMIN_PASSWORD": "admin"
                        },
                        "volumes": [
                            "./monitoring/grafana/dashboards:/var/lib/grafana/dashboards",
                            "./monitoring/grafana/provisioning:/etc/grafana/provisioning"
                        ]
                    },
                    "node-exporter": {
                        "image": "prom/node-exporter:latest",
                        "ports": ["9100:9100"],
                        "volumes": [
                            "/proc:/host/proc:ro",
                            "/sys:/host/sys:ro",
                            "/:/rootfs:ro"
                        ],
                        "command": [
                            "--path.procfs=/host/proc",
                            "--path.rootfs=/rootfs",
                            "--path.sysfs=/host/sys",
                            "--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)"
                        ]
                    }
                }
            }
            
            # Write monitoring compose file
            with open("monitoring/docker-compose.monitoring.yml", "w") as f:
                import yaml
                yaml.dump(monitoring_compose, f, default_flow_style=False)
            
            # Create Prometheus config
            prometheus_config = {
                "global": {
                    "scrape_interval": "15s",
                    "evaluation_interval": "15s"
                },
                "scrape_configs": [
                    {
                        "job_name": "prometheus",
                        "static_configs": [{"targets": ["localhost:9090"]}]
                    },
                    {
                        "job_name": "node-exporter",
                        "static_configs": [{"targets": ["node-exporter:9100"]}]
                    },
                    {
                        "job_name": "application",
                        "static_configs": [{"targets": ["host.docker.internal:8000"]}]
                    }
                ]
            }
            
            # Write Prometheus config
            import os
            os.makedirs("monitoring", exist_ok=True)
            with open("monitoring/prometheus.yml", "w") as f:
                import yaml
                yaml.dump(prometheus_config, f, default_flow_style=False)
            
            # Start monitoring stack
            subprocess.run([
                "docker-compose", "-f", "monitoring/docker-compose.monitoring.yml", "up", "-d"
            ], check=True, capture_output=True, text=True)
            
            return {
                "prometheus_url": "http://localhost:9090",
                "grafana_url": "http://localhost:3000",
                "node_exporter_url": "http://localhost:9100",
                "status": "monitoring_stack_deployed"
            }
            
        except Exception as e:
            raise Exception(f"Failed to setup monitoring stack: {str(e)}")
    
    async def _configure_alerting(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Configure alerting rules and notifications"""
        try:
            # Define alerting rules
            alert_rules = {
                "groups": [
                    {
                        "name": "application_alerts",
                        "rules": [
                            {
                                "alert": "HighCPUUsage",
                                "expr": "cpu_usage_percent > 80",
                                "for": "2m",
                                "labels": {"severity": "warning"},
                                "annotations": {
                                    "summary": "High CPU usage detected",
                                    "description": "CPU usage is above 80% for more than 2 minutes"
                                }
                            },
                            {
                                "alert": "HighMemoryUsage", 
                                "expr": "memory_usage_bytes > 1073741824",  # 1GB
                                "for": "2m",
                                "labels": {"severity": "warning"},
                                "annotations": {
                                    "summary": "High memory usage detected",
                                    "description": "Memory usage is above 1GB for more than 2 minutes"
                                }
                            },
                            {
                                "alert": "ApplicationDown",
                                "expr": "up == 0",
                                "for": "1m",
                                "labels": {"severity": "critical"},
                                "annotations": {
                                    "summary": "Application is down",
                                    "description": "Application has been down for more than 1 minute"
                                }
                            }
                        ]
                    }
                ]
            }
            
            # Write alert rules
            with open("monitoring/alert_rules.yml", "w") as f:
                import yaml
                yaml.dump(alert_rules, f, default_flow_style=False)
            
            return {
                "alert_rules_configured": True,
                "alert_rules_file": "monitoring/alert_rules.yml",
                "notification_channels": ["console", "webhook"]
            }
            
        except Exception as e:
            raise Exception(f"Failed to configure alerting: {str(e)}")
    
    async def _start_health_monitoring(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Start continuous health monitoring"""
        try:
            # Start metrics collection
            start_http_server(8001, registry=self.metrics_registry)
            
            # Start monitoring loop
            asyncio.create_task(self._monitoring_loop())
            
            return {
                "health_monitoring_active": True,
                "metrics_port": 8001,
                "monitoring_interval": "30s"
            }
            
        except Exception as e:
            raise Exception(f"Failed to start health monitoring: {str(e)}")
    
    async def _setup_auto_recovery(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Setup automatic recovery mechanisms"""
        try:
            # Create recovery scripts
            recovery_scripts = {
                "restart_application": """#!/bin/bash
echo "Restarting application containers..."
docker-compose restart
echo "Application restarted successfully"
""",
                "scale_up": """#!/bin/bash
echo "Scaling up application..."
docker-compose up --scale web=3 -d
echo "Application scaled up successfully"
""",
                "cleanup_resources": """#!/bin/bash
echo "Cleaning up system resources..."
docker system prune -f
echo "System cleanup completed"
"""
            }
            
            # Write recovery scripts
            import os
            os.makedirs("scripts/recovery", exist_ok=True)
            for script_name, script_content in recovery_scripts.items():
                script_path = f"scripts/recovery/{script_name}.sh"
                with open(script_path, "w") as f:
                    f.write(script_content)
                os.chmod(script_path, 0o755)
            
            return {
                "auto_recovery_enabled": True,
                "recovery_scripts": list(recovery_scripts.keys()),
                "recovery_triggers": ["high_cpu", "high_memory", "application_down"]
            }
            
        except Exception as e:
            raise Exception(f"Failed to setup auto-recovery: {str(e)}")
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while True:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # Update Prometheus metrics
                self.cpu_usage.set(cpu_percent)
                self.memory_usage.set(memory.used)
                
                # Check for anomalies and trigger recovery if needed
                if cpu_percent > 80:
                    await self._trigger_recovery("high_cpu")
                
                if memory.percent > 85:
                    await self._trigger_recovery("high_memory")
                
                # Check application health
                try:
                    response = requests.get("http://localhost:8000/health", timeout=5)
                    if response.status_code != 200:
                        await self._trigger_recovery("application_unhealthy")
                except requests.RequestException:
                    await self._trigger_recovery("application_down")
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _trigger_recovery(self, trigger_type: str):
        """Trigger automatic recovery based on issue type"""
        try:
            self.log_info(f"🚨 Triggering auto-recovery for: {trigger_type}")
            
            recovery_actions = {
                "high_cpu": "cleanup_resources",
                "high_memory": "restart_application", 
                "application_down": "restart_application",
                "application_unhealthy": "restart_application"
            }
            
            action = recovery_actions.get(trigger_type, "restart_application")
            script_path = f"scripts/recovery/{action}.sh"
            
            # Execute recovery script
            result = subprocess.run(["/bin/bash", script_path], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_info(f"✅ Auto-recovery successful: {action}")
            else:
                self.log_error(f"❌ Auto-recovery failed: {result.stderr}")
                
        except Exception as e:
            self.log_error(f"Recovery trigger failed: {str(e)}")
