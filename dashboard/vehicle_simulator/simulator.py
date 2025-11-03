import json
import random
import asyncio
import websockets
from datetime import datetime
import aiohttp  # for sending HTTP requests

WS_URL = "ws://localhost:8001/ws/vehicle_data/"
UNIFIED_URL = "https://vahan-rakshak.onrender.com/v1/vehicle/update"

class VehicleSimulator:
    def __init__(self, vehicle_id="VEH001"):
        self.vehicle_id = vehicle_id
        self.speed = 60
        self.eye_closure = 30
        self.yawning_rate = 2
        self.blink_duration = 200  # milliseconds
        self.is_running = False
        self.incident_count = 0

    # ----------------- Data generation -----------------
    def generate_driver_data(self):
        self.eye_closure = min(100, self.eye_closure + random.uniform(-5, 8))
        self.yawning_rate = min(10, max(0, self.yawning_rate + random.uniform(-0.5, 1)))
        self.blink_duration = min(500, max(100, self.blink_duration + random.uniform(-20, 30)))

        return {
            "vehicle_id": self.vehicle_id,
            "eye_closure_pct": round(self.eye_closure, 2),
            "blink_duration_ms": round(self.blink_duration),
            "yawning_rate_per_min": round(self.yawning_rate, 2),
            "steering_variability": round(random.uniform(0, 1), 2),
            "lane_departures": random.randint(0, 2) if random.random() < 0.1 else 0
        }

    def generate_speed_data(self):
        speed_change = random.uniform(-5, 5)
        self.speed = min(120, max(0, self.speed + speed_change))

        return {
            "vehicle_id": self.vehicle_id,
            "current_speed_kmh": round(self.speed, 1),
            "speed_limit_kmh": 80,
            "timestamp_ms": int(datetime.now().timestamp() * 1000)
        }

    def generate_incident_data(self):
        fire_detected = random.random() < 0.05
        water_submersion = random.random() < 0.03
        collision_detected = random.random() < 0.02

        if fire_detected or water_submersion or collision_detected:
            self.incident_count += 1

        return {
            "vehicle_id": self.vehicle_id,
            "timestamp_ms": int(datetime.now().timestamp() * 1000),
            "lat": round(random.uniform(12.9, 13.1), 6),
            "lon": round(random.uniform(77.5, 77.7), 6),
            "alt": round(random.uniform(900, 1200), 2),
            "vehicle_safety_state": {
                "fire": {
                    "detected": fire_detected,
                    "confidence_pct": round(random.uniform(70, 100) if fire_detected else 0, 1),
                    "cabin_temp_c": round(random.uniform(25, 50) if fire_detected else 25, 1),
                    "battery_pack_temp_c": round(random.uniform(30, 60) if fire_detected else 30, 1)
                },
                "water": {
                    "level_cm": round(random.uniform(0, 100) if water_submersion else 0, 1),
                    "flood_risk_level": random.choice(["low","medium","high","critical"]) if water_submersion else "none",
                    "submersion_detected": water_submersion
                },
                "accident": {
                    "collision_detected": collision_detected,
                    "impact_g_force": round(random.uniform(5, 30) if collision_detected else 0, 1),
                    "collision_severity_level": random.choice(["low","medium","high","critical"]) if collision_detected else "none"
                }
            }
        }

    # ----------------- WebSocket & backend -----------------
    async def send_data_to_websocket(self, websocket, data):
        try:
            await websocket.send(json.dumps(data))
            return True
        except websockets.exceptions.ConnectionClosed:
            print(f"[{datetime.now().isoformat()}] WebSocket closed, reconnecting...")
            return False
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] WebSocket error: {str(e)}")
            return False

    async def send_data_to_backend(self, payload):
        """Fire-and-forget backend POST"""
        async def _send():
            async with aiohttp.ClientSession() as session:
                try:
                    print(UNIFIED_URL)
                    await session.post(UNIFIED_URL, json=payload)
                    print(UNIFIED_URL)
                    print(f"[{datetime.now().isoformat()}] Pinged backend (not waiting for response)")
                except Exception as e:
                    print(f"[{datetime.now().isoformat()}] Error sending to backend: {str(e)}")
        asyncio.create_task(_send())

    async def listen_to_server(self, websocket):
        """Listen to server messages (like ping) and respond with pong"""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        # respond with pong
                        await websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }))
                except Exception as e:
                    print(f"Error processing server message: {str(e)}")
        except websockets.exceptions.ConnectionClosed:
            print(f"[{datetime.now().isoformat()}] WebSocket listener closed")

    # ----------------- Main simulation loop -----------------
    async def start_simulation(self):
        self.is_running = True
        consecutive_failures = 0

        while True:
            try:
                # Disable client-side ping; server handles heartbeat
                async with websockets.connect(WS_URL, ping_interval=None) as websocket:
                    print(f"[{datetime.now().isoformat()}] Connected to WebSocket at {WS_URL}")

                    # Start listener for server pings
                    listener_task = asyncio.create_task(self.listen_to_server(websocket))

                    while self.is_running:
                        driver_data = self.generate_driver_data()
                        speed_data = self.generate_speed_data()
                        incident_data = self.generate_incident_data()

                        payload = {
                            "driver_data": driver_data,
                            "speed_data": speed_data,
                            "emergency_data": incident_data
                        }

                        ws_success = await self.send_data_to_websocket(websocket, payload)
                        await self.send_data_to_backend(payload)  # fire-and-forget

                        if ws_success:
                            consecutive_failures = 0
                        else:
                            consecutive_failures += 1
                            if consecutive_failures >= 5:
                                print(f"[{datetime.now().isoformat()}] Too many failures. Waiting 30 seconds...")
                                await asyncio.sleep(30)
                                consecutive_failures = 0

                        await asyncio.sleep(60)

                    listener_task.cancel()
                    try:
                        await listener_task
                    except asyncio.CancelledError:
                        pass

            except Exception as e:
                print(f"[{datetime.now().isoformat()}] WebSocket connection error: {str(e)}. Retrying in 5 seconds...")
                await asyncio.sleep(5)

    def stop_simulation(self):
        self.is_running = False

# ----------------- Entry point -----------------
async def main():
    simulator = VehicleSimulator("VEH001")
    print("Starting vehicle simulation. Press Ctrl+C to stop.")
    try:
        await simulator.start_simulation()
    except KeyboardInterrupt:
        print("\nStopping simulation...")
        simulator.stop_simulation()

if __name__ == "__main__":
    asyncio.run(main())
