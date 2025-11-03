"""
Incident and alert models for Vāhan-Rakshak
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime


class IncidentType(str, Enum):
    """Types of incidents"""
    CRASH = "crash"
    FIRE = "fire"
    MECHANICAL_FAILURE = "mechanical_failure"
    COLLISION = "collision"
    FATIGUE = "fatigue"
    SPEEDING = "speeding"
    UNKNOWN = "unknown"


class FireType(str, Enum):
    """Types of fires detectable"""
    LITHIUM_ION = "lithium_ion"
    DIESEL = "diesel"
    CHEMICAL = "chemical"
    ELECTRICAL = "electrical"
    UNKNOWN = "unknown"


class SeverityLevel(str, Enum):
    """Severity levels for incidents"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SensorReading(BaseModel):
    """Individual sensor reading"""
    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime = datetime.now()
    location: Optional[str] = None


class Incident(BaseModel):
    """Main incident model"""
    incident_id: str
    vehicle_id: str
    vehicle_number: str
    incident_type: IncidentType
    fire_type: Optional[FireType] = None
    severity: SeverityLevel
    timestamp: datetime = datetime.now()
    location: Dict[str, float]  # {lat, lon, altitude}
    sensor_readings: list[SensorReading] = []
    actions_taken: list[str] = []
    sos_sent: bool = False
    sos_timestamp: Optional[datetime] = None
    description: str = ""

    class Config:
        use_enum_values = True

    def add_action(self, action: str) -> None:
        """Log an action taken during incident"""
        self.actions_taken.append(action)

    def trigger_sos(self) -> None:
        """Mark SOS as triggered"""
        self.sos_sent = True
        self.sos_timestamp = datetime.now()


class Alert(BaseModel):
    """Alert notification model"""
    alert_id: str
    incident_id: str
    alert_type: str
    message_en: str
    message_hi: Optional[str] = None
    message_regional: Optional[str] = None
    severity: SeverityLevel
    timestamp: datetime = datetime.now()
    acknowledged: bool = False
    target_recipients: list[str] = []  # phone numbers, emails

    class Config:
        use_enum_values = True

    def get_message(self, language: str = "en") -> str:
        """Get message in specified language"""
        if language == "hi":
            return self.message_hi or self.message_en
        return self.message_en
