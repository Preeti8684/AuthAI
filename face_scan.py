import cv2
import os
from pymongo import MongoClient

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["AuthAI"]
users_collection = db["users"]

IMAGE_FOLDER = "saved_faces"
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# Get user input
username = input("Enter your username: ")

user = users_collection.find_one({"username": username})
if not user:
    print("User not found. Please sign up first.")
    exit()

# Capture image
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
cap.release()

if not ret:
    print("Failed to capture image")
    exit()

image_filename = f"{username}.jpg"
image_path = os.path.join(IMAGE_FOLDER, image_filename)

# Save image
cv2.imwrite(image_path, frame)

# Check if the face is already registered with a different name
existing_user = users_collection.find_one({"image_filename": image_filename})
if existing_user and existing_user["username"] != username:
    print(f"This face is already registered with {existing_user['username']}")
    exit()

# Update MongoDB with image filename
users_collection.update_one({"username": username}, {"$set": {"image_filename": image_filename}})

print("Face scanned and stored successfully.")
