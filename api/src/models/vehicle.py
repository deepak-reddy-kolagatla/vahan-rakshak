"""
Vehicle state and configuration models for Vāhan-Rakshak
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime


class VehicleClass(str, Enum):
    """Types of vehicles"""
    SLEEPER_COACH = "sleeper_coach"
    AC_COACH = "ac_coach"
    NON_AC_COACH = "non_ac_coach"
    BUS = "bus"
    MINIBUS = "minibus"
    TRUCK = "truck"
    AMBULANCE = "ambulance"


class VehicleStatus(str, Enum):
    """Vehicle operational status"""
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class VehicleState(BaseModel):
    """Current state of vehicle"""
    vehicle_id: str
    vehicle_number: str
    vehicle_class: VehicleClass
    status: VehicleStatus
    current_location: Dict[str, float] = {"lat": 0.0, "lon": 0.0}
    speed_kmh: float = 0.0
    gps_enabled: bool = True
    sensors_active: bool = True
    doors_locked: bool = True
    alarm_active: bool = False
    ignition_enabled: bool = True
    last_update: datetime = datetime.now()

    class Config:
        use_enum_values = True


class VehicleConfiguration(BaseModel):
    """Vehicle sensor and safety configuration"""
    vehicle_id: str
    vehicle_number: str
    vehicle_class: VehicleClass
    
    # Sensor configurations
    imu_enabled: bool = True
    imu_sensitivity: float = 4.0  # G-forces
    
    temperature_sensors: int = 2
    fire_detection_enabled: bool = True
    
    gps_enabled: bool = True
    cellular_enabled: bool = True
    
    # Safety features
    automated_doors: bool = True
    pa_system_enabled: bool = True
    emergency_lighting: bool = True
    
    # Supported languages
    languages: list[str] = ["en", "hi"]
    
    # Emergency contacts
    emergency_numbers: list[str] = []
    fleet_manager_contact: str = ""
    
    last_maintenance: datetime = datetime.now()
    next_maintenance: datetime = datetime.now()

    class Config:
        use_enum_values = True
