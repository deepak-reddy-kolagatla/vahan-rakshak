"""
Configuration management for Vāhan-Rakshak
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class Config:
    """Application configuration"""

    # Gatekeeper settings
    GATEKEEPER_ENABLED = os.getenv("GATEKEEPER_ENABLED", "true").lower() == "true"
    GATEKEEPER_HOST = os.getenv("GATEKEEPER_HOST", "localhost")
    GATEKEEPER_PORT = int(os.getenv("GATEKEEPER_PORT", "5000"))

    # Guardian settings
    GUARDIAN_ENABLED = os.getenv("GUARDIAN_ENABLED", "true").lower() == "true"
    GUARDIAN_HOST = os.getenv("GUARDIAN_HOST", "localhost")
    GUARDIAN_PORT = int(os.getenv("GUARDIAN_PORT", "5001"))

    # IoT settings
    IOT_MQTT_BROKER = os.getenv("IOT_MQTT_BROKER", "localhost")
    IOT_MQTT_PORT = int(os.getenv("IOT_MQTT_PORT", "1883"))

    # Sensor thresholds
    CRASH_SENSITIVITY_THRESHOLD = float(os.getenv("CRASH_SENSITIVITY_THRESHOLD", "4.0"))
    FIRE_DETECTION_ENABLED = os.getenv("FIRE_DETECTION_ENABLED", "true").lower() == "true"

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/vahan_rakshak.db")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "./logs/vahan_rakshak.log")


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


# Get current config
current_env = os.getenv("ENVIRONMENT", "development").lower()
if current_env == "production":
    current_config = ProductionConfig()
elif current_env == "testing":
    current_config = TestingConfig()
else:
    current_config = DevelopmentConfig()
