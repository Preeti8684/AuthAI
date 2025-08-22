"""
Fix Login Redirect Script for AuthAI

This script will modify the login_direct route to redirect to face_recognize.
"""

import os

def fix_login_redirect():
    # Path to server.py
    server_file = 'server.py'
    
    # Read the file
    with open(server_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all instances of redirect to dashboard and change to face_recognize
    content = content.replace('redirect(url_for("dashboard"))', 'redirect(url_for("face_recognize"))')
    content = content.replace('"redirect": url_for("dashboard")', '"redirect": url_for("face_recognize")')
    
    # Write the modified content back
    with open(server_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Successfully changed dashboard redirects to face_recognize!")
    
    # Also update the test account to force face recognition
    print("Now updating test account in MongoDB...")
    
    # Import MongoDB libraries
    import pymongo
    from bson import ObjectId
    from datetime import datetime
    
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
        
        # Create image path if it doesn't exist
        import os
        import cv2
        import numpy as np
        
        image_path = "static/faces/user_67fe5abac0216a01406da0f9.jpg"
        if not os.path.exists(image_path):
            # Create directory if needed
            os.makedirs("static/faces", exist_ok=True)
            
            # Create a blank image for testing
            blank_image = np.ones((300, 300, 3), np.uint8) * 255
            cv2.imwrite(image_path, blank_image)
            print(f"Created blank image at {image_path}")
        
        print(f"MongoDB test account updated: {result.modified_count} document(s) modified")
        print("\nNow restart your Flask server and try logging in again!")
        print("Email: kpreeti09050@gmail.com")
        print("Password: test123")
        
    except Exception as e:
        print(f"Error updating MongoDB: {e}")

if __name__ == "__main__":
    fix_login_redirect() 