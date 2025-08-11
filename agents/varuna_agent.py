import os
import git
import zipfile
import tempfile
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List
import ast
import re
from .base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

class VarunaAgent(BaseAgent):
    """Code Intake & Analysis Agent - Varuna"""
    
    def __init__(self, llm_client, config: Dict[str, Any]):
        super().__init__("Varuna", llm_client, config)
        self.supported_languages = {
            '.py': 'Python',
            '.js': 'JavaScript', 
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.go': 'Go',
            '.rs': 'Rust',
            '.cpp': 'C++',
            '.c': 'C',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.cs': 'C#'
        }
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code analysis"""
        self.start_execution()
        
        try:
            project_path = self._extract_project(input_data)
            
            # Analyze project structure
            structure = self._analyze_structure(project_path)
            
            # Detect languages and frameworks
            tech_stack = self._detect_tech_stack(project_path)
            
            # Analyze dependencies
            dependencies = self._analyze_dependencies(project_path, tech_stack)
            
            # Perform static code analysis
            code_quality = self._analyze_code_quality(project_path, tech_stack)
            
            # Generate build plan
            build_plan = self._generate_build_plan(project_path, tech_stack, dependencies)
            
            self.results = {
                "project_path": str(project_path),
                "structure": structure,
                "tech_stack": tech_stack,
                "dependencies": dependencies,
                "code_quality": code_quality,
                "build_plan": build_plan,
                "analysis_summary": self._generate_summary()
            }
            
            self.end_execution(True)
            return self.results
            
        except Exception as e:
            self.add_error(f"Code analysis failed: {str(e)}")
            self.end_execution(False)
            raise
    
    def _extract_project(self, input_data: Dict[str, Any]) -> Path:
        """Extract project from various sources"""
        project_type = input_data.get('type')
        
        if project_type == 'zip':
            return self._extract_zip(input_data['file'])
        elif project_type == 'git':
            return self._clone_repository(input_data['url'], input_data.get('branch', 'main'))
        elif project_type == 'local':
            return Path(input_data['path'])
        else:
            raise ValueError(f"Unsupported project type: {project_type}")
    
    def _extract_zip(self, zip_file) -> Path:
        """Extract ZIP file to temporary directory"""
        temp_dir = Path(tempfile.mkdtemp(prefix="vedops_"))
        
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the actual project root (handle nested directories)
        contents = list(temp_dir.iterdir())
        if len(contents) == 1 and contents[0].is_dir():
            return contents[0]
        
        return temp_dir
    
    def _clone_repository(self, repo_url: str, branch: str) -> Path:
        """Clone Git repository"""
        temp_dir = Path(tempfile.mkdtemp(prefix="vedops_git_"))
        
        try:
            repo = git.Repo.clone_from(repo_url, temp_dir, branch=branch)
            logger.info(f"Cloned repository {repo_url} (branch: {branch})")
            return temp_dir
        except Exception as e:
            raise Exception(f"Failed to clone repository: {str(e)}")
    
    def _analyze_structure(self, project_path: Path) -> Dict[str, Any]:
        """Analyze project directory structure"""
        structure = {
            "total_files": 0,
            "total_directories": 0,
            "file_types": {},
            "directory_tree": {},
            "large_files": []
        }
        
        for root, dirs, files in os.walk(project_path):
            structure["total_directories"] += len(dirs)
            structure["total_files"] += len(files)
            
            for file in files:
                file_path = Path(root) / file
                file_size = file_path.stat().st_size
                
                # Track file types
                suffix = file_path.suffix.lower()
                structure["file_types"][suffix] = structure["file_types"].get(suffix, 0) + 1
                
                # Track large files (>1MB)
                if file_size > 1024 * 1024:
                    structure["large_files"].append({
                        "path": str(file_path.relative_to(project_path)),
                        "size_mb": round(file_size / (1024 * 1024), 2)
                    })
        
        return structure
    
    def _detect_tech_stack(self, project_path: Path) -> Dict[str, Any]:
        """Detect programming languages and frameworks"""
        tech_stack = {
            "primary_language": None,
            "languages": {},
            "frameworks": [],
            "build_tools": [],
            "package_managers": []
        }
        
        # Detect languages by file extensions
        language_counts = {}
        for root, _, files in os.walk(project_path):
            for file in files:
                suffix = Path(file).suffix.lower()
                if suffix in self.supported_languages:
                    lang = self.supported_languages[suffix]
                    language_counts[lang] = language_counts.get(lang, 0) + 1
        
        if language_counts:
            tech_stack["primary_language"] = max(language_counts, key=language_counts.get)
            tech_stack["languages"] = language_counts
        
        # Detect frameworks and tools by configuration files
        config_files = {
            "package.json": {"frameworks": ["Node.js"], "package_manager": "npm"},
            "requirements.txt": {"frameworks": ["Python"], "package_manager": "pip"},
            "Pipfile": {"frameworks": ["Python"], "package_manager": "pipenv"},
            "poetry.lock": {"frameworks": ["Python"], "package_manager": "poetry"},
            "pom.xml": {"frameworks": ["Java", "Maven"], "build_tool": "Maven"},
            "build.gradle": {"frameworks": ["Java", "Gradle"], "build_tool": "Gradle"},
            "Cargo.toml": {"frameworks": ["Rust"], "package_manager": "cargo"},
            "go.mod": {"frameworks": ["Go"], "package_manager": "go mod"},
            "composer.json": {"frameworks": ["PHP"], "package_manager": "composer"},
            "Gemfile": {"frameworks": ["Ruby"], "package_manager": "bundler"},
            "Dockerfile": {"frameworks": ["Docker"]},
            "docker-compose.yml": {"frameworks": ["Docker Compose"]},
            "kubernetes.yaml": {"frameworks": ["Kubernetes"]},
            "terraform.tf": {"frameworks": ["Terraform"]},
        }
        
        for config_file, info in config_files.items():
            if (project_path / config_file).exists():
                tech_stack["frameworks"].extend(info.get("frameworks", []))
                if "package_manager" in info:
                    tech_stack["package_managers"].append(info["package_manager"])
                if "build_tool" in info:
                    tech_stack["build_tools"].append(info["build_tool"])
        
        # Detect specific frameworks by analyzing package.json
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    package_data = json.load(f)
                    dependencies = {**package_data.get("dependencies", {}), 
                                  **package_data.get("devDependencies", {})}
                    
                    framework_patterns = {
                        "react": "React",
                        "vue": "Vue.js", 
                        "angular": "Angular",
                        "express": "Express.js",
                        "next": "Next.js",
                        "nuxt": "Nuxt.js",
                        "svelte": "Svelte",
                        "fastify": "Fastify"
                    }
                    
                    for dep, framework in framework_patterns.items():
                        if any(dep in key.lower() for key in dependencies.keys()):
                            if framework not in tech_stack["frameworks"]:
                                tech_stack["frameworks"].append(framework)
            except Exception as e:
                logger.warning(f"Failed to parse package.json: {e}")
        
        return tech_stack
    
    def _analyze_dependencies(self, project_path: Path, tech_stack: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project dependencies"""
        dependencies = {
            "total_dependencies": 0,
            "outdated_dependencies": [],
            "vulnerable_dependencies": [],
            "dependency_files": []
        }
        
        # Python dependencies
        if "Python" in tech_stack.get("languages", {}):
            self._analyze_python_dependencies(project_path, dependencies)
        
        # Node.js dependencies  
        if "JavaScript" in tech_stack.get("languages", {}) or "TypeScript" in tech_stack.get("languages", {}):
            self._analyze_nodejs_dependencies(project_path, dependencies)
        
        return dependencies
    
    def _analyze_python_dependencies(self, project_path: Path, dependencies: Dict[str, Any]):
        """Analyze Python dependencies"""
        req_files = ["requirements.txt", "Pipfile", "pyproject.toml"]
        
        for req_file in req_files:
            req_path = project_path / req_file
            if req_path.exists():
                dependencies["dependency_files"].append(req_file)
                
                if req_file == "requirements.txt":
                    try:
                        with open(req_path) as f:
                            lines = f.readlines()
                            deps = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
                            dependencies["total_dependencies"] += len(deps)
                            
                            # Check for vulnerable packages using safety
                            try:
                                result = subprocess.run(
                                    ["safety", "check", "-r", str(req_path), "--json"],
                                    capture_output=True, text=True, timeout=30
                                )
                                if result.returncode == 0:
                                    safety_data = json.loads(result.stdout)
                                    dependencies["vulnerable_dependencies"].extend(safety_data)
                            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                                logger.warning("Safety check failed or not available")
                                
                    except Exception as e:
                        logger.warning(f"Failed to analyze {req_file}: {e}")
    
    def _analyze_nodejs_dependencies(self, project_path: Path, dependencies: Dict[str, Any]):
        """Analyze Node.js dependencies"""
        package_json = project_path / "package.json"
        
        if package_json.exists():
            dependencies["dependency_files"].append("package.json")
            
            try:
                with open(package_json) as f:
                    package_data = json.load(f)
                    
                    deps = package_data.get("dependencies", {})
                    dev_deps = package_data.get("devDependencies", {})
                    dependencies["total_dependencies"] = len(deps) + len(dev_deps)
                    
                    # Check for vulnerabilities using npm audit
                    try:
                        result = subprocess.run(
                            ["npm", "audit", "--json"],
                            cwd=project_path, capture_output=True, text=True, timeout=60
                        )
                        if result.stdout:
                            audit_data = json.loads(result.stdout)
                            if "vulnerabilities" in audit_data:
                                for vuln_name, vuln_data in audit_data["vulnerabilities"].items():
                                    dependencies["vulnerable_dependencies"].append({
                                        "package": vuln_name,
                                        "severity": vuln_data.get("severity", "unknown"),
                                        "title": vuln_data.get("title", "")
                                    })
                    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                        logger.warning("npm audit failed or not available")
                        
            except Exception as e:
                logger.warning(f"Failed to analyze package.json: {e}")
    
    def _analyze_code_quality(self, project_path: Path, tech_stack: Dict[str, Any]) -> Dict[str, Any]:
        """Perform static code analysis"""
        quality_metrics = {
            "complexity_score": 0,
            "maintainability_index": 0,
            "code_smells": [],
            "security_issues": [],
            "test_coverage": 0
        }
        
        primary_lang = tech_stack.get("primary_language")
        
        if primary_lang == "Python":
            self._analyze_python_quality(project_path, quality_metrics)
        elif primary_lang in ["JavaScript", "TypeScript"]:
            self._analyze_javascript_quality(project_path, quality_metrics)
        
        return quality_metrics
    
    def _analyze_python_quality(self, project_path: Path, quality_metrics: Dict[str, Any]):
        """Analyze Python code quality"""
        try:
            # Use radon for complexity analysis
            result = subprocess.run(
                ["radon", "cc", str(project_path), "-j"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                complexity_data = json.loads(result.stdout)
                # Calculate average complexity
                total_complexity = 0
                total_functions = 0
                for file_data in complexity_data.values():
                    for item in file_data:
                        if item["type"] in ["function", "method"]:
                            total_complexity += item["complexity"]
                            total_functions += 1
                
                if total_functions > 0:
                    quality_metrics["complexity_score"] = total_complexity / total_functions
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            logger.warning("Radon analysis failed or not available")
        
        try:
            # Use bandit for security analysis
            result = subprocess.run(
                ["bandit", "-r", str(project_path), "-f", "json"],
                capture_output=True, text=True, timeout=60
            )
            if result.stdout:
                bandit_data = json.loads(result.stdout)
                quality_metrics["security_issues"] = bandit_data.get("results", [])
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            logger.warning("Bandit analysis failed or not available")
    
    def _analyze_javascript_quality(self, project_path: Path, quality_metrics: Dict[str, Any]):
        """Analyze JavaScript/TypeScript code quality"""
        try:
            # Use ESLint for code quality
            result = subprocess.run(
                ["npx", "eslint", ".", "--format", "json"],
                cwd=project_path, capture_output=True, text=True, timeout=60
            )
            if result.stdout:
                eslint_data = json.loads(result.stdout)
                total_issues = sum(len(file_data.get("messages", [])) for file_data in eslint_data)
                quality_metrics["code_smells"] = [
                    {"file": item["filePath"], "issues": len(item.get("messages", []))}
                    for item in eslint_data if item.get("messages")
                ]
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            logger.warning("ESLint analysis failed or not available")
    
    def _generate_build_plan(self, project_path: Path, tech_stack: Dict[str, Any], 
                           dependencies: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive build plan"""
        build_plan = {
            "build_steps": [],
            "docker_strategy": "multi-stage",
            "base_image": self._select_base_image(tech_stack),
            "build_tools": tech_stack.get("build_tools", []),
            "package_managers": tech_stack.get("package_managers", []),
            "environment_variables": [],
            "ports": [],
            "volumes": [],
            "health_check": None
        }
        
        primary_lang = tech_stack.get("primary_language")
        
        if primary_lang == "Python":
            build_plan["build_steps"] = [
                "COPY requirements.txt .",
                "RUN pip install --no-cache-dir -r requirements.txt",
                "COPY . .",
                "RUN python -m pytest --cov=. --cov-report=xml || true",
                "EXPOSE 8000",
                "CMD [\"python\", \"app.py\"]"
            ]
            build_plan["ports"] = [8000]
            build_plan["health_check"] = "curl -f http://localhost:8000/health || exit 1"
            
        elif primary_lang in ["JavaScript", "TypeScript"]:
            build_plan["build_steps"] = [
                "COPY package*.json ./",
                "RUN npm ci --only=production",
                "COPY . .",
                "RUN npm run build || true",
                "RUN npm test || true",
                "EXPOSE 3000",
                "CMD [\"npm\", \"start\"]"
            ]
            build_plan["ports"] = [3000]
            build_plan["health_check"] = "curl -f http://localhost:3000/health || exit 1"
        
        return build_plan
    
    def _select_base_image(self, tech_stack: Dict[str, Any]) -> str:
        """Select appropriate base Docker image"""
        primary_lang = tech_stack.get("primary_language")
        
        base_images = {
            "Python": "python:3.11-slim",
            "JavaScript": "node:18-alpine",
            "TypeScript": "node:18-alpine", 
            "Java": "openjdk:17-jre-slim",
            "Go": "golang:1.21-alpine",
            "Rust": "rust:1.70-slim",
            "PHP": "php:8.2-fpm-alpine",
            "Ruby": "ruby:3.2-alpine"
        }
        
        return base_images.get(primary_lang, "ubuntu:22.04")
    
    def _generate_summary(self) -> str:
        """Generate AI-powered analysis summary"""
        try:
            summary_prompt = f"""
            Analyze this project and provide a concise summary:
            
            Tech Stack: {self.results.get('tech_stack', {})}
            Dependencies: {self.results.get('dependencies', {})}
            Code Quality: {self.results.get('code_quality', {})}
            
            Provide:
            1. Project type and main technology
            2. Key findings and recommendations
            3. Potential risks or issues
            4. Build complexity assessment
            """
            
            response = self.llm_client.invoke(summary_prompt)
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.warning(f"Failed to generate AI summary: {e}")
            return "Analysis completed successfully. Review detailed results for insights."
