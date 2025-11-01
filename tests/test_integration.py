"""
Integration tests for FastAPI backend
"""

import pytest
from fastapi.testclient import TestClient
from src.api.server import app


class TestSystemIntegration:
    """Integration tests for API"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_health(self, client):
        r = client.get("/healthz")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_guardian_driver_monitoring(self, client):
        payload = {
            "vehicle_id": "VEH001",
            "eye_closure_pct": 55.0,
            "blink_duration_ms": 450.0,
            "yawning_rate_per_min": 5.0,
            "steering_variability": 0.25,
            "lane_departures": 0,
        }
        r = client.post("/v1/driver/monitoring", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["vehicle_id"] == "VEH001"
        # In watsonx mode we only verify structure
        assert data.get("backend") == "watsonx"
        assert isinstance(data.get("result", {}), dict)

    def test_speed_violation(self, client):
        # Ensure vehicle context exists via monitoring call
        client.post("/v1/driver/monitoring", json={
            "vehicle_id": "VEH002",
            "eye_closure_pct": 10.0,
            "blink_duration_ms": 200.0,
            "yawning_rate_per_min": 1.0,
            "steering_variability": 0.05,
            "lane_departures": 0,
        })
        r = client.post("/v1/speed", json={
            "vehicle_id": "VEH002",
            "current_speed_kmh": 110.0,
            "speed_limit_kmh": 80.0
        })
        assert r.status_code == 200
        res = r.json()
        assert res.get("backend") == "watsonx"
        assert isinstance(res.get("result", {}), dict)

    def test_status_and_logs(self, client):
        # In watsonx-only mode, these endpoints are not implemented
        s = client.get("/v1/status/VEH003")
        assert s.status_code == 501
        inc = client.get("/v1/incidents/VEH003")
        assert inc.status_code == 501
        al = client.get("/v1/alerts/VEH003")
        assert al.status_code == 501

    def test_incident_response_flow(self, client):
        # Not implemented for watsonx-only backend
        assert client.get("/v1/incidents/VEH004").status_code == 501
        assert client.get("/v1/alerts/VEH004").status_code == 501
