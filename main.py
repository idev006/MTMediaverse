"""
MediaVerse Application Entry Point
For PyInstaller/PyArmor compatibility
"""

import sys
import os

# Ensure app directory is in path (for PyInstaller)
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add app to path
sys.path.insert(0, BASE_DIR)

# Import and run
from app.core.database import init_database
from app.core.event_bus import get_event_bus
from app.core.log_orchestrator import get_log_orchestrator


def main():
    """Main entry point."""
    log = get_log_orchestrator()
    log.info("MediaVerse starting...")
    
    # Initialize database
    init_database()
    log.info("Database initialized")
    
    # Start EventBus
    event_bus = get_event_bus()
    event_bus.start_async_worker()
    
    log.info("MediaVerse ready!")
    
    # Import and run API server
    import uvicorn
    from app.api.main import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
