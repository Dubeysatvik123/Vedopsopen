"""
Agent Orchestration Layer using LangGraph
Coordinates all AI agents and manages workflow execution
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

from langchain.schema import BaseMessage
from langchain.agents import AgentExecutor
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor

from agents.varuna import VarunaAgent
from agents.agni import AgniAgent  
from agents.yama import YamaAgent
from agents.vayu import VayuAgent
from agents.hanuman import HanumanAgent
from agents.krishna import KrishnaAgent
from core.state_manager import StateManager

class PipelineStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class AgentState:
    """Shared state between agents"""
    project_manifest: Dict[str, Any]
    build_artifacts: Dict[str, Any]
    security_report: Dict[str, Any]
    deployment_status: Dict[str, Any]
    test_results: Dict[str, Any]
    governance_decision: Dict[str, Any]
    current_step: str
    pipeline_status: PipelineStatus
    error_log: List[str]
    metadata: Dict[str, Any]

class AgentOrchestrator:
    """Main orchestrator for all DevSecOps agents"""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.logger = logging.getLogger(__name__)
        self.agents = self._initialize_agents()
        self.workflow = self._build_workflow()
        
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all AI agents"""
        return {
            'varuna': VarunaAgent(),
            'agni': AgniAgent(),
            'yama': YamaAgent(), 
            'vayu': VayuAgent(),
            'hanuman': HanumanAgent(),
            'krishna': KrishnaAgent()
        }
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add agent nodes
        workflow.add_node("varuna", self._run_varuna)
        workflow.add_node("agni", self._run_agni)
        workflow.add_node("yama", self._run_yama)
        workflow.add_node("vayu", self._run_vayu)
        workflow.add_node("hanuman", self._run_hanuman)
        workflow.add_node("krishna", self._run_krishna)
        
        # Define workflow edges
        workflow.set_entry_point("varuna")
        workflow.add_edge("varuna", "agni")
        workflow.add_edge("agni", "yama")
        workflow.add_edge("yama", "vayu")
        workflow.add_edge("vayu", "hanuman")
        workflow.add_edge("hanuman", "krishna")
        workflow.add_edge("krishna", END)
        
        return workflow.compile()
    
    async def execute_pipeline(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete DevSecOps pipeline"""
        
        # Initialize state
        initial_state = AgentState(
            project_manifest={},
            build_artifacts={},
            security_report={},
            deployment_status={},
            test_results={},
            governance_decision={},
            current_step="varuna",
            pipeline_status=PipelineStatus.RUNNING,
            error_log=[],
            metadata=project_data
        )
        
        try:
            # Execute workflow
            result = await self.workflow.ainvoke(initial_state)
            
            # Update state manager
            self.state_manager.update_pipeline_state(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {str(e)}")
            initial_state.pipeline_status = PipelineStatus.FAILED
            initial_state.error_log.append(str(e))
            return initial_state
    
    def _run_varuna(self, state: AgentState) -> AgentState:
        """Execute Varuna - Code Intake & Analysis Agent"""
        try:
            result = self.agents['varuna'].execute(state.metadata)
            state.project_manifest = result
            state.current_step = "agni"
            return state
        except Exception as e:
            state.error_log.append(f"Varuna failed: {str(e)}")
            state.pipeline_status = PipelineStatus.FAILED
            return state
    
    def _run_agni(self, state: AgentState) -> AgentState:
        """Execute Agni - Build & Dockerization Agent"""
        try:
            result = self.agents['agni'].execute(state.project_manifest)
            state.build_artifacts = result
            state.current_step = "yama"
            return state
        except Exception as e:
            state.error_log.append(f"Agni failed: {str(e)}")
            state.pipeline_status = PipelineStatus.FAILED
            return state
    
    def _run_yama(self, state: AgentState) -> AgentState:
        """Execute Yama - Security & Compliance Agent"""
        try:
            result = self.agents['yama'].execute(state.build_artifacts)
            state.security_report = result
            state.current_step = "vayu"
            return state
        except Exception as e:
            state.error_log.append(f"Yama failed: {str(e)}")
            state.pipeline_status = PipelineStatus.FAILED
            return state
    
    def _run_vayu(self, state: AgentState) -> AgentState:
        """Execute Vayu - Orchestration & Deployment Agent"""
        try:
            result = self.agents['vayu'].execute({
                'artifacts': state.build_artifacts,
                'security': state.security_report
            })
            state.deployment_status = result
            state.current_step = "hanuman"
            return state
        except Exception as e:
            state.error_log.append(f"Vayu failed: {str(e)}")
            state.pipeline_status = PipelineStatus.FAILED
            return state
    
    def _run_hanuman(self, state: AgentState) -> AgentState:
        """Execute Hanuman - Testing & Resilience Agent"""
        try:
            result = self.agents['hanuman'].execute(state.deployment_status)
            state.test_results = result
            state.current_step = "krishna"
            return state
        except Exception as e:
            state.error_log.append(f"Hanuman failed: {str(e)}")
            state.pipeline_status = PipelineStatus.FAILED
            return state
    
    def _run_krishna(self, state: AgentState) -> AgentState:
        """Execute Krishna - Governance & Decision Agent"""
        try:
            result = self.agents['krishna'].execute({
                'manifest': state.project_manifest,
                'artifacts': state.build_artifacts,
                'security': state.security_report,
                'deployment': state.deployment_status,
                'tests': state.test_results
            })
            state.governance_decision = result
            state.pipeline_status = PipelineStatus.SUCCESS
            state.current_step = "completed"
            return state
        except Exception as e:
            state.error_log.append(f"Krishna failed: {str(e)}")
            state.pipeline_status = PipelineStatus.FAILED
            return state
