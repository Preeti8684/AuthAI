"""
Login Override Script for AuthAI

This script adds a hook to redirect login directly to face_recognize.
Save it to a file called login_override.py and run it before starting the server:
python login_override.py

Then run your server as normal:
python server.py
"""

import os
import re

SERVER_FILE = 'server.py'

def patch_login_route():
    # Read the server.py file
    with open(SERVER_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for dashboard redirect patterns in login functions
    dashboard_patterns = [
        ('return redirect(url_for("dashboard"))', 'return redirect(url_for("face_recognize"))'),
        ('"redirect": url_for("dashboard")', '"redirect": url_for("face_recognize")')
    ]
    
    modified = False
    for pattern, replacement in dashboard_patterns:
        if pattern in content:
            content = content.replace(pattern, replacement)
            modified = True
    
    if modified:
        # Create backup
        backup_file = SERVER_FILE + '.bak'
        if not os.path.exists(backup_file):
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created backup at {backup_file}")
        
        # Write modified content
        with open(SERVER_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("Successfully patched login routes to redirect to face_recognize!")
    else:
        print("No changes were made. Login routes might already be redirecting to face_recognize.")

if __name__ == "__main__":
    patch_login_route() 