"""
Regulator API Tool - Transport rules and compliance verification
"""

import logging
from typing import List, Dict, Any, Optional
from src.models import CargoType, VehicleClass, ViolationType

logger = logging.getLogger(__name__)


class RegulatorAPI:
    """Tool for verifying transport regulations and rules"""

    # Prohibited cargo by vehicle class
    PROHIBITED_CARGO = {
        "sleeper_coach": [CargoType.HAZMAT, CargoType.LITHIUM_BATTERIES, CargoType.CHEMICALS],
        "ac_coach": [CargoType.HAZMAT, CargoType.LITHIUM_BATTERIES],
        "non_ac_coach": [CargoType.LITHIUM_BATTERIES],
        "bus": [],
        "truck": [],
    }

    # Weight limits by vehicle class (kg)
    WEIGHT_LIMITS = {
        "sleeper_coach": 5000,
        "ac_coach": 6000,
        "non_ac_coach": 6000,
        "bus": 7000,
        "truck": 20000,
    }

    # Sensor requirements by vehicle class
    SENSOR_REQUIREMENTS = {
        "sleeper_coach": ["gps", "imu", "fire_detection", "temperature"],
        "ac_coach": ["gps", "imu", "fire_detection"],
        "non_ac_coach": ["gps", "imu"],
        "bus": ["gps", "imu"],
        "truck": ["gps", "imu", "fire_detection"],
    }

    def __init__(self):
        self.violation_history = []

    def check_cargo_compliance(
        self,
        vehicle_class: str,
        cargo_types: List[str],
    ) -> Dict[str, Any]:
        """
        Check if cargo types are allowed for vehicle class
        
        Args:
            vehicle_class: Class of vehicle
            cargo_types: List of cargo types
            
        Returns:
            Compliance check result with violations
        """
        violations = []
        
        prohibited = self.PROHIBITED_CARGO.get(vehicle_class.lower(), [])
        
        for cargo_type in cargo_types:
            cargo_enum = CargoType(cargo_type.lower())
            if cargo_enum in prohibited:
                violations.append({
                    "type": ViolationType.PROHIBITED_HAZMAT.value,
                    "detail": f"{cargo_type} prohibited on {vehicle_class}"
                })
                logger.warning(f"Prohibited cargo: {cargo_type} on {vehicle_class}")

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "vehicle_class": vehicle_class,
            "cargo_checked": len(cargo_types)
        }

    def check_weight_compliance(
        self,
        vehicle_class: str,
        total_weight_kg: float
    ) -> Dict[str, Any]:
        """
        Verify total weight is within limits
        
        Args:
            vehicle_class: Class of vehicle
            total_weight_kg: Total cargo weight
            
        Returns:
            Weight compliance result
        """
        limit = self.WEIGHT_LIMITS.get(vehicle_class.lower(), 5000)
        compliant = total_weight_kg <= limit
        
        result = {
            "compliant": compliant,
            "weight_kg": total_weight_kg,
            "limit_kg": limit,
            "utilization_percent": (total_weight_kg / limit) * 100
        }
        
        if not compliant:
            result["violation"] = ViolationType.OVERWEIGHT.value
            logger.warning(f"Weight limit exceeded: {total_weight_kg}kg > {limit}kg")
        
        return result

    def check_sensor_requirements(
        self,
        vehicle_class: str,
        installed_sensors: List[str]
    ) -> Dict[str, Any]:
        """
        Verify vehicle has required sensors
        
        Args:
            vehicle_class: Class of vehicle
            installed_sensors: List of installed sensor types
            
        Returns:
            Sensor requirement check result
        """
        required = set(self.SENSOR_REQUIREMENTS.get(vehicle_class.lower(), []))
        installed = set(installed_sensors)
        
        missing_sensors = required - installed
        compliant = len(missing_sensors) == 0
        
        result = {
            "compliant": compliant,
            "required_sensors": list(required),
            "installed_sensors": list(installed),
            "missing_sensors": list(missing_sensors)
        }
        
        if not compliant:
            result["violation"] = ViolationType.SENSOR_MALFUNCTION.value
            logger.warning(f"Missing sensors: {missing_sensors}")
        
        return result

    def verify_transport_permit(
        self,
        vehicle_id: str,
        route: str,
        cargo_type: str
    ) -> Dict[str, Any]:
        """
        Verify transport permit for specific route and cargo
        
        Args:
            vehicle_id: Vehicle identifier
            route: Route identifier
            cargo_type: Type of cargo
            
        Returns:
            Permit verification result
        """
        # In production, this would query a database
        logger.info(f"Verifying permit: {vehicle_id} | {route} | {cargo_type}")
        
        return {
            "permit_valid": True,
            "vehicle_id": vehicle_id,
            "route": route,
            "cargo_type": cargo_type,
            "expiry_date": "2025-12-31"
        }

    def get_violation_history(self, vehicle_id: str) -> List[Dict[str, Any]]:
        """
        Get violation history for a vehicle
        
        Args:
            vehicle_id: Vehicle identifier
            
        Returns:
            List of historical violations
        """
        return [v for v in self.violation_history if v.get("vehicle_id") == vehicle_id]

    def report_violation(
        self,
        vehicle_id: str,
        violation_type: str,
        timestamp: str
    ) -> None:
        """
        Report a violation to history
        
        Args:
            vehicle_id: Vehicle identifier
            violation_type: Type of violation
            timestamp: When violation occurred
        """
        self.violation_history.append({
            "vehicle_id": vehicle_id,
            "violation_type": violation_type,
            "timestamp": timestamp
        })
        logger.info(f"Violation recorded: {vehicle_id} - {violation_type}")
