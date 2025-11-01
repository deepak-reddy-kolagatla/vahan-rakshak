"""
Main entry point for Vāhan-Rakshak FastAPI backend
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from config import current_config
import uvicorn


def main():
    """Launch FastAPI server"""
    logger.info("=" * 70)
    logger.info("PROJECT VĀHAN-RAKSHAK (वाहन-रक्षक) - API Server")
    logger.info("=" * 70)
    logger.info(f"Environment: {current_config.__class__.__name__}")

    # Run FastAPI app
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
