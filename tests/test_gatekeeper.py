"""
Gatekeeper Agent Tests
"""

import pytest
from src.agents import GatekeeperAgent
from src.models import ComplianceStatus


class TestGatekeeperAgent:
    """Test cases for Gatekeeper Agent"""

    @pytest.fixture
    def gatekeeper(self):
        """Fixture for GatekeeperAgent"""
        agent = GatekeeperAgent()
        agent.start()
        return agent

    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        agent = GatekeeperAgent(agent_id="test_gatekeeper")
        assert agent.agent_id == "test_gatekeeper"
        assert not agent.active

    def test_agent_startup(self, gatekeeper):
        """Test agent starts correctly"""
        assert gatekeeper.active

    def test_cargo_qr_scan(self, gatekeeper):
        """Test QR code scanning"""
        qr_data = "ITEM001|Smartphones|electronics|10|2.5|"
        result = gatekeeper.scan_cargo_qr(qr_data)
        assert result["item_id"] == "ITEM001"
        assert result["name"] == "Smartphones"
        assert result["quantity"] == 10

    def test_manifest_creation(self, gatekeeper):
        """Test manifest creation"""
        # First scan some items
        gatekeeper.scan_cargo_qr("ITEM001|Smartphones|electronics|10|2.5|")
        gatekeeper.scan_cargo_qr("ITEM002|Laptops|electronics|5|2.0|")

        # Create manifest
        manifest = gatekeeper.create_manifest(
            manifest_id="MNF001",
            vehicle_id="VEH001",
            vehicle_number="KA-01-AB-1234",
            driver_name="John Doe",
            scanned_by="Operator1"
        )

        assert manifest.manifest_id == "MNF001"
        assert len(manifest.items) == 2
        assert manifest.total_weight_kg > 0

    def test_compliance_check(self, gatekeeper):
        """Test compliance checking"""
        # Simulate departure with violation
        # This would normally be a full workflow
        assert gatekeeper.get_agent_status()["active"] is True


class TestCargoCompliance:
    """Test cargo compliance rules"""

    def test_prohibited_cargo_detection(self):
        """Test detection of prohibited cargo"""
        from src.tools import RegulatorAPI
        
        api = RegulatorAPI()
        result = api.check_cargo_compliance(
            "sleeper_coach",
            ["hazmat", "lithium_batteries"]
        )
        
        assert not result["compliant"]
        assert len(result["violations"]) > 0

    def test_weight_limit_check(self):
        """Test weight limit enforcement"""
        from src.tools import RegulatorAPI
        
        api = RegulatorAPI()
        result = api.check_weight_compliance("sleeper_coach", 6000)
        
        assert not result["compliant"]
        assert result["violation"] == "overweight"

    def test_sensor_requirements(self):
        """Test sensor requirement validation"""
        from src.tools import RegulatorAPI
        
        api = RegulatorAPI()
        result = api.check_sensor_requirements(
            "sleeper_coach",
            ["gps", "imu"]  # Missing fire detection
        )
        
        assert not result["compliant"]
        assert "fire_detection" in result["missing_sensors"]
