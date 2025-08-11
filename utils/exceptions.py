"""
Custom exceptions for VedOps with detailed error context
"""

class VedOpsException(Exception):
    """Base exception for all VedOps errors"""
    
    def __init__(self, message: str, error_code: str = None, context: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "VEDOPS_ERROR"
        self.context = context or {}
        self.timestamp = None
        
        import datetime
        self.timestamp = datetime.datetime.now().isoformat()

class AgentExecutionError(VedOpsException):
    """Raised when an agent fails to execute"""
    
    def __init__(self, agent_name: str, message: str, context: dict = None):
        super().__init__(
            message=f"Agent {agent_name} execution failed: {message}",
            error_code="AGENT_EXECUTION_ERROR",
            context={**(context or {}), "agent_name": agent_name}
        )
        self.agent_name = agent_name

class ToolIntegrationError(VedOpsException):
    """Raised when external tool integration fails"""
    
    def __init__(self, tool_name: str, message: str, context: dict = None):
        super().__init__(
            message=f"Tool integration failed for {tool_name}: {message}",
            error_code="TOOL_INTEGRATION_ERROR", 
            context={**(context or {}), "tool_name": tool_name}
        )
        self.tool_name = tool_name

class PipelineExecutionError(VedOpsException):
    """Raised when pipeline execution fails"""
    
    def __init__(self, stage: str, message: str, context: dict = None):
        super().__init__(
            message=f"Pipeline failed at stage {stage}: {message}",
            error_code="PIPELINE_EXECUTION_ERROR",
            context={**(context or {}), "stage": stage}
        )
        self.stage = stage

class ConfigurationError(VedOpsException):
    """Raised when configuration is invalid"""
    
    def __init__(self, config_type: str, message: str, context: dict = None):
        super().__init__(
            message=f"Configuration error in {config_type}: {message}",
            error_code="CONFIGURATION_ERROR",
            context={**(context or {}), "config_type": config_type}
        )
        self.config_type = config_type

class ResourceExhaustionError(VedOpsException):
    """Raised when system resources are exhausted"""
    
    def __init__(self, resource_type: str, message: str, context: dict = None):
        super().__init__(
            message=f"Resource exhaustion ({resource_type}): {message}",
            error_code="RESOURCE_EXHAUSTION_ERROR",
            context={**(context or {}), "resource_type": resource_type}
        )
        self.resource_type = resource_type

class SecurityViolationError(VedOpsException):
    """Raised when security policies are violated"""
    
    def __init__(self, violation_type: str, message: str, context: dict = None):
        super().__init__(
            message=f"Security violation ({violation_type}): {message}",
            error_code="SECURITY_VIOLATION_ERROR",
            context={**(context or {}), "violation_type": violation_type}
        )
        self.violation_type = violation_type

class TimeoutError(VedOpsException):
    """Raised when operations timeout"""
    
    def __init__(self, operation: str, timeout_seconds: int, context: dict = None):
        super().__init__(
            message=f"Operation {operation} timed out after {timeout_seconds} seconds",
            error_code="TIMEOUT_ERROR",
            context={**(context or {}), "operation": operation, "timeout_seconds": timeout_seconds}
        )
        self.operation = operation
        self.timeout_seconds = timeout_seconds
