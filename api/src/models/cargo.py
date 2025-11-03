"""
Cargo data models for Vāhan-Rakshak
"""

from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
from datetime import datetime


class CargoType(str, Enum):
    """Enumeration of cargo types"""
    ELECTRONICS = "electronics"
    HAZMAT = "hazmat"
    FOOD = "food"
    CHEMICALS = "chemicals"
    TEXTILES = "textiles"
    MACHINERY = "machinery"
    LITHIUM_BATTERIES = "lithium_batteries"
    PHARMACEUTICALS = "pharmaceuticals"
    OTHER = "other"


class CargoItem(BaseModel):
    """Individual cargo item model"""
    item_id: str
    name: str
    cargo_type: CargoType
    quantity: int
    weight_kg: float
    hazmat_code: Optional[str] = None
    qr_code: str
    declared: bool = True
    timestamp: datetime = datetime.now()

    class Config:
        use_enum_values = True


class CargoManifest(BaseModel):
    """Complete cargo manifest for a vehicle"""
    manifest_id: str
    vehicle_id: str
    vehicle_number: str
    driver_name: str
    departure_time: datetime
    items: List[CargoItem]
    total_weight_kg: float
    scanned_by: str
    gatekeeper_approval: bool = False
    violations: List[str] = []

    class Config:
        use_enum_values = True

    def calculate_total_weight(self) -> float:
        """Calculate total weight from items"""
        return sum(item.weight_kg * item.quantity for item in self.items)

    def has_violations(self) -> bool:
        """Check if manifest has any violations"""
        return len(self.violations) > 0
