"""
Safety Actuator Tool - Emergency response actions
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class SafetyActuator:
    """Tool for triggering emergency safety actions"""

    def __init__(self):
        """Initialize safety actuator"""
        self.doors_unlocked = False
        self.alarm_active = False
        self.pa_system_active = False
        self.emergency_lighting = False
        self.actions_log = []
        # Fatigue-specific actuators
        self.driver_alert_tone_active = False
        self.seat_vibration_active = False
        self.cabin_light_flash_active = False

    def unlock_all_doors(self) -> Dict[str, Any]:
        """
        Unlock all vehicle doors for emergency evacuation
        
        Returns:
            Status of door unlock operation
        """
        timestamp = datetime.now()
        
        try:
            # In production, this would send command to vehicle CAN bus or API
            logger.critical("EMERGENCY: Unlocking all doors")
            
            self.doors_unlocked = True
            self._log_action("unlock_all_doors", "success", timestamp)
            
            return {
                "action": "unlock_all_doors",
                "status": "success",
                "doors_unlocked": True,
                "timestamp": timestamp.isoformat(),
                "message": "All doors unlocked for emergency evacuation"
            }
        except Exception as e:
            logger.error(f"Failed to unlock doors: {e}")
            self._log_action("unlock_all_doors", "failed", timestamp, str(e))
            return {
                "action": "unlock_all_doors",
                "status": "failed",
                "error": str(e),
                "timestamp": timestamp.isoformat()
            }

    def activate_emergency_alarm(self) -> Dict[str, Any]:
        """
        Activate emergency alarm system
        
        Returns:
            Status of alarm activation
        """
        timestamp = datetime.now()
        
        try:
            logger.critical("EMERGENCY: Activating alarm")
            
            self.alarm_active = True
            self._log_action("activate_alarm", "success", timestamp)
            
            return {
                "action": "activate_alarm",
                "status": "success",
                "alarm_active": True,
                "timestamp": timestamp.isoformat(),
                "message": "Emergency alarm activated - continuous loud siren"
            }
        except Exception as e:
            logger.error(f"Failed to activate alarm: {e}")
            self._log_action("activate_alarm", "failed", timestamp, str(e))
            return {
                "action": "activate_alarm",
                "status": "failed",
                "error": str(e),
                "timestamp": timestamp.isoformat()
            }

    def activate_pa_system(self, message: str, language: str = "en") -> Dict[str, Any]:
        """
        Activate PA system with emergency message
        
        Args:
            message: Message to broadcast
            language: Language code (en, hi, etc.)
            
        Returns:
            Status of PA system activation
        """
        timestamp = datetime.now()
        
        try:
            logger.critical(f"EMERGENCY PA: [{language}] {message}")
            
            self.pa_system_active = True
            self._log_action("pa_announcement", "success", timestamp, message)
            
            return {
                "action": "pa_announcement",
                "status": "success",
                "message": message,
                "language": language,
                "timestamp": timestamp.isoformat(),
                "multilingual": language in ["hi", "mr", "ta", "te"]
            }
        except Exception as e:
            logger.error(f"Failed to activate PA system: {e}")
            self._log_action("pa_announcement", "failed", timestamp, str(e))
            return {
                "action": "pa_announcement",
                "status": "failed",
                "error": str(e),
                "timestamp": timestamp.isoformat()
            }

    def activate_emergency_lighting(self) -> Dict[str, Any]:
        """
        Activate emergency lighting and hazard lights
        
        Returns:
            Status of emergency lighting
        """
        timestamp = datetime.now()
        
        try:
            logger.warning("EMERGENCY: Activating emergency lighting")
            
            self.emergency_lighting = True
            self._log_action("emergency_lighting", "success", timestamp)
            
            return {
                "action": "emergency_lighting",
                "status": "success",
                "lighting_active": True,
                "timestamp": timestamp.isoformat(),
                "features": ["hazard_lights", "interior_lights", "exit_signs"]
            }
        except Exception as e:
            logger.error(f"Failed to activate lighting: {e}")
            self._log_action("emergency_lighting", "failed", timestamp, str(e))
            return {
                "action": "emergency_lighting",
                "status": "failed",
                "error": str(e),
                "timestamp": timestamp.isoformat()
            }

    def play_driver_alert_tone(self, intensity: str = "high") -> Dict[str, Any]:
        """Play driver fatigue alert tone."""
        timestamp = datetime.now()
        try:
            logger.warning(f"FATIGUE ALERT: Playing driver alert tone (intensity={intensity})")
            self.driver_alert_tone_active = True
            self._log_action("driver_alert_tone", "success", timestamp, f"intensity={intensity}")
            return {
                "action": "driver_alert_tone",
                "status": "success",
                "intensity": intensity,
                "timestamp": timestamp.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to play driver alert tone: {e}")
            self._log_action("driver_alert_tone", "failed", timestamp, str(e))
            return {"action": "driver_alert_tone", "status": "failed", "error": str(e), "timestamp": timestamp.isoformat()}

    def seat_vibration(self, intensity: str = "high", duration_s: int = 2) -> Dict[str, Any]:
        """Activate seat vibration to wake driver."""
        timestamp = datetime.now()
        try:
            logger.warning(f"FATIGUE ALERT: Seat vibration (intensity={intensity}, duration={duration_s}s)")
            self.seat_vibration_active = True
            self._log_action("seat_vibration", "success", timestamp, f"intensity={intensity},duration={duration_s}")
            return {
                "action": "seat_vibration",
                "status": "success",
                "intensity": intensity,
                "duration_s": duration_s,
                "timestamp": timestamp.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to activate seat vibration: {e}")
            self._log_action("seat_vibration", "failed", timestamp, str(e))
            return {"action": "seat_vibration", "status": "failed", "error": str(e), "timestamp": timestamp.isoformat()}

    def flash_cabin_lights(self, pattern: str = "fast") -> Dict[str, Any]:
        """Flash cabin lights to alert driver and passengers."""
        timestamp = datetime.now()
        try:
            logger.warning(f"FATIGUE ALERT: Flashing cabin lights (pattern={pattern})")
            self.cabin_light_flash_active = True
            self._log_action("flash_cabin_lights", "success", timestamp, f"pattern={pattern}")
            return {
                "action": "flash_cabin_lights",
                "status": "success",
                "pattern": pattern,
                "timestamp": timestamp.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to flash cabin lights: {e}")
            self._log_action("flash_cabin_lights", "failed", timestamp, str(e))
            return {"action": "flash_cabin_lights", "status": "failed", "error": str(e), "timestamp": timestamp.isoformat()}

    def execute_emergency_response(self, incident_type: str) -> Dict[str, Any]:
        """
        Execute complete emergency response sequence
        
        Args:
            incident_type: Type of incident (crash, fire, etc.)
            
        Returns:
            Summary of all actions executed
        """
        timestamp = datetime.now()
        actions_executed = []
        
        logger.critical(f"EXECUTING EMERGENCY RESPONSE - Type: {incident_type}")
        
        # Sequence of emergency actions
        door_result = self.unlock_all_doors()
        actions_executed.append(door_result)
        
        alarm_result = self.activate_emergency_alarm()
        actions_executed.append(alarm_result)
        
        light_result = self.activate_emergency_lighting()
        actions_executed.append(light_result)
        
        # Multilingual PA announcement
        messages = {
            "en": f"EMERGENCY! {incident_type.upper()} DETECTED. EVACUATE IMMEDIATELY!",
            "hi": f"आपातकाल! {incident_type.upper()} का पता चला। तुरंत बाहर निकलें!",
        }
        
        for lang, msg in messages.items():
            pa_result = self.activate_pa_system(msg, lang)
            actions_executed.append(pa_result)
        
        return {
            "incident_type": incident_type,
            "timestamp": timestamp.isoformat(),
            "actions_executed": len(actions_executed),
            "all_successful": all(a.get("status") == "success" for a in actions_executed),
            "actions": actions_executed
        }

    def deactivate_emergency_systems(self) -> Dict[str, Any]:
        """
        Deactivate emergency systems after incident cleared
        
        Returns:
            Status of deactivation
        """
        timestamp = datetime.now()
        
        logger.info("Deactivating emergency systems")
        
        self.doors_unlocked = False
        self.alarm_active = False
        self.pa_system_active = False
        self.emergency_lighting = False
        
        self._log_action("deactivate_systems", "success", timestamp)
        
        return {
            "action": "deactivate_emergency",
            "status": "success",
            "systems_active": {
                "doors_unlocked": self.doors_unlocked,
                "alarm_active": self.alarm_active,
                "pa_system": self.pa_system_active,
                "emergency_lighting": self.emergency_lighting
            },
            "timestamp": timestamp.isoformat()
        }

    def _log_action(
        self,
        action: str,
        status: str,
        timestamp: datetime,
        details: str = ""
    ) -> None:
        """Log safety action"""
        self.actions_log.append({
            "action": action,
            "status": status,
            "timestamp": timestamp.isoformat(),
            "details": details
        })

    def get_actions_log(self) -> List[Dict[str, Any]]:
        """Get all logged safety actions"""
        return self.actions_log

    def get_system_status(self) -> Dict[str, Any]:
        """Get current status of all safety systems"""
        return {
            "doors_unlocked": self.doors_unlocked,
            "alarm_active": self.alarm_active,
            "pa_system_active": self.pa_system_active,
            "emergency_lighting": self.emergency_lighting,
            "driver_alert_tone_active": self.driver_alert_tone_active,
            "seat_vibration_active": self.seat_vibration_active,
            "cabin_light_flash_active": self.cabin_light_flash_active,
            "total_actions_logged": len(self.actions_log)
        }
