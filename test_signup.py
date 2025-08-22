from flask import Flask, render_template, request, redirect, url_for, flash
import pymongo
import bcrypt
import os
import logging
from datetime import datetime
from bson import ObjectId

# Configure detailed logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "test_secret_key"

try:
    # Connect to MongoDB
    logger.info("Connecting to MongoDB...")
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    
    # Get or create the database
    db = client.AuthAI_test
    users = db.users_test
    
    # Create index for email
    users.create_index("email", unique=True)
    
    logger.info("MongoDB connection successful")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    raise

# Create upload folder for faces
UPLOAD_FOLDER = "static/faces"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return redirect(url_for("signup"))

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

        logger.debug(f"Signup attempt: name={name}, email={email}, password_length={len(password)}, pic_name={pic_name}")

        # Input validation
        if not all([name, email, password, pic_name]):
            logger.warning("Signup validation failed: Missing required fields")
            flash("All fields are required!", "error")
            return render_template("signup.html")
            
        if not "@" in email or not "." in email:
            logger.warning(f"Signup validation failed: Invalid email format: {email}")
            flash("Please enter a valid email address!", "error")
            return render_template("signup.html")

        # Check if email already exists
        existing_user = users.find_one({"email": email})
        if existing_user:
            logger.warning(f"Signup failed: Email already exists: {email}")
            flash("Email already registered!", "error")
            return render_template("signup.html")

        try:
            # Hash password
            logger.debug("Hashing password...")
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            hashed_password_str = hashed_password.decode('utf-8')
            logger.debug("Password hashing completed")
            
            # Generate a new ObjectId
            user_id = ObjectId()
            logger.debug(f"Generated new user ID: {user_id}")
            
            # Create user document
            new_user = {
                "_id": user_id,
                "username": name,
                "email": email,
                "password": hashed_password_str,
                "image_name": pic_name,
                "created_at": datetime.utcnow()
            }
            
            # Insert user into database
            logger.debug("Inserting user into database...")
            result = users.insert_one(new_user)
            logger.info(f"User created with ID: {result.inserted_id}")
            
            # Set success message
            flash("Account created successfully!", "success")
            logger.info(f"Account created successfully for {email}")
            
            # Redirect to signup page after success for this test
            return redirect(url_for('signup'))
        except Exception as e:
            logger.error(f"Error in user creation: {str(e)}", exc_info=True)
            flash(f"An error occurred during account creation: {str(e)}", "error")
            return render_template("signup.html")

    except Exception as e:
        logger.error(f"Unhandled exception in signup: {str(e)}", exc_info=True)
        flash("An unexpected error occurred during signup!", "error")
        return render_template("signup.html")

# Route to show all registered users (for testing)
@app.route("/users")
def users_list():
    try:
        user_list = list(users.find())
        return render_template("users.html", users=user_list)
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Create a simple users template
    if not os.path.exists("templates"):
        os.makedirs("templates")
    
    with open("templates/users.html", "w") as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Registered Users</title>
</head>
<body>
    <h1>Registered Users</h1>
    <table border="1">
        <tr>
            <th>ID</th>
            <th>Username</th>
            <th>Email</th>
            <th>Created At</th>
        </tr>
        {% for user in users %}
        <tr>
            <td>{{ user._id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>{{ user.created_at }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
        """)
    
    app.run(debug=True, host='0.0.0.0', port=5001) 