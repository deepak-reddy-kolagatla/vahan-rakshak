"""
Cargo Scanner Tool - QR code scanning and manifest parsing
"""

import logging
from typing import Optional, Dict, Any
from src.models import CargoManifest, CargoItem, CargoType

logger = logging.getLogger(__name__)


class CargoScanner:
    """Tool for scanning and validating cargo manifests"""

    def __init__(self):
        self.scanned_items = []
        self.current_manifest: Optional[CargoManifest] = None

    def scan_qr_code(self, qr_data: str) -> Dict[str, Any]:
        """
        Parse QR code data for cargo item
        
        Args:
            qr_data: QR code string containing item information
            
        Returns:
            Dictionary with parsed cargo item data
        """
        try:
            # Parse QR data format: ITEM_ID|NAME|TYPE|QUANTITY|WEIGHT|HAZMAT_CODE
            parts = qr_data.split("|")
            
            if len(parts) < 5:
                logger.error(f"Invalid QR format: {qr_data}")
                return {"error": "Invalid QR code format"}

            item_data = {
                "item_id": parts[0],
                "name": parts[1],
                "cargo_type": parts[2].lower(),
                "quantity": int(parts[3]),
                "weight_kg": float(parts[4]),
                "hazmat_code": parts[5] if len(parts) > 5 else None,
                "qr_code": qr_data,
            }
            
            self.scanned_items.append(item_data)
            logger.info(f"QR scan successful: {item_data['item_id']}")
            return item_data
            
        except Exception as e:
            logger.error(f"Error parsing QR code: {e}")
            return {"error": str(e)}

    def scan_cargo_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze cargo bay image for undeclared items
        
        Args:
            image_path: Path to cargo bay image
            
        Returns:
            Analysis results
        """
        logger.info(f"Scanning cargo image: {image_path}")
        
        # In production, this would use computer vision APIs
        # For now, return placeholder response
        return {
            "image_path": image_path,
            "analysis_status": "pending",
            "undeclared_items": [],
            "confidence": 0.85
        }

    def create_manifest(
        self,
        manifest_id: str,
        vehicle_id: str,
        vehicle_number: str,
        driver_name: str,
        scanned_by: str
    ) -> CargoManifest:
        """
        Create cargo manifest from scanned items
        
        Args:
            manifest_id: Unique manifest identifier
            vehicle_id: Vehicle identifier
            vehicle_number: License plate number
            driver_name: Driver name
            scanned_by: Scanner operator name
            
        Returns:
            CargoManifest object
        """
        from datetime import datetime
        
        items = []
        total_weight = 0
        
        for item_data in self.scanned_items:
            try:
                cargo_item = CargoItem(
                    item_id=item_data["item_id"],
                    name=item_data["name"],
                    cargo_type=item_data["cargo_type"],
                    quantity=item_data["quantity"],
                    weight_kg=item_data["weight_kg"],
                    hazmat_code=item_data.get("hazmat_code"),
                    qr_code=item_data["qr_code"],
                    declared=True,
                    timestamp=datetime.now()
                )
                items.append(cargo_item)
                total_weight += item_data["weight_kg"] * item_data["quantity"]
            except Exception as e:
                logger.error(f"Error creating cargo item: {e}")

        manifest = CargoManifest(
            manifest_id=manifest_id,
            vehicle_id=vehicle_id,
            vehicle_number=vehicle_number,
            driver_name=driver_name,
            departure_time=datetime.now(),
            items=items,
            total_weight_kg=total_weight,
            scanned_by=scanned_by
        )
        
        self.current_manifest = manifest
        logger.info(f"Manifest created: {manifest_id}")
        return manifest

    def clear_scanned_items(self) -> None:
        """Clear scanned items cache"""
        self.scanned_items = []
        self.current_manifest = None
        logger.info("Scanned items cleared")
