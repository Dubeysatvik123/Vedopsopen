"""
Project Manager
Handles project data, file operations, and state management
"""

import os
import json
import shutil
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

class ProjectManager:
    """
    Manages project lifecycle, file operations, and metadata
    """
    
    def __init__(self, workspace_dir: str = "./workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.workspace_dir / "projects").mkdir(exist_ok=True)
        (self.workspace_dir / "artifacts").mkdir(exist_ok=True)
        (self.workspace_dir / "reports").mkdir(exist_ok=True)
        (self.workspace_dir / "temp").mkdir(exist_ok=True)
    
    def create_project(self, project_name: str, source_type: str, source_data: Any) -> Dict[str, Any]:
        """Create a new project from various sources"""
        project_id = self._generate_project_id(project_name)
        project_dir = self.workspace_dir / "projects" / project_id
        project_dir.mkdir(exist_ok=True)
        
        project_metadata = {
            "id": project_id,
            "name": project_name,
            "source_type": source_type,
            "created_at": datetime.now().isoformat(),
            "status": "created",
            "source_path": str(project_dir / "source"),
            "artifacts_path": str(self.workspace_dir / "artifacts" / project_id),
            "reports_path": str(self.workspace_dir / "reports" / project_id)
        }
        
        # Create project subdirectories
        (project_dir / "source").mkdir(exist_ok=True)
        (self.workspace_dir / "artifacts" / project_id).mkdir(exist_ok=True)
        (self.workspace_dir / "reports" / project_id).mkdir(exist_ok=True)
        
        # Handle different source types
        if source_type == "zip":
            self._extract_zip(source_data, project_dir / "source")
        elif source_type == "git":
            self._clone_repository(source_data, project_dir / "source")
        elif source_type == "local":
            self._copy_local_files(source_data, project_dir / "source")
        
        # Save project metadata
        self._save_project_metadata(project_id, project_metadata)
        
        return project_metadata
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project metadata by ID"""
        metadata_file = self.workspace_dir / "projects" / project_id / "metadata.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        
        return None
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects"""
        projects = []
        projects_dir = self.workspace_dir / "projects"
        
        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir():
                metadata = self.get_project(project_dir.name)
                if metadata:
                    projects.append(metadata)
        
        return projects
    
    def update_project_status(self, project_id: str, status: str, additional_data: Dict[str, Any] = None):
        """Update project status and metadata"""
        project_metadata = self.get_project(project_id)
        
        if project_metadata:
            project_metadata["status"] = status
            project_metadata["updated_at"] = datetime.now().isoformat()
            
            if additional_data:
                project_metadata.update(additional_data)
            
            self._save_project_metadata(project_id, project_metadata)
    
    def save_artifact(self, project_id: str, artifact_name: str, artifact_data: Any, artifact_type: str = "file"):
        """Save project artifacts"""
        artifacts_dir = self.workspace_dir / "artifacts" / project_id
        artifacts_dir.mkdir(exist_ok=True)
        
        if artifact_type == "file":
            artifact_path = artifacts_dir / artifact_name
            with open(artifact_path, 'w') as f:
                if isinstance(artifact_data, dict):
                    json.dump(artifact_data, f, indent=2)
                else:
                    f.write(str(artifact_data))
        
        elif artifact_type == "binary":
            artifact_path = artifacts_dir / artifact_name
            with open(artifact_path, 'wb') as f:
                f.write(artifact_data)
    
    def get_artifact(self, project_id: str, artifact_name: str) -> Optional[Any]:
        """Retrieve project artifact"""
        artifact_path = self.workspace_dir / "artifacts" / project_id / artifact_name
        
        if artifact_path.exists():
            if artifact_name.endswith('.json'):
                with open(artifact_path, 'r') as f:
                    return json.load(f)
            else:
                with open(artifact_path, 'r') as f:
                    return f.read()
        
        return None
    
    def save_report(self, project_id: str, report_name: str, report_data: Dict[str, Any]):
        """Save agent reports"""
        reports_dir = self.workspace_dir / "reports" / project_id
        reports_dir.mkdir(exist_ok=True)
        
        report_path = reports_dir / f"{report_name}.json"
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
    
    def get_report(self, project_id: str, report_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve agent report"""
        report_path = self.workspace_dir / "reports" / project_id / f"{report_name}.json"
        
        if report_path.exists():
            with open(report_path, 'r') as f:
                return json.load(f)
        
        return None
    
    def analyze_project_structure(self, project_id: str) -> Dict[str, Any]:
        """Analyze project structure and detect technologies"""
        project_metadata = self.get_project(project_id)
        if not project_metadata:
            return {}
        
        source_path = Path(project_metadata["source_path"])
        
        analysis = {
            "languages": [],
            "frameworks": [],
            "dependencies": {},
            "file_count": 0,
            "total_size": 0,
            "structure": {}
        }
        
        # Analyze files
        for file_path in source_path.rglob("*"):
            if file_path.is_file():
                analysis["file_count"] += 1
                analysis["total_size"] += file_path.stat().st_size
                
                # Detect languages by file extension
                suffix = file_path.suffix.lower()
                language_map = {
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
                
                if suffix in language_map:
                    lang = language_map[suffix]
                    if lang not in analysis["languages"]:
                        analysis["languages"].append(lang)
        
        # Detect frameworks and dependencies
        self._detect_dependencies(source_path, analysis)
        
        return analysis
    
    def _generate_project_id(self, project_name: str) -> str:
        """Generate unique project ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_hash = hashlib.md5(project_name.encode()).hexdigest()[:8]
        return f"{project_name.lower().replace(' ', '_')}_{timestamp}_{name_hash}"
    
    def _extract_zip(self, zip_data: bytes, target_dir: Path):
        """Extract ZIP file to target directory"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            temp_file.write(zip_data)
            temp_file.flush()
            
            with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
        
        os.unlink(temp_file.name)
    
    def _clone_repository(self, repo_url: str, target_dir: Path):
        """Clone Git repository"""
        # This would use git commands or GitPython library
        # For now, we'll simulate it
        pass
    
    def _copy_local_files(self, source_path: str, target_dir: Path):
        """Copy local files to project directory"""
        source = Path(source_path)
        if source.exists():
            shutil.copytree(source, target_dir, dirs_exist_ok=True)
    
    def _save_project_metadata(self, project_id: str, metadata: Dict[str, Any]):
        """Save project metadata to file"""
        metadata_file = self.workspace_dir / "projects" / project_id / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _detect_dependencies(self, source_path: Path, analysis: Dict[str, Any]):
        """Detect project dependencies and frameworks"""
        # Check for common dependency files
        dependency_files = {
            'requirements.txt': 'Python',
            'package.json': 'Node.js',
            'pom.xml': 'Java/Maven',
            'build.gradle': 'Java/Gradle',
            'Cargo.toml': 'Rust',
            'go.mod': 'Go',
            'composer.json': 'PHP'
        }
        
        for dep_file, tech in dependency_files.items():
            file_path = source_path / dep_file
            if file_path.exists():
                if tech not in analysis["frameworks"]:
                    analysis["frameworks"].append(tech)
                
                # Parse dependency file
                try:
                    if dep_file == 'package.json':
                        with open(file_path, 'r') as f:
                            package_data = json.load(f)
                            analysis["dependencies"]["npm"] = {
                                **package_data.get("dependencies", {}),
                                **package_data.get("devDependencies", {})
                            }
                    
                    elif dep_file == 'requirements.txt':
                        with open(file_path, 'r') as f:
                            deps = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
                            analysis["dependencies"]["pip"] = deps
                
                except Exception as e:
                    # Log error but continue
                    pass
