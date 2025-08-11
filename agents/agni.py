"""
Agni - The Build & Dockerization Agent
Handles Docker containerization, builds, and Kubernetes manifest generation
"""

import os
import json
import docker
import yaml
import tempfile
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import shutil
from datetime import datetime

from langchain_community.llms import Ollama

@dataclass
class BuildArtifacts:
    """Build artifacts and metadata"""
    dockerfile_path: str
    docker_compose_path: Optional[str]
    kubernetes_manifests: Dict[str, str]  # filename -> path
    image_name: str
    image_tag: str
    build_logs: List[str]
    build_time: float
    image_size: int
    optimization_notes: List[str]
    multi_stage: bool

class AgniAgent:
    """Build & Dockerization Agent"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.docker_client = None
        self.temp_dir = None
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
            self.logger.info("Docker client initialized successfully")
        except Exception as e:
            self.logger.warning(f"Docker client initialization failed: {str(e)}")
        
        # Initialize LLM for intelligent build optimization
        self.llm = Ollama(model="codellama", base_url="http://localhost:11434")
        
        # Base images for different tech stacks
        self.base_images = {
            'python': {
                'slim': 'python:3.11-slim',
                'alpine': 'python:3.11-alpine',
                'full': 'python:3.11'
            },
            'javascript': {
                'slim': 'node:18-slim',
                'alpine': 'node:18-alpine',
                'full': 'node:18'
            },
            'typescript': {
                'slim': 'node:18-slim',
                'alpine': 'node:18-alpine',
                'full': 'node:18'
            },
            'java': {
                'slim': 'openjdk:17-jre-slim',
                'alpine': 'openjdk:17-jre-alpine',
                'full': 'openjdk:17'
            },
            'go': {
                'slim': 'golang:1.21-alpine',
                'alpine': 'golang:1.21-alpine',
                'full': 'golang:1.21'
            },
            'rust': {
                'slim': 'rust:1.70-slim',
                'alpine': 'rust:1.70-alpine',
                'full': 'rust:1.70'
            }
        }
        
        # Port mappings for common frameworks
        self.framework_ports = {
            'django': 8000,
            'flask': 5000,
            'fastapi': 8000,
            'express': 3000,
            'react': 3000,
            'nextjs': 3000,
            'vue': 8080,
            'angular': 4200,
            'spring': 8080,
            'gin': 8080,
            'actix': 8080
        }
    
    def execute(self, project_manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution method for Agni agent"""
        try:
            self.logger.info("Agni: Starting build and containerization")
            
            # Create temporary working directory
            self.temp_dir = tempfile.mkdtemp(prefix="agni_")
            work_dir = Path(self.temp_dir)
            
            # Step 1: Generate Dockerfile
            dockerfile_path = self._generate_dockerfile(project_manifest, work_dir)
            
            # Step 2: Generate docker-compose.yml if needed
            compose_path = self._generate_docker_compose(project_manifest, work_dir)
            
            # Step 3: Generate Kubernetes manifests
            k8s_manifests = self._generate_kubernetes_manifests(project_manifest, work_dir)
            
            # Step 4: Build Docker image
            image_name, image_tag, build_logs, build_time, image_size = self._build_docker_image(
                dockerfile_path, project_manifest
            )
            
            # Step 5: Generate optimization recommendations
            optimization_notes = self._generate_optimization_notes(
                project_manifest, dockerfile_path, image_size
            )
            
            # Create build artifacts
            artifacts = BuildArtifacts(
                dockerfile_path=str(dockerfile_path),
                docker_compose_path=str(compose_path) if compose_path else None,
                kubernetes_manifests=k8s_manifests,
                image_name=image_name,
                image_tag=image_tag,
                build_logs=build_logs,
                build_time=build_time,
                image_size=image_size,
                optimization_notes=optimization_notes,
                multi_stage=self._is_multi_stage_build(project_manifest)
            )
            
            # Convert to dict for JSON serialization
            result = {
                'dockerfile_path': artifacts.dockerfile_path,
                'docker_compose_path': artifacts.docker_compose_path,
                'kubernetes_manifests': artifacts.kubernetes_manifests,
                'image_name': artifacts.image_name,
                'image_tag': artifacts.image_tag,
                'build_logs': artifacts.build_logs,
                'build_time': artifacts.build_time,
                'image_size': artifacts.image_size,
                'optimization_notes': artifacts.optimization_notes,
                'multi_stage': artifacts.multi_stage,
                'build_timestamp': str(datetime.now()),
                'agent': 'agni'
            }
            
            # Save artifacts
            self._save_artifacts(result)
            
            self.logger.info("Agni: Build and containerization completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Agni execution failed: {str(e)}")
            raise
        finally:
            self._cleanup()
    
    def _generate_dockerfile(self, manifest: Dict[str, Any], work_dir: Path) -> Path:
        """Generate optimized Dockerfile based on project manifest"""
        
        tech_stack = manifest.get('tech_stack', [])
        build_config = manifest.get('build_config', {})
        dependencies = manifest.get('dependencies', {})
        complexity = manifest.get('estimated_complexity', 'medium')
        
        # Determine primary language
        primary_lang = self._get_primary_language(manifest)
        
        # Choose base image
        base_image = self._choose_base_image(primary_lang, complexity)
        
        # Generate Dockerfile content
        dockerfile_content = self._build_dockerfile_content(
            primary_lang, base_image, tech_stack, build_config, dependencies, manifest
        )
        
        # Write Dockerfile
        dockerfile_path = work_dir / "Dockerfile"
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        # Generate .dockerignore
        dockerignore_path = work_dir / ".dockerignore"
        with open(dockerignore_path, 'w') as f:
            f.write(self._generate_dockerignore(tech_stack))
        
        self.logger.info(f"Generated Dockerfile at {dockerfile_path}")
        return dockerfile_path
    
    def _build_dockerfile_content(self, primary_lang: str, base_image: str, 
                                tech_stack: List[str], build_config: Dict[str, Any],
                                dependencies: Dict[str, Any], manifest: Dict[str, Any]) -> str:
        """Build Dockerfile content based on tech stack"""
        
        lines = []
        
        # Multi-stage build for production optimization
        if self._is_multi_stage_build(manifest):
            lines.extend(self._generate_multi_stage_dockerfile(
                primary_lang, base_image, tech_stack, build_config, dependencies
            ))
        else:
            lines.extend(self._generate_single_stage_dockerfile(
                primary_lang, base_image, tech_stack, build_config, dependencies
            ))
        
        # Add health check
        health_check = build_config.get('health_check')
        port = build_config.get('port', 8000)
        
        if health_check:
            lines.append(f"HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\")
            lines.append(f"  CMD curl -f http://localhost:{port}{health_check} || exit 1")
        
        # Expose port
        lines.append(f"EXPOSE {port}")
        
        # Add labels for metadata
        lines.extend([
            "",
            "# Metadata labels",
            f'LABEL maintainer="VedOps AI"',
            f'LABEL project="{manifest.get("project_name", "unknown")}"',
            f'LABEL tech_stack="{",".join(tech_stack)}"',
            f'LABEL build_agent="agni"',
            f'LABEL build_timestamp="{datetime.now().isoformat()}"'
        ])
        
        return "\n".join(lines)
    
    def _generate_multi_stage_dockerfile(self, primary_lang: str, base_image: str,
                                       tech_stack: List[str], build_config: Dict[str, Any],
                                       dependencies: Dict[str, Any]) -> List[str]:
        """Generate multi-stage Dockerfile for production optimization"""
        
        lines = []
        
        if primary_lang == 'python':
            lines.extend([
                "# Multi-stage build for Python application",
                "# Stage 1: Build dependencies",
                f"FROM {base_image} as builder",
                "",
                "WORKDIR /app",
                "",
                "# Install build dependencies",
                "RUN apt-get update && apt-get install -y \\",
                "    build-essential \\",
                "    && rm -rf /var/lib/apt/lists/*",
                "",
                "# Copy requirements and install dependencies",
                "COPY requirements*.txt ./",
                "RUN pip install --no-cache-dir --user -r requirements.txt",
                "",
                "# Stage 2: Production image",
                f"FROM {base_image.replace('python:', 'python:').replace('-slim', '-slim')}",
                "",
                "WORKDIR /app",
                "",
                "# Copy installed packages from builder",
                "COPY --from=builder /root/.local /root/.local",
                "",
                "# Copy application code",
                "COPY . .",
                "",
                "# Create non-root user",
                "RUN useradd --create-home --shell /bin/bash app \\",
                "    && chown -R app:app /app",
                "USER app",
                "",
                "# Update PATH",
                "ENV PATH=/root/.local/bin:$PATH"
            ])
            
            # Add framework-specific commands
            if 'django' in tech_stack:
                lines.extend([
                    "",
                    "# Django specific setup",
                    "RUN python manage.py collectstatic --noinput",
                    "CMD [\"gunicorn\", \"--bind\", \"0.0.0.0:8000\", \"wsgi:application\"]"
                ])
            elif 'flask' in tech_stack:
                lines.append("CMD [\"gunicorn\", \"--bind\", \"0.0.0.0:5000\", \"app:app\"]")
            elif 'fastapi' in tech_stack:
                lines.append("CMD [\"uvicorn\", \"main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]")
            else:
                lines.append("CMD [\"python\", \"main.py\"]")
        
        elif primary_lang in ['javascript', 'typescript']:
            lines.extend([
                "# Multi-stage build for Node.js application",
                "# Stage 1: Build dependencies and application",
                f"FROM {base_image} as builder",
                "",
                "WORKDIR /app",
                "",
                "# Copy package files",
                "COPY package*.json ./",
                "",
                "# Install dependencies",
                "RUN npm ci --only=production",
                "",
                "# Copy source code and build",
                "COPY . .",
            ])
            
            if 'react' in tech_stack or 'nextjs' in tech_stack:
                lines.extend([
                    "RUN npm run build",
                    "",
                    "# Stage 2: Production image",
                    f"FROM {base_image.replace('node:', 'node:').replace('-slim', '-alpine')}",
                    "",
                    "WORKDIR /app",
                    "",
                    "# Copy built application",
                    "COPY --from=builder /app/build ./build",
                    "COPY --from=builder /app/node_modules ./node_modules",
                    "COPY --from=builder /app/package*.json ./",
                    "",
                    "# Create non-root user",
                    "RUN addgroup -g 1001 -S nodejs",
                    "RUN adduser -S nextjs -u 1001",
                    "USER nextjs",
                    "",
                    "CMD [\"npm\", \"start\"]"
                ])
            else:
                lines.extend([
                    "",
                    "# Stage 2: Production image",
                    f"FROM {base_image}",
                    "",
                    "WORKDIR /app",
                    "",
                    "# Copy application",
                    "COPY --from=builder /app .",
                    "",
                    "CMD [\"npm\", \"start\"]"
                ])
        
        elif primary_lang == 'go':
            lines.extend([
                "# Multi-stage build for Go application",
                "# Stage 1: Build binary",
                f"FROM {base_image} as builder",
                "",
                "WORKDIR /app",
                "",
                "# Copy go mod files",
                "COPY go.mod go.sum ./",
                "RUN go mod download",
                "",
                "# Copy source code and build",
                "COPY . .",
                "RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .",
                "",
                "# Stage 2: Production image",
                "FROM alpine:latest",
                "",
                "# Install ca-certificates for HTTPS",
                "RUN apk --no-cache add ca-certificates",
                "",
                "WORKDIR /root/",
                "",
                "# Copy binary from builder",
                "COPY --from=builder /app/main .",
                "",
                "CMD [\"./main\"]"
            ])
        
        return lines
    
    def _generate_single_stage_dockerfile(self, primary_lang: str, base_image: str,
                                        tech_stack: List[str], build_config: Dict[str, Any],
                                        dependencies: Dict[str, Any]) -> List[str]:
        """Generate single-stage Dockerfile for simpler applications"""
        
        lines = [f"FROM {base_image}", "", "WORKDIR /app"]
        
        if primary_lang == 'python':
            lines.extend([
                "",
                "# Install system dependencies",
                "RUN apt-get update && apt-get install -y \\",
                "    curl \\",
                "    && rm -rf /var/lib/apt/lists/*",
                "",
                "# Copy requirements and install Python dependencies",
                "COPY requirements*.txt ./",
                "RUN pip install --no-cache-dir -r requirements.txt",
                "",
                "# Copy application code",
                "COPY . .",
                "",
                "# Create non-root user",
                "RUN useradd --create-home --shell /bin/bash app \\",
                "    && chown -R app:app /app",
                "USER app"
            ])
            
            # Add framework-specific commands
            if 'django' in tech_stack:
                lines.extend([
                    "",
                    "# Django setup",
                    "RUN python manage.py collectstatic --noinput",
                    "CMD [\"python\", \"manage.py\", \"runserver\", \"0.0.0.0:8000\"]"
                ])
            elif 'flask' in tech_stack:
                lines.append("CMD [\"python\", \"app.py\"]")
            elif 'fastapi' in tech_stack:
                lines.append("CMD [\"uvicorn\", \"main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]")
            else:
                lines.append("CMD [\"python\", \"main.py\"]")
        
        elif primary_lang in ['javascript', 'typescript']:
            lines.extend([
                "",
                "# Copy package files",
                "COPY package*.json ./",
                "",
                "# Install dependencies",
                "RUN npm install",
                "",
                "# Copy application code",
                "COPY . .",
                "",
                "# Build application if needed"
            ])
            
            if 'react' in tech_stack or 'nextjs' in tech_stack:
                lines.extend([
                    "RUN npm run build",
                    "",
                    "CMD [\"npm\", \"start\"]"
                ])
            else:
                lines.append("CMD [\"npm\", \"start\"]")
        
        elif primary_lang == 'java':
            lines.extend([
                "",
                "# Copy Maven files",
                "COPY pom.xml ./",
                "",
                "# Download dependencies",
                "RUN mvn dependency:go-offline",
                "",
                "# Copy source code and build",
                "COPY src ./src",
                "RUN mvn clean package -DskipTests",
                "",
                "CMD [\"java\", \"-jar\", \"target/*.jar\"]"
            ])
        
        return lines
    
    def _generate_dockerignore(self, tech_stack: List[str]) -> str:
        """Generate .dockerignore file"""
        
        ignore_patterns = [
            "# Git",
            ".git",
            ".gitignore",
            "",
            "# Documentation",
            "README.md",
            "*.md",
            "docs/",
            "",
            "# IDE",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "",
            "# OS",
            ".DS_Store",
            "Thumbs.db",
            "",
            "# Logs",
            "*.log",
            "logs/",
            "",
            "# Testing",
            "coverage/",
            ".coverage",
            ".pytest_cache/",
            "",
            "# Build artifacts",
            "dist/",
            "build/",
            "target/"
        ]
        
        # Add language-specific patterns
        if 'python' in tech_stack:
            ignore_patterns.extend([
                "",
                "# Python",
                "__pycache__/",
                "*.pyc",
                "*.pyo",
                "*.pyd",
                ".Python",
                "env/",
                "venv/",
                ".venv/",
                ".env",
                "pip-log.txt",
                "pip-delete-this-directory.txt",
                ".tox/",
                ".cache/",
                ".pytest_cache/",
                "*.egg-info/"
            ])
        
        if any(lang in tech_stack for lang in ['javascript', 'typescript']):
            ignore_patterns.extend([
                "",
                "# Node.js",
                "node_modules/",
                "npm-debug.log*",
                "yarn-debug.log*",
                "yarn-error.log*",
                ".npm",
                ".yarn-integrity",
                ".next/",
                ".nuxt/",
                "dist/"
            ])
        
        if 'java' in tech_stack:
            ignore_patterns.extend([
                "",
                "# Java",
                "target/",
                "*.class",
                "*.jar",
                "*.war",
                "*.ear",
                ".mvn/",
                "mvnw",
                "mvnw.cmd"
            ])
        
        return "\n".join(ignore_patterns)
    
    def _generate_docker_compose(self, manifest: Dict[str, Any], work_dir: Path) -> Optional[Path]:
        """Generate docker-compose.yml for multi-service applications"""
        
        tech_stack = manifest.get('tech_stack', [])
        build_config = manifest.get('build_config', {})
        project_name = manifest.get('project_name', 'app')
        
        # Check if we need docker-compose (multiple services)
        needs_compose = any([
            'database' in tech_stack,
            'redis' in tech_stack,
            'postgres' in tech_stack,
            'mysql' in tech_stack,
            'mongodb' in tech_stack,
            len(tech_stack) > 3  # Complex applications
        ])
        
        if not needs_compose:
            return None
        
        # Build compose configuration
        compose_config = {
            'version': '3.8',
            'services': {},
            'volumes': {},
            'networks': {
                'app-network': {
                    'driver': 'bridge'
                }
            }
        }
        
        # Main application service
        app_service = {
            'build': {
                'context': '.',
                'dockerfile': 'Dockerfile'
            },
            'ports': [f"{build_config.get('port', 8000)}:{build_config.get('port', 8000)}"],
            'environment': [
                'NODE_ENV=production',
                'PYTHONUNBUFFERED=1'
            ],
            'networks': ['app-network'],
            'restart': 'unless-stopped'
        }
        
        # Add health check if available
        health_check = build_config.get('health_check')
        if health_check:
            app_service['healthcheck'] = {
                'test': f"curl -f http://localhost:{build_config.get('port', 8000)}{health_check} || exit 1",
                'interval': '30s',
                'timeout': '10s',
                'retries': 3,
                'start_period': '40s'
            }
        
        compose_config['services'][project_name] = app_service
        
        # Add database services based on dependencies
        dependencies = manifest.get('dependencies', {})
        all_deps = []
        for dep_list in dependencies.values():
            all_deps.extend(dep_list)
        
        # PostgreSQL
        if any('psycopg' in dep or 'postgresql' in dep for dep in all_deps):
            compose_config['services']['postgres'] = {
                'image': 'postgres:15-alpine',
                'environment': [
                    'POSTGRES_DB=appdb',
                    'POSTGRES_USER=appuser',
                    'POSTGRES_PASSWORD=apppass'
                ],
                'volumes': ['postgres_data:/var/lib/postgresql/data'],
                'networks': ['app-network'],
                'restart': 'unless-stopped'
            }
            compose_config['volumes']['postgres_data'] = {}
            app_service['depends_on'] = app_service.get('depends_on', []) + ['postgres']
            app_service['environment'].append('DATABASE_URL=postgresql://appuser:apppass@postgres:5432/appdb')
        
        # Redis
        if any('redis' in dep for dep in all_deps):
            compose_config['services']['redis'] = {
                'image': 'redis:7-alpine',
                'networks': ['app-network'],
                'restart': 'unless-stopped'
            }
            app_service['depends_on'] = app_service.get('depends_on', []) + ['redis']
            app_service['environment'].append('REDIS_URL=redis://redis:6379')
        
        # MongoDB
        if any('mongo' in dep or 'pymongo' in dep for dep in all_deps):
            compose_config['services']['mongodb'] = {
                'image': 'mongo:6',
                'environment': [
                    'MONGO_INITDB_ROOT_USERNAME=root',
                    'MONGO_INITDB_ROOT_PASSWORD=rootpass',
                    'MONGO_INITDB_DATABASE=appdb'
                ],
                'volumes': ['mongodb_data:/data/db'],
                'networks': ['app-network'],
                'restart': 'unless-stopped'
            }
            compose_config['volumes']['mongodb_data'] = {}
            app_service['depends_on'] = app_service.get('depends_on', []) + ['mongodb']
            app_service['environment'].append('MONGODB_URL=mongodb://root:rootpass@mongodb:27017/appdb')
        
        # Write docker-compose.yml
        compose_path = work_dir / "docker-compose.yml"
        with open(compose_path, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False, indent=2)
        
        self.logger.info(f"Generated docker-compose.yml at {compose_path}")
        return compose_path
    
    def _generate_kubernetes_manifests(self, manifest: Dict[str, Any], work_dir: Path) -> Dict[str, str]:
        """Generate Kubernetes deployment manifests"""
        
        project_name = manifest.get('project_name', 'app').lower().replace('_', '-')
        build_config = manifest.get('build_config', {})
        port = build_config.get('port', 8000)
        
        k8s_dir = work_dir / "k8s"
        k8s_dir.mkdir(exist_ok=True)
        
        manifests = {}
        
        # 1. Namespace
        namespace_manifest = {
            'apiVersion': 'v1',
            'kind': 'Namespace',
            'metadata': {
                'name': f"{project_name}-ns",
                'labels': {
                    'app': project_name,
                    'managed-by': 'vedops'
                }
            }
        }
        
        namespace_path = k8s_dir / "namespace.yaml"
        with open(namespace_path, 'w') as f:
            yaml.dump(namespace_manifest, f, default_flow_style=False)
        manifests['namespace'] = str(namespace_path)
        
        # 2. Deployment
        deployment_manifest = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': f"{project_name}-deployment",
                'namespace': f"{project_name}-ns",
                'labels': {
                    'app': project_name,
                    'version': 'v1'
                }
            },
            'spec': {
                'replicas': 3,
                'selector': {
                    'matchLabels': {
                        'app': project_name
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': project_name,
                            'version': 'v1'
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': project_name,
                            'image': f"{project_name}:latest",
                            'ports': [{
                                'containerPort': port,
                                'name': 'http'
                            }],
                            'env': [
                                {
                                    'name': 'NODE_ENV',
                                    'value': 'production'
                                },
                                {
                                    'name': 'PORT',
                                    'value': str(port)
                                }
                            ],
                            'resources': {
                                'requests': {
                                    'memory': '128Mi',
                                    'cpu': '100m'
                                },
                                'limits': {
                                    'memory': '512Mi',
                                    'cpu': '500m'
                                }
                            },
                            'livenessProbe': {
                                'httpGet': {
                                    'path': build_config.get('health_check', '/'),
                                    'port': port
                                },
                                'initialDelaySeconds': 30,
                                'periodSeconds': 10
                            },
                            'readinessProbe': {
                                'httpGet': {
                                    'path': build_config.get('health_check', '/'),
                                    'port': port
                                },
                                'initialDelaySeconds': 5,
                                'periodSeconds': 5
                            }
                        }]
                    }
                }
            }
        }
        
        deployment_path = k8s_dir / "deployment.yaml"
        with open(deployment_path, 'w') as f:
            yaml.dump(deployment_manifest, f, default_flow_style=False)
        manifests['deployment'] = str(deployment_path)
        
        # 3. Service
        service_manifest = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': f"{project_name}-service",
                'namespace': f"{project_name}-ns",
                'labels': {
                    'app': project_name
                }
            },
            'spec': {
                'selector': {
                    'app': project_name
                },
                'ports': [{
                    'port': 80,
                    'targetPort': port,
                    'protocol': 'TCP',
                    'name': 'http'
                }],
                'type': 'ClusterIP'
            }
        }
        
        service_path = k8s_dir / "service.yaml"
        with open(service_path, 'w') as f:
            yaml.dump(service_manifest, f, default_flow_style=False)
        manifests['service'] = str(service_path)
        
        # 4. Ingress
        ingress_manifest = {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'Ingress',
            'metadata': {
                'name': f"{project_name}-ingress",
                'namespace': f"{project_name}-ns",
                'annotations': {
                    'nginx.ingress.kubernetes.io/rewrite-target': '/',
                    'kubernetes.io/ingress.class': 'nginx'
                }
            },
            'spec': {
                'rules': [{
                    'host': f"{project_name}.local",
                    'http': {
                        'paths': [{
                            'path': '/',
                            'pathType': 'Prefix',
                            'backend': {
                                'service': {
                                    'name': f"{project_name}-service",
                                    'port': {
                                        'number': 80
                                    }
                                }
                            }
                        }]
                    }
                }]
            }
        }
        
        ingress_path = k8s_dir / "ingress.yaml"
        with open(ingress_path, 'w') as f:
            yaml.dump(ingress_manifest, f, default_flow_style=False)
        manifests['ingress'] = str(ingress_path)
        
        # 5. HPA (Horizontal Pod Autoscaler)
        hpa_manifest = {
            'apiVersion': 'autoscaling/v2',
            'kind': 'HorizontalPodAutoscaler',
            'metadata': {
                'name': f"{project_name}-hpa",
                'namespace': f"{project_name}-ns"
            },
            'spec': {
                'scaleTargetRef': {
                    'apiVersion': 'apps/v1',
                    'kind': 'Deployment',
                    'name': f"{project_name}-deployment"
                },
                'minReplicas': 2,
                'maxReplicas': 10,
                'metrics': [{
                    'type': 'Resource',
                    'resource': {
                        'name': 'cpu',
                        'target': {
                            'type': 'Utilization',
                            'averageUtilization': 70
                        }
                    }
                }]
            }
        }
        
        hpa_path = k8s_dir / "hpa.yaml"
        with open(hpa_path, 'w') as f:
            yaml.dump(hpa_manifest, f, default_flow_style=False)
        manifests['hpa'] = str(hpa_path)
        
        self.logger.info(f"Generated Kubernetes manifests in {k8s_dir}")
        return manifests
    
    def _build_docker_image(self, dockerfile_path: Path, manifest: Dict[str, Any]) -> Tuple[str, str, List[str], float, int]:
        """Build Docker image and return metadata"""
        
        if not self.docker_client:
            self.logger.warning("Docker client not available, skipping image build")
            return "unknown", "latest", ["Docker not available"], 0.0, 0
        
        project_name = manifest.get('project_name', 'app').lower().replace('_', '-')
        image_tag = f"v{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        image_name = f"{project_name}:{image_tag}"
        
        build_logs = []
        start_time = datetime.now()
        
        try:
            # Build image
            self.logger.info(f"Building Docker image: {image_name}")
            
            image, build_log = self.docker_client.images.build(
                path=str(dockerfile_path.parent),
                dockerfile=str(dockerfile_path.name),
                tag=image_name,
                rm=True,
                forcerm=True,
                pull=True,
                nocache=False  # Use cache for faster builds
            )
            
            # Collect build logs
            for log_entry in build_log:
                if 'stream' in log_entry:
                    build_logs.append(log_entry['stream'].strip())
            
            # Calculate build time
            build_time = (datetime.now() - start_time).total_seconds()
            
            # Get image size
            image_size = image.attrs['Size']
            
            self.logger.info(f"Successfully built image {image_name} ({image_size / 1024 / 1024:.1f} MB)")
            
            return project_name, image_tag, build_logs, build_time, image_size
            
        except Exception as e:
            self.logger.error(f"Docker build failed: {str(e)}")
            build_logs.append(f"Build failed: {str(e)}")
            return project_name, image_tag, build_logs, 0.0, 0
    
    def _generate_optimization_notes(self, manifest: Dict[str, Any], 
                                   dockerfile_path: Path, image_size: int) -> List[str]:
        """Generate build optimization recommendations"""
        
        notes = []
        
        # Image size optimization
        if image_size > 1024 * 1024 * 1024:  # > 1GB
            notes.append("Consider using multi-stage builds to reduce image size")
            notes.append("Use alpine-based images for smaller footprint")
        elif image_size > 500 * 1024 * 1024:  # > 500MB
            notes.append("Image size is moderate - consider optimizing dependencies")
        
        # Tech stack specific optimizations
        tech_stack = manifest.get('tech_stack', [])
        
        if 'python' in tech_stack:
            notes.append("Use pip install --no-cache-dir to reduce image size")
            notes.append("Consider using python:slim or python:alpine base images")
            
            if 'django' in tech_stack:
                notes.append("Use gunicorn or uwsgi for production Django deployments")
            elif 'flask' in tech_stack:
                notes.append("Use gunicorn for production Flask deployments")
        
        if any(lang in tech_stack for lang in ['javascript', 'typescript']):
            notes.append("Use npm ci instead of npm install for faster, reliable builds")
            notes.append("Consider using node:alpine for smaller images")
            
            if 'react' in tech_stack:
                notes.append("Implement proper build caching for React applications")
        
        if 'java' in tech_stack:
            notes.append("Use openjdk:jre-slim for smaller runtime images")
            notes.append("Consider using jlink to create custom JRE")
        
        # Security optimizations
        notes.append("Run containers as non-root user for better security")
        notes.append("Regularly update base images to patch security vulnerabilities")
        notes.append("Use .dockerignore to exclude unnecessary files")
        
        # Performance optimizations
        notes.append("Implement proper health checks for container orchestration")
        notes.append("Use build caching to speed up subsequent builds")
        notes.append("Consider using BuildKit for advanced build features")
        
        return notes
    
    def _get_primary_language(self, manifest: Dict[str, Any]) -> str:
        """Determine primary programming language"""
        languages = manifest.get('languages', {})
        if not languages:
            tech_stack = manifest.get('tech_stack', [])
            if 'python' in tech_stack:
                return 'python'
            elif any(lang in tech_stack for lang in ['javascript', 'typescript']):
                return 'javascript'
            elif 'java' in tech_stack:
                return 'java'
            elif 'go' in tech_stack:
                return 'go'
            elif 'rust' in tech_stack:
                return 'rust'
            else:
                return 'python'  # Default
        
        # Return language with highest percentage
        return max(languages.items(), key=lambda x: x[1])[0]
    
    def _choose_base_image(self, primary_lang: str, complexity: str) -> str:
        """Choose optimal base image"""
        if primary_lang not in self.base_images:
            return 'ubuntu:22.04'  # Fallback
        
        lang_images = self.base_images[primary_lang]
        
        # Choose based on complexity
        if complexity == 'low':
            return lang_images.get('alpine', lang_images['slim'])
        elif complexity == 'high':
            return lang_images['full']
        else:
            return lang_images['slim']
    
    def _is_multi_stage_build(self, manifest: Dict[str, Any]) -> bool:
        """Determine if multi-stage build is beneficial"""
        complexity = manifest.get('estimated_complexity', 'medium')
        tech_stack = manifest.get('tech_stack', [])
        
        # Use multi-stage for complex applications or specific tech stacks
        return (
            complexity == 'high' or
            'react' in tech_stack or
            'nextjs' in tech_stack or
            'go' in tech_stack or
            'rust' in tech_stack or
            len(tech_stack) > 4
        )
    
    def _save_artifacts(self, artifacts: Dict[str, Any]):
        """Save build artifacts to artifacts directory"""
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        
        # Save build metadata
        metadata_path = artifacts_dir / f"build_artifacts_{artifacts.get('image_name', 'unknown')}.json"
        with open(metadata_path, 'w') as f:
            json.dump(artifacts, f, indent=2, default=str)
        
        # Copy generated files to artifacts
        if artifacts.get('dockerfile_path'):
            dockerfile_src = Path(artifacts['dockerfile_path'])
            if dockerfile_src.exists():
                shutil.copy2(dockerfile_src, artifacts_dir / "Dockerfile")
        
        if artifacts.get('docker_compose_path'):
            compose_src = Path(artifacts['docker_compose_path'])
            if compose_src.exists():
                shutil.copy2(compose_src, artifacts_dir / "docker-compose.yml")
        
        # Copy Kubernetes manifests
        k8s_artifacts_dir = artifacts_dir / "k8s"
        k8s_artifacts_dir.mkdir(exist_ok=True)
        
        for manifest_type, manifest_path in artifacts.get('kubernetes_manifests', {}).items():
            manifest_src = Path(manifest_path)
            if manifest_src.exists():
                shutil.copy2(manifest_src, k8s_artifacts_dir / f"{manifest_type}.yaml")
        
        self.logger.info(f"Build artifacts saved to {artifacts_dir}")
    
    def _cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
            self.logger.info("Temporary build files cleaned up")
