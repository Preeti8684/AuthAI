from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, flash
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import pymongo
import os
import bcrypt
from simple_face_match import is_face_duplicate, save_user_face, verify_face as face_verify
from datetime import timedelta, datetime
import logging
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import cv2
import numpy as np
import pyotp
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import functools
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add this after the imports but before the app configuration
def permission_required(f):
    """Decorator to check if the user has granted permission to access the app."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
            
        # Skip permission check - automatically grant permission
        user = users.find_one({"_id": ObjectId(session["user_id"])})
        if not user:
            session.clear()
            return redirect(url_for("login"))
            
        # Auto-set permission in session
        session["permission_granted"] = True
            
        # Proceed with the original function
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')
app.permanent_session_lifetime = timedelta(minutes=30)

# Initialize CSRF protection (disabled for forms/views while testing)
csrf = CSRFProtect()
csrf.init_app(app)
app.config['WTF_CSRF_ENABLED'] = False

# Provide a safe csrf_token helper for templates that reference it
@app.context_processor
def inject_csrf_token():
    def csrf_token():
        return ""
    return dict(csrf_token=csrf_token)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Fixed rate limiter configuration

# MongoDB connection (Render/Atlas friendly)
try:
    mongo_uri = os.environ.get("MONGODB_URI")
    if mongo_uri:
        client = pymongo.MongoClient(mongo_uri)
        db = client.get_default_database() or client["AuthAI"]
    else:
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client.AuthAI

    users = db.users
    activities = db.activities

    # Create indexes for better performance (safe on Atlas/local)
    try:
        users.create_index("email", unique=True)
        activities.create_index([("user_email", 1), ("timestamp", -1)])
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")

    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# Create upload folder
UPLOAD_FOLDER = "static/faces"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
# Get credentials from environment or default to placeholders
SMTP_USERNAME = os.environ.get("EMAIL_USERNAME", "preeti8684093365@gmail.com")
SMTP_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")

if not SMTP_PASSWORD:
    logger.warning("Email password not set! Permission emails will fail. Set EMAIL_PASSWORD environment variable.")

def log_activity(user_email, activity_type, details=None):
    """Log user activity to the database."""
    try:
        activities.insert_one({
            "user_email": user_email,
            "activity_type": activity_type,
            "details": details,
            "timestamp": datetime.utcnow()
        })
    except Exception as e:
        logger.error(f"Error logging activity: {e}")

def send_email(to_email, subject, body):
    """No-op email sender for testing: do not send emails."""
    logger.info(f"[EMAIL DISABLED] Skipping email to {to_email} with subject '{subject}'")
    return True

def generate_2fa_code():
    """Generate a 6-digit 2FA code."""
    return pyotp.random_base32()

def generate_recovery_codes():
    """Generate recovery codes for 2FA backup."""
    return [secrets.token_urlsafe(8)[:10] for _ in range(8)]

@app.route("/")
def index():
    """Home page with landing content."""
    # Always show home page, even if user is logged in
    return render_template("home.html")

@app.route("/dashboard")
def dashboard():
    """Dashboard page for authenticated users."""
    if "user_id" not in session:
        logger.info("Dashboard access attempted without user_id in session")
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    logger.info(f"Dashboard access for user_id: {user_id}")
    logger.info(f"Session data: pic_name='{session.get('pic_name', 'None')}', face_verified_at='{session.get('face_verified_at', 'None')}'")
    
    try:
        user = users.find_one({"_id": ObjectId(user_id)})
        if not user:
            logger.error(f"User not found for ID: {user_id}")
            session.clear()
            return redirect(url_for("login"))
        
        logger.info(f"User data from DB: username='{user.get('username', 'None')}', image_name='{user.get('image_name', 'None')}'")
    
        # Check if permission is granted and set in session
        if "permission_granted" in user:
            session["permission_granted"] = user["permission_granted"]
        
        # Check if face verification has been completed
        # If not, redirect to face_recognize
        if not user.get("face_verified_at"):
            logger.info(f"User {user_id} has not completed face verification, redirecting")
            return redirect(url_for("face_recognize"))
    
        # Get recent activities
        try:
            recent_activities = list(activities.find(
                {"user_email": user_id}
            ).sort("timestamp", -1).limit(5))
        except Exception as e:
            logger.error(f"Error fetching activities: {str(e)}")
            recent_activities = []
        
        logger.info(f"Rendering dashboard for user: {user.get('username', 'User')}")
        return render_template("dashboard.html", 
                             username=user.get("username", "User"),
                             email=user.get("email", ""),
                             image_path=user.get("image_path", ""),
                             recent_activities=recent_activities)
    except Exception as e:
        logger.error(f"Error in dashboard: {str(e)}")
        session.clear()
        return redirect(url_for("login"))

@app.route("/profile")
def profile():
    """Profile page for authenticated users."""
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user = users.find_one({"_id": ObjectId(session["user_id"])})
    if not user:
        session.clear()
        return redirect(url_for("login"))
    
    # Get all activities for the user
    user_activities = list(activities.find(
        {"user_email": session["user_id"]}
    ).sort("timestamp", -1))
        
    return render_template("profile.html", 
                         username=user.get("username", "User"),
                         email=user.get("email", ""),
                         image_path=user.get("image_path", ""),
                         activities=user_activities)

@app.route("/settings")
def settings():
    """Settings page for authenticated users."""
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user = users.find_one({"_id": ObjectId(session["user_id"])})
    if not user:
        session.clear()
        return redirect(url_for("login"))
        
    return render_template("settings.html", user=user)

@app.route("/update_profile", methods=["POST"])
def update_profile():
    """Update user profile information."""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        username = request.form.get("username", "").strip()
        if not username:
            return jsonify({"success": False, "message": "Username is required"})
            
        users.update_one(
            {"_id": session["user_id"]},
            {"$set": {"username": username}}
        )
        
        session["username"] = username
        log_activity(session["user_id"], "profile_update", {"username": username})
        return jsonify({"success": True, "message": "Profile updated successfully"})
        
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return jsonify({"success": False, "message": "Error updating profile"}), 500

@app.route("/change_password", methods=["POST"])
def change_password():
    """Change user password."""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        
        if not current_password or not new_password:
            return jsonify({"success": False, "message": "All fields are required"})
            
        user = users.find_one({"_id": session["user_id"]})
        if not user:
            return jsonify({"success": False, "message": "User not found"})
            
        if not bcrypt.checkpw(current_password.encode('utf-8'), user["password"].encode('utf-8')):
            return jsonify({"success": False, "message": "Current password is incorrect"})
            
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        users.update_one(
            {"_id": session["user_id"]},
            {"$set": {"password": hashed_password.decode('utf-8')}}
        )
        
        log_activity(session["user_id"], "password_change")
        return jsonify({"success": True, "message": "Password changed successfully"})
        
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        return jsonify({"success": False, "message": "Error changing password"}), 500

@app.route("/delete_account", methods=["POST"])
def delete_account():
    """Delete user account."""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        password = request.form.get("password")
        if not password:
            return jsonify({"success": False, "message": "Password is required"})
            
        user = users.find_one({"_id": session["user_id"]})
        if not user:
            return jsonify({"success": False, "message": "User not found"})
            
        if not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
            return jsonify({"success": False, "message": "Password is incorrect"})
            
        # Delete user's face image if exists
        if user.get("image_path") and os.path.exists(user["image_path"]):
            os.remove(user["image_path"])
            
        # Delete user's activities
        activities.delete_many({"user_email": session["user_id"]})
            
        # Delete user from database
        users.delete_one({"_id": session["user_id"]})
        
        # Clear session
        session.clear()
        
        return jsonify({"success": True, "message": "Account deleted successfully"})
        
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        return jsonify({"success": False, "message": "Error deleting account"}), 500

@app.route("/get_image/<path:filename>")
def get_image(filename):
    """Serve user's profile image."""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
        
    try:
        return send_file(filename)
    except Exception as e:
        logger.error(f"Error serving image: {e}")
        return jsonify({"success": False, "message": "Error serving image"}), 404

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    try:
        # Get form data
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        pic_name = request.form.get("pic_name", "").strip()

        # Input validation
        if not all([name, email, password, pic_name]):
            flash("All fields are required!", "error")
            return render_template("signup.html")
            
        if not "@" in email or not "." in email:
            flash("Please enter a valid email address!", "error")
            return render_template("signup.html")

        # Check if email already exists
        if users.find_one({"email": email}):
            flash("Email already registered!", "error")
            return render_template("signup.html")

        # Hash password and create user
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_id = ObjectId()  # Generate a new ObjectId
        
        new_user = {
            "_id": user_id,
            "username": name,
            "email": email,
            "password": hashed_password.decode('utf-8'),
            "image_name": pic_name,
            "created_at": datetime.utcnow()
        }
        
        users.insert_one(new_user)

        # Set the user created message
        flash("Account created successfully! Please login with your credentials.", "success")
        
        # Redirect to login page after signup
        return redirect(url_for('login'))

    except Exception as e:
        logger.error(f"Signup error: {e}")
        flash("An error occurred during signup!", "error")
        return render_template("signup.html")

@csrf.exempt
@app.route("/face_login", methods=["GET"])
def face_login_page():
    """Serve the face login page."""
    return render_template("face_login.html")

@csrf.exempt
@app.route("/login", methods=["GET", "POST"])
@limiter.exempt  # Remove rate limiting from login to make testing easier
def login():
    """Handle user login."""
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password", "")
        
        logger.info(f"Login attempt for email: {email}")
        
        # Special case for test account
        if email == "kpreeti09050@gmail.com":
            # Look up the actual user in database
            user = users.find_one({"email": email})
            if user:
                session.permanent = True
                session["user_id"] = str(user["_id"])
                session["email"] = email
                session["username"] = user.get("username", "User")
                session["permission_granted"] = True
                
                logger.info(f"Test account login successful for {email}")
                # Redirect directly to face recognition
                return redirect(url_for("face_recognize"))
            else:
                logger.error(f"Test account {email} not found in database")
                flash("Test account not found in database", "error")
                return render_template("login.html")
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if not email or not password:
            logger.warning("Login attempt with missing email or password")
            error_msg = "Please enter both email and password."
            if is_ajax:
                return jsonify({"success": False, "message": error_msg})
            flash(error_msg, "error")
            return render_template("login.html")
        
        try:
            # Look for user in database (case-insensitive email search)
            user = users.find_one({"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}})
            logger.info(f"User lookup result for {email}: {user is not None}")
            
            if not user:
                logger.warning(f"No user found with email: {email}")
                error_msg = "Invalid email or password."
                if is_ajax:
                    return jsonify({"success": False, "message": error_msg})
                flash(error_msg, "error")
                return render_template("login.html")
            
            # For regular users, verify password
            try:
                password_matches = bcrypt.checkpw(
                    password.encode('utf-8'),
                    user["password"].encode('utf-8')
                )
            except Exception as e:
                logger.error(f"Error checking password for {email}: {str(e)}")
                password_matches = False
            
            if not password_matches:
                logger.warning(f"Invalid password for user: {email}")
                error_msg = "Invalid email or password."
                if is_ajax:
                    return jsonify({"success": False, "message": error_msg})
                flash(error_msg, "error")
                return render_template("login.html")
            
            # Set session data
            session.permanent = True
            session["user_id"] = str(user["_id"])
            session["email"] = user["email"]
            logger.info(f"Login successful for {email}")
            
            # Log successful login
            log_activity(user["email"], "login_success")
            
            # Redirect to face_recognize instead of dashboard  
            return redirect(url_for("face_recognize"))
            
        except Exception as e:
            logger.error(f"Error during login for {email}: {str(e)}")
            error_msg = "An error occurred during login. Please try again."
            if is_ajax:
                return jsonify({"success": False, "message": error_msg})
            flash(error_msg, "error")
            return render_template("login.html")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    if "user_id" in session:
        user_id = session["user_id"]
        try:
            # Get user data before deletion for logging
            user = users.find_one({"_id": ObjectId(user_id)})
            
            if user:
                # Delete user's face image if exists
                if user.get("image_path") and os.path.exists(user.get("image_path")):
                    try:
                        os.remove(user.get("image_path"))
                        logger.info(f"Deleted face image for user {user_id}")
                    except Exception as e:
                        logger.error(f"Error deleting face image: {str(e)}")
                
                # Delete user's activity logs
                activities.delete_many({"user_email": user_id})
                logger.info(f"Deleted activity logs for user {user_id}")
                
                # Delete user record
                users.delete_one({"_id": ObjectId(user_id)})
                logger.info(f"Deleted user {user_id} from database")
                
                log_activity("system", "user_deleted", {"deleted_user_id": user_id})
        
        except Exception as e:
            logger.error(f"Error deleting user data during logout: {str(e)}")
    
    # Clear the session regardless of whether deletion succeeded
    session.clear()
    return redirect(url_for("login"))

@csrf.exempt
@app.route("/face_scan", methods=["GET", "POST"])
@limiter.exempt  # Exempt this route from rate limiting
def face_scan():
    """Handle face scanning and image upload."""
    if "user_id" not in session:
        logger.warning("Attempted to access face_scan without being logged in")
        flash("Please sign up or log in first!", "error")
        return redirect(url_for('login'))

    user_id = session["user_id"]
    logger.info(f"Processing face_scan for user: {user_id}")

    if request.method == "GET":
        try:
            user = users.find_one({"_id": ObjectId(user_id)})
            if not user:
                logger.error(f"User not found for ID: {user_id} in face_scan")
                session.clear()
                return redirect(url_for("login"))
                
            logger.info(f"Rendering face_scan template for user: {user.get('username', 'Unknown')}")
            return render_template("face_scan.html", current_user=user)
        except Exception as e:
            logger.error(f"Error in face_scan GET: {str(e)}")
            session.clear()
            return redirect(url_for("login"))

    try:
        # Handle image upload
        if 'image' not in request.files:
            logger.warning("No image file provided in face_scan")
            return jsonify({"success": False, "message": "No image file provided"})
        
        file = request.files['image']
        
        if file.filename == '':
            logger.warning("Empty filename in face_scan")
            return jsonify({"success": False, "message": "No selected file"})
        
        # Get pic_name from form data if provided
        pic_name = request.form.get("pic_name", "").strip()
            
        # Generate a unique filename
        file_path = os.path.join(UPLOAD_FOLDER, f"user_{user_id}.jpg")
        
        # Save the image to a temporary location first for duplicate checking
        temp_file_path = os.path.join(UPLOAD_FOLDER, f"temp_check_{user_id}.jpg")
        file.save(temp_file_path)
        
        # Check if this face is a duplicate of any other user's face
        try:
            is_duplicate, duplicate_user = is_face_duplicate(temp_file_path)
            
            if is_duplicate:
                # Remove the temporary file
                os.remove(temp_file_path)
                
                # Get the duplicate user's details
                duplicate_user_info = users.find_one({"_id": ObjectId(duplicate_user)})
                duplicate_name = duplicate_user_info.get("image_name", "another user") if duplicate_user_info else "another user"
                
                logger.warning(f"Face duplicate detected: User {user_id} attempted to register a face similar to {duplicate_user}")
                return jsonify({
                    "success": False,
                    "message": f"This face appears to be already registered by '{duplicate_name}'. Please try again with a different face image.",
                    "duplicate": True
                })
        except Exception as e:
            logger.error(f"Error during face duplicate check: {str(e)}")
            # Continue with registration if the duplicate check fails
        
        # If not a duplicate, move from temp to final location
        try:
            os.rename(temp_file_path, file_path)
        except Exception as e:
            # If rename fails, try copy and delete
            import shutil
            shutil.copy(temp_file_path, file_path)
            os.remove(temp_file_path)
        
        logger.info(f"Saved user face image to {file_path}")
        
        # Update user record with image path and pic_name
        update_data = {"image_path": file_path}
        if pic_name:
            update_data["image_name"] = pic_name
            logger.info(f"Saved pic_name '{pic_name}' for user {user_id}")
            # Also save to session
            session["pic_name"] = pic_name
            
        users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        # Log this activity
        log_activity(user_id, "face_registered")
        logger.info(f"Face registered for user: {user_id}")
        
        # Include pic_name in the response if provided
        response_data = {
            "success": True,
            "message": "Your face has been registered successfully. You can now use face recognition for login.",
            "redirect": url_for('face_recognize')
        }
        
        if pic_name:
            response_data["pic_name"] = pic_name
            
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error in face scanning: {str(e)}")
        return jsonify({"success": False, "message": f"Error processing image: {str(e)}"})

@csrf.exempt
@app.route('/verify_face', methods=['POST'])
@permission_required
def verify_face():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        # Get current user and check registered face
        user_id = session['user_id']
        user = users.find_one({"_id": ObjectId(user_id)})
        
        if not user or not user.get('image_path'):
            return jsonify({
                'success': False, 
                'message': 'No registered face found',
                'error': 'no_registered_face'
            })
            
        stored_image_path = user.get('image_path')
        if not os.path.exists(stored_image_path):
            return jsonify({
                'success': False, 
                'message': 'Registered face image not found',
                'error': 'image_not_found'
            })
        
        # Get image data from request
        image_data = request.files.get('face_image')
        if not image_data:
            return jsonify({
                'success': False, 
                'message': 'No image provided',
                'error': 'no_image'
            })
        
        # Save the image temporarily
        temp_path = os.path.join(UPLOAD_FOLDER, "temp_verify.jpg")
        image_data.save(temp_path)
        
        try:
            # Use the enhanced face_match.py verify_face function
            verification_result = face_verify(
                image_path=temp_path,
                stored_image_path=stored_image_path,
                threshold=0.05,  # Very low threshold for easier matching
                align_faces=True,
                enhance_contrast=True
            )
            
            # Add user details to the response
            if verification_result.get('match', False):
                verification_result['username'] = user.get('username', 'User')
                verification_result['email'] = user.get('email', '')
            
            # Log the verification attempt
            log_data = {
                "status": "success" if verification_result.get('match', False) else "failed",
                "similarity": verification_result.get('similarity'),
                "method": verification_result.get('method'),
                "username": user.get('username', 'User')
            }
            log_activity(user_id, "face_verification", log_data)
            
            # Return the detailed verification results
            return jsonify(verification_result)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    logger.error(f"Error removing temporary file: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error verifying face: {str(e)}")
        # Clean up temporary file if it exists
        temp_path = os.path.join(UPLOAD_FOLDER, "temp_verify.jpg")
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return jsonify({
            'success': False, 
            'message': 'An error occurred during verification',
            'error': 'verification_error'
        })

@app.route("/delete_face", methods=["POST"])
def delete_face():
    """Delete user's face image."""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        
        if str(user_id) != str(session["user_id"]):
            return jsonify({"success": False, "message": "Unauthorized to delete this face image"}), 403
            
        user = users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"success": False, "message": "User not found"})
            
        # Delete face image if exists
        if user.get("image_path") and os.path.exists(user["image_path"]):
            os.remove(user["image_path"])
            
        # Update user record
        users.update_one(
            {"_id": ObjectId(user_id)},
            {"$unset": {"image_path": ""}}
        )
        
        log_activity(session["user_id"], "face_delete")
        return jsonify({
            "success": True,
            "message": "Face image deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Error deleting face: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An error occurred while deleting the face image"
        }), 500

@csrf.exempt
@app.route("/face_recognize", methods=["GET", "POST"])
@limiter.exempt  # Exempt this route from rate limiting
def face_recognize():
    """Handle face recognition."""
    if "user_id" not in session:
        logger.error("face_recognize called without user_id in session")
        return redirect(url_for("login"))
        
    # Get the user ID from session
    user_id = session["user_id"]
    logger.info(f"Processing face_recognize for user_id: {user_id}")

    if request.method == "GET":
        try:
            # Get user information
            user = users.find_one({"_id": ObjectId(user_id)})
            if not user:
                logger.error(f"User not found for ID: {user_id}")
                session.clear()
                return redirect(url_for("login"))
        
            # Check if user has a registered face image
            has_face = bool(user.get("image_path"))
            logger.info(f"User {user.get('username')} has_face={has_face}")
            
            # Return the face recognition template
            return render_template("face_recognize.html", current_user=user, has_registered_face=has_face)
        except Exception as e:
            logger.error(f"Error in face_recognize GET: {str(e)}")
            session.clear()
            return redirect(url_for("login"))
        
    try:
        # Handle POST request
        logger.info(f"Processing face_recognize POST for user: {user_id}")
        
        # Get the user
        try:
            user = users.find_one({"_id": ObjectId(user_id)})
            if not user:
                logger.error(f"User not found in POST: {user_id}")
                return jsonify({"success": False, "message": "User not found"}), 404
        except Exception as e:
            logger.error(f"Error finding user in POST: {str(e)}")
            return jsonify({"success": False, "message": "Error finding user"}), 500
            
        # Check if a pic_name was provided directly in the form
        form_pic_name = request.form.get("pic_name", "").strip()
        if form_pic_name:
            logger.info(f"Found pic_name in form: '{form_pic_name}'")
        
        if 'image' not in request.files:
            logger.error("No image file provided in request")
            return jsonify({"success": False, "message": "No image file provided"}), 400
            
        file = request.files['image']
        
        if file.filename == '':
            logger.error("Empty filename in request")
            return jsonify({"success": False, "message": "No selected file"}), 400

        # Create a temporary file path
        temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{user_id}.jpg")
        
        try:
            # Save the file temporarily
            file.save(temp_path)
            logger.info(f"Saved temporary file to {temp_path}")
            
            # Check if user already has a registered face
            user = users.find_one({"_id": ObjectId(user_id)})
            has_registered_face = bool(user.get("image_path") and os.path.exists(user.get("image_path")))
            
            if has_registered_face:
                # User has a registered face - VERIFY against it
                logger.info(f"User has registered face, performing verification")
                
                # Get the stored face path
                stored_face_path = user.get("image_path")
                
                # Verify the new image against stored face
                verification_result = face_verify(temp_path, stored_face_path, threshold=0.05)
                
                if verification_result.get("match", False):
                    # Face matches - update verification timestamp
                    verification_time = datetime.utcnow()
                    
                    # Update user with verification timestamp
                    users.update_one(
                        {"_id": ObjectId(user_id)},
                        {"$set": {
                            "face_verified_at": verification_time
                        }}
                    )
                    
                    # Set session data
                    session["face_verified_at"] = verification_time.strftime("%Y-%m-%d %H:%M:%S")
                    if user.get("image_name"):
                        session["pic_name"] = user.get("image_name")
                    
                    # Clean up temp file
                    os.remove(temp_path)
                    
                    log_activity(str(user_id), "face_verification_successful")
                    logger.info(f"Face verification successful for user {user.get('username', 'User')}")
                    
                    return jsonify({
                        "success": True,
                        "name": user.get("username", "User"),
                        "pic_name": user.get("image_name", ""),
                        "message": "Face verification successful! Redirecting to dashboard...",
                        "redirect": url_for('dashboard')
                    })
                else:
                    # Face doesn't match
                    os.remove(temp_path)
                    logger.warning(f"Face verification failed for user {user.get('username', 'User')}")
                    
                    return jsonify({
                        "success": False,
                        "message": "Face verification failed. The face doesn't match your registered face. Please try again.",
                        "similarity": verification_result.get("display_similarity", 0)
                    }), 400
            else:
                # User doesn't have a registered face - REGISTER it
                logger.info(f"User has no registered face, performing registration")
                
                file_path = os.path.join(UPLOAD_FOLDER, f"user_{user_id}.jpg")
                
                # Save a copy as the registered face
                import shutil
                shutil.copy2(temp_path, file_path)
                
                # Get current time for verification timestamp
                verification_time = datetime.utcnow()
                
                # Check for pic_name in request form
                form_pic_name = request.form.get("pic_name", "").strip()
                if form_pic_name:
                    logger.info(f"Found pic_name in form: '{form_pic_name}'")
                    # Update user with pic_name from form
                    users.update_one(
                        {"_id": ObjectId(user_id)},
                        {"$set": {
                            "image_path": file_path,
                            "face_verified_at": verification_time,
                            "image_name": form_pic_name
                        }}
                    )
                    # Also set in session
                    session["pic_name"] = form_pic_name
                else:
                    # Update user record without changing pic_name
                    users.update_one(
                        {"_id": ObjectId(user_id)},
                        {"$set": {
                            "image_path": file_path,
                            "face_verified_at": verification_time
                        }}
                    )
                
                # Reload user to get fresh data
                user = users.find_one({"_id": ObjectId(user_id)})
                
                log_activity(str(user_id), "face_registered")
                logger.info(f"Face registered for user {user.get('username', 'User')}")
                
                # Store face verification info in session for welcome message on dashboard
                pic_name = user.get("image_name", "")
                username = user.get("username", "User")
                
                logger.info(f"User data - username: '{username}', pic_name: '{pic_name}'")
                
                session["face_verified_at"] = verification_time.strftime("%Y-%m-%d %H:%M:%S")
                
                if pic_name:
                    session["pic_name"] = pic_name
                    logger.info(f"Set session pic_name to '{pic_name}'")
                
                # Clean up temp file
                os.remove(temp_path)
                
                # Return success response with pic_name and username
                return jsonify({
                    "success": True,
                    "name": username,
                    "pic_name": pic_name or session.get("pic_name", ""),
                    "message": "Face registration successful! Redirecting to dashboard...",
                    "redirect": url_for('dashboard')
                })
                
        except Exception as e:
            logger.error(f"Error processing face image: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"Error processing face image: {str(e)}. Please try again."
            }), 500
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.info(f"Removed temporary file {temp_path}")
                except Exception as e:
                    logger.error(f"Error removing temporary file: {str(e)}")

    except Exception as e:
        logger.error(f"Face recognition error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"An error occurred during face recognition: {str(e)}. Please try again."
        }), 500

@app.route("/two_factor")
def two_factor():
    """Two-Factor Authentication settings page."""
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user = users.find_one({"_id": ObjectId(session["user_id"])})
    if not user:
        session.clear()
        return redirect(url_for("login"))
        
    return render_template("two_factor.html", user=user)

@app.route("/toggle_2fa", methods=["POST"])
def toggle_2fa():
    """Enable or disable 2FA."""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        data = request.get_json()
        enabled = data.get("enabled", False)
        
        user = users.find_one({"_id": ObjectId(session["user_id"])})
        if not user:
            return jsonify({"success": False, "message": "User not found"})
            
        if enabled:
            # Directly enable 2FA without sending any email/code
            secret = generate_2fa_code()
            recovery_codes = generate_recovery_codes()
            users.update_one(
                {"_id": ObjectId(session["user_id"])},
                {"$set": {
                    "two_factor_enabled": True,
                    "two_factor_secret": secret,
                    "recovery_codes": recovery_codes
                }}
            )
            return jsonify({"success": True, "message": "2FA enabled (no email sent)."})
        else:
            # Disable 2FA
            users.update_one(
                {"_id": ObjectId(session["user_id"])},
                {
                    "$unset": {
                        "two_factor_secret": "",
                        "recovery_codes": "",
                        "two_factor_enabled": ""
                    }
                }
            )
            return jsonify({"success": True})
            
    except Exception as e:
        logger.error(f"Error toggling 2FA: {e}")
        return jsonify({
            "success": False,
            "message": "An error occurred while updating 2FA settings"
        }), 500

@app.route("/permission")
def permission():
    """Send a permission request email."""
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user = users.find_one({"_id": ObjectId(session["user_id"])})
    if not user or not user.get("email"):
        return redirect(url_for("login"))
    
    # Generate a permission token
    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(hours=24)
    
    # Store the token in the database
    users.update_one(
        {"_id": ObjectId(session["user_id"])},
        {"$set": {
            "permission_token": token,
            "permission_token_expiry": expiry
        }}
    )
    
    # Construct verification URLs
    verification_url = request.host_url.rstrip('/') + url_for('permission_verify', token=token, granted=True)
    deny_url = request.host_url.rstrip('/') + url_for('permission_verify', token=token, granted=False)
    
    # Skip sending permission email and auto-grant permission for testing
    users.update_one(
        {"_id": ObjectId(session["user_id"])},
        {"$set": {
            "permission_granted": True,
            "permission_date": datetime.utcnow()
        }}
    )
    session["permission_granted"] = True
    log_activity(str(user["_id"]), "permission_bypassed_for_testing")
    return redirect(url_for("face_recognize"))

@app.route("/permission_verify")
def permission_verify():
    """Verify user permission from email link."""
    token = request.args.get("token")
    granted = request.args.get("granted", "false").lower() == "true"
    
    if not token:
        return render_template("permission_invalid.html", error="Missing token")
    
    # Find user with this token
    user = users.find_one({
        "permission_token": token,
        "permission_token_expiry": {"$gt": datetime.utcnow()}
    })
    
    if not user:
        return render_template("permission_invalid.html", error="Invalid or expired token. For security reasons, permission links expire after 30 minutes.")
    
    # Update user's permission status
    users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "permission_granted": granted,
            "permission_date": datetime.utcnow()
        },
        "$unset": {
            "permission_token": "",
            "permission_token_expiry": ""
        }}
    )
    
    # If the user is logged in, also update their session
    if "user_id" in session and str(user["_id"]) == session["user_id"]:
        session["permission_granted"] = granted
    
    # Log this activity
    log_activity(str(user["_id"]), "permission_updated", {"granted": granted})
    
    if granted:
        return render_template("permission_granted.html")
    else:
        return render_template("permission_denied.html")

@app.route("/reset_permissions", methods=["POST"])
def reset_permissions():
    """Reset the user's permission settings."""
    try:
        if "user_id" not in session:
            return jsonify({"success": False, "message": "Not authenticated"}), 401
            
        # Remove permission related fields from database
        users.update_one(
            {"_id": ObjectId(session["user_id"])},
            {"$unset": {
                "permission_granted": "",
                "permission_date": ""
            }}
        )
        
        # Remove from session as well
        if "permission_granted" in session:
            session.pop("permission_granted")
            
        # Log this activity
        log_activity(session["user_id"], "reset_permissions")
            
        return jsonify({
            "success": True,
            "message": "Permission settings reset successfully."
        })
    except Exception as e:
        logger.error(f"Error resetting permissions: {e}")
        return jsonify({
            "success": False,
            "message": "An error occurred while resetting permissions."
        }), 500

@app.route("/check_permission_status")
def check_permission_status():
    """Check the current permission status for a user."""
    if "user_id" not in session:
        return jsonify({"granted": False, "remembered": False})
        
    user = users.find_one({"_id": ObjectId(session["user_id"])})
    if not user:
        return jsonify({"granted": False, "remembered": False})
        
    return jsonify({
        "granted": user.get("permission_granted", False),
        "remembered": True if "permission_date" in user else False
    })

@app.route("/bypass_permission", methods=["GET", "POST"])
def bypass_permission():
    """Bypass permission requirement for testing purposes."""
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        # Set permission to granted directly in the database
        users.update_one(
            {"_id": ObjectId(session["user_id"])},
            {"$set": {
                "permission_granted": True,
                "permission_granted_at": datetime.utcnow()
            }}
        )
        
        # Update session
        session["permission_granted"] = True
        
        # Log this activity
        log_activity(str(session["user_id"]), "permission_bypassed")
        
        flash("Permission has been granted for testing purposes.", "success")
        return redirect(url_for("face_recognize"))
    
    return render_template("bypass_permission.html")

@app.route("/permission_email_error")
def permission_email_error():
    """Display error page for permission email failures."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Clear the error flag from session
    session.pop('email_send_failed', None)
    
    return render_template("permission_email_error.html")

# Error handlers
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="Too many requests, please try again later."), 429

@app.errorhandler(404)
def not_found_error(e):
    return jsonify({"success": False, "message": "Resource not found."}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"success": False, "message": "An internal error occurred. Please try again later."}), 500

@app.route("/api/login", methods=["POST"])
def login_api():
    """API endpoint for handling login requests, always returns JSON responses."""
    try:
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password", "")
        
        logger.info(f"Login attempt for email: {email}")
        
        if not email or not password:
            logger.warning("Login attempt with missing email or password")
            return jsonify({"success": False, "message": "Please enter both email and password."})
            
        user = users.find_one({"email": email})
        
        if not user:
            # Log failed login attempt
            logger.warning(f"Login failed: User not found for email: {email}")
            log_activity(email, "failed_login", {"reason": "user_not_found"})
            return jsonify({"success": False, "message": "Invalid email or password."})
            
        # Check password
        try:
            # Convert both to bytes for bcrypt
            password_bytes = password.encode('utf-8')
            stored_hash_bytes = user["password"].encode('utf-8')
            
            logger.info(f"Checking password for user: {email}")
            
            if not bcrypt.checkpw(password_bytes, stored_hash_bytes):
                # Log failed login attempt
                logger.warning(f"Login failed: Invalid password for email: {email}")
                log_activity(str(user["_id"]), "failed_login", {"reason": "invalid_password"})
                return jsonify({"success": False, "message": "Invalid email or password."})
        except Exception as e:
            logger.error(f"Password check error: {str(e)}")
            return jsonify({"success": False, "message": "Authentication error. Please try again."})
            
        # Check 2FA if enabled
        if user.get("two_factor_enabled", False):
            # Store user ID in session temporarily
            session["temp_user_id"] = str(user["_id"])
            session["temp_email"] = email
            logger.info(f"2FA required for user: {email}")
            return jsonify({"success": True, "redirect": url_for("two_factor")})
            
        # Login successful
        logger.info(f"Login successful for user: {email}")
        session.permanent = True
        session["user_id"] = str(user["_id"])
        session["email"] = email
        
        # Update last login
        users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Log successful login
        log_activity(str(user["_id"]), "login_success")
        
        # Return success with redirect
        return jsonify({
            "success": True, 
            "message": "Login successful!", 
            "redirect": url_for("face_recognize")
        })
    except Exception as e:
        logger.error(f"Login API error: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred during login. Please try again."})

@app.route("/login_direct", methods=["POST"])
def login_direct():
    """Simplified login endpoint that always returns JSON."""
    try:
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password", "")
        
        logger.info(f"Login_direct attempt for email: {email}")
        
        # Basic validation
        if not email or not password:
            return jsonify({"success": False, "message": "Please enter both email and password."})
        
        # Special case for known test user
        if email == "kpreeti09050@gmail.com":
            # Create a session directly
            session.permanent = True
            session["user_id"] = "67fe5abac0216a01406da0f9"  # Use the ID from logs
            session["email"] = email
            
            # Remove any face_verified_at to force face recognition
            users.update_one(
                {"_id": ObjectId("67fe5abac0216a01406da0f9")},
                {"$unset": {"face_verified_at": ""}}
            )
            
            # Log this bypass
            logger.info(f"Bypass login for test user: {email}")
            
            return jsonify({
                "success": True,
                "message": "Login successful!",
                "redirect": url_for("face_recognize")  # Redirect to face recognition
            })
        else:
            # Find user
            user = users.find_one({"email": email})
            if not user:
                return jsonify({"success": False, "message": "Invalid email or password."})
            
            # Manual password verification without bcrypt to avoid encoding issues
            try:
                # Save password type and length info for debugging
                logger.info(f"Password type: {type(password)}")
                logger.info(f"Stored password type: {type(user['password'])}")
                
                # Just do a direct compare for now
                if password == user.get("raw_password"):
                    # Success path
                    session.permanent = True
                    session["user_id"] = str(user["_id"])
                    session["email"] = email
                    
                    # Update login timestamp
                    users.update_one(
                        {"_id": user["_id"]},
                        {"$set": {"last_login": datetime.utcnow()}}
                    )
                    
                    return jsonify({
                        "success": True,
                        "message": "Login successful!",
                        "redirect": url_for("face_recognize")
                    })
                else:
                    return jsonify({"success": False, "message": "Invalid email or password."})
                
            except Exception as e:
                logger.error(f"Password check error: {str(e)}")
                return jsonify({"success": False, "message": f"Authentication error: {str(e)}"})
            
    except Exception as e:
        logger.error(f"Login direct error: {str(e)}")
        return jsonify({"success": False, "message": f"Login error: {str(e)}"})

@app.route("/test_face")
def test_face():
    """Test route for face recognition without login requirement."""
    return render_template("face_recognize.html", current_user={"username": "Test User"}, has_registered_face=False)

@app.route("/debug_session")
def debug_session():
    """Debugging endpoint to view session data."""
    if not app.debug:
        return jsonify({"error": "Debug endpoints disabled in production"}), 403
        
    # Get everything from session
    session_data = dict(session)
    
    # Get current user info if logged in
    user_data = None
    if "user_id" in session:
        try:
            user = users.find_one({"_id": ObjectId(session["user_id"])})
            if user:
                # Convert ObjectId to string for JSON serialization
                user["_id"] = str(user["_id"])
                # Remove sensitive data
                if "password" in user:
                    user["password"] = "***REDACTED***"
                user_data = user
        except Exception as e:
            user_data = {"error": str(e)}
    
    return jsonify({
        "session": session_data,
        "user": user_data
    })

if __name__ == "__main__":
    # Use threaded=False to avoid socket errors on Windows
    app.run(debug=True, threaded=False, use_reloader=False)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

 
