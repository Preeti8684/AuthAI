import pymongo
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    # Connect to MongoDB
    logger.info("Connecting to MongoDB...")
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    
    # Test database connection
    client.server_info()
    logger.info("MongoDB connection successful")
    
    # Create a test database and collection
    db = client.AuthAI_test
    test_collection = db.test_users
    
    # Insert a test document
    test_user = {
        "username": "test_user",
        "email": "test@example.com",
        "created_at": datetime.utcnow()
    }
    
    # Clear previous test data
    test_collection.delete_many({"email": "test@example.com"})
    
    # Insert new test data
    result = test_collection.insert_one(test_user)
    logger.info(f"Test document inserted with ID: {result.inserted_id}")
    
    # Retrieve the document
    found_user = test_collection.find_one({"email": "test@example.com"})
    logger.info(f"Retrieved document: {found_user}")
    
    logger.info("MongoDB tests completed successfully")
    
except Exception as e:
    logger.error(f"MongoDB test failed: {str(e)}")
    raise
