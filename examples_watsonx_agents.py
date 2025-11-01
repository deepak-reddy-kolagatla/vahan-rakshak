#!/usr/bin/env python3
"""
Example Usage: Calling watsonx Agents from Your Application

This file demonstrates how to use watsonx agents from your Python code.
"""

import logging
import json
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_1_direct_agent_call():
    """Example 1: Direct call to Gatekeeper agent"""
    logger.info("\n" + "="*70)
    logger.info("EXAMPLE 1: Direct Gatekeeper Agent Call")
    logger.info("="*70)
    
    from src.watsonx_agent_caller import WatsonxAgentCaller
    
    caller = WatsonxAgentCaller()
    
    # Call Gatekeeper agent to scan cargo
    result = caller.call_gatekeeper_agent(
        agent_id="gatekeeper_v1",
        action="scan_cargo",
        payload={
            "vehicle_id": "VEH_001",
            "cargo": {
                "description": "Electronics - Laptops and Phones",
                "weight_kg": 500,
                "hazmat": False,
                "fragile": True
            }
        }
    )
    
    print("\nGatekeeper Agent Response:")
    print(json.dumps(result, indent=2))


def example_2_guardian_agent_call():
    """Example 2: Direct call to Guardian agent"""
    logger.info("\n" + "="*70)
    logger.info("EXAMPLE 2: Direct Guardian Agent Call")
    logger.info("="*70)
    
    from src.watsonx_agent_caller import WatsonxAgentCaller
    
    caller = WatsonxAgentCaller()
    
    # Call Guardian agent to monitor sensors
    result = caller.call_guardian_agent(
        agent_id="guardian_v1",
        vehicle_id="VEH_001",
        action="monitor_sensors",
        sensor_data={
            "imu_accel_x": 0.5,
            "imu_accel_y": 0.3,
            "imu_accel_z": 1.0,
            "temperature": 45,
            "gas_co2": 400,
            "gps_lat": 17.3850,
            "gps_lon": 78.4867,
            "gps_altitude": 500
        }
    )
    
    print("\nGuardian Agent Response:")
    print(json.dumps(result, indent=2))


def example_3_departure_workflow():
    """Example 3: Complete departure workflow"""
    logger.info("\n" + "="*70)
    logger.info("EXAMPLE 3: Vehicle Departure Workflow")
    logger.info("="*70)
    
    from src.watsonx_agent_caller import WatsonxAgentCaller
    
    caller = WatsonxAgentCaller()
    
    # Run complete departure workflow
    result = caller.orchestrate_departure_workflow(
        gatekeeper_agent_id="gatekeeper_v1",
        guardian_agent_id="guardian_v1",
        vehicle_id="VEH_001",
        cargo_data={
            "vehicle_number": "KA-05-AB-1234",
            "vehicle_class": "LCV",
            "driver_name": "Rajesh Kumar",
            "scanned_by": "Operator_001",
            "cargo": {
                "description": "Frozen Food",
                "weight_kg": 2000,
                "hazmat": False,
                "temperature_controlled": True,
                "target_temp": -18
            }
        }
    )
    
    print("\nDeparture Workflow Result:")
    print(json.dumps({
        "workflow_id": result.get("workflow_id"),
        "status": result.get("status"),
        "vehicle_id": result.get("vehicle_id"),
        "total_steps": len(result.get("steps", []))
    }, indent=2))


def example_4_emergency_response():
    """Example 4: Emergency response workflow"""
    logger.info("\n" + "!"*70)
    logger.info("EXAMPLE 4: 🚨 Emergency Response Workflow")
    logger.info("!"*70)
    
    from src.watsonx_agent_caller import WatsonxAgentCaller
    
    caller = WatsonxAgentCaller()
    
    # Simulate crash detection
    result = caller.orchestrate_emergency_response(
        guardian_agent_id="guardian_v1",
        vehicle_id="VEH_001",
        incident_type="crash",
        sensor_data={
            "imu_accel_x": 25.5,      # High impact
            "imu_accel_y": 18.2,
            "imu_accel_z": -22.3,
            "temperature": 45,
            "gps_lat": 17.3850,
            "gps_lon": 78.4867,
            "timestamp": "2025-11-01T17:30:00Z"
        }
    )
    
    print("\nEmergency Response Result:")
    print(json.dumps({
        "workflow_id": result.get("workflow_id"),
        "status": result.get("status"),
        "vehicle_id": result.get("vehicle_id"),
        "incident_type": result.get("incident_type"),
        "total_steps": len(result.get("steps", []))
    }, indent=2))


def example_5_hybrid_orchestrator():
    """Example 5: Using Hybrid Orchestrator (recommended)"""
    logger.info("\n" + "="*70)
    logger.info("EXAMPLE 5: Using Hybrid Orchestrator")
    logger.info("="*70)
    
    from src.orchestrator_hybrid import HybridOrchestrator
    
    # Initialize orchestrator (auto-detects watsonx vs local)
    orchestrator = HybridOrchestrator()
    
    # Get agent info
    print("\n1. Agent Configuration:")
    agent_info = orchestrator.get_agent_info()
    print(json.dumps(agent_info, indent=2))
    
    # Start agents
    print("\n2. Starting Agents...")
    status = orchestrator.start_all_agents()
    print(json.dumps(status, indent=2))
    
    # Process vehicle departure
    print("\n3. Processing Vehicle Departure...")
    departure_result = orchestrator.process_vehicle_departure(
        vehicle_id="VEH_002",
        vehicle_number="KA-05-XY-5678",
        vehicle_class="HCV",
        driver_name="Priya Singh",
        scanned_by="Operator_002",
        cargo_data={
            "description": "Construction Materials",
            "weight_kg": 5000,
            "hazmat": False
        }
    )
    print(f"Departure Status: {departure_result.get('status')}")
    
    # Get system status
    print("\n4. System Status:")
    system_status = orchestrator.get_system_status()
    print(json.dumps({
        "mode": system_status.get("mode"),
        "running": system_status.get("orchestrator_running")
    }, indent=2))


def example_6_full_application_flow():
    """Example 6: Complete application flow"""
    logger.info("\n" + "="*70)
    logger.info("EXAMPLE 6: Complete Application Flow")
    logger.info("="*70)
    
    from src.orchestrator_hybrid import HybridOrchestrator
    
    orchestrator = HybridOrchestrator()
    
    # Initialize
    logger.info("\n[Phase 1] Initialization")
    orchestrator.start_all_agents()
    
    # Vehicle arrivals (3 vehicles)
    vehicles = [
        {
            "vehicle_id": "VEH_100",
            "vehicle_number": "KA-05-AA-1001",
            "driver_name": "Rajesh Kumar",
            "cargo": {"description": "Electronics", "weight_kg": 500}
        },
        {
            "vehicle_id": "VEH_101",
            "vehicle_number": "KA-05-AA-1002",
            "driver_name": "Priya Singh",
            "cargo": {"description": "Textiles", "weight_kg": 1000}
        },
        {
            "vehicle_id": "VEH_102",
            "vehicle_number": "KA-05-AA-1003",
            "driver_name": "Amit Patel",
            "cargo": {"description": "Food Items", "weight_kg": 2000}
        }
    ]
    
    # Process departures
    logger.info("\n[Phase 2] Processing Departures")
    for i, vehicle in enumerate(vehicles, 1):
        logger.info(f"\nVehicle {i}/3: {vehicle['vehicle_number']}")
        
        result = orchestrator.process_vehicle_departure(
            vehicle_id=vehicle["vehicle_id"],
            vehicle_number=vehicle["vehicle_number"],
            vehicle_class="LCV",
            driver_name=vehicle["driver_name"],
            scanned_by="Admin",
            cargo_data=vehicle["cargo"]
        )
        
        logger.info(f"Status: {result.get('status')}")
    
    # Simulate incident
    logger.info("\n[Phase 3] Incident Detection")
    incident_result = orchestrator.handle_guardian_incident(
        vehicle_id="VEH_100",
        incident_type="crash",
        sensor_data={
            "imu_accel_x": 20.0,
            "imu_accel_y": 15.0,
            "imu_accel_z": -18.0,
            "temperature": 50
        }
    )
    logger.info(f"Incident Response: {incident_result.get('status')}")
    
    # Shutdown
    logger.info("\n[Phase 4] Shutdown")
    orchestrator.stop_all_agents()
    logger.info("✓ System shutdown complete")


def main():
    """Run all examples"""
    print("\n" + "█"*70)
    print("PROJECT VĀHAN-RAKSHAK")
    print("watsonx Agent Integration Examples")
    print("█"*70)
    
    examples = [
        ("Direct Gatekeeper Call", example_1_direct_agent_call),
        ("Direct Guardian Call", example_2_guardian_agent_call),
        ("Departure Workflow", example_3_departure_workflow),
        ("Emergency Response", example_4_emergency_response),
        ("Hybrid Orchestrator", example_5_hybrid_orchestrator),
        ("Complete Flow", example_6_full_application_flow),
    ]
    
    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nRun specific examples:")
    print("  python examples_watsonx_agents.py 1")
    print("  python examples_watsonx_agents.py 1,2,3")
    print("  python examples_watsonx_agents.py all")
    
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            example_nums = list(range(1, len(examples) + 1))
        else:
            example_nums = [int(x) for x in sys.argv[1].split(",")]
        
        for num in example_nums:
            if 1 <= num <= len(examples):
                try:
                    _, func = examples[num - 1]
                    func()
                except Exception as e:
                    logger.error(f"Example {num} failed: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"Invalid example number: {num}")
    else:
        # Run example 5 by default (Hybrid Orchestrator)
        print("\nRunning Example 5 (Hybrid Orchestrator) by default...")
        try:
            example_5_hybrid_orchestrator()
        except Exception as e:
            logger.error(f"Example failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "█"*70)
    print("Examples complete!")
    print("█"*70 + "\n")


if __name__ == "__main__":
    main()
