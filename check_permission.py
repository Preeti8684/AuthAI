from bson import ObjectId
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_user_permission(db, user_id):
    """
    Check if a user has granted permission for facial recognition.
    
    Args:
        db: MongoDB database connection
        user_id: The user's ID as string
        
    Returns:
        bool: True if permission granted, False otherwise
    """
    try:
        # Convert string ID to ObjectId if needed
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
            
        user = db.users.find_one({"_id": user_id})
        if not user:
            logger.warning(f"User {user_id} not found when checking permissions")
            return False
            
        return user.get("permission_granted", False)
    except Exception as e:
        logger.error(f"Error checking permission for user {user_id}: {str(e)}")
        return False

def send_permission_email(send_email_func, user, verification_url, deny_url):
    """
    Send a permission request email to the user.
    
    Args:
        send_email_func: Function to send email
        user: User document from database
        verification_url: URL to grant permission
        deny_url: URL to deny permission
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = "AuthAI - Permission Request"
        body = f"""
        Hello {user.get('username', 'User')},
        
        AuthAI is requesting your permission to access facial recognition features.
        
        By clicking "Yes", you allow the application to:
        - Access your device camera
        - Process facial images for authentication
        - Store encrypted facial data securely
        
        Click here to GRANT access: {verification_url}
        
        Click here to DENY access: {deny_url}
        
        If you did not request this, please ignore this email.
        
        Thank you,
        AuthAI Security Team
        """
        
        return send_email_func(user["email"], subject, body)
    except Exception as e:
        logger.error(f"Error sending permission email to {user.get('email')}: {str(e)}")
        return False 