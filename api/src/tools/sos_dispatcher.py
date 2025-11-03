"""
SOS Dispatcher Tool - Emergency services notification
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SOSDispatcher:
    """Tool for dispatching SOS and emergency notifications"""

    def __init__(self):
        """Initialize SOS dispatcher"""
        self.emergency_services = {
            "fire_brigade": {"number": "101", "priority": "critical"},
            "police": {"number": "100", "priority": "high"},
            "ambulance": {"number": "102", "priority": "high"},
            "highway_control": {"number": "1033", "priority": "high"},
        }
        self.dispatch_log = []
        self.emergency_contacts = []

    def send_sos_alert(
        self,
        incident_type: str,
        location: Dict[str, float],
        vehicle_id: str,
        vehicle_number: str,
        fire_type: Optional[str] = None,
        severity: str = "critical"
    ) -> Dict[str, Any]:
        """
        Send SOS alert to emergency services
        
        Args:
            incident_type: Type of incident (crash, fire, etc.)
            location: GPS location {lat, lon, altitude}
            vehicle_id: Vehicle identifier
            vehicle_number: License plate number
            fire_type: Type of fire (if fire incident)
            severity: Severity level
            
        Returns:
            SOS dispatch status
        """
        timestamp = datetime.now()
        dispatch_id = f"SOS_{vehicle_id}_{int(timestamp.timestamp())}"
        
        logger.critical(
            f"SENDING SOS - Type: {incident_type}, "
            f"Location: {location}, Vehicle: {vehicle_number}"
        )
        
        # Prepare SOS message
        sos_message = {
            "dispatch_id": dispatch_id,
            "timestamp": timestamp.isoformat(),
            "incident_type": incident_type,
            "vehicle_number": vehicle_number,
            "vehicle_id": vehicle_id,
            "location": location,
            "fire_type": fire_type,
            "severity": severity,
            "occupants": "unknown",
            "injuries": "potential"
        }
        
        # Send to emergency services
        recipients = self._determine_recipients(incident_type)
        notifications = []
        
        for service in recipients:
            notification = self._send_to_service(service, sos_message)
            notifications.append(notification)
            logger.info(f"SOS sent to {service}: {notification['status']}")
        
        # Log dispatch
        self.dispatch_log.append({
            "dispatch_id": dispatch_id,
            "timestamp": timestamp.isoformat(),
            "sos_message": sos_message,
            "services_notified": recipients,
            "notifications": notifications
        })
        
        return {
            "dispatch_id": dispatch_id,
            "status": "sent",
            "timestamp": timestamp.isoformat(),
            "services_notified": recipients,
            "notifications": notifications,
            "sos_message": sos_message
        }

    def send_gps_location_update(
        self,
        vehicle_id: str,
        latitude: float,
        longitude: float,
        altitude_m: float = 0.0
    ) -> Dict[str, Any]:
        """
        Send real-time GPS location update
        
        Args:
            vehicle_id: Vehicle identifier
            latitude: Current latitude
            longitude: Current longitude
            altitude_m: Altitude in meters
            
        Returns:
            Location update status
        """
        timestamp = datetime.now()
        
        location_update = {
            "vehicle_id": vehicle_id,
            "timestamp": timestamp.isoformat(),
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude,
                "altitude_m": altitude_m
            }
        }
        
        logger.info(
            f"GPS Update - Vehicle: {vehicle_id}, "
            f"Location: {latitude}, {longitude}"
        )
        
        return {
            "status": "sent",
            "timestamp": timestamp.isoformat(),
            "location_update": location_update
        }

    def notify_fleet_manager(
        self,
        vehicle_id: str,
        incident_type: str,
        incident_details: str,
        contact_info: str
    ) -> Dict[str, Any]:
        """
        Send notification to fleet manager
        
        Args:
            vehicle_id: Vehicle identifier
            incident_type: Type of incident
            incident_details: Detailed incident description
            contact_info: Fleet manager contact (email/phone)
            
        Returns:
            Notification status
        """
        timestamp = datetime.now()
        
        notification = {
            "recipient": contact_info,
            "vehicle_id": vehicle_id,
            "incident_type": incident_type,
            "details": incident_details,
            "timestamp": timestamp.isoformat(),
            "subject": f"ALERT: {incident_type.upper()} - {vehicle_id}"
        }
        
        logger.warning(f"Fleet manager notified: {contact_info}")
        
        return {
            "status": "sent",
            "recipient": contact_info,
            "notification": notification,
            "timestamp": timestamp.isoformat()
        }

    def _determine_recipients(self, incident_type: str) -> list:
        """Determine which emergency services to contact"""
        recipients = ["highway_control"]  # Always notify highway control
        
        if "fire" in incident_type.lower():
            recipients.append("fire_brigade")
        
        if "crash" in incident_type.lower() or "collision" in incident_type.lower():
            recipients.extend(["police", "ambulance"])
        
        return recipients

    def _send_to_service(self, service: str, message: Dict) -> Dict[str, Any]:
        """
        Send message to specific emergency service
        
        Args:
            service: Emergency service name
            message: SOS message content
            
        Returns:
            Send status
        """
        # In production, this would use:
        # - SMS API for phone numbers
        # - REST API for emergency dispatch systems
        # - CAD (Computer Aided Dispatch) systems
        
        timestamp = datetime.now()
        service_number = self.emergency_services.get(service, {}).get("number", "unknown")
        
        logger.info(f"Sending SOS to {service} ({service_number})")
        
        return {
            "service": service,
            "service_number": service_number,
            "status": "sent",
            "timestamp": timestamp.isoformat(),
            "message_type": "SOS",
            "incident": message.get("incident_type"),
            "location": message.get("location")
        }

    def get_dispatch_history(self, vehicle_id: Optional[str] = None) -> list:
        """
        Get dispatch history
        
        Args:
            vehicle_id: Optional filter by vehicle ID
            
        Returns:
            List of dispatch records
        """
        if vehicle_id:
            return [
                d for d in self.dispatch_log
                if d.get("sos_message", {}).get("vehicle_id") == vehicle_id
            ]
        return self.dispatch_log

    def add_emergency_contact(self, vehicle_id: str, contact: Dict[str, str]) -> None:
        """
        Add emergency contact for vehicle
        
        Args:
            vehicle_id: Vehicle identifier
            contact: Contact details {name, phone, email}
        """
        contact["vehicle_id"] = vehicle_id
        self.emergency_contacts.append(contact)
        logger.info(f"Emergency contact added for {vehicle_id}: {contact.get('name')}")

    def get_emergency_contacts(self, vehicle_id: str) -> list:
        """Get emergency contacts for vehicle"""
        return [c for c in self.emergency_contacts if c.get("vehicle_id") == vehicle_id]
