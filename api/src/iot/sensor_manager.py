"""
Sensor Manager - Unified sensor interface
"""

import logging
from typing import Dict, Any, Callable, List

logger = logging.getLogger(__name__)


class SensorManager:
    """Manages all vehicle sensors"""

    def __init__(self):
        """Initialize sensor manager"""
        self.sensors = {}
        self.sensor_handlers = {}
        logger.info("Sensor Manager initialized")

    def register_sensor(
        self,
        sensor_id: str,
        sensor_type: str,
        location: str = "",
        callback: Callable = None
    ) -> None:
        """
        Register a sensor
        
        Args:
            sensor_id: Unique sensor identifier
            sensor_type: Type of sensor (imu, temperature, gas, etc.)
            location: Physical location of sensor
            callback: Function to call on data update
        """
        self.sensors[sensor_id] = {
            "type": sensor_type,
            "location": location,
            "active": True,
            "last_reading": None,
            "last_update": None
        }
        
        if callback:
            self.sensor_handlers[sensor_id] = callback
        
        logger.info(f"Sensor registered: {sensor_id} ({sensor_type}) at {location}")

    def update_sensor_reading(self, sensor_id: str, data: Any) -> None:
        """
        Update sensor reading
        
        Args:
            sensor_id: Sensor identifier
            data: Sensor reading data
        """
        if sensor_id not in self.sensors:
            logger.warning(f"Unknown sensor: {sensor_id}")
            return

        from datetime import datetime
        self.sensors[sensor_id]["last_reading"] = data
        self.sensors[sensor_id]["last_update"] = datetime.now()

        # Call registered handler
        if sensor_id in self.sensor_handlers:
            try:
                self.sensor_handlers[sensor_id](data)
            except Exception as e:
                logger.error(f"Error calling handler for {sensor_id}: {e}")

    def get_sensor_status(self) -> Dict[str, Any]:
        """Get status of all sensors"""
        return {
            "total_sensors": len(self.sensors),
            "active_sensors": sum(1 for s in self.sensors.values() if s.get("active")),
            "sensors": self.sensors
        }

    def get_sensor_reading(self, sensor_id: str) -> Any:
        """Get latest reading from sensor"""
        if sensor_id in self.sensors:
            return self.sensors[sensor_id].get("last_reading")
        return None
