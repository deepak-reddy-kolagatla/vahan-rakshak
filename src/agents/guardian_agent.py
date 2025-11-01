"""
Guardian Agent - Driver Fatigue and Sleep Monitoring System
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from src.tools import (
    SafetyActuator, SOSDispatcher, SpeedDetector
)
from src.models import (
    Incident, IncidentType, SeverityLevel, Alert
)

logger = logging.getLogger(__name__)


class GuardianAgent:
    """
    Guardian Agent - Driver Fatigue and Sleep Monitor
    
    Responsibilities:
    - Monitor driver attention signals (PERCLOS, blinks, yawns, steering, lane)
    - Detect fatigue and micro-sleep events
    - Trigger graduated alerts to safely wake the driver
    """

    def __init__(self, agent_id: str = "guardian_v1", vehicle_id: str = "UNKNOWN"):
        """
        Initialize Guardian Agent
        
        Args:
            agent_id: Unique agent identifier
            vehicle_id: Vehicle this agent protects
        """
        self.agent_id = agent_id
        self.vehicle_id = vehicle_id

        # Initialize tools for driver alerts and notifications
        self.safety_actuator = SafetyActuator()
        self.sos_dispatcher = SOSDispatcher()
        self.speed_detector = SpeedDetector()

        self.active = False
        self.incidents = []
        self.alerts = []
        self.current_location = {"lat": 0.0, "lon": 0.0, "altitude": 0.0}
        # Driver state
        self.last_fatigue_score = 0.0
        self.fatigue_state = "normal"  # normal | fatigue | sleep

        logger.info(f"Guardian Agent initialized: {agent_id} for vehicle {vehicle_id}")

    def start(self) -> None:
        """Start Guardian Agent"""
        self.active = True
        logger.info(f"Guardian Agent {self.agent_id} started - monitoring enabled")

    def stop(self) -> None:
        """Stop Guardian Agent"""
        self.active = False
        logger.info(f"Guardian Agent {self.agent_id} stopped")

    def process_driver_monitoring(
        self,
        eye_closure_pct: float,
        blink_duration_ms: float,
        yawning_rate_per_min: float,
        steering_variability: float,
        lane_departures: int,
    ) -> Dict[str, Any]:
        """
        Process driver monitoring signals and detect fatigue/sleep.

        Args:
            eye_closure_pct: Percentage of time eyes are closed over recent window (0-100)
            blink_duration_ms: Average blink duration in ms
            yawning_rate_per_min: Yawns per minute
            steering_variability: Normalized steering variability (0-1)
            lane_departures: Count of lane departures in recent window

        Returns:
            Dict with fatigue_score and state: normal | fatigue | sleep
        """
        if not self.active:
            return {"status": "agent_inactive"}

        score = 0.0
        state = "normal"

        if eye_closure_pct > 80:
            score += 50
        elif eye_closure_pct > 40:
            score += 30

        if blink_duration_ms > 400:
            score += 20

        if yawning_rate_per_min > 4:
            score += 20

        if steering_variability > 0.2:
            score += 10

        if lane_departures > 0:
            score += 20

        # Determine state
        if eye_closure_pct > 80 or score >= 60:
            state = "sleep"
        elif score >= 30:
            state = "fatigue"

        self.last_fatigue_score = score
        self.fatigue_state = state

        result = {
            "fatigue_score": score,
            "state": state,
            "metrics": {
                "eye_closure_pct": eye_closure_pct,
                "blink_duration_ms": blink_duration_ms,
                "yawning_rate_per_min": yawning_rate_per_min,
                "steering_variability": steering_variability,
                "lane_departures": lane_departures,
            },
        }

        # Trigger graduated alerts
        if state == "fatigue":
            self._handle_fatigue_alert(severity=SeverityLevel.HIGH, details="Driver fatigue detected", result=result)
        elif state == "sleep":
            self._handle_fatigue_alert(severity=SeverityLevel.CRITICAL, details="Driver micro-sleep detected", result=result)

        return result

    def process_speed_sensor(
        self,
        current_speed_kmh: float,
        speed_limit_kmh: float,
        timestamp_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Process speed readings and detect overspeed violations."""
        if not self.active:
            return {"status": "agent_inactive"}

        analysis = self.speed_detector.process_speed_reading(current_speed_kmh, speed_limit_kmh, timestamp_ms)

        if analysis.get("alert_level") in ("warning", "high", "critical", "sustained"):
            self._handle_speed_violation(analysis)

        return analysis

    # Crash/Fire processing methods removed per new scope

    # Gas processing removed per new scope

    def _handle_fatigue_alert(self, severity: SeverityLevel, details: str, result: Dict[str, Any]) -> None:
        """Create incident for fatigue/sleep and trigger driver alerts."""
        logger.warning(f"FATIGUE ALERT: {details} | score={result.get('fatigue_score')}")

        incident = Incident(
            incident_id=f"INC_FATIGUE_{int(datetime.now().timestamp())}",
            vehicle_id=self.vehicle_id,
            vehicle_number="UNKNOWN",
            incident_type=IncidentType.FATIGUE,
            severity=severity,
            location=self.current_location,
            description=details,
        )

        self.incidents.append(incident)
        incident.add_action("PERCEIVE: DRIVER FATIGUE")

        # Graduated actions
        self.safety_actuator.play_driver_alert_tone(intensity="high")
        incident.add_action("ACT: DRIVER ALERT TONE")
        self.safety_actuator.flash_cabin_lights(pattern="fast")
        incident.add_action("ACT: FLASH CABIN LIGHTS")

        if severity == SeverityLevel.CRITICAL:
            self.safety_actuator.seat_vibration(intensity="high", duration_s=3)
            incident.add_action("ACT: SEAT VIBRATION")
            # Dispatch SOS for micro-sleep to highway control and notify fleet
            self.sos_dispatcher.send_sos_alert(
                incident_type="fatigue",
                location=self.current_location,
                vehicle_id=self.vehicle_id,
                vehicle_number="UNKNOWN",
                fire_type=None,
                severity=severity.value,
            )
            incident.trigger_sos()
            incident.add_action("ACT: SENDING SOS TO EMERGENCY SERVICES")

        # Create alert notification
        self._create_alerts(incident)

    def _handle_speed_violation(self, analysis: Dict[str, Any]) -> None:
        """Create incident and alerts for speeding violations."""
        over_kmh = analysis.get("over_by_kmh", 0.0)
        limit = analysis.get("speed_limit_kmh", 0.0)
        level = analysis.get("alert_level", "warning")

        # Map level to severity
        if level in ("critical", "sustained"):
            severity = SeverityLevel.CRITICAL
        elif level == "high":
            severity = SeverityLevel.HIGH
        else:
            severity = SeverityLevel.MEDIUM

        # Use string incident_type to avoid enum churn in tests
        incident = Incident(
            incident_id=f"INC_SPEED_{int(datetime.now().timestamp())}",
            vehicle_id=self.vehicle_id,
            vehicle_number="UNKNOWN",
            incident_type="speeding",
            severity=severity,
            location=self.current_location,
            description=f"Speeding {over_kmh:.1f}km/h over limit {limit:.1f}km/h (level={level})",
        )

        self.incidents.append(incident)

        # Alert the driver: tone + flash; seat vibration if severe
        self.safety_actuator.play_driver_alert_tone(intensity="high")
        incident.add_action("ACT: DRIVER ALERT TONE")
        self.safety_actuator.flash_cabin_lights(pattern="fast")
        incident.add_action("ACT: FLASH CABIN LIGHTS")

        if severity == SeverityLevel.CRITICAL:
            self.safety_actuator.seat_vibration(intensity="high", duration_s=2)
            incident.add_action("ACT: SEAT VIBRATION")

        # Notify fleet manager on speeding (no SOS by default)
        try:
            self.sos_dispatcher.notify_fleet_manager(
                vehicle_id=self.vehicle_id,
                incident_type="speeding",
                incident_details=incident.description,
                contact_info="fleet.manager@example.com",
            )
        except Exception:
            pass

        # Create alert for records
        self._create_alerts(incident)

    # Temperature/gas anomaly handlers removed

    # Gas anomaly handler removed

    # Emergency evacuation flow removed in fatigue-only mode

    def _create_alerts(self, incident: Incident) -> None:
        """Create alert notifications for incident"""
        alert = Alert(
            alert_id=f"ALR_{incident.incident_id}",
            incident_id=incident.incident_id,
            alert_type=incident.incident_type,
            message_en=f"DRIVER ALERT: {incident.description} at {incident.location}",
            message_hi="चेतावनी: चालक थकान/नींद का पता चला!",
            severity=incident.severity,
            target_recipients=[]
        )
        
        self.alerts.append(alert)

    def update_location(self, lat: float, lon: float, altitude: float = 0.0) -> None:
        """
        Update current GPS location
        
        Args:
            lat: Latitude
            lon: Longitude
            altitude: Altitude in meters
        """
        self.current_location = {
            "lat": lat,
            "lon": lon,
            "altitude": altitude
        }

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "vehicle_id": self.vehicle_id,
            "active": self.active,
            "current_location": self.current_location,
            "incidents_detected": len(self.incidents),
            "alerts_issued": len(self.alerts),
            "fatigue_state": self.fatigue_state,
            "last_fatigue_score": self.last_fatigue_score,
            "emergency_systems": self.safety_actuator.get_system_status(),
            "speed_status": self.speed_detector.get_status(),
        }

    def get_incident_log(self) -> List[Incident]:
        """Get all recorded incidents"""
        return self.incidents

    def get_alert_history(self) -> List[Alert]:
        """Get alert history"""
        return self.alerts

    # Crash+Fire simulation removed
