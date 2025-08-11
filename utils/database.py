import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Thread-safe database manager for VedOps with comprehensive persistence"""
    
    def __init__(self, db_path: str = "data/vedops.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.ensure_db_dir()
        self.init_database()
    
    def ensure_db_dir(self):
        """Ensure database directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Thread-safe database connection context manager"""
        with self.lock:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            try:
                yield conn
            finally:
                conn.close()
    
    def init_database(self):
        """Initialize all database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Pipeline runs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pipeline_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_name TEXT NOT NULL,
                        project_type TEXT NOT NULL,
                        project_url TEXT,
                        status TEXT NOT NULL DEFAULT 'pending',
                        config TEXT NOT NULL,
                        results TEXT,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        duration_seconds INTEGER,
                        user_id TEXT DEFAULT 'anonymous',
                        tags TEXT DEFAULT '[]'
                    )
                """)
                
                # Agent executions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS agent_executions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pipeline_run_id INTEGER NOT NULL,
                        agent_name TEXT NOT NULL,
                        agent_type TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        input_data TEXT,
                        output_data TEXT,
                        error_message TEXT,
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        duration_seconds INTEGER,
                        retry_count INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 3,
                        FOREIGN KEY (pipeline_run_id) REFERENCES pipeline_runs (id) ON DELETE CASCADE
                    )
                """)
                
                # Security findings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS security_findings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pipeline_run_id INTEGER NOT NULL,
                        agent_execution_id INTEGER,
                        severity TEXT NOT NULL,
                        category TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        file_path TEXT,
                        line_number INTEGER,
                        column_number INTEGER,
                        rule_id TEXT,
                        remediation TEXT,
                        status TEXT DEFAULT 'open',
                        false_positive BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        resolved_at TIMESTAMP,
                        FOREIGN KEY (pipeline_run_id) REFERENCES pipeline_runs (id) ON DELETE CASCADE,
                        FOREIGN KEY (agent_execution_id) REFERENCES agent_executions (id) ON DELETE SET NULL
                    )
                """)
                
                # Performance metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pipeline_run_id INTEGER NOT NULL,
                        agent_execution_id INTEGER,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        metric_unit TEXT,
                        metric_type TEXT DEFAULT 'gauge',
                        labels TEXT DEFAULT '{}',
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (pipeline_run_id) REFERENCES pipeline_runs (id) ON DELETE CASCADE,
                        FOREIGN KEY (agent_execution_id) REFERENCES agent_executions (id) ON DELETE SET NULL
                    )
                """)
                
                # Build artifacts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS build_artifacts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pipeline_run_id INTEGER NOT NULL,
                        agent_execution_id INTEGER,
                        artifact_type TEXT NOT NULL,
                        artifact_name TEXT NOT NULL,
                        artifact_path TEXT,
                        artifact_size INTEGER,
                        artifact_hash TEXT,
                        metadata TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (pipeline_run_id) REFERENCES pipeline_runs (id) ON DELETE CASCADE,
                        FOREIGN KEY (agent_execution_id) REFERENCES agent_executions (id) ON DELETE SET NULL
                    )
                """)
                
                # Deployment history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS deployment_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pipeline_run_id INTEGER NOT NULL,
                        environment TEXT NOT NULL,
                        deployment_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        endpoint_url TEXT,
                        deployment_config TEXT,
                        rollback_info TEXT,
                        deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        rolled_back_at TIMESTAMP,
                        FOREIGN KEY (pipeline_run_id) REFERENCES pipeline_runs (id) ON DELETE CASCADE
                    )
                """)
                
                # Configuration history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS configuration_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        config_type TEXT NOT NULL,
                        config_name TEXT NOT NULL,
                        config_data TEXT NOT NULL,
                        version INTEGER DEFAULT 1,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT DEFAULT 'system'
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_runs_created_at ON pipeline_runs(created_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_executions_pipeline_run_id ON agent_executions(pipeline_run_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_findings_pipeline_run_id ON security_findings(pipeline_run_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_findings_severity ON security_findings(severity)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_metrics_pipeline_run_id ON performance_metrics(pipeline_run_id)")
                
                conn.commit()
                logger.info("Database initialized successfully with all tables and indexes")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_pipeline_run(self, project_name: str, project_type: str, 
                           project_url: str, config: Dict[str, Any], 
                           user_id: str = "anonymous", tags: List[str] = None) -> int:
        """Create a new pipeline run record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO pipeline_runs 
                    (project_name, project_type, project_url, config, user_id, tags)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    project_name, 
                    project_type, 
                    project_url,
                    json.dumps(config), 
                    user_id,
                    json.dumps(tags or [])
                ))
                
                run_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Created pipeline run {run_id} for project {project_name}")
                return run_id
                
        except Exception as e:
            logger.error(f"Failed to create pipeline run: {e}")
            raise
    
    def update_pipeline_run(self, run_id: int, status: str, 
                           results: Optional[Dict[str, Any]] = None,
                           error_message: Optional[str] = None):
        """Update pipeline run status and results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                update_fields = ["status = ?"]
                params = [status]
                
                if status == 'running' and not self.get_pipeline_run(run_id).get('started_at'):
                    update_fields.append("started_at = CURRENT_TIMESTAMP")
                
                if status in ['completed', 'failed']:
                    update_fields.extend([
                        "completed_at = CURRENT_TIMESTAMP",
                        "duration_seconds = (julianday(CURRENT_TIMESTAMP) - julianday(COALESCE(started_at, created_at))) * 86400"
                    ])
                
                if results:
                    update_fields.append("results = ?")
                    params.append(json.dumps(results))
                
                if error_message:
                    update_fields.append("error_message = ?")
                    params.append(error_message)
                
                params.append(run_id)
                
                cursor.execute(f"""
                    UPDATE pipeline_runs 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """, params)
                
                conn.commit()
                logger.info(f"Updated pipeline run {run_id} status to {status}")
                
        except Exception as e:
            logger.error(f"Failed to update pipeline run: {e}")
            raise
    
    def get_pipeline_run(self, run_id: int) -> Optional[Dict[str, Any]]:
        """Get pipeline run by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM pipeline_runs WHERE id = ?", (run_id,))
                row = cursor.fetchone()
                
                if row:
                    result = dict(row)
                    # Parse JSON fields
                    result['config'] = json.loads(result['config']) if result['config'] else {}
                    result['results'] = json.loads(result['results']) if result['results'] else {}
                    result['tags'] = json.loads(result['tags']) if result['tags'] else []
                    return result
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get pipeline run: {e}")
            return None
    
    def create_agent_execution(self, pipeline_run_id: int, agent_name: str, 
                             agent_type: str, input_data: Dict[str, Any],
                             max_retries: int = 3) -> int:
        """Create agent execution record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO agent_executions 
                    (pipeline_run_id, agent_name, agent_type, input_data, max_retries)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    pipeline_run_id, 
                    agent_name, 
                    agent_type,
                    json.dumps(input_data), 
                    max_retries
                ))
                
                execution_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Created agent execution {execution_id} for {agent_name}")
                return execution_id
                
        except Exception as e:
            logger.error(f"Failed to create agent execution: {e}")
            raise
    
    def update_agent_execution(self, execution_id: int, status: str, 
                             output_data: Optional[Dict[str, Any]] = None,
                             error_message: Optional[str] = None,
                             increment_retry: bool = False):
        """Update agent execution results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                update_fields = ["status = ?"]
                params = [status]
                
                if status == 'running':
                    update_fields.append("started_at = CURRENT_TIMESTAMP")
                
                if status in ['completed', 'failed']:
                    update_fields.extend([
                        "completed_at = CURRENT_TIMESTAMP",
                        "duration_seconds = (julianday(CURRENT_TIMESTAMP) - julianday(started_at)) * 86400"
                    ])
                
                if output_data:
                    update_fields.append("output_data = ?")
                    params.append(json.dumps(output_data))
                
                if error_message:
                    update_fields.append("error_message = ?")
                    params.append(error_message)
                
                if increment_retry:
                    update_fields.append("retry_count = retry_count + 1")
                
                params.append(execution_id)
                
                cursor.execute(f"""
                    UPDATE agent_executions 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """, params)
                
                conn.commit()
                logger.info(f"Updated agent execution {execution_id} status to {status}")
                
        except Exception as e:
            logger.error(f"Failed to update agent execution: {e}")
            raise
    
    def add_security_finding(self, pipeline_run_id: int, finding: Dict[str, Any],
                           agent_execution_id: Optional[int] = None):
        """Add security finding"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO security_findings 
                    (pipeline_run_id, agent_execution_id, severity, category, title, 
                     description, file_path, line_number, column_number, rule_id, remediation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pipeline_run_id,
                    agent_execution_id,
                    finding.get('severity', 'medium'),
                    finding.get('category', 'unknown'),
                    finding.get('title', ''),
                    finding.get('description', ''),
                    finding.get('file_path', ''),
                    finding.get('line_number', 0),
                    finding.get('column_number', 0),
                    finding.get('rule_id', ''),
                    finding.get('remediation', '')
                ))
                
                conn.commit()
                logger.info(f"Added security finding for pipeline {pipeline_run_id}")
                
        except Exception as e:
            logger.error(f"Failed to add security finding: {e}")
            raise
    
    def add_performance_metric(self, pipeline_run_id: int, metric_name: str, 
                             metric_value: float, metric_unit: str = "",
                             metric_type: str = "gauge", labels: Dict[str, str] = None,
                             agent_execution_id: Optional[int] = None):
        """Add performance metric"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO performance_metrics 
                    (pipeline_run_id, agent_execution_id, metric_name, metric_value, 
                     metric_unit, metric_type, labels)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    pipeline_run_id, 
                    agent_execution_id,
                    metric_name, 
                    metric_value, 
                    metric_unit,
                    metric_type,
                    json.dumps(labels or {})
                ))
                
                conn.commit()
                logger.info(f"Added performance metric {metric_name} for pipeline {pipeline_run_id}")
                
        except Exception as e:
            logger.error(f"Failed to add performance metric: {e}")
            raise
    
    def add_build_artifact(self, pipeline_run_id: int, artifact_type: str,
                          artifact_name: str, artifact_path: str,
                          artifact_size: int = 0, artifact_hash: str = "",
                          metadata: Dict[str, Any] = None,
                          agent_execution_id: Optional[int] = None):
        """Add build artifact"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO build_artifacts 
                    (pipeline_run_id, agent_execution_id, artifact_type, artifact_name,
                     artifact_path, artifact_size, artifact_hash, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pipeline_run_id,
                    agent_execution_id,
                    artifact_type,
                    artifact_name,
                    artifact_path,
                    artifact_size,
                    artifact_hash,
                    json.dumps(metadata or {})
                ))
                
                conn.commit()
                logger.info(f"Added build artifact {artifact_name} for pipeline {pipeline_run_id}")
                
        except Exception as e:
            logger.error(f"Failed to add build artifact: {e}")
            raise
    
    def get_pipeline_history(self, limit: int = 50, status: str = None,
                           user_id: str = None) -> List[Dict[str, Any]]:
        """Get pipeline execution history with filters"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, project_name, project_type, status, created_at, 
                           started_at, completed_at, duration_seconds, user_id, tags
                    FROM pipeline_runs 
                """
                params = []
                conditions = []
                
                if status:
                    conditions.append("status = ?")
                    params.append(status)
                
                if user_id:
                    conditions.append("user_id = ?")
                    params.append(user_id)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    result = dict(row)
                    result['tags'] = json.loads(result['tags']) if result['tags'] else []
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get pipeline history: {e}")
            return []
    
    def get_security_summary(self, pipeline_run_id: int) -> Dict[str, Any]:
        """Get security findings summary for a pipeline run"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get findings by severity
                cursor.execute("""
                    SELECT severity, COUNT(*) as count
                    FROM security_findings 
                    WHERE pipeline_run_id = ? AND status = 'open'
                    GROUP BY severity
                """, (pipeline_run_id,))
                
                findings_by_severity = dict(cursor.fetchall())
                
                # Get total counts
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_findings,
                        COUNT(CASE WHEN status = 'open' THEN 1 END) as open_findings,
                        COUNT(CASE WHEN false_positive = 1 THEN 1 END) as false_positives
                    FROM security_findings 
                    WHERE pipeline_run_id = ?
                """, (pipeline_run_id,))
                
                counts = dict(cursor.fetchone())
                
                return {
                    'findings_by_severity': findings_by_severity,
                    'total_findings': counts['total_findings'],
                    'open_findings': counts['open_findings'],
                    'false_positives': counts['false_positives'],
                    'security_score': self._calculate_security_score(findings_by_severity)
                }
                
        except Exception as e:
            logger.error(f"Failed to get security summary: {e}")
            return {}
    
    def _calculate_security_score(self, findings_by_severity: Dict[str, int]) -> int:
        """Calculate security score based on findings"""
        severity_weights = {'critical': 10, 'high': 5, 'medium': 2, 'low': 1}
        total_weight = sum(findings_by_severity.get(sev, 0) * weight 
                          for sev, weight in severity_weights.items())
        
        # Score from 0-100, where 100 is perfect (no findings)
        if total_weight == 0:
            return 100
        elif total_weight <= 5:
            return 90
        elif total_weight <= 15:
            return 75
        elif total_weight <= 30:
            return 50
        else:
            return 25
    
    def get_performance_summary(self, pipeline_run_id: int) -> Dict[str, Any]:
        """Get performance metrics summary"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT metric_name, AVG(metric_value) as avg_value, 
                           MIN(metric_value) as min_value, MAX(metric_value) as max_value,
                           metric_unit, COUNT(*) as count
                    FROM performance_metrics 
                    WHERE pipeline_run_id = ?
                    GROUP BY metric_name, metric_unit
                """, (pipeline_run_id,))
                
                metrics = []
                for row in cursor.fetchall():
                    metrics.append(dict(row))
                
                return {'metrics': metrics}
                
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {'metrics': []}
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old pipeline data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete old pipeline runs and related data (CASCADE will handle related tables)
                cursor.execute("""
                    DELETE FROM pipeline_runs 
                    WHERE created_at < datetime('now', '-{} days')
                """.format(days_to_keep))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} old pipeline runs")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return 0
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Table counts
                tables = ['pipeline_runs', 'agent_executions', 'security_findings', 
                         'performance_metrics', 'build_artifacts', 'deployment_history']
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                
                # Database size
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                stats['database_size_bytes'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
