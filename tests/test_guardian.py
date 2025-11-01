"""
Guardian Agent Tests
"""

import pytest
from src.agents import GuardianAgent
from src.models import IncidentType, SeverityLevel


class TestGuardianAgent:
    """Test cases for Guardian Agent"""

    @pytest.fixture
    def guardian(self):
        """Fixture for GuardianAgent"""
        agent = GuardianAgent(vehicle_id="VEH001")
        agent.start()
        return agent

    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        agent = GuardianAgent(agent_id="test_guardian", vehicle_id="VEH001")
        assert agent.agent_id == "test_guardian"
        assert agent.vehicle_id == "VEH001"
        assert not agent.active

    def test_agent_startup(self, guardian):
        """Test agent starts correctly"""
        assert guardian.active

    def test_driver_fatigue_detection(self, guardian):
        """Detect driver fatigue (not full sleep)."""
        result = guardian.process_driver_monitoring(
            eye_closure_pct=50.0,
            blink_duration_ms=450.0,
            yawning_rate_per_min=5.0,
            steering_variability=0.25,
            lane_departures=0,
        )

        assert result["state"] in ["fatigue", "sleep"]
        incidents = guardian.get_incident_log()
        assert len(incidents) > 0
        assert incidents[0].incident_type == IncidentType.FATIGUE

    def test_sleep_detection(self, guardian):
        """Detect micro-sleep and trigger strong alerts."""
        result = guardian.process_driver_monitoring(
            eye_closure_pct=90.0,
            blink_duration_ms=500.0,
            yawning_rate_per_min=6.0,
            steering_variability=0.3,
            lane_departures=1,
        )
        assert result["state"] == "sleep"

    def test_location_update(self, guardian):
        """Test GPS location update"""
        guardian.update_location(13.0827, 80.2707, 7.0)

        status = guardian.get_agent_status()
        assert status["current_location"]["lat"] == 13.0827
        assert status["current_location"]["lon"] == 80.2707

    def test_driver_alert_actions(self, guardian):
        """Fatigue triggers alert tone and light flash; sleep adds seat vibration."""
        # Fatigue level
        guardian.process_driver_monitoring(60.0, 420.0, 5.0, 0.25, 0)
        inc1 = guardian.get_incident_log()[-1]
        assert any("DRIVER ALERT TONE" in a for a in inc1.actions_taken)
        assert any("FLASH CABIN LIGHTS" in a for a in inc1.actions_taken)

        # Sleep level
        guardian.process_driver_monitoring(90.0, 500.0, 6.0, 0.3, 1)
        inc2 = guardian.get_incident_log()[-1]
        assert any("SEAT VIBRATION" in a for a in inc2.actions_taken)

    # Simulation removed in fatigue-only mode

    def test_incident_logging(self, guardian):
        """Test incident logging for fatigue."""
        guardian.process_driver_monitoring(55.0, 450.0, 5.0, 0.3, 0)
        incidents = guardian.get_incident_log()
        assert len(incidents) > 0
        assert incidents[0].incident_type == IncidentType.FATIGUE


class TestDriverMonitoring:
    """Test driver monitoring scoring"""

    def test_normal_state(self):
        agent = GuardianAgent(vehicle_id="VEH001")
        agent.start()
        result = agent.process_driver_monitoring(10.0, 200.0, 1.0, 0.05, 0)
        assert result["state"] == "normal"

    def test_sleep_state(self):
        agent = GuardianAgent(vehicle_id="VEH001")
        agent.start()
        result = agent.process_driver_monitoring(85.0, 500.0, 6.0, 0.3, 1)
        assert result["state"] == "sleep"
