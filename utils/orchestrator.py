import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from .database import DatabaseManager
from .llm_config import LLMConfigManager
from agents import (
    VarunaAgent, AgniAgent, YamaAgent, VayuAgent, 
    HanumanAgent, KrishnaAgent, ObservabilityAgent, OptimizationAgent
)
from agents.terraform_agent import TerraformAgent
from .performance import profile, cached, parallel_executor, profiler, MemoryOptimizer
from .database_optimizer import DatabaseOptimizer
import time

logger = logging.getLogger(__name__)

class VedOpsOrchestrator:
    """Main orchestrator for VedOps pipeline with database persistence and performance optimization"""
    
    def __init__(self, llm_config: Dict[str, Any], pipeline_config: Dict[str, Any]):
        self.llm_config = llm_config
        self.pipeline_config = pipeline_config
        self.db = DatabaseManager()
        self.db_optimizer = DatabaseOptimizer(self.db.db_path)
        self.llm_config_manager = LLMConfigManager()
        self.current_run_id = None
        self.agents = {}
        self.pipeline_state = {}
        self.errors = []
        
        self.enable_parallel_execution = pipeline_config.get('parallel_execution', True)
        self.max_parallel_agents = pipeline_config.get('max_parallel_agents', 3)
        self.enable_caching = pipeline_config.get('enable_caching', True)
        self.memory_optimization = pipeline_config.get('memory_optimization', True)
        
        self.llm_client = self.llm_config_manager.get_llm_client(llm_config)
        
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all agents with LLM client and config"""
        agent_classes = {
            'varuna': VarunaAgent,
            'agni': AgniAgent,
            'yama': YamaAgent,
            'vayu': VayuAgent,
            'hanuman': HanumanAgent,
            'krishna': KrishnaAgent,
            'observability': ObservabilityAgent,
            'optimization': OptimizationAgent,
            'terraform': TerraformAgent,
        }
        
        for agent_name, agent_class in agent_classes.items():
            try:
                # Instantiate with unified constructor signature
                self.agents[agent_name] = agent_class(self.llm_client, self.pipeline_config)
                logger.info(f"Initialized {agent_name} agent")
            except Exception as e:
                logger.error(f"Failed to initialize {agent_name} agent: {e}")
                self.errors.append(f"Agent initialization failed: {agent_name} - {str(e)}")
    
    @profile("pipeline_execution")
    @MemoryOptimizer.memory_limit_decorator(max_memory_mb=2048)
    def execute_pipeline(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete DevSecOps pipeline with performance optimization"""
        try:
            start_time = time.perf_counter()
            initial_memory = MemoryOptimizer.get_memory_usage()
            
            self.current_run_id = self.db.create_pipeline_run(
                project_name=self._extract_project_name(project_data),
                project_type=project_data.get('type', 'unknown'),
                project_url=project_data.get('url', ''),
                config=self.pipeline_config,
                user_id=self.pipeline_config.get('user_id', 'anonymous'),
                tags=self.pipeline_config.get('tags', [])
            )
            
            logger.info(f"Started pipeline run {self.current_run_id}")
            self.db.update_pipeline_run(self.current_run_id, 'running')
            
            if self.enable_parallel_execution:
                pipeline_results = self._execute_pipeline_parallel(project_data)
            else:
                pipeline_results = self._execute_pipeline_sequential(project_data)
            
            final_summary = self._generate_pipeline_summary(pipeline_results)
            pipeline_results['summary'] = final_summary
            
            end_time = time.perf_counter()
            final_memory = MemoryOptimizer.get_memory_usage()
            
            performance_metrics = {
                'total_duration': end_time - start_time,
                'memory_usage': {
                    'initial': initial_memory,
                    'final': final_memory,
                    'peak_delta': final_memory['rss_mb'] - initial_memory['rss_mb']
                },
                'agent_profiles': profiler.get_all_profiles()
            }
            
            pipeline_results['performance'] = performance_metrics
            
            if self.memory_optimization:
                MemoryOptimizer.optimize_memory()
            
            logger.info(f"Pipeline run {self.current_run_id} completed successfully in {end_time - start_time:.2f}s")
            return pipeline_results
            
        except Exception as e:
            error_msg = f"Pipeline execution failed: {str(e)}"
            logger.error(error_msg)
            
            if self.current_run_id:
                self.db.update_pipeline_run(self.current_run_id, 'failed', error_message=error_msg)
            
            raise
    
    def _execute_pipeline_sequential(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pipeline sequentially (original implementation)"""
        pipeline_results = {}
        
        varuna_result = self._execute_agent_with_persistence('varuna', project_data)
        pipeline_results['code_analysis'] = varuna_result
        
        agni_input = {**project_data, **varuna_result}
        agni_result = self._execute_agent_with_persistence('agni', agni_input)
        pipeline_results['build'] = agni_result
        
        yama_input = {**agni_input, **agni_result}
        yama_result = self._execute_agent_with_persistence('yama', yama_input)
        pipeline_results['security'] = yama_result
        
        # Provision infra (terraform agent) then deploy
        tf_input = {**yama_input, **yama_result, 'cloud_credentials': self.pipeline_config.get('cloud_credentials', {})}
        tf_result = self._execute_agent_with_persistence('terraform', tf_input)
        pipeline_results['provision'] = tf_result

        vayu_input = {**yama_input, **yama_result, **tf_result}
        vayu_result = self._execute_agent_with_persistence('vayu', vayu_input)
        pipeline_results['deployment'] = vayu_result
        
        hanuman_input = {**vayu_input, **vayu_result}
        hanuman_result = self._execute_agent_with_persistence('hanuman', hanuman_input)
        pipeline_results['testing'] = hanuman_result
        
        krishna_input = {**hanuman_input, **hanuman_result, 'all_results': pipeline_results}
        krishna_result = self._execute_agent_with_persistence('krishna', krishna_input)
        pipeline_results['governance'] = krishna_result
        
        if vayu_result.get('deployment_status') == 'success':
            obs_input = {**krishna_input, **krishna_result}
            obs_result = self._execute_agent_with_persistence('observability', obs_input)
            pipeline_results['observability'] = obs_result
            
            opt_input = {**obs_input, **obs_result}
            opt_result = self._execute_agent_with_persistence('optimization', opt_input)
            pipeline_results['optimization'] = opt_result
        
        return pipeline_results
    
    def _execute_pipeline_parallel(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pipeline with intelligent parallelization"""
        pipeline_results = {}
        
        varuna_result = self._execute_agent_with_persistence('varuna', project_data)
        pipeline_results['code_analysis'] = varuna_result
        
        agni_input = {**project_data, **varuna_result}
        agni_result = self._execute_agent_with_persistence('agni', agni_input)
        pipeline_results['build'] = agni_result
        
        yama_input = {**agni_input, **agni_result}
        
        with parallel_executor(max_workers=self.max_parallel_agents) as executor:
            security_future = executor.submit(
                self._execute_agent_with_persistence, 'yama', yama_input
            )
            
            yama_result = security_future.result()
            pipeline_results['security'] = yama_result
        
        vayu_input = {**yama_input, **yama_result}
        vayu_result = self._execute_agent_with_persistence('vayu', vayu_input)
        pipeline_results['deployment'] = vayu_result
        
        if vayu_result.get('deployment_status') == 'success':
            hanuman_input = {**vayu_input, **vayu_result}
            
            with parallel_executor(max_workers=self.max_parallel_agents) as executor:
                testing_future = executor.submit(
                    self._execute_agent_with_persistence, 'hanuman', hanuman_input
                )
                
                krishna_input = {**hanuman_input, 'all_results': pipeline_results}
                governance_future = executor.submit(
                    self._execute_agent_with_persistence, 'krishna', krishna_input
                )
                
                hanuman_result = testing_future.result()
                krishna_result = governance_future.result()
                
                pipeline_results['testing'] = hanuman_result
                pipeline_results['governance'] = krishna_result
            
            with parallel_executor(max_workers=self.max_parallel_agents) as executor:
                obs_input = {**krishna_input, **krishna_result}
                obs_future = executor.submit(
                    self._execute_agent_with_persistence, 'observability', obs_input
                )
                
                opt_input = {**obs_input}
                opt_future = executor.submit(
                    self._execute_agent_with_persistence, 'optimization', opt_input
                )
                
                pipeline_results['observability'] = obs_future.result()
                pipeline_results['optimization'] = opt_future.result()
        
        return pipeline_results
    
    def _execute_agent_with_persistence(self, agent_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent with database persistence and error handling"""
        if agent_name not in self.agents:
            raise Exception(f"Agent {agent_name} not available")
        
        agent = self.agents[agent_name]
        
        execution_id = self.db.create_agent_execution(
            pipeline_run_id=self.current_run_id,
            agent_name=agent_name,
            agent_type=agent.__class__.__name__,
            input_data=input_data
        )
        
        max_retries = self.pipeline_config.get('max_retries', 3)
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                self.db.update_agent_execution(execution_id, 'running')
                
                result = agent.execute(input_data)
                
                self.db.update_agent_execution(execution_id, 'completed', result)
                
                if 'security_findings' in result:
                    for finding in result['security_findings']:
                        self.db.add_security_finding(
                            self.current_run_id, finding, execution_id
                        )
                
                if 'performance_metrics' in result:
                    for metric in result['performance_metrics']:
                        self.db.add_performance_metric(
                            pipeline_run_id=self.current_run_id,
                            agent_execution_id=execution_id,
                            **metric
                        )
                
                if 'artifacts' in result:
                    for artifact in result['artifacts']:
                        self.db.add_build_artifact(
                            pipeline_run_id=self.current_run_id,
                            agent_execution_id=execution_id,
                            **artifact
                        )
                
                logger.info(f"Agent {agent_name} completed successfully")
                return result
                
            except Exception as e:
                retry_count += 1
                error_msg = f"Agent {agent_name} failed (attempt {retry_count}): {str(e)}"
                logger.error(error_msg)
                
                if retry_count <= max_retries:
                    self.db.update_agent_execution(
                        execution_id, 'retrying', 
                        error_message=error_msg,
                        increment_retry=True
                    )
                    
                    time.sleep(2 ** retry_count)
                else:
                    self.db.update_agent_execution(
                        execution_id, 'failed',
                        error_message=error_msg
                    )
                    
                    if self.pipeline_config.get('auto_rollback', True):
                        self._handle_rollback(agent_name, error_msg)
                    
                    raise Exception(error_msg)
    
    def _handle_rollback(self, failed_agent: str, error_msg: str):
        """Handle automatic rollback on failure"""
        logger.warning(f"Initiating rollback due to {failed_agent} failure")
        
        try:
            if failed_agent in ['vayu', 'hanuman']:
                if 'vayu' in self.agents:
                    rollback_result = self.agents['vayu'].rollback()
                    logger.info(f"Rollback completed: {rollback_result}")
            
        except Exception as rollback_error:
            logger.error(f"Rollback failed: {rollback_error}")
    
    def _extract_project_name(self, project_data: Dict[str, Any]) -> str:
        """Extract project name from project data"""
        if project_data.get('type') == 'git':
            url = project_data.get('url', '')
            return url.split('/')[-1].replace('.git', '') if url else 'unknown'
        elif project_data.get('type') == 'local':
            path = project_data.get('path', '')
            return path.split('/')[-1] if path else 'unknown'
        else:
            return f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _generate_pipeline_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive pipeline summary"""
        try:
            security_summary = self.db.get_security_summary(self.current_run_id)
            performance_summary = self.db.get_performance_summary(self.current_run_id)
            
            summary = {
                'pipeline_run_id': self.current_run_id,
                'status': 'completed',
                'total_stages': len([k for k in results.keys() if k != 'summary']),
                'security_summary': security_summary,
                'performance_summary': performance_summary,
                'recommendations': [],
                'next_steps': []
            }
            
            summary_prompt = f"""
            Analyze this DevSecOps pipeline execution and provide recommendations:
            
            Security Score: {security_summary.get('security_score', 0)}/100
            Security Findings: {security_summary.get('total_findings', 0)}
            Performance Metrics: {len(performance_summary.get('metrics', []))}
            
            Pipeline Results Summary:
            {json.dumps({k: v.get('status', 'unknown') if isinstance(v, dict) else str(v)[:100] 
                        for k, v in results.items() if k != 'summary'}, indent=2)}
            
            Provide:
            1. Top 3 recommendations for improvement
            2. Security priorities
            3. Performance optimization suggestions
            4. Next steps for deployment
            """
            
            try:
                response = self.llm_client.invoke(summary_prompt)
                ai_recommendations = response.content if hasattr(response, 'content') else str(response)
                summary['ai_recommendations'] = ai_recommendations
            except Exception as e:
                logger.warning(f"Failed to generate AI recommendations: {e}")
                summary['ai_recommendations'] = "AI recommendations unavailable"
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate pipeline summary: {e}")
            return {'status': 'completed', 'error': str(e)}
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current pipeline progress"""
        if not self.current_run_id:
            return {'percentage': 0, 'current_stage': 'Not started', 'logs': []}
        
        try:
            run_info = self.db.get_pipeline_run(self.current_run_id)
            if not run_info:
                return {'percentage': 0, 'current_stage': 'Unknown', 'logs': []}
            
            total_agents = len(self.agents)
            completed_agents = 0
            current_stage = 'Starting'
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT agent_name, status FROM agent_executions 
                    WHERE pipeline_run_id = ? 
                    ORDER BY started_at DESC
                """, (self.current_run_id,))
                
                agent_statuses = dict(cursor.fetchall())
                
                for agent_name in self.agents.keys():
                    status = agent_statuses.get(agent_name, 'pending')
                    if status == 'completed':
                        completed_agents += 1
                    elif status in ['running', 'retrying']:
                        current_stage = f"Running {agent_name.title()} Agent"
                        break
                    elif status == 'failed':
                        current_stage = f"Failed at {agent_name.title()} Agent"
                        break
            
            percentage = (completed_agents / total_agents) * 100 if total_agents > 0 else 0
            
            return {
                'percentage': percentage,
                'current_stage': current_stage,
                'completed_agents': completed_agents,
                'total_agents': total_agents,
                'status': run_info['status'],
                'logs': self._get_recent_logs()
            }
            
        except Exception as e:
            logger.error(f"Failed to get progress: {e}")
            return {'percentage': 0, 'current_stage': 'Error', 'logs': []}
    
    def _get_recent_logs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent pipeline logs"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT agent_name, status, error_message, started_at, completed_at
                    FROM agent_executions 
                    WHERE pipeline_run_id = ? 
                    ORDER BY started_at DESC 
                    LIMIT ?
                """, (self.current_run_id, limit))
                
                logs = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    timestamp = row_dict['started_at'] or row_dict['completed_at'] or ''
                    
                    if row_dict['status'] == 'completed':
                        level = 'INFO'
                        message = f"{row_dict['agent_name'].title()} agent completed successfully"
                    elif row_dict['status'] == 'failed':
                        level = 'ERROR'
                        message = f"{row_dict['agent_name'].title()} agent failed: {row_dict['error_message']}"
                    elif row_dict['status'] == 'running':
                        level = 'INFO'
                        message = f"{row_dict['agent_name'].title()} agent is running"
                    else:
                        level = 'INFO'
                        message = f"{row_dict['agent_name'].title()} agent status: {row_dict['status']}"
                    
                    logs.append({
                        'timestamp': timestamp,
                        'level': level,
                        'message': message
                    })
                
                return logs
                
        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            return []
    
    def get_agent_status(self, agent_name: str) -> Dict[str, str]:
        """Get current status of a specific agent"""
        if not self.current_run_id:
            return {"type": "info", "message": "Pipeline not started"}
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT status, error_message FROM agent_executions 
                    WHERE pipeline_run_id = ? AND agent_name = ?
                    ORDER BY started_at DESC LIMIT 1
                """, (self.current_run_id, agent_name.lower().split()[0]))
                
                row = cursor.fetchone()
                if row:
                    status, error_msg = row
                    if status == 'completed':
                        return {"type": "success", "message": "Completed"}
                    elif status == 'failed':
                        return {"type": "error", "message": f"Failed: {error_msg}"}
                    elif status == 'running':
                        return {"type": "info", "message": "Running"}
                    elif status == 'retrying':
                        return {"type": "warning", "message": "Retrying"}
                    else:
                        return {"type": "info", "message": status.title()}
                else:
                    return {"type": "info", "message": "Pending"}
                    
        except Exception as e:
            logger.error(f"Failed to get agent status: {e}")
            return {"type": "error", "message": "Status unknown"}
    
    @cached(ttl=300)
    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Get cached pipeline statistics"""
        return self.db_optimizer.execute_cached_query("""
            SELECT 
                COUNT(*) as total_runs,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_runs,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_runs,
                AVG(duration_seconds) as avg_duration,
                MAX(duration_seconds) as max_duration,
                MIN(duration_seconds) as min_duration
            FROM pipeline_runs
            WHERE created_at > datetime('now', '-30 days')
        """)
    
    def optimize_performance(self) -> Dict[str, Any]:
        """Run performance optimization operations"""
        optimization_results = {}
        
        db_optimization = self.db_optimizer.optimize_database()
        optimization_results['database'] = db_optimization
        
        memory_optimization = MemoryOptimizer.optimize_memory()
        optimization_results['memory'] = memory_optimization
        
        performance_analysis = self.db_optimizer.analyze_performance()
        optimization_results['analysis'] = performance_analysis
        
        return optimization_results
