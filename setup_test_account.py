import pymongo
from bson import ObjectId
from datetime import datetime

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client.AuthAI
users = db.users

# Test account details
test_user = {
    "_id": ObjectId("67fe5abac0216a01406da0f9"),
    "email": "kpreeti09050@gmail.com",
    "username": "Test User",
    "password": "test123",
    "created_at": datetime.utcnow(),
    "permission_granted": True,
    "face_verified_at": datetime.utcnow()
}

# Delete existing test account if it exists
users.delete_one({"email": "kpreeti09050@gmail.com"})

# Create new test account
result = users.insert_one(test_user)
print(f"Test account created with ID: {result.inserted_id}") 