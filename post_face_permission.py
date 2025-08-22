from flask import request, url_for, session
from bson import ObjectId
from datetime import datetime, timedelta
import secrets
import logging

# Setup logging
logger = logging.getLogger(__name__)

def send_permission_after_face_verify(db, user_id, send_email_func, host_url):
    """
    Send a permission email after successful face verification.
    
    Args:
        db: MongoDB database connection
        user_id: User ID string
        send_email_func: Function to send emails
        host_url: Base URL of the application
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get user record
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user or not user.get("email"):
            logger.error(f"User {user_id} not found or has no email")
            return False
            
        # Check if permission email was already sent
        if user.get("permission_email_sent", False):
            logger.info(f"Permission email already sent to user {user_id}")
            return True
            
        # Generate permission token
        token = secrets.token_urlsafe(32)
        # Set token to expire in 30 minutes instead of 24 hours
        expiry = datetime.utcnow() + timedelta(minutes=30)
        
        # Update user record with token
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "permission_token": token,
                "permission_token_expiry": expiry,
                "permission_email_sent": True,
                "face_verified_at": datetime.utcnow()
            }}
        )
        
        # Generate verification URLs
        verification_url = f"{host_url.rstrip('/')}/permission_verify?token={token}&granted=true"
        deny_url = f"{host_url.rstrip('/')}/permission_verify?token={token}&granted=false"
        
        # Prepare email content
        subject = "AuthAI - Permission Request after Face Verification"
        body = f"""
        Hello {user.get('username', 'User')},
        
        Your face has been successfully verified in the AuthAI system!
        
        To complete the setup, we need your permission to use facial recognition for future logins.
        
        By clicking "Yes", you allow the application to:
        - Access your device camera
        - Process facial images for authentication
        - Store encrypted facial data securely
        
        Click here to GRANT access: {verification_url}
        
        Click here to DENY access: {deny_url}
        
        Note: This link will expire in 30 minutes for security reasons.
        
        Thank you,
        AuthAI Security Team
        """
        
        # Send the email
        result = send_email_func(user["email"], subject, body)
        
        if result:
            # Log the activity
            db.activities.insert_one({
                "user_email": user_id,
                "activity_type": "permission_email_sent",
                "details": {"after_face_verify": True},
                "timestamp": datetime.utcnow()
            })
            
        return result
        
    except Exception as e:
        logger.error(f"Error sending permission email after face verification: {str(e)}")
        return False

def check_permission_status(db, user_id):
    """
    Check if a user has granted permission.
    
    Args:
        db: MongoDB database connection
        user_id: User ID string
        
    Returns:
        dict: Status information including granted (bool) and status (string)
    """
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"granted": False, "status": "user_not_found"}
            
        # Check if permission was granted
        if user.get("permission_granted", False):
            return {
                "granted": True, 
                "status": "granted",
                "timestamp": user.get("permission_date", datetime.utcnow())
            }
            
        # Check if permission email was sent
        if user.get("permission_email_sent", False):
            # Check if token is still valid
            if user.get("permission_token_expiry", datetime.utcnow()) > datetime.utcnow():
                return {"granted": False, "status": "email_sent_pending"}
            else:
                return {"granted": False, "status": "token_expired"}
        
        # No permission email sent yet
        return {"granted": False, "status": "not_requested"}
        
    except Exception as e:
        logger.error(f"Error checking permission status: {str(e)}")
        return {"granted": False, "status": "error", "message": str(e)} 