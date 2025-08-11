"""
Varuna - The Code Intake & Analysis Agent
Handles code ingestion, analysis, and project structure detection
"""

import os
import json
import git
import zipfile
import tempfile
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import requests
import yaml
import toml
import xml.etree.ElementTree as ET

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import BaseTool
from langchain.schema import SystemMessage
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate

@dataclass
class ProjectManifest:
    """Project analysis results"""
    project_name: str
    tech_stack: List[str]
    languages: Dict[str, float]  # language -> percentage
    dependencies: Dict[str, List[str]]  # package_manager -> [dependencies]
    architecture: Dict[str, Any]
    build_config: Dict[str, Any]
    security_notes: List[str]
    recommendations: List[str]
    file_structure: Dict[str, Any]
    estimated_complexity: str  # low, medium, high
    build_time_estimate: int  # minutes

class VarunaAgent:
    """Code Intake & Analysis Agent"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.temp_dir = None
        self.project_path = None
        
        # Initialize LLM
        self.llm = Ollama(model="codellama", base_url="http://localhost:11434")
        
        # Language detection patterns
        self.language_patterns = {
            'python': ['.py', 'requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile'],
            'javascript': ['.js', '.jsx', 'package.json', '.npmrc'],
            'typescript': ['.ts', '.tsx', 'tsconfig.json'],
            'java': ['.java', 'pom.xml', 'build.gradle', 'gradle.properties'],
            'go': ['.go', 'go.mod', 'go.sum'],
            'rust': ['.rs', 'Cargo.toml', 'Cargo.lock'],
            'php': ['.php', 'composer.json', 'composer.lock'],
            'ruby': ['.rb', 'Gemfile', 'Gemfile.lock'],
            'csharp': ['.cs', '.csproj', '.sln', 'packages.config'],
            'cpp': ['.cpp', '.hpp', '.cc', '.h', 'CMakeLists.txt', 'Makefile'],
            'docker': ['Dockerfile', 'docker-compose.yml', '.dockerignore'],
            'kubernetes': ['.yaml', '.yml', 'kustomization.yaml']
        }
        
        # Framework detection patterns
        self.framework_patterns = {
            'react': ['react', '@types/react', 'react-dom'],
            'vue': ['vue', '@vue/cli', 'nuxt'],
            'angular': ['@angular/core', '@angular/cli'],
            'express': ['express', 'express-generator'],
            'fastapi': ['fastapi', 'uvicorn'],
            'django': ['django', 'djangorestframework'],
            'flask': ['flask', 'flask-restful'],
            'spring': ['spring-boot-starter', 'springframework'],
            'laravel': ['laravel/framework', 'laravel/tinker'],
            'rails': ['rails', 'railties'],
            'nextjs': ['next', '@next/'],
            'gatsby': ['gatsby', 'gatsby-cli'],
            'svelte': ['svelte', '@sveltejs/kit']
        }
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution method for Varuna agent"""
        try:
            self.logger.info("Varuna: Starting code intake and analysis")
            
            # Step 1: Ingest code
            project_path = self._ingest_code(input_data)
            
            # Step 2: Analyze project structure
            file_structure = self._analyze_file_structure(project_path)
            
            # Step 3: Detect languages and tech stack
            languages, tech_stack = self._detect_tech_stack(project_path)
            
            # Step 4: Parse dependencies
            dependencies = self._parse_dependencies(project_path)
            
            # Step 5: Analyze architecture
            architecture = self._analyze_architecture(project_path, tech_stack)
            
            # Step 6: Generate build configuration
            build_config = self._generate_build_config(project_path, tech_stack)
            
            # Step 7: Security analysis
            security_notes = self._analyze_security_concerns(project_path, dependencies)
            
            # Step 8: Generate recommendations
            recommendations = self._generate_recommendations(
                tech_stack, dependencies, architecture
            )
            
            # Step 9: Estimate complexity and build time
            complexity, build_time = self._estimate_complexity(
                file_structure, dependencies, tech_stack
            )
            
            # Create project manifest
            manifest = ProjectManifest(
                project_name=input_data.get('project_name', 'unknown'),
                tech_stack=tech_stack,
                languages=languages,
                dependencies=dependencies,
                architecture=architecture,
                build_config=build_config,
                security_notes=security_notes,
                recommendations=recommendations,
                file_structure=file_structure,
                estimated_complexity=complexity,
                build_time_estimate=build_time
            )
            
            # Convert to dict for JSON serialization
            result = {
                'project_name': manifest.project_name,
                'tech_stack': manifest.tech_stack,
                'languages': manifest.languages,
                'dependencies': manifest.dependencies,
                'architecture': manifest.architecture,
                'build_config': manifest.build_config,
                'security_notes': manifest.security_notes,
                'recommendations': manifest.recommendations,
                'file_structure': manifest.file_structure,
                'estimated_complexity': manifest.estimated_complexity,
                'build_time_estimate': manifest.build_time_estimate,
                'analysis_timestamp': str(datetime.now()),
                'agent': 'varuna'
            }
            
            # Save manifest to artifacts
            self._save_manifest(result)
            
            self.logger.info("Varuna: Analysis completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Varuna execution failed: {str(e)}")
            raise
        finally:
            self._cleanup()
    
    def _ingest_code(self, input_data: Dict[str, Any]) -> Path:
        """Ingest code from various sources"""
        source_type = input_data.get('source_type', 'upload')
        
        if source_type == 'git':
            return self._clone_repository(input_data['git_url'])
        elif source_type == 'zip':
            return self._extract_zip(input_data['zip_path'])
        elif source_type == 'local':
            return Path(input_data['local_path'])
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
    
    def _clone_repository(self, git_url: str) -> Path:
        """Clone Git repository"""
        self.temp_dir = tempfile.mkdtemp(prefix="varuna_")
        repo_path = Path(self.temp_dir) / "repo"
        
        try:
            git.Repo.clone_from(git_url, repo_path)
            self.logger.info(f"Successfully cloned repository: {git_url}")
            return repo_path
        except Exception as e:
            self.logger.error(f"Failed to clone repository: {str(e)}")
            raise
    
    def _extract_zip(self, zip_path: str) -> Path:
        """Extract ZIP file"""
        self.temp_dir = tempfile.mkdtemp(prefix="varuna_")
        extract_path = Path(self.temp_dir) / "extracted"
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # Find the actual project root (handle nested folders)
            contents = list(extract_path.iterdir())
            if len(contents) == 1 and contents[0].is_dir():
                return contents[0]
            return extract_path
            
        except Exception as e:
            self.logger.error(f"Failed to extract ZIP: {str(e)}")
            raise
    
    def _analyze_file_structure(self, project_path: Path) -> Dict[str, Any]:
        """Analyze project file structure"""
        structure = {
            'total_files': 0,
            'total_size': 0,
            'directories': [],
            'file_types': {},
            'important_files': []
        }
        
        important_files = [
            'README.md', 'README.txt', 'LICENSE', 'Dockerfile', 
            'docker-compose.yml', '.gitignore', 'Makefile',
            'requirements.txt', 'package.json', 'pom.xml',
            'setup.py', 'pyproject.toml', 'Cargo.toml', 'go.mod'
        ]
        
        for root, dirs, files in os.walk(project_path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'target', 'build']]
            
            rel_root = Path(root).relative_to(project_path)
            if rel_root != Path('.'):
                structure['directories'].append(str(rel_root))
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = Path(root) / file
                structure['total_files'] += 1
                structure['total_size'] += file_path.stat().st_size
                
                # Track file extensions
                ext = file_path.suffix.lower()
                structure['file_types'][ext] = structure['file_types'].get(ext, 0) + 1
                
                # Track important files
                if file in important_files:
                    structure['important_files'].append(str(file_path.relative_to(project_path)))
        
        return structure
    
    def _detect_tech_stack(self, project_path: Path) -> Tuple[Dict[str, float], List[str]]:
        """Detect programming languages and tech stack"""
        languages = {}
        tech_stack = []
        
        # Count files by language
        total_files = 0
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = Path(root) / file
                ext = file_path.suffix.lower()
                
                # Map extensions to languages
                lang_mapping = {
                    '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                    '.java': 'java', '.go': 'go', '.rs': 'rust', '.php': 'php',
                    '.rb': 'ruby', '.cs': 'csharp', '.cpp': 'cpp', '.cc': 'cpp',
                    '.h': 'cpp', '.hpp': 'cpp', '.jsx': 'javascript', '.tsx': 'typescript'
                }
                
                if ext in lang_mapping:
                    lang = lang_mapping[ext]
                    languages[lang] = languages.get(lang, 0) + 1
                    total_files += 1
        
        # Convert to percentages
        if total_files > 0:
            languages = {lang: (count / total_files) * 100 for lang, count in languages.items()}
        
        # Detect tech stack from file patterns
        for lang, patterns in self.language_patterns.items():
            for pattern in patterns:
                if self._find_files(project_path, pattern):
                    if lang not in tech_stack:
                        tech_stack.append(lang)
        
        # Detect frameworks
        dependencies = self._parse_dependencies(project_path)
        for framework, indicators in self.framework_patterns.items():
            for indicator in indicators:
                for dep_list in dependencies.values():
                    if any(indicator in dep for dep in dep_list):
                        tech_stack.append(framework)
                        break
        
        return languages, list(set(tech_stack))
    
    def _parse_dependencies(self, project_path: Path) -> Dict[str, List[str]]:
        """Parse project dependencies from various package managers"""
        dependencies = {}
        
        # Python dependencies
        req_files = ['requirements.txt', 'requirements-dev.txt', 'dev-requirements.txt']
        for req_file in req_files:
            req_path = project_path / req_file
            if req_path.exists():
                dependencies['pip'] = self._parse_requirements_txt(req_path)
                break
        
        # Python setup.py
        setup_py = project_path / 'setup.py'
        if setup_py.exists():
            setup_deps = self._parse_setup_py(setup_py)
            if setup_deps:
                dependencies['setuptools'] = setup_deps
        
        # Python pyproject.toml
        pyproject = project_path / 'pyproject.toml'
        if pyproject.exists():
            pyproject_deps = self._parse_pyproject_toml(pyproject)
            if pyproject_deps:
                dependencies['poetry'] = pyproject_deps
        
        # Node.js dependencies
        package_json = project_path / 'package.json'
        if package_json.exists():
            npm_deps = self._parse_package_json(package_json)
            if npm_deps:
                dependencies['npm'] = npm_deps
        
        # Java dependencies
        pom_xml = project_path / 'pom.xml'
        if pom_xml.exists():
            maven_deps = self._parse_pom_xml(pom_xml)
            if maven_deps:
                dependencies['maven'] = maven_deps
        
        # Go dependencies
        go_mod = project_path / 'go.mod'
        if go_mod.exists():
            go_deps = self._parse_go_mod(go_mod)
            if go_deps:
                dependencies['go'] = go_deps
        
        # Rust dependencies
        cargo_toml = project_path / 'Cargo.toml'
        if cargo_toml.exists():
            cargo_deps = self._parse_cargo_toml(cargo_toml)
            if cargo_deps:
                dependencies['cargo'] = cargo_deps
        
        return dependencies
    
    def _parse_requirements_txt(self, req_path: Path) -> List[str]:
        """Parse Python requirements.txt"""
        try:
            with open(req_path, 'r') as f:
                lines = f.readlines()
            
            deps = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    # Extract package name (before version specifiers)
                    pkg = line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].split('~=')[0]
                    deps.append(pkg.strip())
            
            return deps
        except Exception as e:
            self.logger.warning(f"Failed to parse requirements.txt: {str(e)}")
            return []
    
    def _parse_package_json(self, package_path: Path) -> List[str]:
        """Parse Node.js package.json"""
        try:
            with open(package_path, 'r') as f:
                package_data = json.load(f)
            
            deps = []
            for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
                if dep_type in package_data:
                    deps.extend(package_data[dep_type].keys())
            
            return deps
        except Exception as e:
            self.logger.warning(f"Failed to parse package.json: {str(e)}")
            return []
    
    def _parse_pom_xml(self, pom_path: Path) -> List[str]:
        """Parse Maven pom.xml"""
        try:
            tree = ET.parse(pom_path)
            root = tree.getroot()
            
            # Handle XML namespaces
            ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            if root.tag.startswith('{'):
                ns_uri = root.tag.split('}')[0][1:]
                ns = {'maven': ns_uri}
            
            deps = []
            dependencies = root.findall('.//maven:dependency', ns)
            for dep in dependencies:
                group_id = dep.find('maven:groupId', ns)
                artifact_id = dep.find('maven:artifactId', ns)
                if group_id is not None and artifact_id is not None:
                    deps.append(f"{group_id.text}:{artifact_id.text}")
            
            return deps
        except Exception as e:
            self.logger.warning(f"Failed to parse pom.xml: {str(e)}")
            return []
    
    def _parse_go_mod(self, go_mod_path: Path) -> List[str]:
        """Parse Go go.mod"""
        try:
            with open(go_mod_path, 'r') as f:
                content = f.read()
            
            deps = []
            in_require = False
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('require'):
                    in_require = True
                    if '(' in line:
                        continue
                    else:
                        # Single require line
                        parts = line.split()
                        if len(parts) >= 2:
                            deps.append(parts[1])
                elif in_require:
                    if line == ')':
                        in_require = False
                    elif line and not line.startswith('//'):
                        parts = line.split()
                        if parts:
                            deps.append(parts[0])
            
            return deps
        except Exception as e:
            self.logger.warning(f"Failed to parse go.mod: {str(e)}")
            return []
    
    def _parse_cargo_toml(self, cargo_path: Path) -> List[str]:
        """Parse Rust Cargo.toml"""
        try:
            with open(cargo_path, 'r') as f:
                cargo_data = toml.load(f)
            
            deps = []
            for dep_type in ['dependencies', 'dev-dependencies', 'build-dependencies']:
                if dep_type in cargo_data:
                    deps.extend(cargo_data[dep_type].keys())
            
            return deps
        except Exception as e:
            self.logger.warning(f"Failed to parse Cargo.toml: {str(e)}")
            return []
    
    def _parse_setup_py(self, setup_path: Path) -> List[str]:
        """Parse Python setup.py (basic extraction)"""
        try:
            with open(setup_path, 'r') as f:
                content = f.read()
            
            # Simple regex-based extraction (not perfect but functional)
            import re
            
            # Look for install_requires
            install_requires_match = re.search(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if install_requires_match:
                deps_str = install_requires_match.group(1)
                deps = []
                for line in deps_str.split(','):
                    line = line.strip().strip('"\'')
                    if line and not line.startswith('#'):
                        pkg = line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0]
                        deps.append(pkg.strip())
                return deps
            
            return []
        except Exception as e:
            self.logger.warning(f"Failed to parse setup.py: {str(e)}")
            return []
    
    def _parse_pyproject_toml(self, pyproject_path: Path) -> List[str]:
        """Parse Python pyproject.toml"""
        try:
            with open(pyproject_path, 'r') as f:
                pyproject_data = toml.load(f)
            
            deps = []
            
            # Poetry dependencies
            if 'tool' in pyproject_data and 'poetry' in pyproject_data['tool']:
                poetry_deps = pyproject_data['tool']['poetry'].get('dependencies', {})
                deps.extend([k for k in poetry_deps.keys() if k != 'python'])
                
                dev_deps = pyproject_data['tool']['poetry'].get('dev-dependencies', {})
                deps.extend(dev_deps.keys())
            
            # PEP 621 dependencies
            if 'project' in pyproject_data:
                project_deps = pyproject_data['project'].get('dependencies', [])
                for dep in project_deps:
                    pkg = dep.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0]
                    deps.append(pkg.strip())
            
            return deps
        except Exception as e:
            self.logger.warning(f"Failed to parse pyproject.toml: {str(e)}")
            return []
    
    def _analyze_architecture(self, project_path: Path, tech_stack: List[str]) -> Dict[str, Any]:
        """Analyze project architecture"""
        architecture = {
            'type': 'unknown',
            'patterns': [],
            'entry_points': [],
            'config_files': [],
            'test_directories': [],
            'documentation': []
        }
        
        # Detect architecture type
        if 'docker' in tech_stack:
            architecture['type'] = 'containerized'
        elif 'kubernetes' in tech_stack:
            architecture['type'] = 'microservices'
        elif any(fw in tech_stack for fw in ['react', 'vue', 'angular']):
            architecture['type'] = 'spa'
        elif any(fw in tech_stack for fw in ['django', 'flask', 'fastapi', 'express']):
            architecture['type'] = 'web_api'
        elif 'python' in tech_stack:
            architecture['type'] = 'python_app'
        
        # Find entry points
        entry_points = [
            'main.py', 'app.py', 'server.py', 'index.js', 'index.ts',
            'main.go', 'main.rs', 'Main.java', 'Program.cs'
        ]
        
        for entry in entry_points:
            if (project_path / entry).exists():
                architecture['entry_points'].append(entry)
        
        # Find config files
        config_files = [
            'config.py', 'config.js', 'config.json', 'config.yaml',
            'settings.py', '.env', '.env.example', 'application.properties'
        ]
        
        for config in config_files:
            if (project_path / config).exists():
                architecture['config_files'].append(config)
        
        # Find test directories
        test_dirs = ['tests', 'test', '__tests__', 'spec']
        for test_dir in test_dirs:
            if (project_path / test_dir).exists():
                architecture['test_directories'].append(test_dir)
        
        # Find documentation
        doc_files = ['README.md', 'README.txt', 'CHANGELOG.md', 'docs']
        for doc in doc_files:
            if (project_path / doc).exists():
                architecture['documentation'].append(doc)
        
        # Detect patterns
        if (project_path / 'models').exists() or (project_path / 'model').exists():
            architecture['patterns'].append('mvc')
        if (project_path / 'controllers').exists() or (project_path / 'views').exists():
            architecture['patterns'].append('mvc')
        if (project_path / 'services').exists():
            architecture['patterns'].append('service_layer')
        if (project_path / 'api').exists():
            architecture['patterns'].append('api_first')
        
        return architecture
    
    def _generate_build_config(self, project_path: Path, tech_stack: List[str]) -> Dict[str, Any]:
        """Generate build configuration recommendations"""
        build_config = {
            'build_tool': 'unknown',
            'build_commands': [],
            'test_commands': [],
            'dependencies_install': [],
            'environment_setup': [],
            'port': 8000,
            'health_check': None
        }
        
        # Detect build tools and commands
        if 'python' in tech_stack:
            build_config['build_tool'] = 'pip'
            build_config['dependencies_install'] = ['pip install -r requirements.txt']
            
            if 'django' in tech_stack:
                build_config['build_commands'] = [
                    'python manage.py collectstatic --noinput',
                    'python manage.py migrate'
                ]
                build_config['test_commands'] = ['python manage.py test']
                build_config['port'] = 8000
                build_config['health_check'] = '/admin/'
            elif 'flask' in tech_stack:
                build_config['port'] = 5000
                build_config['health_check'] = '/'
            elif 'fastapi' in tech_stack:
                build_config['port'] = 8000
                build_config['health_check'] = '/docs'
        
        elif 'javascript' in tech_stack or 'typescript' in tech_stack:
            build_config['build_tool'] = 'npm'
            build_config['dependencies_install'] = ['npm install']
            
            if 'react' in tech_stack or 'nextjs' in tech_stack:
                build_config['build_commands'] = ['npm run build']
                build_config['test_commands'] = ['npm test']
                build_config['port'] = 3000
            elif 'express' in tech_stack:
                build_config['port'] = 3000
                build_config['health_check'] = '/'
        
        elif 'java' in tech_stack:
            if (project_path / 'pom.xml').exists():
                build_config['build_tool'] = 'maven'
                build_config['dependencies_install'] = ['mvn clean install']
                build_config['build_commands'] = ['mvn package']
                build_config['test_commands'] = ['mvn test']
            elif (project_path / 'build.gradle').exists():
                build_config['build_tool'] = 'gradle'
                build_config['dependencies_install'] = ['gradle build']
                build_config['test_commands'] = ['gradle test']
            build_config['port'] = 8080
        
        elif 'go' in tech_stack:
            build_config['build_tool'] = 'go'
            build_config['dependencies_install'] = ['go mod download']
            build_config['build_commands'] = ['go build']
            build_config['test_commands'] = ['go test ./...']
            build_config['port'] = 8080
        
        elif 'rust' in tech_stack:
            build_config['build_tool'] = 'cargo'
            build_config['dependencies_install'] = ['cargo fetch']
            build_config['build_commands'] = ['cargo build --release']
            build_config['test_commands'] = ['cargo test']
            build_config['port'] = 8000
        
        return build_config
    
    def _analyze_security_concerns(self, project_path: Path, dependencies: Dict[str, List[str]]) -> List[str]:
        """Analyze potential security concerns"""
        security_notes = []
        
        # Check for common security files
        security_files = ['.env', 'config.py', 'settings.py', 'application.properties']
        for sec_file in security_files:
            if (project_path / sec_file).exists():
                security_notes.append(f"Found configuration file: {sec_file} - ensure secrets are not hardcoded")
        
        # Check for dependency vulnerabilities (basic patterns)
        vulnerable_patterns = {
            'python': ['django<3.0', 'flask<1.0', 'requests<2.20'],
            'javascript': ['express<4.17', 'lodash<4.17.12', 'axios<0.21.1'],
            'java': ['spring-core<5.3.21', 'jackson-databind<2.13.3']
        }
        
        for pkg_manager, deps in dependencies.items():
            if pkg_manager in ['pip', 'setuptools', 'poetry']:
                lang = 'python'
            elif pkg_manager == 'npm':
                lang = 'javascript'
            elif pkg_manager == 'maven':
                lang = 'java'
            else:
                continue
            
            if lang in vulnerable_patterns:
                for pattern in vulnerable_patterns[lang]:
                    pkg_name = pattern.split('<')[0]
                    if any(pkg_name in dep for dep in deps):
                        security_notes.append(f"Potentially vulnerable dependency: {pattern}")
        
        # Check for hardcoded secrets (basic patterns)
        secret_patterns = ['password', 'secret', 'key', 'token', 'api_key']
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.java', '.go', '.rs')):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read().lower()
                            for pattern in secret_patterns:
                                if f'{pattern}=' in content or f'"{pattern}"' in content:
                                    security_notes.append(f"Potential hardcoded secret in {file_path.relative_to(project_path)}")
                                    break
                    except Exception:
                        continue
        
        return security_notes
    
    def _generate_recommendations(self, tech_stack: List[str], dependencies: Dict[str, List[str]], 
                                architecture: Dict[str, Any]) -> List[str]:
        """Generate build and deployment recommendations"""
        recommendations = []
        
        # Docker recommendations
        if 'docker' not in tech_stack:
            recommendations.append("Consider adding Docker for consistent deployment environments")
        
        # Testing recommendations
        if not architecture['test_directories']:
            recommendations.append("Add automated tests to improve code quality and reliability")
        
        # Documentation recommendations
        if not architecture['documentation']:
            recommendations.append("Add README.md with setup and usage instructions")
        
        # Security recommendations
        recommendations.append("Implement dependency vulnerability scanning in CI/CD pipeline")
        recommendations.append("Use environment variables for sensitive configuration")
        
        # Performance recommendations
        if 'python' in tech_stack:
            recommendations.append("Consider using gunicorn or uvicorn for production deployment")
        elif 'javascript' in tech_stack:
            recommendations.append("Implement code splitting and lazy loading for better performance")
        
        # Monitoring recommendations
        recommendations.append("Add health check endpoints for monitoring")
        recommendations.append("Implement structured logging for better observability")
        
        return recommendations
    
    def _estimate_complexity(self, file_structure: Dict[str, Any], dependencies: Dict[str, List[str]], 
                           tech_stack: List[str]) -> Tuple[str, int]:
        """Estimate project complexity and build time"""
        complexity_score = 0
        
        # File count factor
        file_count = file_structure['total_files']
        if file_count > 1000:
            complexity_score += 3
        elif file_count > 100:
            complexity_score += 2
        elif file_count > 10:
            complexity_score += 1
        
        # Dependency factor
        total_deps = sum(len(deps) for deps in dependencies.values())
        if total_deps > 100:
            complexity_score += 3
        elif total_deps > 50:
            complexity_score += 2
        elif total_deps > 10:
            complexity_score += 1
        
        # Tech stack complexity
        complex_techs = ['kubernetes', 'docker', 'microservices', 'spring', 'django']
        complexity_score += sum(1 for tech in tech_stack if tech in complex_techs)
        
        # Determine complexity level
        if complexity_score >= 6:
            complexity = 'high'
            build_time = 15 + (complexity_score * 2)
        elif complexity_score >= 3:
            complexity = 'medium'
            build_time = 8 + complexity_score
        else:
            complexity = 'low'
            build_time = 3 + complexity_score
        
        return complexity, min(build_time, 60)  # Cap at 60 minutes
    
    def _find_files(self, project_path: Path, pattern: str) -> List[Path]:
        """Find files matching a pattern"""
        matches = []
        if pattern.startswith('.'):
            # Extension pattern
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.endswith(pattern):
                        matches.append(Path(root) / file)
        else:
            # Filename pattern
            for root, dirs, files in os.walk(project_path):
                if pattern in files:
                    matches.append(Path(root) / pattern)
        return matches
    
    def _save_manifest(self, manifest: Dict[str, Any]):
        """Save project manifest to artifacts directory"""
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        
        manifest_path = artifacts_dir / f"project_manifest_{manifest['project_name']}.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2, default=str)
        
        self.logger.info(f"Project manifest saved to {manifest_path}")
    
    def _cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and Path(self.temp_dir).exists():
            import shutil
            shutil.rmtree(self.temp_dir)
            self.logger.info("Temporary files cleaned up")
