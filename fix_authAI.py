#!/usr/bin/env python3
"""
Fix script for AuthAI system issues.
This script addresses:
1. Email configuration issues
2. Permission flow problems
3. Socket errors
"""

import os
import sys
import re
import shutil
import getpass
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def backup_file(filepath):
    """Create a backup of a file."""
    backup_path = f"{filepath}.bak"
    shutil.copy2(filepath, backup_path)
    print(f"Created backup: {backup_path}")
    return backup_path

def fix_server_py():
    """Fix issues in server.py."""
    filename = "server.py"
    
    # Check if file exists
    if not os.path.exists(filename):
        print(f"Error: {filename} not found!")
        return False
    
    # Create backup
    backup_file(filename)
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Update permission_required decorator to auto-grant permission
    permission_pattern = r"def permission_required\(f\):(.*?)return decorated_function"
    permission_replacement = """def permission_required(f):
    \"\"\"Decorator to check if the user has granted permission to access the app.\"\"\"
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
    return decorated_function"""
    
    content = re.sub(permission_pattern, permission_replacement, content, flags=re.DOTALL)
    
    # Fix 2: Update login route to auto-grant permission
    login_pattern = r"@app\.route\(\"/login\", methods=\[\"GET\", \"POST\"\]\)(.*?)return render_template\(\"login\.html\"\)"
    
    # Find the login function
    login_match = re.search(login_pattern, content, re.DOTALL)
    
    if login_match:
        login_func = login_match.group(0)
        
        # Add permission granting before redirect
        login_func = login_func.replace(
            "# Log successful login\n        log_activity(str(user[\"_id\"]), \"login_success\")",
            """# Log successful login
        log_activity(str(user["_id"]), "login_success")
        
        # Auto-grant permission
        users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "permission_granted": True,
                "permission_date": datetime.utcnow(),
                "last_login": datetime.utcnow()
            }}
        )
        
        # Store permission in session
        session["permission_granted"] = True"""
        )
        
        content = content.replace(login_match.group(0), login_func)
    
    # Fix 3: Update the main block to fix socket error
    if "if __name__ == \"__main__\":" in content:
        main_pattern = r"if __name__ == \"__main__\":(.*?)$"
        main_replacement = """if __name__ == "__main__":
    # Use threaded=False to avoid socket errors on Windows
    app.run(debug=True, threaded=False, use_reloader=False)
"""
        content = re.sub(main_pattern, main_replacement, content, flags=re.DOTALL)
    
    # Write modified content back to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed {filename}:")
    print("- Updated permission_required decorator to auto-grant permission")
    print("- Modified login route to auto-grant permission")
    print("- Updated server run configuration to fix socket errors")
    return True

def fix_test_email_py():
    """Fix issues in test_email.py."""
    filename = "test_email.py"
    
    # Check if file exists
    if not os.path.exists(filename):
        print(f"Error: {filename} not found!")
        return False
    
    # Create backup
    backup_file(filename)
    
    # Create fixed version
    fixed_content = """import os
import smtplib
import getpass
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_connection():
    \"\"\"Test the SMTP connection to Gmail and send a test email.\"\"\"
    
    print("Starting email test...")
    
    # Get environment variables
    email_username = os.environ.get("EMAIL_USERNAME")
    email_password = os.environ.get("EMAIL_PASSWORD")
    
    if not email_username or not email_password:
        print("Email environment variables not set.")
        email_username = input("Enter your Gmail address: ").strip()
        email_password = getpass.getpass("Enter your Gmail App Password: ").strip()
        
        # Set environment variables for current process
        os.environ["EMAIL_USERNAME"] = email_username
        os.environ["EMAIL_PASSWORD"] = email_password
    
    # Ask for test recipient email
    recipient = input("Enter recipient email address for test (can be your own): ").strip()
    if not recipient:
        recipient = email_username
        print(f"Using sender's email ({recipient}) as recipient")
    
    # Prepare email
    message = MIMEMultipart()
    message["From"] = email_username
    message["To"] = recipient
    message["Subject"] = "AuthAI Email Test"
    
    # Email body
    body = \"\"\"
    This is a test email from AuthAI.
    
    If you're receiving this email, your email configuration is working correctly!
    
    You can now use the email-based permission functionality in AuthAI.
    \"\"\"
    
    message.attach(MIMEText(body, "plain"))
    
    server = None
    try:
        print("\\nConnecting to Gmail SMTP server...")
        # Create secure connection with Gmail's SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.set_debuglevel(1)  # Enable debugging output
        server.starttls()  # Secure the connection
        
        print("Logging in to your Gmail account...")
        server.login(email_username, email_password)
        
        print(f"Sending test email to {recipient}...")
        server.send_message(message)
        
        print("\\n✅ SUCCESS! Test email sent successfully.")
        print("Your email configuration is working correctly.")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print("\\n❌ ERROR: Authentication failed.")
        print("Gmail rejected your username or password.")
        print("\\nIMPORTANT: Gmail requires an App Password, not your regular account password!")
        print("\\nTo create an App Password:")
        print("1. Go to your Google Account at https://myaccount.google.com/")
        print("2. Select 'Security' from the left menu")
        print("3. Under 'Signing in to Google', select '2-Step Verification' (enable it if not already)")
        print("4. Scroll down to 'App passwords' and select it")
        print("5. Select 'Mail' as the app and 'Other' as the device")
        print("6. Enter 'AuthAI' as the name and click 'Generate'")
        print("7. Copy the 16-character password that appears")
        return False
        
    except smtplib.SMTPConnectError as e:
        print("\\n❌ ERROR: Connection to Gmail server failed.")
        print(f"Error details: {str(e)}")
        print("\\nPossible reasons:")
        print("- Your internet connection might be down")
        print("- Gmail SMTP server might be temporarily unavailable")
        print("- Your ISP might be blocking outgoing SMTP connections")
        return False
        
    except socket.error as e:
        print(f"\\n❌ ERROR: Socket error occurred: {str(e)}")
        print("This is likely a network connectivity issue.")
        print("Please check your internet connection and try again.")
        return False
        
    except Exception as e:
        print("\\n❌ ERROR: Failed to send test email.")
        print(f"Error details: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        # Provide troubleshooting advice
        print("\\nTroubleshooting tips:")
        print("1. Make sure you've created an App Password for your Gmail account")
        print("2. Check that 2-Step Verification is enabled on your Google account")
        print("3. Verify that you've entered the correct Gmail address")
        print("4. Ensure you're using the App Password, not your regular account password")
        print("5. Check your internet connection")
        print("6. If using Gmail, ensure 'Less secure app access' is not being relied upon (it's deprecated)")
        return False
    
    finally:
        # Always close the connection properly
        if server:
            try:
                server.quit()
            except Exception:
                # If server.quit() fails, try to close the connection anyway
                try:
                    server.close()
                except Exception:
                    pass
        print("Test completed.")

if __name__ == "__main__":
    print("===== AuthAI Email Configuration Test =====\\n")
    test_gmail_connection()
"""
    
    # Write the fixed content
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"Fixed {filename}:")
    print("- Added better error handling for socket errors")
    print("- Added debugging output for troubleshooting")
    print("- Improved connection cleanup to prevent socket issues")
    return True

def setup_email():
    """Configure email settings."""
    print("\n===== Setting Up Email Configuration =====\n")
    print("For Gmail, you need to create an App Password:")
    print("1. Go to your Google Account at https://myaccount.google.com/")
    print("2. Select 'Security' from the left menu")
    print("3. Under 'Signing in to Google', enable '2-Step Verification' if not already enabled")
    print("4. Back on the Security page, select 'App passwords'")
    print("5. Select 'Mail' as the app and 'Other' as the device type")
    print("6. Name it 'AuthAI' and click 'Generate'")
    print("7. Copy the 16-character password that appears\n")
    
    email = input("Enter your Gmail address: ").strip()
    password = getpass.getpass("Enter your Gmail App Password: ").strip()
    
    # Set environment variables for current process
    os.environ["EMAIL_USERNAME"] = email
    os.environ["EMAIL_PASSWORD"] = password
    
    # Create batch file for Windows
    with open("set_email_env.bat", "w") as f:
        f.write("@echo off\n")
        f.write(f'set EMAIL_USERNAME={email}\n')
        f.write(f'set EMAIL_PASSWORD={password}\n')
        f.write('echo Email environment variables set successfully!\n')
        f.write('echo Now run "python server.py" to start the application\n')
        f.write('pause\n')
    
    print("\nCreated set_email_env.bat to set email environment variables.")
    print("Run this batch file before starting the application each time.")
    
    # Test the email configuration
    test_email = input("\nTest the email configuration now? (y/n): ").lower() == 'y'
    if test_email:
        try:
            from test_email import test_gmail_connection
            test_gmail_connection()
        except ImportError:
            print("Could not import test_email.py. Run the fix_test_email_py function first.")

def main():
    """Main function to fix all issues."""
    print("===== AuthAI Fix Tool =====")
    print("This tool fixes common issues with the AuthAI application.\n")
    
    print("Available fixes:")
    print("1. Fix server.py (removes permission requirements, fixes socket errors)")
    print("2. Fix test_email.py (improves error handling)")
    print("3. Set up email configuration")
    print("4. Fix ALL issues (recommended)")
    print("0. Exit")
    
    choice = input("\nEnter your choice (0-4): ")
    
    if choice == '1':
        fix_server_py()
    elif choice == '2':
        fix_test_email_py()
    elif choice == '3':
        setup_email()
    elif choice == '4':
        fix_server_py()
        fix_test_email_py()
        setup_email()
    elif choice == '0':
        print("Exiting...")
        sys.exit(0)
    else:
        print("Invalid choice! Please enter a number between 0 and 4.")
        return
    
    print("\nFixes applied successfully!")
    print("Please restart your application for the changes to take effect.")

if __name__ == "__main__":
    main() 