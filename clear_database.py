import pymongo
import os
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_database():
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["authai"]
        
        # Clear all collections
        db.users.delete_many({})
        db.activities.delete_many({})
        logger.info("Successfully cleared all database collections")

        # Clear face images directory
        faces_dir = "static/faces"
        if os.path.exists(faces_dir):
            shutil.rmtree(faces_dir)
            os.makedirs(faces_dir)
            logger.info("Successfully cleared face images directory")
        else:
            os.makedirs(faces_dir)
            logger.info("Created face images directory")

    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        raise

if __name__ == "__main__":
    clear_database()
    print("Database and face images cleared successfully!") 