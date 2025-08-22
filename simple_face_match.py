import cv2
import numpy as np
import os
import logging
from datetime import datetime
import pymongo
from pymongo import MongoClient
from bson import ObjectId
from skimage.metrics import structural_similarity as ssim

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize face detection cascade
cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
if not os.path.exists(cascade_path):
    raise Exception(f"Cascade file not found at {cascade_path}")

face_cascade = cv2.CascadeClassifier(cascade_path)
if face_cascade.empty():
    logger.error("Failed to load face detection cascade")
    raise Exception("Failed to load face detection cascade")
logger.info("Successfully loaded face detection cascade")

# Initialize eye detection cascade
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
if eye_cascade.empty():
    logger.warning("Failed to load eye detection cascade - face alignment may be limited")

# Initialize MongoDB connection
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['AuthAI']  # Match the database name with server.py
    users = db['users']    # Match the collection name with server.py
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Error connecting to MongoDB: {str(e)}")
    raise

def preprocess_image(image, normalize_lighting=True, enhance_contrast=False):
    """Enhanced image preprocessing with multiple options."""
    try:
        if image is None:
            return None
            
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply additional preprocessing based on parameters
        if normalize_lighting:
            # Normalize lighting with histogram equalization
            gray = cv2.equalizeHist(gray)
        
        if enhance_contrast:
            # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
        
        return gray
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        return None

def extract_face(image, align_faces=False, enhance_contrast=False, normalize_lighting=True):
    """Extract face from image using cascade classifier."""
    try:
        if image is None:
            logger.error("Input image is None")
            return None
            
        # Preprocess image
        gray = preprocess_image(image, normalize_lighting, enhance_contrast)
        if gray is None:
            return None
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)
                
        if len(faces) == 0:
            logger.warning("No face detected in image")
            return None
            
        # Get the largest face
        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
        (x, y, w, h) = largest_face
        
        # Extract face region
        face_roi = gray[y:y+h, x:x+w]
        
        # Resize to standard size (200x200)
        face_roi = cv2.resize(face_roi, (200, 200))
            
        return face_roi
    except Exception as e:
        logger.error(f"Error extracting face: {str(e)}")
        return None

def compute_similarity(face1, face2):
    """Compute similarity between two face images."""
    try:
        if face1 is None or face2 is None:
            logger.error("One or both faces are None")
            return 0.0
            
        # Ensure both faces are the same size
        face1 = cv2.resize(face1, (200, 200))
        face2 = cv2.resize(face2, (200, 200))
        
        # 1. Template Matching
        template_score = cv2.matchTemplate(face1, face2, cv2.TM_CCOEFF_NORMED)[0][0]
        
        # 2. Structural Similarity Index
        ssim_score = ssim(face1, face2)
        
        # 3. Histogram Comparison
        hist1 = cv2.calcHist([face1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([face2], [0], None, [256], [0, 256])
        cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)
        hist_score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        # Take the best score
        best_score = max(float(template_score), float(ssim_score), float(hist_score))
        return best_score
    except Exception as e:
        logger.error(f"Error computing similarity: {str(e)}")
        return 0.0

def is_face_duplicate(image):
    """Check if face is duplicate of any registered user."""
    try:
        # Extract face from input image
        input_face = extract_face(image, enhance_contrast=True)
        if input_face is None:
            logger.warning("No face detected in input image")
            return False, None
        
        # Get all registered users
        registered_users = users.find({"image_path": {"$exists": True}})
        
        # Lower threshold for better matching
        threshold = 0.05
        best_match = None
        best_similarity = 0.0
        
        for user in registered_users:
            image_path = user.get('image_path')
            if image_path and os.path.exists(image_path):
                try:
                    registered_image = cv2.imread(image_path)
                    if registered_image is None:
                        logger.warning(f"Could not read image at {image_path}")
                        continue
                        
                    registered_face = extract_face(registered_image, enhance_contrast=True)
                    if registered_face is None:
                        continue
                    
                    # Compute similarity
                    similarity = compute_similarity(input_face, registered_face)
                    
                    logger.info(f"Face similarity with user {user.get('username')}: {similarity}")
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = user
                    
                    if similarity > threshold:
                        user_info = user.get('username', 'Unknown')
                        if user.get('email'):
                            user_info = f"{user_info} ({user.get('email')})"
                        return True, user_info
                except Exception as e:
                    logger.error(f"Error processing registered face: {str(e)}")
                    continue
        
        # If we get here, no match above threshold was found
        if best_match:
            logger.info(f"Best match was user {best_match.get('username')} with similarity {best_similarity}, but below threshold {threshold}")
            
        return False, None
    except Exception as e:
        logger.error(f"Error checking for duplicate face: {str(e)}")
        return False, None

def save_user_face(image_path, user_id):
    """Save user's face image."""
    try:
        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Failed to read image from {image_path}")
            return False
        
        # Extract face
        face = extract_face(image, enhance_contrast=True)
        if face is None:
            logger.error("No face detected in image")
            return False
        
        # Create the faces directory if it doesn't exist
        os.makedirs("static/faces", exist_ok=True)
        
        # Save processed face image
        output_path = os.path.join("static/faces", f"{user_id}.jpg")
        success = cv2.imwrite(output_path, face)
        
        if not success:
            logger.error("Failed to save face image")
            return False
        
        # Update user record with the relative path
        try:
            users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"image_path": output_path}}
            )
            logger.info(f"Successfully saved face for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update user record: {str(e)}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
            
    except Exception as e:
        logger.error(f"Error saving user face: {str(e)}")
        return False

def verify_face(image_path, stored_image_path, threshold=0.05, align_faces=True, enhance_contrast=True):
    """Verify if the face image matches the stored face."""
    try:
        # Check if paths exist
        if not os.path.exists(image_path):
            logger.error(f"Input image path does not exist: {image_path}")
            return {
                "match": False,
                "face_detected": False,
                "error": "Input image not found"
            }
            
        if not os.path.exists(stored_image_path):
            logger.error(f"Stored image path does not exist: {stored_image_path}")
            return {
                "match": False,
                "face_detected": False,
                "error": "Stored image not found"
            }
        
        # Read the images
        image = cv2.imread(image_path)
        stored_image = cv2.imread(stored_image_path)
        
        if image is None or stored_image is None:
            logger.error("Failed to read one or both images")
            return {
                "match": False,
                "face_detected": False,
                "error": "Failed to read images"
            }
        
        # Extract faces with preprocessing
        input_face = extract_face(
            image, 
            align_faces=align_faces, 
            enhance_contrast=enhance_contrast,
            normalize_lighting=True
        )
        stored_face = extract_face(
            stored_image, 
            align_faces=align_faces, 
            enhance_contrast=enhance_contrast,
            normalize_lighting=True
        )
        
        if input_face is None:
            logger.error("No face detected in input image")
            return {
                "match": False,
                "face_detected": False,
                "error": "No face detected in input image"
            }
        
        if stored_face is None:
            logger.error("No face detected in stored image")
            return {
                "match": False,
                "face_detected": False,
                "error": "No face detected in stored image"
            }
        
        # Compute similarity with multiple metrics
        similarity = compute_similarity(input_face, stored_face)
        logger.info(f"Face similarity: {similarity}, threshold: {threshold}")
        
        # Determine if there's a match
        is_match = bool(similarity >= threshold)
        
        # For display purposes, scale similarity to percentage
        display_similarity = min(100, max(0, similarity * 100))
        
        result = {
            "match": is_match,
            "face_detected": True,
            "similarity": float(similarity),
            "display_similarity": int(display_similarity),
            "threshold": float(threshold)
        }
        
        logger.info(f"Verification result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error verifying face: {str(e)}")
        return {
            "match": False,
            "face_detected": False,
            "error": str(e)
        }