"""
Centralized State Management for VedOps Platform
Handles shared state between agents and UI components
"""

import json
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import threading
import logging

class StateManager:
    """Manages application state and persistence"""
    
    def __init__(self, db_path: str = "vedops_state.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self._init_database()
        
        # In-memory state cache
        self.current_pipeline = {}
        self.agent_states = {}
        self.project_history = []
        
    def _init_database(self):
        """Initialize SQLite database for persistence"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    manifest TEXT,
                    results TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pipeline_id INTEGER,
                    agent_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_data TEXT,
                    output_data TEXT,
                    error_message TEXT,
                    execution_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pipeline_id) REFERENCES pipeline_runs (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS project_artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pipeline_id INTEGER,
                    artifact_type TEXT NOT NULL,
                    artifact_name TEXT NOT NULL,
                    artifact_path TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pipeline_id) REFERENCES pipeline_runs (id)
                )
            """)
    
    def start_pipeline(self, project_name: str, metadata: Dict[str, Any]) -> int:
        """Start a new pipeline run"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO pipeline_runs (project_name, status, start_time, manifest)
                    VALUES (?, ?, ?, ?)
                """, (project_name, "running", datetime.now(), json.dumps(metadata)))
                
                pipeline_id = cursor.lastrowid
                
                self.current_pipeline = {
                    'id': pipeline_id,
                    'project_name': project_name,
                    'status': 'running',
                    'start_time': datetime.now(),
                    'metadata': metadata,
                    'current_step': 'varuna',
                    'progress': 0
                }
                
                return pipeline_id
    
    def update_pipeline_state(self, state: Any):
        """Update pipeline state from orchestrator"""
        with self.lock:
            if hasattr(state, 'pipeline_status'):
                self.current_pipeline['status'] = state.pipeline_status.value
                self.current_pipeline['current_step'] = state.current_step
                
                # Calculate progress based on current step
                step_progress = {
                    'varuna': 16,
                    'agni': 32,
                    'yama': 48,
                    'vayu': 64,
                    'hanuman': 80,
                    'krishna': 95,
                    'completed': 100
                }
                self.current_pipeline['progress'] = step_progress.get(state.current_step, 0)
    
    def log_agent_execution(self, pipeline_id: int, agent_name: str, 
                          status: str, input_data: Dict, output_data: Dict,
                          error_message: str = None, execution_time: float = 0):
        """Log agent execution details"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO agent_logs 
                (pipeline_id, agent_name, status, input_data, output_data, error_message, execution_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                pipeline_id, agent_name, status,
                json.dumps(input_data), json.dumps(output_data),
                error_message, execution_time
            ))
    
    def save_artifact(self, pipeline_id: int, artifact_type: str, 
                     artifact_name: str, artifact_path: str, metadata: Dict = None):
        """Save pipeline artifact information"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO project_artifacts 
                (pipeline_id, artifact_type, artifact_name, artifact_path, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                pipeline_id, artifact_type, artifact_name, 
                artifact_path, json.dumps(metadata or {})
            ))
    
    def get_pipeline_history(self, limit: int = 50) -> List[Dict]:
        """Get recent pipeline execution history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM pipeline_runs 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_agent_logs(self, pipeline_id: int) -> List[Dict]:
        """Get agent execution logs for a pipeline"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM agent_logs 
                WHERE pipeline_id = ?
                ORDER BY created_at ASC
            """, (pipeline_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_current_pipeline(self) -> Dict:
        """Get current pipeline state"""
        return self.current_pipeline.copy()
    
    def complete_pipeline(self, pipeline_id: int, results: Dict):
        """Mark pipeline as completed"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE pipeline_runs 
                    SET status = ?, end_time = ?, results = ?
                    WHERE id = ?
                """, ("completed", datetime.now(), json.dumps(results), pipeline_id))
                
            if self.current_pipeline.get('id') == pipeline_id:
                self.current_pipeline['status'] = 'completed'
                self.current_pipeline['end_time'] = datetime.now()
                self.current_pipeline['progress'] = 100
