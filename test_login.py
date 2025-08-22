import pymongo
import bcrypt
import logging
from bson import ObjectId

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mongodb_connection():
    """Test MongoDB connection."""
    try:
        # Simple connection to MongoDB
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        
        # Create database and collections
        db = client.AuthAI
        users = db.users
        
        # Test the connection
        client.server_info()
        logger.info("MongoDB connection test: SUCCESS")
        return True, db
    except Exception as e:
        logger.error(f"MongoDB connection test: FAILED - {e}")
        return False, None

def test_user_lookup(db, email):
    """Test looking up a user by email."""
    try:
        users = db.users
        user = users.find_one({"email": email})
        if user:
            logger.info(f"User lookup test: SUCCESS - Found user with ID: {user['_id']}")
            return True, user
        else:
            logger.info(f"User lookup test: No user found with email: {email}")
            return False, None
    except Exception as e:
        logger.error(f"User lookup test: FAILED - {e}")
        return False, None

def test_password_verification(user, password):
    """Test password verification."""
    try:
        # Test with raw_password if available (for test users)
        if "raw_password" in user:
            if password == user["raw_password"]:
                logger.info("Password verification test (raw): SUCCESS")
                return True
            else:
                logger.info("Password verification test (raw): FAILED - password mismatch")
                return False
        
        # Test with hashed password
        stored_password = user["password"]
        
        # Convert both to bytes for bcrypt
        password_bytes = password.encode('utf-8')
        stored_hash_bytes = stored_password.encode('utf-8')
        
        if bcrypt.checkpw(password_bytes, stored_hash_bytes):
            logger.info("Password verification test (bcrypt): SUCCESS")
            return True
        else:
            logger.info("Password verification test (bcrypt): FAILED - bcrypt hash mismatch")
            return False
    except Exception as e:
        logger.error(f"Password verification test: FAILED - {e}")
        return False

def test_create_user(db, email, password):
    """Test creating a new user."""
    try:
        users = db.users
        
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create a new user document
        new_user = {
            "_id": ObjectId(),
            "username": email.split('@')[0],
            "email": email,
            "password": hashed_password.decode('utf-8'),
            "raw_password": password,
            "created_at": "test_timestamp"
        }
        
        # Insert the user
        result = users.insert_one(new_user)
        logger.info(f"User creation test: SUCCESS - Created user with ID: {result.inserted_id}")
        return True, str(result.inserted_id)
    except Exception as e:
        logger.error(f"User creation test: FAILED - {e}")
        return False, None

def list_all_users(db):
    """List all users in the database."""
    try:
        users = db.users
        all_users = list(users.find({}, {"email": 1, "password": 1, "raw_password": 1}))
        logger.info(f"Found {len(all_users)} users in database")
        for user in all_users:
            logger.info(f"User: {user.get('email')} - ID: {user.get('_id')}")
        return all_users
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return []

if __name__ == "__main__":
    # Test MongoDB connection
    mongo_success, db = test_mongodb_connection()
    if not mongo_success:
        logger.error("MongoDB connection failed, aborting tests")
        exit(1)
    
    # List all users
    all_users = list_all_users(db)
    
    # Test email to check
    test_email = "kpreeti09050@gmail.com"
    test_password = "123456"
    
    # Test user lookup
    lookup_success, user = test_user_lookup(db, test_email)
    
    if lookup_success:
        # Test password verification
        test_password_verification(user, test_password)
    else:
        # Test creating a new user
        create_success, user_id = test_create_user(db, test_email, test_password)
        if create_success:
            logger.info(f"Successfully created test user: {test_email}")
            
    print("\nTests completed. Check logs above for results.") 