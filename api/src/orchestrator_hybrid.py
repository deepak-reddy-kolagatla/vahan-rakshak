"""
Hybrid Orchestrator - Works with both local and watsonx agents
"""

import logging
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from src.agents import GatekeeperAgent, GuardianAgent

# Try to import watsonx agent caller (optional)
try:
    from src.watsonx_agent_caller import WatsonxAgentCaller
    HAS_WATSONX = True
except ImportError:
    HAS_WATSONX = False

load_dotenv()

logger = logging.getLogger(__name__)


class HybridOrchestrator:
    """
    Hybrid orchestrator that can work with:
    1. Local agents (GatekeeperAgent, GuardianAgent)
    2. watsonx-hosted agents (via WatsonxAgentCaller)
    
    Automatically chooses based on configuration
    """
    
    def __init__(self, use_watsonx: bool = None):
        """
        Initialize hybrid orchestrator
        
        Args:
            use_watsonx: Use watsonx agents (None = auto-detect from .env)
        """
        # Auto-detect if not specified
        if use_watsonx is None:
            use_watsonx = os.getenv("USE_WATSONX_ORCHESTRATE", "false").lower() == "true"
        
        self.use_watsonx = use_watsonx
        self.watsonx_caller = None
        self.gatekeeper = None
        self.guardian = None
        self.shared_state = {}
        self.running = False
        
        if self.use_watsonx and HAS_WATSONX:
            logger.info("🚀 Using watsonx Orchestrate agents")
            try:
                self.watsonx_caller = WatsonxAgentCaller()
                # Get agent IDs from environment
                self.gatekeeper_agent_id = os.getenv("GATEKEEPER_AGENT_ID", "gatekeeper_v1")
                self.guardian_agent_id = os.getenv("GUARDIAN_AGENT_ID", "guardian_v1")
                logger.info(f"✓ Gatekeeper Agent ID: {self.gatekeeper_agent_id}")
                logger.info(f"✓ Guardian Agent ID: {self.guardian_agent_id}")
            except Exception as e:
                logger.error(f"Failed to initialize watsonx: {e}")
                logger.info("Falling back to local agents")
                self.use_watsonx = False
                self.gatekeeper = GatekeeperAgent()
                self.guardian = GuardianAgent()
        else:
            logger.info("📱 Using local agents")
            self.gatekeeper = GatekeeperAgent()
            self.guardian = GuardianAgent()
        
        logger.info("Hybrid Orchestrator initialized")
    
    def start_all_agents(self) -> Dict[str, Any]:
        """Start all agents"""
        logger.info("Starting all agents...")
        
        if self.use_watsonx and self.watsonx_caller:
            logger.info("✓ watsonx agents ready")
        else:
            self.gatekeeper.start()
            self.guardian.start()
        
        self.running = True
        
        return {
            "status": "started",
            "mode": "watsonx" if self.use_watsonx else "local",
            "gatekeeper": "active",
            "guardian": "active",
            "orchestrator": "running"
        }
    
    def stop_all_agents(self) -> Dict[str, Any]:
        """Stop all agents"""
        logger.info("Stopping all agents...")
        
        if not self.use_watsonx and self.gatekeeper and self.guardian:
            self.gatekeeper.stop()
            self.guardian.stop()
        
        self.running = False
        
        return {
            "status": "stopped",
            "gatekeeper": "inactive",
            "guardian": "inactive",
            "orchestrator": "stopped"
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of entire system"""
        status = {
            "orchestrator_running": self.running,
            "mode": "watsonx" if self.use_watsonx else "local",
            "shared_state": self.shared_state
        }
        
        if self.use_watsonx:
            status["gatekeeper"] = f"watsonx:{self.gatekeeper_agent_id}"
            status["guardian"] = f"watsonx:{self.guardian_agent_id}"
        else:
            status["gatekeeper"] = self.gatekeeper.get_agent_status()
            status["guardian"] = self.guardian.get_agent_status()
        
        return status
    
    def process_vehicle_departure(
        self,
        vehicle_id: str,
        vehicle_number: str,
        vehicle_class: str,
        driver_name: str,
        scanned_by: str,
        cargo_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate vehicle departure
        
        Works with either local or watsonx agents
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"VEHICLE DEPARTURE: {vehicle_number}")
        logger.info(f"{'='*70}")
        
        if self.use_watsonx and self.watsonx_caller:
            # Use watsonx agents via orchestrated workflow
            logger.info("Using watsonx Orchestrate workflow")
            
            result = self.watsonx_caller.orchestrate_departure_workflow(
                gatekeeper_agent_id=self.gatekeeper_agent_id,
                guardian_agent_id=self.guardian_agent_id,
                vehicle_id=vehicle_id,
                cargo_data=cargo_data or {
                    "vehicle_number": vehicle_number,
                    "vehicle_class": vehicle_class,
                    "driver_name": driver_name,
                    "scanned_by": scanned_by
                }
            )
            
            return result
        else:
            # Use local agents
            logger.info("Using local agents")
            
            # Gatekeeper processes departure
            gk_decision = self.gatekeeper.process_departure(
                vehicle_id=vehicle_id,
                vehicle_number=vehicle_number,
                vehicle_class=vehicle_class,
                driver_name=driver_name,
                scanned_by=scanned_by
            )
            
            # If approved, activate Guardian
            if gk_decision.get("approved"):
                self.guardian.start_monitoring(vehicle_id, vehicle_number)
            
            return gk_decision
    
    def handle_guardian_incident(
        self,
        vehicle_id: str,
        incident_type: str,
        sensor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle emergency incident reported by Guardian
        
        Works with either local or watsonx agents
        """
        logger.info(f"\n{'!'*70}")
        logger.info(f"🚨 INCIDENT: {incident_type.upper()}")
        logger.info(f"Vehicle: {vehicle_id}")
        logger.info(f"{'!'*70}")
        
        if self.use_watsonx and self.watsonx_caller:
            # Use watsonx emergency workflow
            logger.info("Using watsonx Orchestrate emergency workflow")
            
            result = self.watsonx_caller.orchestrate_emergency_response(
                guardian_agent_id=self.guardian_agent_id,
                vehicle_id=vehicle_id,
                incident_type=incident_type,
                sensor_data=sensor_data
            )
            
            return result
        else:
            # Use local agent
            logger.info("Using local Guardian agent")
            
            incident_response = self.guardian.handle_incident(
                incident_type=incident_type,
                sensor_data=sensor_data
            )
            
            return incident_response
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about running agents"""
        info = {
            "mode": "watsonx" if self.use_watsonx else "local",
            "use_watsonx_orchestrate": self.use_watsonx,
            "has_watsonx_support": HAS_WATSONX
        }
        
        if self.use_watsonx:
            info["gatekeeper"] = {
                "type": "watsonx",
                "agent_id": self.gatekeeper_agent_id,
                "url": os.getenv("WATSONX_API_URL"),
                "project_id": os.getenv("WATSONX_PROJECT_ID"),
                "space_id": os.getenv("WATSONX_SPACE_ID")
            }
            info["guardian"] = {
                "type": "watsonx",
                "agent_id": self.guardian_agent_id,
                "url": os.getenv("WATSONX_API_URL"),
                "project_id": os.getenv("WATSONX_PROJECT_ID"),
                "space_id": os.getenv("WATSONX_SPACE_ID")
            }
        else:
            info["gatekeeper"] = {"type": "local"}
            info["guardian"] = {"type": "local"}
        
        return info


# Keep legacy class name for backward compatibility
class VahanOrchestrator(HybridOrchestrator):
    """Backward compatible orchestrator (alias to HybridOrchestrator)"""
    pass


if __name__ == "__main__":
    # Test the orchestrator
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize orchestrator (auto-detects watsonx vs local)
    orchestrator = HybridOrchestrator()
    
    # Show agent info
    print("\n" + "="*70)
    print("ORCHESTRATOR INFO")
    print("="*70)
    info = orchestrator.get_agent_info()
    import json
    print(json.dumps(info, indent=2))
    
    # Start agents
    print("\n" + "="*70)
    print("STARTING AGENTS")
    print("="*70)
    status = orchestrator.start_all_agents()
    print(json.dumps(status, indent=2))
