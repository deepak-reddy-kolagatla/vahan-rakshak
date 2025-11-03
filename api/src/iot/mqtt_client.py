"""
MQTT Client - IoT communication
"""

import logging
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT client for sensor communication"""

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        client_id: str = "vahan_rakshak"
    ):
        """
        Initialize MQTT client
        
        Args:
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port
            client_id: MQTT client identifier
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.connected = False
        self.subscriptions = {}
        
        logger.info(
            f"MQTT Client initialized: {broker_host}:{broker_port} "
            f"({client_id})"
        )

    def connect(self) -> bool:
        """
        Connect to MQTT broker
        
        Returns:
            Connection success status
        """
        try:
            logger.info(f"Connecting to MQTT broker: {self.broker_host}:{self.broker_port}")
            self.connected = True
            logger.info("MQTT connection established")
            return True
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from MQTT broker"""
        self.connected = False
        logger.info("MQTT disconnected")

    def subscribe(
        self,
        topic: str,
        callback: Callable[[str, Any], None]
    ) -> None:
        """
        Subscribe to MQTT topic
        
        Args:
            topic: Topic to subscribe to
            callback: Callback function for messages
        """
        self.subscriptions[topic] = callback
        logger.info(f"Subscribed to topic: {topic}")

    def publish(self, topic: str, payload: str) -> bool:
        """
        Publish message to MQTT topic
        
        Args:
            topic: Target topic
            payload: Message payload
            
        Returns:
            Publish success status
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return False

        logger.info(f"Publishing to {topic}: {payload}")
        return True

    def get_connection_status(self) -> Dict[str, Any]:
        """Get MQTT connection status"""
        return {
            "connected": self.connected,
            "broker": f"{self.broker_host}:{self.broker_port}",
            "client_id": self.client_id,
            "subscriptions": len(self.subscriptions)
        }
