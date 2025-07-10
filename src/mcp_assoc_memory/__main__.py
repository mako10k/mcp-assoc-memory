"""
Main entry point for MCP Associative Memory Server
Production-ready server with environment-based configuration
"""

import os
import sys
import logging
from pathlib import Path
from .server import mcp


def setup_logging():
    """Setup logging configuration based on environment variables."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE")
    
    # Configure logging
    logging_config = {
        "level": getattr(logging, log_level, logging.INFO),
        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S"
    }
    
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logging_config["filename"] = log_file
    
    logging.basicConfig(**logging_config)


def get_server_config():
    """Get server configuration from environment variables."""
    return {
        "host": os.getenv("SERVER_HOST", "0.0.0.0"),
        "port": int(os.getenv("SERVER_PORT", "8000")),
        "workers": int(os.getenv("WORKERS", "0")) or None,
    }


def main():
    """Main entry point."""
    # Setup logging
    setup_logging()
    
    # Get configuration
    config = get_server_config()
    
    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info("Starting MCP Associative Memory Server")
    logger.info(f"Server configuration: {config}")
    
    # Ensure required directories exist
    data_dir = Path(os.getenv("DATA_DIR", "./data"))
    logs_dir = Path(os.getenv("LOGS_DIR", "./logs"))
    
    data_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Start server with HTTP transport
        mcp.run(
            transport="http",
            host=config["host"],
            port=config["port"]
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
