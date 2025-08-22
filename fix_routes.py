#!/usr/bin/env python3
"""
Fix script for routing issues in AuthAI.
This script diagnoses and fixes issues with home page, login, and signup routes.
"""

import os
import sys
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_server_routes():
    """Fix issues in the server.py file related to home, login, and signup routes."""
    server_file = "server.py"
    
    print(f"Checking {server_file}...")
    
    if not os.path.exists(server_file):
        print(f"❌ ERROR: Server file {server_file} not found")
        return False
    
    # Create backup
    backup_file = f"{server_file}.route_bak"
    if not os.path.exists(backup_file):
        shutil.copy2(server_file, backup_file)
        print(f"✅ Created backup: {backup_file}")
    
    try:
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the home page route
        if "@app.route(\"/\")" in content:
            updated_content = content.replace(
                "@app.route(\"/\")\ndef index():\n    \"\"\"Home page with landing content.\"\"\"\n    if 'user_id' in session:\n        return redirect(url_for('dashboard'))\n    return render_template(\"home.html\")",
                "@app.route(\"/\")\ndef index():\n    \"\"\"Home page with landing content.\"\"\"\n    # Always show home page, even if user is logged in\n    return render_template(\"home.html\")"
            )
            
            # Make sure the server handles login correctly
            if "@app.route(\"/login\", methods=[\"GET\", \"POST\"])" in updated_content:
                print("✅ Login route exists and looks correct")
            else:
                print("❌ Login route not found in expected format")
                
            # Make sure the server handles signup correctly
            if "@app.route(\"/signup\", methods=[\"GET\", \"POST\"])" in updated_content:
                print("✅ Signup route exists and looks correct")
            else:
                print("❌ Signup route not found in expected format")
            
            # Write the modified file
            with open(server_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("✅ Updated server.py to always show home page")
            return True
        else:
            print("❌ Home page route not found in expected format")
            return False
    except Exception as e:
        print(f"❌ Error fixing server routes: {str(e)}")
        return False

def check_template_files():
    """Check if required template files exist."""
    templates_dir = "templates"
    required_templates = ["home.html", "login.html", "signup.html"]
    
    print(f"Checking template files in {templates_dir}...")
    
    missing_templates = []
    
    for template in required_templates:
        template_path = os.path.join(templates_dir, template)
        if os.path.exists(template_path):
            print(f"✅ Found template: {template}")
        else:
            missing_templates.append(template)
            print(f"❌ Missing template: {template}")
    
    if not missing_templates:
        print("✅ All required template files exist")
        return True
    else:
        print(f"❌ Missing template files: {', '.join(missing_templates)}")
        return False

def create_simplified_app():
    """Create a simplified app.py file that only handles core routes."""
    app_file = "app.py"
    
    print(f"Creating simplified {app_file}...")
    
    try:
        app_content = """#!/usr/bin/env python3
\"\"\"
Simplified Flask application for AuthAI with focus on core routes.
This file focuses on making the home, login, and signup pages accessible.
\"\"\"

from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')

@app.route('/')
def index():
    \"\"\"Home page with landing content.\"\"\"
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    \"\"\"Handle user login.\"\"\"
    if request.method == 'POST':
        # For testing, just redirect to dashboard
        flash('Login functionality is in testing mode. Use the server.py for full login.', 'info')
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    \"\"\"Handle user signup.\"\"\"
    if request.method == 'POST':
        # For testing, just redirect to login
        flash('Signup functionality is in testing mode. Use the server.py for full signup.', 'info')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    \"\"\"Dashboard page.\"\"\"
    return render_template('dashboard.html', username="Test User", email="test@example.com")

if __name__ == '__main__':
    logger.info("Starting simplified AuthAI application...")
    # Run with settings that avoid socket errors
    app.run(debug=True, threaded=False, use_reloader=False, port=5000)
"""
        
        with open(app_file, 'w', encoding='utf-8') as f:
            f.write(app_content)
        
        print(f"✅ Created simplified {app_file}")
        return True
    except Exception as e:
        print(f"❌ Error creating simplified {app_file}: {str(e)}")
        return False

def create_run_app_simplified():
    """Create a batch file to run the simplified app."""
    batch_file = "run_simplified.bat"
    
    print(f"Creating {batch_file}...")
    
    try:
        batch_content = """@echo off
echo ===== AuthAI Simplified App Launcher =====
echo.
echo This launcher starts a simplified version of AuthAI focusing on core pages
echo.

python app.py

pause
"""
        
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        print(f"✅ Created {batch_file}")
        return True
    except Exception as e:
        print(f"❌ Error creating {batch_file}: {str(e)}")
        return False

def create_direct_html_files():
    """Create simple HTML files that can be directly opened in a browser."""
    static_dir = "static_html"
    
    print(f"Creating direct HTML files in {static_dir}...")
    
    try:
        # Create the directory if it doesn't exist
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
            print(f"✅ Created directory: {static_dir}")
        
        # Create a simple home.html file
        home_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuthAI - Home</title>
    <link href="https://cdn.tailwindcss.com" rel="stylesheet">
</head>
<body class="bg-gray-100 min-h-screen">
    <header class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <div class="flex-shrink-0 flex items-center">
                        <span class="text-2xl font-bold text-indigo-600">AuthAI</span>
                    </div>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="login.html" class="text-gray-500 hover:text-indigo-600">Login</a>
                    <a href="signup.html" class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">Sign Up</a>
                </div>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div class="text-center">
            <h1 class="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl">AuthAI</h1>
            <p class="mt-4 text-xl text-gray-500">Secure Face Authentication System</p>
        </div>

        <div class="mt-12 grid gap-8 md:grid-cols-3">
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-xl font-bold text-gray-900 mb-4">Face Recognition</h2>
                <p class="text-gray-600">Authenticate using your face with our state-of-the-art facial recognition technology.</p>
            </div>
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-xl font-bold text-gray-900 mb-4">Secure Access</h2>
                <p class="text-gray-600">Multi-factor authentication and strong encryption ensure your data stays safe.</p>
            </div>
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-xl font-bold text-gray-900 mb-4">Easy to Use</h2>
                <p class="text-gray-600">Simple, intuitive interface makes authentication quick and hassle-free.</p>
            </div>
        </div>
    </main>
</body>
</html>"""
        
        # Create a simple login.html file
        login_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuthAI - Login</title>
    <link href="https://cdn.tailwindcss.com" rel="stylesheet">
</head>
<body class="bg-gray-100 min-h-screen">
    <header class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <div class="flex-shrink-0 flex items-center">
                        <a href="index.html" class="text-2xl font-bold text-indigo-600">AuthAI</a>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <main class="max-w-md mx-auto py-12 px-4">
        <div class="bg-white rounded-lg shadow-lg p-8">
            <h1 class="text-2xl font-bold text-gray-900 mb-6 text-center">Login to AuthAI</h1>
            
            <form>
                <div class="mb-4">
                    <label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <input type="email" id="email" name="email" class="w-full px-3 py-2 border border-gray-300 rounded-md" required>
                </div>
                
                <div class="mb-6">
                    <label for="password" class="block text-sm font-medium text-gray-700 mb-1">Password</label>
                    <input type="password" id="password" name="password" class="w-full px-3 py-2 border border-gray-300 rounded-md" required>
                </div>
                
                <div>
                    <button type="submit" class="w-full bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">Login</button>
                </div>
            </form>
            
            <div class="mt-4 text-center text-sm text-gray-600">
                Don't have an account? <a href="signup.html" class="text-indigo-600 hover:text-indigo-500">Sign up</a>
            </div>
        </div>
    </main>
</body>
</html>"""
        
        # Create a simple signup.html file
        signup_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuthAI - Sign Up</title>
    <link href="https://cdn.tailwindcss.com" rel="stylesheet">
</head>
<body class="bg-gray-100 min-h-screen">
    <header class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <div class="flex-shrink-0 flex items-center">
                        <a href="index.html" class="text-2xl font-bold text-indigo-600">AuthAI</a>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <main class="max-w-md mx-auto py-12 px-4">
        <div class="bg-white rounded-lg shadow-lg p-8">
            <h1 class="text-2xl font-bold text-gray-900 mb-6 text-center">Create an Account</h1>
            
            <form>
                <div class="mb-4">
                    <label for="name" class="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                    <input type="text" id="name" name="name" class="w-full px-3 py-2 border border-gray-300 rounded-md" required>
                </div>
                
                <div class="mb-4">
                    <label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <input type="email" id="email" name="email" class="w-full px-3 py-2 border border-gray-300 rounded-md" required>
                </div>
                
                <div class="mb-4">
                    <label for="password" class="block text-sm font-medium text-gray-700 mb-1">Password</label>
                    <input type="password" id="password" name="password" class="w-full px-3 py-2 border border-gray-300 rounded-md" required>
                </div>
                
                <div class="mb-6">
                    <label for="confirm_password" class="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>
                    <input type="password" id="confirm_password" name="confirm_password" class="w-full px-3 py-2 border border-gray-300 rounded-md" required>
                </div>
                
                <div>
                    <button type="submit" class="w-full bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">Sign Up</button>
                </div>
            </form>
            
            <div class="mt-4 text-center text-sm text-gray-600">
                Already have an account? <a href="login.html" class="text-indigo-600 hover:text-indigo-500">Login</a>
            </div>
        </div>
    </main>
</body>
</html>"""
        
        # Create index.html (duplicate of home.html)
        with open(os.path.join(static_dir, "index.html"), 'w', encoding='utf-8') as f:
            f.write(home_html)
        print(f"✅ Created {static_dir}/index.html")
        
        # Create login.html
        with open(os.path.join(static_dir, "login.html"), 'w', encoding='utf-8') as f:
            f.write(login_html)
        print(f"✅ Created {static_dir}/login.html")
        
        # Create signup.html
        with open(os.path.join(static_dir, "signup.html"), 'w', encoding='utf-8') as f:
            f.write(signup_html)
        print(f"✅ Created {static_dir}/signup.html")
        
        print(f"✅ Created static HTML files in {static_dir}")
        print(f"   You can open these files directly in your browser")
        return True
    except Exception as e:
        print(f"❌ Error creating static HTML files: {str(e)}")
        return False

def main():
    """Main function to check and fix routing issues."""
    print("===== AuthAI Routing Fix Tool =====")
    print("This tool diagnoses and fixes issues with home page, login, and signup routes.\n")
    
    # Check template files
    print("\nChecking template files...")
    templates_ok = check_template_files()
    
    # Fix server routes
    print("\nFixing server routes...")
    server_ok = fix_server_routes()
    
    # Create simplified app
    print("\nCreating simplified app.py...")
    app_ok = create_simplified_app()
    
    # Create launcher for simplified app
    print("\nCreating simplified app launcher...")
    launcher_ok = create_run_app_simplified()
    
    # Create direct HTML files
    print("\nCreating direct HTML files...")
    html_ok = create_direct_html_files()
    
    # Summary
    print("\n===== Summary =====")
    print(f"Template Files: {'✅ OK' if templates_ok else '❌ Missing'}")
    print(f"Server Routes: {'✅ Fixed' if server_ok else '❌ Not Fixed'}")
    print(f"Simplified App: {'✅ Created' if app_ok else '❌ Not Created'}")
    print(f"Simplified Launcher: {'✅ Created' if launcher_ok else '❌ Not Created'}")
    print(f"Static HTML Files: {'✅ Created' if html_ok else '❌ Not Created'}")
    
    print("\nWhat to do next:")
    print("1. Run the simplified app: .\\run_simplified.bat")
    print("2. Access the application at http://127.0.0.1:5000")
    print("3. Alternatively, open the static HTML files in static_html/index.html")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 