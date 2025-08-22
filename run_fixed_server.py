#!/usr/bin/env python3
"""
Run the AuthAI server with fixed configuration to prevent socket errors.
This script imports the Flask app from server.py and runs it with the
correct configuration settings.
"""

import os
import sys
import signal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def handle_exit(sig, frame):
    """Clean up resources before exiting."""
    logger.info("Shutting down server...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    try:
        # Set environment variables if needed
        if not os.environ.get("EMAIL_USERNAME") or not os.environ.get("EMAIL_PASSWORD"):
            if os.path.exists("set_email_env.bat"):
                logger.info("Email environment variables not set. Run set_email_env.bat first.")
                print("Email environment variables not set.")
                print("Please run set_email_env.bat first to configure your email credentials.")
        
        # Import the Flask app
        from server import app
        
        # Run with optimized settings to prevent socket errors
        logger.info("Starting AuthAI server with fixed configuration...")
        app.run(debug=True, 
                threaded=False,    # Prevent socket errors
                use_reloader=False, # Prevent duplicate processes
                port=5000)         # Use fixed port
                
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1) 