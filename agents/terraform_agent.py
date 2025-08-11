import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any

from .base_agent import BaseAgent


class TerraformAgent(BaseAgent):
    """Provision infrastructure using Terraform or simulate when unavailable"""

    def __init__(self, llm_client, config: Dict[str, Any]):
        super().__init__("Terraform", llm_client, config)

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        target = input_data.get("project_data", {}).get("deployment_target") or input_data.get("cloud", "local").lower()
        cloud_creds = input_data.get("cloud_credentials", {})
        project_name = input_data.get("project_data", {}).get("name", "app").lower().replace(" ", "-")

        # Determine endpoint URL based on provider (simulated)
        endpoint_url = ""
        if target in ["aws", "amazon", "amazon web services"]:
            endpoint_url = f"https://{project_name}.aws.example.com"
        elif target in ["azure"]:
            endpoint_url = f"https://{project_name}.azure.example.com"
        elif target in ["google", "gcp", "google cloud"]:
            endpoint_url = f"https://{project_name}.gcp.example.com"
        elif target in ["digitalocean", "do"]:
            endpoint_url = f"https://{project_name}.do.example.com"
        else:
            endpoint_url = "http://localhost:8000"

        terraform_path = shutil.which("terraform")
        used_terraform = False

        # If terraform exists, create a minimal working dir and init/plan (no real apply for safety)
        if terraform_path and target not in ["local", "on-premise", "on-premises"]:
            used_terraform = True
            work_dir = Path(tempfile.mkdtemp(prefix="vedops_tf_"))
            main_tf = work_dir / "main.tf"
            # Minimal placeholder terraform config; real modules would be added here
            main_tf.write_text(
                """
                terraform {
                  required_version = ">= 1.3.0"
                }
                # Placeholder - integrate real modules/providers in production
                """.strip()
            )
            env = os.environ.copy()
            # Export basic credentials if provided (user may set them globally as well)
            env.update({k: v for k, v in cloud_creds.items() if isinstance(v, str)})
            try:
                subprocess.run([terraform_path, "init"], cwd=str(work_dir), check=True, capture_output=True, text=True, env=env)
                subprocess.run([terraform_path, "validate"], cwd=str(work_dir), check=False, capture_output=True, text=True, env=env)
                subprocess.run([terraform_path, "plan"], cwd=str(work_dir), check=False, capture_output=True, text=True, env=env)
            except Exception:
                used_terraform = False

        return {
            "status": "completed",
            "agent_name": "Terraform",
            "used_terraform": used_terraform,
            "infrastructure": {
                "provider": target,
                "endpoints": [
                    {"name": "application", "url": endpoint_url, "type": "https" if endpoint_url.startswith("https") else "http"}
                ]
            },
            "endpoint_url": endpoint_url,
            "timestamp": input_data.get("timestamp"),
        }


