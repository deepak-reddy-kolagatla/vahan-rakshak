"""
watsonx Agent Caller - Calls agents created in watsonx Orchestrate
Direct integration with watsonx-hosted agents
"""

import logging
import os
import requests
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class WatsonxAgentCaller:
    """
    Call agents that are created and hosted in IBM watsonx Orchestrate
    
    Instead of creating agents programmatically, this calls pre-built
    watsonx agents by their agent ID and workspace ID
    """
    
    def __init__(self):
        """Initialize watsonx agent caller"""
        self.api_url = os.getenv("WATSONX_API_URL")
        self.api_key = os.getenv("WATSONX_API_KEY")
        self.project_id = os.getenv("WATSONX_PROJECT_ID")
        self.space_id = os.getenv("WATSONX_SPACE_ID")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Try to initialize the official IBM watsonx.orchestrate Agent SDK if available
        self._use_sdk: bool = False
        self._sdk_invoke: Optional[Callable[..., Dict[str, Any]]] = None
        try:
            self._init_sdk_client()
        except Exception as e:
            logger.debug(f"SDK initialization not used (falling back to REST): {e}")
            self._use_sdk = False
            self._sdk_invoke = None

        logger.info("watsonx Agent Caller initialized")
        logger.info(f"API URL: {self.api_url}")
        logger.info(f"Project ID: {self.project_id}")
        logger.info(f"Space ID: {self.space_id}")
        logger.info(f"Using Agent SDK: {self._use_sdk}")

    def _init_sdk_client(self) -> None:
        """Attempt to initialize the IBM watsonx.orchestrate Agent SDK client.

        This method is defensive: it tries a few likely import paths and
        method names since SDK surface can evolve. If successful, sets
        self._use_sdk=True and prepares self._sdk_invoke(agent_id, action, payload).
        """
        # Import candidates
        sdk_client = None
        errors = []
        
        # Candidate 1: High-level Orchestrate class factory
        try:
            from ibm_watsonx_orchestrate import Orchestrate  # type: ignore
            if hasattr(Orchestrate, "from_api_key"):
                sdk_client = Orchestrate.from_api_key(
                    api_key=self.api_key,
                    url=self.api_url,
                    project_id=self.project_id,
                    space_id=self.space_id,
                )
        except Exception as e:
            errors.append(f"Orchestrate.from_api_key: {e}")
        
        # Candidate 2: Explicit client class
        if sdk_client is None:
            try:
                from ibm_watsonx_orchestrate import OrchestrateClient  # type: ignore
                sdk_client = OrchestrateClient(
                    api_key=self.api_key,
                    url=self.api_url,
                    project_id=self.project_id,
                    space_id=self.space_id,
                )
            except Exception as e:
                errors.append(f"OrchestrateClient: {e}")
        
        # Candidate 3: Agents-scoped client
        agents_client = None
        if sdk_client is None:
            try:
                from ibm_watsonx_orchestrate.agents import AgentsClient  # type: ignore
                agents_client = AgentsClient(
                    api_key=self.api_key,
                    url=self.api_url,
                    project_id=self.project_id,
                    space_id=self.space_id,
                )
            except Exception as e:
                errors.append(f"AgentsClient: {e}")

        # Determine invoke method
        invoke_fn: Optional[Callable[..., Dict[str, Any]]] = None
        if sdk_client is not None:
            # Common patterns to try: client.agents.run / client.run_agent / client.invoke
            if hasattr(sdk_client, "agents") and hasattr(sdk_client.agents, "run"):
                def _invoke(agent_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
                    return sdk_client.agents.run(agent_id=agent_id, action=action, input=payload)  # type: ignore
                invoke_fn = _invoke
            elif hasattr(sdk_client, "run_agent"):
                def _invoke(agent_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
                    return sdk_client.run_agent(agent_id=agent_id, action=action, input=payload)  # type: ignore
                invoke_fn = _invoke
            elif hasattr(sdk_client, "invoke"):
                def _invoke(agent_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
                    return sdk_client.invoke(agent_id=agent_id, action=action, input=payload)  # type: ignore
                invoke_fn = _invoke
        elif agents_client is not None:
            # AgentsClient patterns to try: run / invoke
            if hasattr(agents_client, "run"):
                def _invoke(agent_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
                    return agents_client.run(agent_id=agent_id, action=action, input=payload)  # type: ignore
                invoke_fn = _invoke
            elif hasattr(agents_client, "invoke"):
                def _invoke(agent_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
                    return agents_client.invoke(agent_id=agent_id, action=action, input=payload)  # type: ignore
                invoke_fn = _invoke

        if invoke_fn is None:
            # Couldn't wire the SDK — fall back to REST
            raise RuntimeError("IBM watsonx.orchestrate Agent SDK not available or no compatible invoke method found. "
                               + "; ".join(errors))

        # Success: record for use
        self._use_sdk = True
        self._sdk_invoke = invoke_fn
    
    def call_gatekeeper_agent(
        self,
        agent_id: str,
        action: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call the Gatekeeper Agent created in watsonx
        
        Args:
            agent_id: Gatekeeper agent ID in watsonx (e.g., "gatekeeper_v1")
            action: Action to perform (scan_cargo, check_compliance, authorize_vehicle)
            payload: Input data for the action
            
        Returns:
            Response from watsonx agent
        """
        logger.info(f"Calling Gatekeeper Agent: {agent_id}")
        logger.info(f"Action: {action}")
        
        try:
            if self._use_sdk and self._sdk_invoke:
                result = self._sdk_invoke(agent_id, action, {**payload, "project_id": self.project_id, "space_id": self.space_id})
            else:
                result = self._invoke_agent_rest(agent_id, action, payload)

            logger.info(f"✓ Gatekeeper response: {result.get('status', 'success')}")
            
            return {
                "agent": "gatekeeper",
                "action": action,
                "status": result.get("status", "success"),
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call Gatekeeper Agent: {e}")
            return {
                "agent": "gatekeeper",
                "action": action,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to call Gatekeeper Agent via SDK: {e}")
            return {
                "agent": "gatekeeper",
                "action": action,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def call_guardian_agent(
        self,
        agent_id: str,
        vehicle_id: str,
        action: str,
        sensor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call the Guardian Agent created in watsonx
        
        Args:
            agent_id: Guardian agent ID in watsonx (e.g., "guardian_v1")
            vehicle_id: Vehicle identifier
            action: Action to perform (monitor_sensors, detect_crash, detect_fire)
            sensor_data: Sensor readings from vehicle
            
        Returns:
            Response from watsonx agent
        """
        logger.info(f"Calling Guardian Agent: {agent_id}")
        logger.info(f"Vehicle: {vehicle_id}")
        logger.info(f"Action: {action}")
        
        try:
            if self._use_sdk and self._sdk_invoke:
                payload = {
                    "project_id": self.project_id,
                    "space_id": self.space_id,
                    "vehicle_id": vehicle_id,
                    "sensor_data": sensor_data,
                }
                result = self._sdk_invoke(agent_id, action, payload)
            else:
                result = self._invoke_agent_rest(
                    agent_id,
                    action,
                    {
                        "vehicle_id": vehicle_id,
                        "sensor_data": sensor_data,
                    },
                )

            logger.info(f"✓ Guardian response: {result.get('status', 'success')}")
            
            return {
                "agent": "guardian",
                "vehicle_id": vehicle_id,
                "action": action,
                "status": result.get("status", "success"),
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call Guardian Agent: {e}")
            return {
                "agent": "guardian",
                "vehicle_id": vehicle_id,
                "action": action,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to call Guardian Agent via SDK: {e}")
            return {
                "agent": "guardian",
                "vehicle_id": vehicle_id,
                "action": action,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _invoke_agent_rest(self, agent_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback REST invocation for a watsonx agent."""
        endpoint = f"{self.api_url}/v1/agents/{agent_id}/run"
        request_body = {
            "project_id": self.project_id,
            "space_id": self.space_id,
            "action": action,
            "input": payload,
            "timestamp": datetime.now().isoformat(),
        }
        logger.debug(f"Request: POST {endpoint}")
        logger.debug(f"Body: {json.dumps(request_body, indent=2)}")
        response = requests.post(
            endpoint,
            headers=self.headers,
            json=request_body,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    
    def orchestrate_departure_workflow(
        self,
        gatekeeper_agent_id: str,
        guardian_agent_id: str,
        vehicle_id: str,
        cargo_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Orchestrate complete departure workflow using both agents
        
        Args:
            gatekeeper_agent_id: Gatekeeper agent ID in watsonx
            guardian_agent_id: Guardian agent ID in watsonx
            vehicle_id: Vehicle identifier
            cargo_data: Cargo manifest and details
            
        Returns:
            Workflow execution result
        """
        logger.info("\n" + "="*70)
        logger.info("VEHICLE DEPARTURE WORKFLOW")
        logger.info("="*70)
        
        workflow_result = {
            "workflow_id": "departure_workflow",
            "vehicle_id": vehicle_id,
            "started_at": datetime.now().isoformat(),
            "steps": []
        }
        
        try:
            # Step 1: Gatekeeper - Scan Cargo
            logger.info("\n[Step 1/6] Gatekeeper scanning cargo...")
            scan_result = self.call_gatekeeper_agent(
                gatekeeper_agent_id,
                "scan_cargo",
                {
                    "vehicle_id": vehicle_id,
                    "cargo": cargo_data
                }
            )
            workflow_result["steps"].append({"step": 1, "result": scan_result})
            
            if scan_result["status"] != "success":
                logger.warning("Cargo scan failed")
                workflow_result["status"] = "failed"
                return workflow_result
            
            # Step 2: Gatekeeper - Check Compliance
            logger.info("[Step 2/6] Gatekeeper checking compliance...")
            compliance_result = self.call_gatekeeper_agent(
                gatekeeper_agent_id,
                "check_compliance",
                {
                    "vehicle_id": vehicle_id,
                    "cargo": cargo_data,
                    "scan_data": scan_result.get("result")
                }
            )
            workflow_result["steps"].append({"step": 2, "result": compliance_result})
            
            if compliance_result["status"] != "success":
                logger.warning("Compliance check failed")
                workflow_result["status"] = "failed"
                return workflow_result
            
            # Step 3: Gatekeeper - Authorize Departure
            logger.info("[Step 3/6] Gatekeeper authorizing vehicle departure...")
            auth_result = self.call_gatekeeper_agent(
                gatekeeper_agent_id,
                "authorize_vehicle",
                {
                    "vehicle_id": vehicle_id,
                    "compliance_status": compliance_result.get("result")
                }
            )
            workflow_result["steps"].append({"step": 3, "result": auth_result})
            
            if auth_result["status"] != "success":
                logger.warning("Vehicle authorization failed")
                workflow_result["status"] = "blocked"
                return workflow_result
            
            logger.info("✓ Vehicle authorized for departure")
            
            # Step 4: Guardian - Activate Monitoring
            logger.info("[Step 4/6] Guardian activating monitoring...")
            monitor_result = self.call_guardian_agent(
                guardian_agent_id,
                vehicle_id,
                "activate_monitoring",
                {}
            )
            workflow_result["steps"].append({"step": 4, "result": monitor_result})
            
            # Step 5: Guardian - Initialize Sensors
            logger.info("[Step 5/6] Guardian initializing sensors...")
            init_result = self.call_guardian_agent(
                guardian_agent_id,
                vehicle_id,
                "initialize_sensors",
                {}
            )
            workflow_result["steps"].append({"step": 5, "result": init_result})
            
            # Step 6: Vehicle Ready for Road
            logger.info("[Step 6/6] Vehicle ready for road operations...")
            workflow_result["steps"].append({
                "step": 6,
                "result": {
                    "status": "success",
                    "message": "Vehicle ready for road"
                }
            })
            
            workflow_result["status"] = "success"
            workflow_result["completed_at"] = datetime.now().isoformat()
            
            logger.info("\n" + "="*70)
            logger.info("✓ DEPARTURE WORKFLOW COMPLETED SUCCESSFULLY")
            logger.info("="*70 + "\n")
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            workflow_result["status"] = "error"
            workflow_result["error"] = str(e)
            return workflow_result
    
    def orchestrate_emergency_response(
        self,
        guardian_agent_id: str,
        vehicle_id: str,
        incident_type: str,
        sensor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Orchestrate emergency response workflow
        
        Args:
            guardian_agent_id: Guardian agent ID in watsonx
            vehicle_id: Vehicle identifier
            incident_type: Type of incident (crash, fire)
            sensor_data: Sensor readings
            
        Returns:
            Emergency response result
        """
        logger.info("\n" + "!"*70)
        logger.info("🚨 EMERGENCY INCIDENT DETECTED")
        logger.info("!"*70)
        
        response_result = {
            "workflow_id": "emergency_response_workflow",
            "vehicle_id": vehicle_id,
            "incident_type": incident_type,
            "started_at": datetime.now().isoformat(),
            "steps": []
        }
        
        try:
            # Step 1: Detect Incident
            logger.info("\n[Step 1/7] Guardian detecting incident...")
            detect_result = self.call_guardian_agent(
                guardian_agent_id,
                vehicle_id,
                "detect_incident",
                sensor_data
            )
            response_result["steps"].append({"step": 1, "result": detect_result})
            
            # Step 2: Unlock Doors
            logger.info("[Step 2/7] Unlocking vehicle doors...")
            unlock_result = self.call_guardian_agent(
                guardian_agent_id,
                vehicle_id,
                "unlock_doors",
                {"incident_type": incident_type}
            )
            response_result["steps"].append({"step": 2, "result": unlock_result})
            
            # Step 3: Activate Alarm
            logger.info("[Step 3/7] Activating alarm...")
            alarm_result = self.call_guardian_agent(
                guardian_agent_id,
                vehicle_id,
                "activate_alarm",
                {"incident_type": incident_type}
            )
            response_result["steps"].append({"step": 3, "result": alarm_result})
            
            # Step 4: Broadcast PA Alert
            logger.info("[Step 4/7] Broadcasting PA alert...")
            pa_result = self.call_guardian_agent(
                guardian_agent_id,
                vehicle_id,
                "broadcast_pa_alert",
                {"incident_type": incident_type}
            )
            response_result["steps"].append({"step": 4, "result": pa_result})
            
            # Step 5: Dispatch SOS
            logger.info("[Step 5/7] Dispatching SOS...")
            sos_result = self.call_guardian_agent(
                guardian_agent_id,
                vehicle_id,
                "dispatch_sos",
                {
                    "incident_type": incident_type,
                    "sensor_data": sensor_data
                }
            )
            response_result["steps"].append({"step": 5, "result": sos_result})
            
            # Step 6: Monitor Situation
            logger.info("[Step 6/7] Continuous monitoring active...")
            response_result["steps"].append({
                "step": 6,
                "result": {"status": "success", "message": "Monitoring active"}
            })
            
            # Step 7: Await Help
            logger.info("[Step 7/7] Awaiting emergency services...")
            response_result["steps"].append({
                "step": 7,
                "result": {"status": "success", "message": "Emergency services notified"}
            })
            
            response_result["status"] = "success"
            response_result["completed_at"] = datetime.now().isoformat()
            
            logger.info("\n" + "!"*70)
            logger.info("✓ EMERGENCY RESPONSE COMPLETED")
            logger.info("!"*70 + "\n")
            
            return response_result
            
        except Exception as e:
            logger.error(f"Emergency response failed: {e}")
            response_result["status"] = "error"
            response_result["error"] = str(e)
            return response_result


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example usage
    caller = WatsonxAgentCaller()
    
    # Example: Call Gatekeeper Agent to scan cargo
    print("\n" + "="*70)
    print("Example 1: Calling Gatekeeper Agent")
    print("="*70)
    
    gk_result = caller.call_gatekeeper_agent(
        agent_id="gatekeeper_v1",
        action="scan_cargo",
        payload={
            "vehicle_id": "VEH_001",
            "cargo": {
                "description": "Electronics",
                "weight_kg": 500,
                "hazmat": False
            }
        }
    )
    print(f"Result: {json.dumps(gk_result, indent=2)}")
    
    # Example: Call Guardian Agent to monitor sensors
    print("\n" + "="*70)
    print("Example 2: Calling Guardian Agent")
    print("="*70)
    
    gn_result = caller.call_guardian_agent(
        agent_id="guardian_v1",
        vehicle_id="VEH_001",
        action="monitor_sensors",
        sensor_data={
            "imu_accel_x": 0.5,
            "imu_accel_y": 0.3,
            "imu_accel_z": 1.0,
            "temperature": 45,
            "gps_lat": 17.3850,
            "gps_lon": 78.4867
        }
    )
    print(f"Result: {json.dumps(gn_result, indent=2)}")
