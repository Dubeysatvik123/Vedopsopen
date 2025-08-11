from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import json
import threading
import time
from utils.exceptions import AgentExecutionError, ToolIntegrationError, ResourceExhaustionError
from utils.resilience import circuit_breaker, retry, timeout, bulkhead, health_checker

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Enhanced base class for all VedOps agents with resilience patterns"""
    
    def __init__(self, name: str, llm_client, config: Dict[str, Any]):
        self.name = name
        self.llm_client = llm_client
        self.config = config
        self.status = "idle"
        self.results = {}
        self.errors = []
        self.start_time = None
        self.end_time = None
        self.lock = threading.Lock()
        
        # Resilience configuration
        self.max_retries = config.get('max_retries', 3)
        self.timeout_seconds = config.get('timeout_seconds', 300)  # 5 minutes default
        self.circuit_breaker_threshold = config.get('circuit_breaker_threshold', 5)
        self.max_concurrent = config.get('max_concurrent', 5)
        
        # Health check registration
        self._register_health_checks()
        
        # Initialize metrics
        self.metrics = {
            'execution_count': 0,
            'success_count': 0,
            'failure_count': 0,
            'total_duration': 0.0,
            'last_execution': None
        }
    
    def _register_health_checks(self):
        """Register health checks for this agent"""
        health_checker.register_check(
            f"{self.name}_agent_health",
            self._health_check,
            interval=60,  # Check every minute
            timeout=10
        )
    
    def _health_check(self) -> Dict[str, Any]:
        """Perform health check for this agent"""
        try:
            # Check LLM client connectivity
            if self.llm_client:
                test_response = self.llm_client.invoke("Health check test")
                llm_healthy = bool(test_response)
            else:
                llm_healthy = False
            
            # Check agent-specific health
            agent_healthy = self._agent_specific_health_check()
            
            return {
                'agent_name': self.name,
                'llm_client_healthy': llm_healthy,
                'agent_specific_healthy': agent_healthy,
                'metrics': self.metrics,
                'status': self.status
            }
            
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            return {
                'agent_name': self.name,
                'healthy': False,
                'error': str(e)
            }
    
    def _agent_specific_health_check(self) -> bool:
        """Override in subclasses for agent-specific health checks"""
        return True
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's main functionality"""
        pass
    
    @bulkhead(max_concurrent=5)
    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    @retry(max_attempts=3, base_delay=1.0)
    @timeout(300)  # 5 minutes timeout
    def execute_with_resilience(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent with full resilience patterns"""
        with self.lock:
            self.metrics['execution_count'] += 1
            self.metrics['last_execution'] = datetime.now().isoformat()
        
        try:
            self.start_execution()
            
            # Validate input
            self._validate_input(input_data)
            
            # Pre-execution checks
            self._pre_execution_checks()
            
            # Execute main logic
            result = self.execute(input_data)
            
            # Post-execution validation
            self._validate_output(result)
            
            # Update metrics
            with self.lock:
                self.metrics['success_count'] += 1
            
            self.end_execution(True)
            return result
            
        except Exception as e:
            with self.lock:
                self.metrics['failure_count'] += 1
            
            self.add_error(f"Execution failed: {str(e)}")
            self.end_execution(False)
            
            # Convert to appropriate exception type
            if isinstance(e, (AgentExecutionError, ToolIntegrationError)):
                raise
            else:
                raise AgentExecutionError(
                    self.name, 
                    str(e), 
                    context={'input_data': input_data, 'agent_status': self.get_status()}
                )
    
    def _validate_input(self, input_data: Dict[str, Any]):
        """Validate input data"""
        if not isinstance(input_data, dict):
            raise AgentExecutionError(
                self.name,
                "Input data must be a dictionary",
                context={'input_type': type(input_data).__name__}
            )
        
        # Agent-specific validation
        self._agent_specific_input_validation(input_data)
    
    def _agent_specific_input_validation(self, input_data: Dict[str, Any]):
        """Override in subclasses for specific input validation"""
        pass
    
    def _validate_output(self, output_data: Dict[str, Any]):
        """Validate output data"""
        if not isinstance(output_data, dict):
            raise AgentExecutionError(
                self.name,
                "Output data must be a dictionary",
                context={'output_type': type(output_data).__name__}
            )
        
        # Agent-specific validation
        self._agent_specific_output_validation(output_data)
    
    def _agent_specific_output_validation(self, output_data: Dict[str, Any]):
        """Override in subclasses for specific output validation"""
        pass
    
    def _pre_execution_checks(self):
        """Perform pre-execution checks"""
        # Check if agent is in a valid state
        if self.status == "failed":
            raise AgentExecutionError(
                self.name,
                "Agent is in failed state",
                context={'current_status': self.status}
            )
        
        # Check resource availability
        self._check_resources()
        
        # Agent-specific pre-checks
        self._agent_specific_pre_checks()
    
    def _check_resources(self):
        """Check system resources"""
        import psutil
        
        # Check memory usage
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            raise ResourceExhaustionError(
                "memory",
                f"Memory usage too high: {memory.percent}%",
                context={'available_memory': memory.available}
            )
        
        # Check disk space
        disk = psutil.disk_usage('/')
        if disk.percent > 95:
            raise ResourceExhaustionError(
                "disk",
                f"Disk usage too high: {disk.percent}%",
                context={'available_disk': disk.free}
            )
    
    def _agent_specific_pre_checks(self):
        """Override in subclasses for specific pre-execution checks"""
        pass
    
    def set_status(self, status: str, message: str = ""):
        """Update agent status thread-safely"""
        with self.lock:
            self.status = status
            logger.info(f"{self.name}: {status} - {message}")
    
    def add_error(self, error: str, error_type: str = "execution_error", 
                  context: Dict[str, Any] = None):
        """Add error to agent's error list with context"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "error_type": error_type,
            "context": context or {}
        }
        
        with self.lock:
            self.errors.append(error_entry)
        
        logger.error(f"{self.name}: {error}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status thread-safely"""
        with self.lock:
            return {
                "name": self.name,
                "status": self.status,
                "errors": list(self.errors),  # Create copy
                "results": dict(self.results),  # Create copy
                "duration": self.get_duration(),
                "metrics": dict(self.metrics),  # Create copy
                "health": health_checker.get_status(f"{self.name}_agent_health")
            }
    
    def get_duration(self) -> Optional[float]:
        """Get execution duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def start_execution(self):
        """Mark start of execution"""
        with self.lock:
            self.start_time = datetime.now()
            self.set_status("running", "Starting execution")
    
    def end_execution(self, success: bool = True):
        """Mark end of execution"""
        with self.lock:
            self.end_time = datetime.now()
            duration = self.get_duration()
            
            if duration:
                self.metrics['total_duration'] += duration
            
            status = "completed" if success else "failed"
            self.set_status(status, f"Execution {status}")
    
    def reset(self):
        """Reset agent state for new execution"""
        with self.lock:
            self.status = "idle"
            self.results = {}
            self.errors = []
            self.start_time = None
            self.end_time = None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        with self.lock:
            metrics = dict(self.metrics)
            
            if metrics['execution_count'] > 0:
                metrics['average_duration'] = metrics['total_duration'] / metrics['execution_count']
                metrics['success_rate'] = metrics['success_count'] / metrics['execution_count']
                metrics['failure_rate'] = metrics['failure_count'] / metrics['execution_count']
            else:
                metrics['average_duration'] = 0.0
                metrics['success_rate'] = 0.0
                metrics['failure_rate'] = 0.0
            
            return metrics
    
    def cleanup(self):
        """Cleanup agent resources"""
        try:
            # Cleanup agent-specific resources
            self._agent_specific_cleanup()
            
            # Reset state
            self.reset()
            
            logger.info(f"Agent {self.name} cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Failed to cleanup agent {self.name}: {e}")
    
    def _agent_specific_cleanup(self):
        """Override in subclasses for specific cleanup"""
        pass
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.cleanup()
        
        if exc_type:
            logger.error(f"Agent {self.name} exited with exception: {exc_val}")
            return False  # Don't suppress exceptions
        
        return True
