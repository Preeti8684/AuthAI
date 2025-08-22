import cv2
import os
from pymongo import MongoClient

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["AuthAI"]
users_collection = db["users"]

IMAGE_FOLDER = "saved_faces"

# Get user input
username = input("Enter your username: ")

user = users_collection.find_one({"username": username})
if not user or not user.get("image_filename"):
    print("No face found for this user.")
    exit()

stored_image_path = os.path.join(IMAGE_FOLDER, user["image_filename"])

if not os.path.exists(stored_image_path):
    print("Face image not found.")
    exit()

# Load and display the image
image = cv2.imread(stored_image_path)
cv2.imshow("Recognized Face", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
