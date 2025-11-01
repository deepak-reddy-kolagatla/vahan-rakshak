"""
Speed Detector Tool - Overspeed detection and analysis
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SpeedDetector:
    """Detects speeding based on current speed vs. limit and duration."""

    def __init__(
        self,
        warn_threshold_pct: float = 0.10,  # 10% over limit -> warning
        high_threshold_pct: float = 0.30,  # 30% over limit -> high
        critical_threshold_pct: float = 0.50,  # 50% over limit -> critical
        sustained_duration_s: int = 10,
    ) -> None:
        self.warn_threshold_pct = warn_threshold_pct
        self.high_threshold_pct = high_threshold_pct
        self.critical_threshold_pct = critical_threshold_pct
        self.sustained_duration_s = sustained_duration_s

        self.is_over_speed = False
        self.over_start_time: Optional[datetime] = None
        self.last_reading_time: Optional[datetime] = None
        self.last_status: Dict[str, Any] = {}

    def process_speed_reading(
        self,
        current_speed_kmh: float,
        speed_limit_kmh: float,
        timestamp_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Analyze current speed against the speed limit.

        Returns: dict with keys: status, over_by_kmh, over_pct, alert_level
        """
        now = datetime.now() if timestamp_ms is None else datetime.fromtimestamp(timestamp_ms / 1000.0)
        self.last_reading_time = now

        over_by_kmh = max(0.0, current_speed_kmh - speed_limit_kmh)
        over_pct = (over_by_kmh / speed_limit_kmh) if speed_limit_kmh > 0 else 0.0

        alert_level = "normal"
        if over_pct >= self.critical_threshold_pct:
            alert_level = "critical"
        elif over_pct >= self.high_threshold_pct:
            alert_level = "high"
        elif over_pct >= self.warn_threshold_pct:
            alert_level = "warning"

        if over_by_kmh > 0:
            if not self.is_over_speed:
                self.is_over_speed = True
                self.over_start_time = now
            duration_s = (now - self.over_start_time).total_seconds() if self.over_start_time else 0
            sustained = duration_s >= self.sustained_duration_s
        else:
            self.is_over_speed = False
            self.over_start_time = None
            sustained = False

        result = {
            "status": "ok",
            "current_speed_kmh": current_speed_kmh,
            "speed_limit_kmh": speed_limit_kmh,
            "over_by_kmh": over_by_kmh,
            "over_pct": round(over_pct, 3),
            "alert_level": "sustained" if (alert_level != "normal" and sustained) else alert_level,
            "sustained": sustained,
            "timestamp": now.isoformat(),
        }

        if result["alert_level"] in ("warning", "high", "critical", "sustained"):
            logger.warning(
                f"SPEED ALERT: {current_speed_kmh:.1f}km/h over {speed_limit_kmh:.1f}km/h | "
                f"+{over_by_kmh:.1f}km/h ({over_pct*100:.0f}%) | level={result['alert_level']}"
            )

        self.last_status = result
        return result

    def reset(self) -> None:
        self.is_over_speed = False
        self.over_start_time = None
        self.last_status = {}
        logger.info("Speed detector state reset")

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_over_speed": self.is_over_speed,
            "over_start_time": self.over_start_time.isoformat() if self.over_start_time else None,
            "last_status": self.last_status,
        }
