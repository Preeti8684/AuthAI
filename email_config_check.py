"""
Email Configuration Check Script for AuthAI

This script checks if the necessary environment variables are set for email functionality
and provides instructions on how to set them up.
"""

import os
import sys
import getpass

def check_email_config():
    """Check if email configuration is properly set up"""
    print("\n=== AuthAI Email Configuration Check ===\n")
    
    # Check for EMAIL_USERNAME
    email_username = os.environ.get("EMAIL_USERNAME")
    if email_username:
        print("✅ EMAIL_USERNAME is set:", email_username)
    else:
        print("❌ EMAIL_USERNAME is not set")
    
    # Check for EMAIL_PASSWORD
    email_password = os.environ.get("EMAIL_PASSWORD")
    if email_password:
        print("✅ EMAIL_PASSWORD is set (value hidden)")
    else:
        print("❌ EMAIL_PASSWORD is not set")
    
    print("\n=== Configuration Status ===\n")
    
    if email_username and email_password:
        print("✅ Email configuration is COMPLETE")
        print("\nYou can now run the application with:")
        print("   python server.py")
        print("\nTo test email sending specifically, run:")
        print("   python test_email.py")
    else:
        print("❌ Email configuration is INCOMPLETE")
        print("\nPlease set the missing environment variables:")
        
        print("\nIn Windows PowerShell:")
        print('   $env:EMAIL_USERNAME="your.email@gmail.com"')
        print('   $env:EMAIL_PASSWORD="your-app-password"')
        
        print("\nIn Windows Command Prompt:")
        print("   set EMAIL_USERNAME=your.email@gmail.com")
        print("   set EMAIL_PASSWORD=your-app-password")
        
        print("\nIn Linux/Mac:")
        print("   export EMAIL_USERNAME=your.email@gmail.com")
        print("   export EMAIL_PASSWORD=your-app-password")
        
        print("\nReminder: You need a Gmail App Password, not your regular Gmail password.")
        print("To create an App Password:")
        print("1. Go to your Google Account security settings")
        print("2. Enable 2-Step Verification if not already enabled")
        print("3. Go to App passwords")
        print("4. Select 'Mail' as the app and 'Windows Computer' as the device")
        print("5. Click Generate")
        
        # Ask if user wants to set them now
        set_now = input("\nWould you like to set these variables now? (y/n): ")
        if set_now.lower() == 'y':
            username = input("Enter your Gmail address: ")
            password = getpass.getpass("Enter your Gmail App Password: ")
            
            # Set the environment variables
            os.environ["EMAIL_USERNAME"] = username
            os.environ["EMAIL_PASSWORD"] = password
            
            print("\n✅ Environment variables set for this session")
            print("\nIMPORTANT: These settings will only apply in this terminal session.")
            print("You should run the application in this same terminal window:")
            print("   python server.py")
            
            # Ask if user wants to test the email
            test_email = input("\nWould you like to test the email configuration now? (y/n): ")
            if test_email.lower() == 'y':
                print("\nRunning email test...")
                # Import the test function
                sys.path.append(".")
                try:
                    from test_email import test_gmail_connection
                    test_gmail_connection()
                except ImportError:
                    print("❌ Could not import test_email.py")
                    print("Make sure you are in the project root directory.")
    
if __name__ == "__main__":
    check_email_config() 