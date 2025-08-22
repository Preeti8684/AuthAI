import cv2
import numpy as np
import os
import logging
from datetime import datetime
import face_recognition
import pickle
import pymongo
from pymongo import MongoClient
from bson import ObjectId
from skimage.metrics import structural_similarity as ssim

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB connection
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['AuthAI']  # Match the database name with server.py
    users = db['users']    # Match the collection name with server.py
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Error connecting to MongoDB: {str(e)}")
    raise

# Storage for face encodings
try:
    if os.path.exists("face_encodings.p"):
        with open("face_encodings.p", 'rb') as file:
            known_face_encodings = pickle.load(file)
        logger.info(f"Loaded {len(known_face_encodings)} face encodings from file")
    else:
        known_face_encodings = {}
        logger.info("No existing face encodings found, creating new storage")
except Exception as e:
    logger.warning(f"Could not load face encodings: {str(e)}")
    known_face_encodings = {}

def save_face_encodings():
    """Save face encodings to file"""
    try:
        with open("face_encodings.p", 'wb') as file:
            pickle.dump(known_face_encodings, file)
        logger.info(f"Saved {len(known_face_encodings)} face encodings to file")
    except Exception as e:
        logger.error(f"Error saving face encodings: {str(e)}")

def preprocess_image(image):
    """Preprocess image for face recognition"""
    try:
        if image is None:
            return None
            
        # Convert to RGB for face_recognition (it expects RGB)
        if len(image.shape) == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            # Convert grayscale to BGR then to RGB
            rgb_image = cv2.cvtColor(cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2RGB)
        
        return rgb_image
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        return None

def extract_face(image):
    """Extract face from image using face_recognition library"""
    try:
        if image is None:
            logger.error("Input image is None")
            return None, None
            
        # Preprocess image to RGB
        rgb_image = preprocess_image(image)
        if rgb_image is None:
            return None, None
        
        # Use face_recognition library for face detection
        face_locations = face_recognition.face_locations(rgb_image)
        
        if not face_locations:
            logger.warning("No face detected in image")
            return None, None
                
        # Use face_recognition result (top, right, bottom, left)
        top, right, bottom, left = face_locations[0]
        
        # Convert to OpenCV format (x, y, w, h)
        x, y, w, h = left, top, right-left, bottom-top
        face_rect = (x, y, w, h)
        
        # Extract face region
        face_roi = rgb_image[y:y+h, x:x+w]
        
        # Resize to standard size
        face_roi = cv2.resize(face_roi, (200, 200))
        
        return face_roi, face_rect
        
    except Exception as e:
        logger.error(f"Error extracting face: {str(e)}")
        return None, None

def get_face_encoding(image):
    """Get face encoding using face_recognition library"""
    try:
        if image is None:
            return None
            
        # Preprocess to RGB
        rgb_image = preprocess_image(image)
        if rgb_image is None:
            return None
        
        # Detect face locations
        face_locations = face_recognition.face_locations(rgb_image)
        
        if not face_locations:
            logger.warning("No face detected for encoding")
            return None
        
        # Get face encodings
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        if not face_encodings:
            logger.warning("Could not compute face encoding")
            return None
            
        return face_encodings[0]
        
    except Exception as e:
        logger.error(f"Error getting face encoding: {str(e)}")
        return None

def compare_faces(encoding1, encoding2, tolerance=0.6):
    """Compare two face encodings using face_recognition library"""
    try:
        if encoding1 is None or encoding2 is None:
            return False, 0.0
            
        # Calculate face distance
        face_distance = face_recognition.face_distance([encoding1], encoding2)[0]
        
        # Convert face distance to a similarity score (0 means identical, higher values mean more different)
        # We'll convert to a 0-1 scale where 1 is identical and 0 is different
        similarity = 1.0 - min(face_distance, 1.0)
        
        # Check if faces match based on tolerance
        match = face_distance <= tolerance
        
        return match, similarity
        
    except Exception as e:
        logger.error(f"Error comparing faces: {str(e)}")
        return False, 0.0

def compute_additional_similarity(face1, face2):
    """Compute additional similarity metrics as backup"""
    if face1 is None or face2 is None:
        return {'best_score': 0.0, 'method': None, 'scores': {}}
    
    # Convert to grayscale if needed
    if len(face1.shape) == 3:
        gray1 = cv2.cvtColor(face1, cv2.COLOR_RGB2GRAY)
    else:
        gray1 = face1
        
    if len(face2.shape) == 3:
        gray2 = cv2.cvtColor(face2, cv2.COLOR_RGB2GRAY)
    else:
        gray2 = face2
    
    # Resize to same dimensions if needed
    if gray1.shape != gray2.shape:
        gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))
    
    # Results dictionary
    results = {'scores': {}}
    
    try:
        # Method 1: Structural similarity index
        ssim_score, _ = ssim(gray1, gray2, full=True)
        results['scores']['ssim'] = float(ssim_score)
        
        # Method 2: Histogram comparison
        hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
        cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)
        hist_score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        results['scores']['histogram'] = float(hist_score)
        
        # Best score is the maximum of all methods
        best_score = max(ssim_score, hist_score)
        best_method = 'ssim' if ssim_score >= hist_score else 'histogram'
        
        results['best_score'] = best_score
        results['method'] = best_method
        
        return results
    except Exception as e:
        logger.error(f"Error computing additional similarity: {str(e)}")
        return {'best_score': 0.0, 'method': None, 'scores': {}}

def is_face_duplicate(image):
    """Check if a face is already registered by another user."""
    try:
        # Preprocess the image to RGB
        rgb_image = preprocess_image(image)
        if rgb_image is None:
            logger.warning("Could not preprocess image in is_face_duplicate")
            return False, None
            
        # Get face encoding
        encoding = get_face_encoding(rgb_image)
        
        if encoding is None:
            logger.warning("Could not get face encoding in is_face_duplicate")
            return False, None
        
        # Get all users with registered faces
        users_with_faces = users.find({"image_path": {"$exists": True}})
        
        best_match = None
        best_similarity = -1
        threshold = 0.6  # Face recognition tolerance threshold
        
        for user in users_with_faces:
            user_id = str(user["_id"])
            user_image_path = user.get("image_path")
            
            if not user_image_path or not os.path.exists(user_image_path):
                continue
                
            # Load the stored face encoding
            if user_id in known_face_encodings:
                # Use stored encoding
                stored_encoding = known_face_encodings[user_id]
            else:
                # Load and calculate encoding
                stored_image = cv2.imread(user_image_path)
                if stored_image is None:
                    continue
                stored_encoding = get_face_encoding(stored_image)
                if stored_encoding is None:
                    continue
                known_face_encodings[user_id] = stored_encoding
            
            # Compare faces
            match, similarity = compare_faces(stored_encoding, encoding, threshold)
            
            # Update best match if this one is better
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = user.get("username", "Unknown User")
            
        # Save face encodings
        save_face_encodings()
            
        # Check against the threshold
        is_duplicate = best_similarity >= threshold
        
        return is_duplicate, best_match
    except Exception as e:
        logger.error(f"Error checking for duplicate face: {str(e)}")
        return False, None

def save_user_face(image_path, user_id):
    """Save a user's face image for later recognition."""
    try:
        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Could not read image at {image_path}")
            return False
            
        # Get the face encoding
        encoding = get_face_encoding(image)
        if encoding is None:
            logger.error("Could not get face encoding for saving")
            return False
            
        # Create the directory if it doesn't exist
        face_dir = os.path.join("static", "faces")
        os.makedirs(face_dir, exist_ok=True)
        
        # Create the path for the face image
        face_file = os.path.join(face_dir, f"{user_id}.jpg")
        
        # Save the image
        cv2.imwrite(face_file, image)
        
        # Update the user's record with the face image path
        users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"image_path": face_file}}
        )
        
        # Store the face encoding
        known_face_encodings[user_id] = encoding
        save_face_encodings()
        
        logger.info(f"Successfully saved face for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving user face: {str(e)}")
        return False

def verify_face(image_path, stored_image_path, threshold=0.5, align_faces=True, enhance_contrast=True):
    """Verify if the face image matches the stored face."""
    try:
        # Check if paths exist
        if not os.path.exists(image_path):
            logger.error(f"Input image path does not exist: {image_path}")
            return {
                "match": False, 
                "similarity": 0.0, 
                "method": "error",
                "error": "Input image not found"
            }
            
        if not os.path.exists(stored_image_path):
            logger.error(f"Stored image path does not exist: {stored_image_path}")
            return {
                "match": False, 
                "similarity": 0.0, 
                "method": "error",
                "error": "Stored image not found"
            }
        
        # Read the images
        image = cv2.imread(image_path)
        stored_image = cv2.imread(stored_image_path)
        
        if image is None or stored_image is None:
            logger.error("Failed to read one or both images")
            return {
                "match": False, 
                "similarity": 0.0, 
                "method": "error",
                "error": "Failed to read images"
            }
        
        # Extract the user ID from the stored image path
        user_id = os.path.basename(stored_image_path).split('.')[0]
        
        # Get face encodings
        encoding = get_face_encoding(image)
        
        # If encoding fails, return an error
        if encoding is None:
            return {
                "match": False,
                "similarity": 0.0,
                "method": "error",
                "error": "Could not detect face in input image",
                "face_detected": False
            }
        
        # Get stored encoding
        if user_id in known_face_encodings:
            # Use stored encoding
            stored_encoding = known_face_encodings[user_id]
        else:
            # Calculate and store encoding
            stored_encoding = get_face_encoding(stored_image)
            if stored_encoding is None:
                return {
                    "match": False,
                    "similarity": 0.0,
                    "method": "error",
                    "error": "Could not detect face in stored image",
                    "face_detected": True
                }
            known_face_encodings[user_id] = stored_encoding
            save_face_encodings()
        
        # Compare faces
        match, similarity = compare_faces(stored_encoding, encoding, threshold)
        
        # Extract faces for additional similarity methods
        face_roi, _ = extract_face(image)
        stored_face_roi, _ = extract_face(stored_image)
        
        additional_scores = {}
        if face_roi is not None and stored_face_roi is not None:
            additional_metrics = compute_additional_similarity(face_roi, stored_face_roi)
            additional_scores = additional_metrics["scores"]
        
        # Testing mode override - force verification to succeed with high similarity
        # Uncomment for testing ONLY
        #match = True
        #similarity = 0.95
        
        # Ensure similarity is at least 80% for UI display if it's a match
        display_similarity = max(int(similarity * 100), 80) if match else int(similarity * 100)
        
        # Prepare result
        result = {
            "match": match,
            "similarity": similarity,
            "display_similarity": display_similarity,
            "method": "face_recognition",
            "face_detected": True,
            "threshold": threshold,
            "alternative_methods": additional_scores
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error verifying face: {str(e)}")
        return {
            "match": False, 
            "similarity": 0.0, 
            "method": "error",
            "error": str(e),
            "face_detected": False
        } 