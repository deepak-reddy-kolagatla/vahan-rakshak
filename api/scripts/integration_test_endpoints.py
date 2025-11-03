import os
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Tuple

import requests

# Base URL of the deployed service
BASE_URL = os.getenv("VR_BASE_URL", "https://vahan-rakshak.onrender.com").strip().rstrip("/")

TIMEOUT = float(os.getenv("VR_TIMEOUT", "15"))
VEHICLE_ID = os.getenv("VR_VEHICLE_ID", "veh-123")


class ProbeResult:
    def __init__(self) -> None:
        self.passed: int = 0
        self.failed: int = 0
        self.failures: List[str] = []

    def ok(self, name: str) -> None:
        self.passed += 1
        print(f"[PASS] {name}")

    def err(self, name: str, status: int, body: Any) -> None:
        self.failed += 1
        self.failures.append(f"{name}: status={status}, body={body}")
        print(f"[FAIL] {name} -> status={status}, body={body}")

    def summary(self) -> int:
        print("\n=== Integration Summary ===")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        if self.failures:
            print("\nFailures:")
            for f in self.failures:
                print(f" - {f}")
        # return appropriate exit code
        return 0 if self.failed == 0 else 1


def get(session: requests.Session, path: str) -> Tuple[int, Any]:
    url = f"{BASE_URL}{path}"
    resp = session.get(url, timeout=TIMEOUT)
    try:
        data = resp.json()
    except Exception:
        data = resp.text
    return resp.status_code, data


def post(session: requests.Session, path: str, payload: Dict[str, Any] | None = None) -> Tuple[int, Any]:
    url = f"{BASE_URL}{path}"
    resp = session.post(url, json=payload or {}, timeout=TIMEOUT)
    try:
        data = resp.json()
    except Exception:
        data = resp.text
    return resp.status_code, data


def main() -> int:
    print(f"Hitting service: {BASE_URL}")
    res = ProbeResult()
    s = requests.Session()

    # 1) Health
    status, body = get(s, "/healthz")
    if status == 200 and isinstance(body, dict) and body.get("status") == "ok":
        res.ok("GET /healthz")
    else:
        res.err("GET /healthz", status, body)

    # 2) Driver monitoring (watsonx-backed)
    dm_payload = {
        "vehicle_id": VEHICLE_ID,
        "eye_closure_pct": 35.0,
        "blink_duration_ms": 210.0,
        "yawning_rate_per_min": 4.0,
        "steering_variability": 0.6,
        "lane_departures": 1,
    }
    status, body = post(s, "/v1/driver/monitoring", dm_payload)
    if status == 200 and isinstance(body, dict) and body.get("vehicle_id") == VEHICLE_ID:
        res.ok("POST /v1/driver/monitoring")
    else:
        res.err("POST /v1/driver/monitoring", status, body)

    # 3) Speed reading (watsonx-backed)
    sp_payload = {
        "vehicle_id": VEHICLE_ID,
        "current_speed_kmh": 88.0,
        "speed_limit_kmh": 60.0,
        "timestamp_ms": int(time.time() * 1000),
    }
    status, body = post(s, "/v1/speed", sp_payload)
    if status == 200 and isinstance(body, dict) and body.get("vehicle_id") == VEHICLE_ID:
        res.ok("POST /v1/speed")
    else:
        res.err("POST /v1/speed", status, body)

    # 4) Cargo tools
    status, body = post(s, "/v1/tools/cargo/scan-qr", {"qr_data": "ITEM123|Hazmat|5kg"})
    if status == 200:
        res.ok("POST /v1/tools/cargo/scan-qr")
    else:
        res.err("POST /v1/tools/cargo/scan-qr", status, body)

    manifest_id = f"m-{uuid.uuid4().hex[:8]}"
    cargo_payload = {
        "manifest_id": manifest_id,
        "vehicle_id": VEHICLE_ID,
        "vehicle_number": "MH12AB1234",
        "driver_name": "John Doe",
        "scanned_by": "gatekeeper-1",
        "items": [
            {
                "item_id": "ITEM123",
                "name": "Chemical X",
                "cargo_type": "hazmat",
                "quantity": 2,
                "weight_kg": 5.0,
                "hazmat_code": "HZ-01",
                "qr_code": "ITEM123|Hazmat|5kg",
            }
        ],
    }
    status, body = post(s, "/v1/tools/cargo/create-manifest", cargo_payload)
    if status == 200 and isinstance(body, dict) and body.get("manifest_id") == manifest_id:
        res.ok("POST /v1/tools/cargo/create-manifest")
    else:
        res.err("POST /v1/tools/cargo/create-manifest", status, body)

    # 5) Regulator API
    status, body = post(s, "/v1/tools/regulator/check-cargo-compliance", {"vehicle_class": "HCV", "cargo_types": ["hazmat"]})
    if status == 200:
        res.ok("POST /v1/tools/regulator/check-cargo-compliance")
    else:
        res.err("POST /v1/tools/regulator/check-cargo-compliance", status, body)

    status, body = post(s, "/v1/tools/regulator/check-weight", {"vehicle_class": "HCV", "total_weight_kg": 7500.0})
    if status == 200:
        res.ok("POST /v1/tools/regulator/check-weight")
    else:
        res.err("POST /v1/tools/regulator/check-weight", status, body)

    status, body = post(s, "/v1/tools/regulator/check-sensors", {"vehicle_class": "HCV", "installed_sensors": ["gps", "speed", "camera"]})
    if status == 200:
        res.ok("POST /v1/tools/regulator/check-sensors")
    else:
        res.err("POST /v1/tools/regulator/check-sensors", status, body)

    status, body = post(s, "/v1/tools/regulator/verify-permit", {"vehicle_id": VEHICLE_ID, "route": "Pune-Mumbai", "cargo_type": "hazmat"})
    if status == 200:
        res.ok("POST /v1/tools/regulator/verify-permit")
    else:
        res.err("POST /v1/tools/regulator/verify-permit", status, body)

    ts = datetime.utcnow().isoformat()
    status, body = post(s, "/v1/tools/regulator/report-violation", {"vehicle_id": VEHICLE_ID, "violation_type": "overspeed", "timestamp": ts})
    if status == 200:
        res.ok("POST /v1/tools/regulator/report-violation")
    else:
        res.err("POST /v1/tools/regulator/report-violation", status, body)

    status, body = get(s, f"/v1/tools/regulator/violations/{VEHICLE_ID}")
    if status == 200 and isinstance(body, list):
        res.ok("GET /v1/tools/regulator/violations/{vehicle_id}")
    else:
        res.err("GET /v1/tools/regulator/violations/{vehicle_id}", status, body)

    # 6) Safety Actuator
    for path, payload, name in [
        (f"/v1/tools/safety/{VEHICLE_ID}/unlock-doors", None, "POST /safety/unlock-doors"),
        (f"/v1/tools/safety/{VEHICLE_ID}/alarm", None, "POST /safety/alarm"),
        (f"/v1/tools/safety/{VEHICLE_ID}/pa", {"message": "Attention please", "language": "en"}, "POST /safety/pa"),
        (f"/v1/tools/safety/{VEHICLE_ID}/lights", {"pattern": "fast"}, "POST /safety/lights"),
        (f"/v1/tools/safety/{VEHICLE_ID}/driver-alert", {"intensity": "high"}, "POST /safety/driver-alert"),
        (f"/v1/tools/safety/{VEHICLE_ID}/seat-vibration", {"intensity": "high", "duration_s": 2}, "POST /safety/seat-vibration"),
        (f"/v1/tools/safety/{VEHICLE_ID}/flash-lights", {"pattern": "fast"}, "POST /safety/flash-lights"),
        (f"/v1/tools/safety/{VEHICLE_ID}/emergency", {"incident_type": "SPEEDING"}, "POST /safety/emergency"),
        (f"/v1/tools/safety/{VEHICLE_ID}/deactivate", None, "POST /safety/deactivate"),
    ]:
        status, body = post(s, path, payload)
        if status == 200:
            res.ok(name)
        else:
            res.err(name, status, body)

    status, body = get(s, f"/v1/tools/safety/{VEHICLE_ID}/actions")
    if status == 200 and isinstance(body, list):
        res.ok("GET /v1/tools/safety/{vehicle_id}/actions")
    else:
        res.err("GET /v1/tools/safety/{vehicle_id}/actions", status, body)

    status, body = get(s, f"/v1/tools/safety/{VEHICLE_ID}/status")
    if status == 200 and isinstance(body, dict):
        res.ok("GET /v1/tools/safety/{vehicle_id}/status")
    else:
        res.err("GET /v1/tools/safety/{vehicle_id}/status", status, body)

    # 7) SOS Dispatcher
    status, body = post(s, "/v1/tools/sos/send-alert", {"vehicle_id": VEHICLE_ID, "incident_type": "SPEEDING", "location": {"lat": 18.5, "lon": 73.8}})
    if status == 200:
        res.ok("POST /v1/tools/sos/send-alert")
    else:
        res.err("POST /v1/tools/sos/send-alert", status, body)

    status, body = post(s, "/v1/tools/sos/gps-update", {"vehicle_id": VEHICLE_ID, "lat": 18.51, "lon": 73.84})
    if status == 200:
        res.ok("POST /v1/tools/sos/gps-update")
    else:
        res.err("POST /v1/tools/sos/gps-update", status, body)

    status, body = post(s, "/v1/tools/sos/notify-fleet", {"vehicle_id": VEHICLE_ID, "message": "Driver assistance dispatched"})
    if status == 200:
        res.ok("POST /v1/tools/sos/notify-fleet")
    else:
        res.err("POST /v1/tools/sos/notify-fleet", status, body)

    status, body = get(s, f"/v1/tools/sos/history/{VEHICLE_ID}")
    if status == 200 and isinstance(body, list):
        res.ok("GET /v1/tools/sos/history/{vehicle_id}")
    else:
        res.err("GET /v1/tools/sos/history/{vehicle_id}", status, body)

    status, body = post(s, f"/v1/tools/sos/{VEHICLE_ID}/contacts/add", {"name": "Fleet Manager", "phone": "+91-9876543210"})
    if status == 200:
        res.ok("POST /v1/tools/sos/{vehicle_id}/contacts/add")
    else:
        res.err("POST /v1/tools/sos/{vehicle_id}/contacts/add", status, body)

    status, body = get(s, f"/v1/tools/sos/{VEHICLE_ID}/contacts")
    if status == 200 and isinstance(body, list):
        res.ok("GET /v1/tools/sos/{vehicle_id}/contacts")
    else:
        res.err("GET /v1/tools/sos/{vehicle_id}/contacts", status, body)

    # 8) Speed Detector tools
    status, body = post(s, "/v1/tools/speed/process", sp_payload)
    if status == 200:
        res.ok("POST /v1/tools/speed/process")
    else:
        res.err("POST /v1/tools/speed/process", status, body)

    status, body = get(s, f"/v1/tools/speed/{VEHICLE_ID}/status")
    if status == 200 and isinstance(body, dict):
        res.ok("GET /v1/tools/speed/{vehicle_id}/status")
    else:
        res.err("GET /v1/tools/speed/{vehicle_id}/status", status, body)

    status, body = post(s, f"/v1/tools/speed/{VEHICLE_ID}/reset")
    if status == 200:
        res.ok("POST /v1/tools/speed/{vehicle_id}/reset")
    else:
        res.err("POST /v1/tools/speed/{vehicle_id}/reset", status, body)

    # 9) Not-implemented endpoints (expect 501)
    for path, name in [
        (f"/v1/status/{VEHICLE_ID}", "GET /v1/status/{vehicle_id}"),
        (f"/v1/incidents/{VEHICLE_ID}", "GET /v1/incidents/{vehicle_id}"),
        (f"/v1/alerts/{VEHICLE_ID}", "GET /v1/alerts/{vehicle_id}"),
    ]:
        status, body = get(s, path)
        if status == 501:
            res.ok(name + " (501 as expected)")
        else:
            res.err(name + " (expect 501)", status, body)

    return res.summary()


if __name__ == "__main__":
    sys.exit(main())
