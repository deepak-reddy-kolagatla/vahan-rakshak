import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime

class VehicleDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection"""
        self.ping_task = None
        self.connected = True
        try:
            await self.channel_layer.group_add("vehicle_data", self.channel_name)
            await self.accept()
            print(f"WebSocket client connected at {datetime.now().isoformat()}")

            # Start ping/pong mechanism
            self.ping_task = asyncio.create_task(self.ping_loop())

            # Send initial connection success message
            await self.send(text_data=json.dumps({
                "type": "connection_established",
                "message": "Connected successfully",
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            print(f"Connection error: {str(e)}")
            self.connected = False
            raise

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        self.connected = False
        if self.ping_task:
            self.ping_task.cancel()
            try:
                await self.ping_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                print(f"Error canceling ping task: {str(e)}")

        try:
            await self.channel_layer.group_discard("vehicle_data", self.channel_name)
        except Exception as e:
            print(f"Error removing from group: {str(e)}")

        print(f"WebSocket client disconnected with code: {close_code}")
        if close_code in [1011, 1006]:
            print("Connection error detected. Please check server logs for details.")

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages"""
        try:
            if not text_data:
                return

            message = json.loads(text_data)
            print(f"Received message: {message}")

            # Normalize timestamps and incident structure
            for key in ["driver_data", "speed_data", "emergency_data"]:
                if key in message and message[key] is not None:
                    if "timestamp_ms" not in message[key] and "timestamp" in message[key]:
                        # convert ISO timestamp to ms
                        dt = datetime.fromisoformat(message[key]["timestamp"])
                        message[key]["timestamp_ms"] = int(dt.timestamp() * 1000)
                    elif "timestamp_ms" not in message[key]:
                        message[key]["timestamp_ms"] = int(datetime.now().timestamp() * 1000)

            # Ensure emergency_data always has VehicleSafetyState structure
            if "emergency_data" in message and message["emergency_data"] is not None:
                incident = message["emergency_data"]
                if "vehicle_safety_state" not in incident or incident["vehicle_safety_state"] is None:
                    incident["vehicle_safety_state"] = {
                        "fire": {
                            "detected": False,
                            "confidence_pct": 0,
                            "cabin_temp_c": 25.0,
                            "battery_pack_temp_c": 25.0
                        },
                        "water": {
                            "level_cm": 0,
                            "flood_risk_level": "none",
                            "submersion_detected": False
                        },
                        "accident": {
                            "collision_detected": False,
                            "impact_g_force": 0.0,
                            "collision_severity_level": "none"
                        }
                    }

            # Handle pong response
            if message.get("type") == "pong" and hasattr(self, "pong_received") and self.pong_received:
                self.pong_received.set()
                return

            # Broadcast the combined message to all connected clients
            await self.channel_layer.group_send(
                "vehicle_data",
                {
                    "type": "broadcast_data",
                    "event_data": message
                }
            )

        except json.JSONDecodeError as e:
            error_msg = f"JSON decode error: {str(e)}"
            print(error_msg)
            await self.send(text_data=json.dumps({"error": error_msg}))
        except Exception as e:
            error_msg = f"Error in receive: {str(e)}"
            print(error_msg)
            if self.connected:
                await self.send(text_data=json.dumps({"error": error_msg}))

    async def ping_loop(self):
        """Send periodic pings to keep the connection alive"""
        ping_interval = 15  # seconds
        ping_timeout = 10   # seconds
        while self.connected:
            try:
                await asyncio.sleep(ping_interval)
                if not self.connected:
                    break

                # Send ping
                await self.send(text_data=json.dumps({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                }))

                # Wait for pong
                try:
                    pong_received = asyncio.Event()
                    self.pong_received = pong_received
                    await asyncio.wait_for(pong_received.wait(), timeout=ping_timeout)
                except asyncio.TimeoutError:
                    print(f"Ping timeout at {datetime.now().isoformat()}")
                    await self.close(code=1000)
                    break

            except Exception as e:
                print(f"Ping error: {str(e)}")
                break

    async def broadcast_data(self, event):
        """Broadcast combined driver, speed, and incident data to WebSocket clients"""
        try:
            message = event.get("event_data")
            if not message:
                print(f"Warning: No event_data in event: {event}")
                return

            await self.send(text_data=json.dumps(message))
            print(f"Broadcasted message keys: {list(message.keys())}")
        except Exception as e:
            print(f"Error in broadcast_data: {str(e)}")
            print(f"Event data: {event}")
