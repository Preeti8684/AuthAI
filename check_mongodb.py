import subprocess
import time
import sys
import pymongo
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_mongodb_running():
    """Check if MongoDB is running by attempting to connect."""
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.server_info()  # Will raise an exception if not connected
        logger.info("MongoDB is running")
        return True
    except Exception as e:
        logger.warning(f"MongoDB is not running: {e}")
        return False

def start_mongodb():
    """Start MongoDB service."""
    try:
        if sys.platform.startswith('win'):
            # For Windows
            subprocess.run(['net', 'start', 'MongoDB'], check=True)
        else:
            # For Unix-like systems
            subprocess.run(['sudo', 'service', 'mongodb', 'start'], check=True)
        logger.info("MongoDB service started")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start MongoDB service: {e}")
        return False

def main():
    """Main function to check and start MongoDB."""
    if is_mongodb_running():
        return True

    logger.info("Attempting to start MongoDB...")
    if not start_mongodb():
        logger.error("Failed to start MongoDB service")
        return False

    # Wait for MongoDB to start
    max_attempts = 10
    attempt = 0
    while attempt < max_attempts:
        if is_mongodb_running():
            logger.info("MongoDB is now running")
            return True
        time.sleep(1)
        attempt += 1

    logger.error("MongoDB failed to start after multiple attempts")
    return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1) 