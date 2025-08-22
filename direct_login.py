import pymongo
from bson import ObjectId
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Connect to MongoDB
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client.AuthAI
    users = db.users
    
    # Test account details
    test_user_id = ObjectId("67fe5abac0216a01406da0f9")
    
    # Create or update test account, making sure it has image_path but no face_verified_at
    result = users.update_one(
        {"_id": test_user_id},
        {
            "$set": {
                "email": "kpreeti09050@gmail.com",
                "username": "Test User",
                "password": "test123",
                "created_at": datetime.utcnow(),
                "permission_granted": True,
                "image_path": "static/faces/user_67fe5abac0216a01406da0f9.jpg"
            },
            "$unset": {"face_verified_at": ""}  # Remove face verification timestamp
        },
        upsert=True
    )
    
    # Check if an image file exists for this user, and create one if it doesn't
    import os
    import shutil
    
    image_path = "static/faces/user_67fe5abac0216a01406da0f9.jpg"
    if not os.path.exists(image_path):
        # Create the directory if it doesn't exist
        os.makedirs("static/faces", exist_ok=True)
        
        # Use a sample image or create a blank one
        try:
            # Try to use the first image from static/faces if any exists
            face_images = [f for f in os.listdir("static/faces") if f.endswith(('.jpg', '.jpeg', '.png'))]
            if face_images:
                sample_image = os.path.join("static/faces", face_images[0])
                shutil.copy(sample_image, image_path)
                logger.info(f"Copied sample image {sample_image} to {image_path}")
            else:
                # Create a blank image
                import cv2
                import numpy as np
                blank_image = np.ones((300, 300, 3), np.uint8) * 255
                cv2.imwrite(image_path, blank_image)
                logger.info(f"Created blank image at {image_path}")
        except Exception as e:
            logger.error(f"Error creating sample image: {e}")
    
    logger.info(f"Test account updated: {result.modified_count} document(s) modified, {result.upserted_id} upserted ID")
    logger.info("Now please restart your Flask server and login with:")
    logger.info("Email: kpreeti09050@gmail.com")
    logger.info("Password: test123")
    logger.info("This will redirect you to face recognition instead of dashboard")
except Exception as e:
    logger.error(f"Error: {e}") 