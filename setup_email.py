import os
import getpass
import platform
import subprocess
import sys

def setup_email_variables():
    """Set up email environment variables for the AuthAI application."""
    print("\n===== Email Configuration for AuthAI =====\n")
    print("This script will help you set up the environment variables needed for sending emails.")
    print("You'll need a Gmail account and an App Password.\n")
    
    # Get Gmail address
    email = input("Enter your Gmail address: ").strip()
    
    # Get App Password
    print("\nFor Gmail, you need to use an App Password instead of your regular password.")
    print("If you don't have an App Password yet, follow these steps:")
    print("1. Go to your Google Account at https://myaccount.google.com/")
    print("2. Select 'Security' from the left menu")
    print("3. Under 'Signing in to Google', select '2-Step Verification' (enable it if not already)")
    print("4. Scroll down to 'App passwords' and select it")
    print("5. Select 'Mail' as the app and 'Other' as the device")
    print("6. Enter 'AuthAI' as the name and click 'Generate'")
    print("7. Copy the 16-character password that appears\n")
    
    password = getpass.getpass("Enter your Gmail App Password: ").strip()
    
    # Detect OS
    system = platform.system()
    
    if system == "Windows":
        # Create batch file
        with open("set_email_env.bat", "w") as f:
            f.write(f"@echo off\n")
            f.write(f"set EMAIL_USERNAME={email}\n")
            f.write(f"set EMAIL_PASSWORD={password}\n")
            f.write("echo Environment variables set successfully!\n")
            f.write("echo Run 'python server.py' to start the application\n")
            f.write("pause\n")
        
        print("\nA batch file 'set_email_env.bat' has been created.")
        print("Run this file before starting the server each time, or:")
        print("1. Open System Properties")
        print("2. Click on 'Environment Variables'")
        print("3. Add EMAIL_USERNAME and EMAIL_PASSWORD to your user variables")
        
        # Ask if they want to run the batch file now
        run_now = input("\nDo you want to run the batch file now? (y/n): ").lower() == 'y'
        if run_now:
            try:
                subprocess.call(["set_email_env.bat"])
            except Exception as e:
                print(f"Error running batch file: {str(e)}")
                print("Please run the batch file manually.")
    
    elif system == "Linux" or system == "Darwin":  # Darwin is macOS
        # Create shell script
        with open("set_email_env.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f"export EMAIL_USERNAME='{email}'\n")
            f.write(f"export EMAIL_PASSWORD='{password}'\n")
            f.write("echo 'Environment variables set successfully!'\n")
            f.write("echo 'Run \"python server.py\" to start the application'\n")
        
        # Make the script executable
        try:
            os.chmod("set_email_env.sh", 0o755)
        except:
            pass
        
        print("\nA shell script 'set_email_env.sh' has been created.")
        print("Run 'source set_email_env.sh' before starting the server each time.")
        print("Or add these lines to your ~/.bashrc or ~/.zshrc file:")
        print(f"export EMAIL_USERNAME='{email}'")
        print("export EMAIL_PASSWORD='your_app_password'")
    
    else:
        print(f"\nUnrecognized operating system: {system}")
        print("Please set the following environment variables manually:")
        print(f"EMAIL_USERNAME={email}")
        print("EMAIL_PASSWORD=your_app_password")
    
    print("\nDo you want to test the email configuration?")
    test_email = input("Run the email test now? (y/n): ").lower() == 'y'
    
    if test_email:
        try:
            # Set environment variables for current process
            os.environ["EMAIL_USERNAME"] = email
            os.environ["EMAIL_PASSWORD"] = password
            
            print("\nRunning email test...")
            from test_email import test_gmail_connection
            test_gmail_connection()
        except Exception as e:
            print(f"Error running email test: {str(e)}")
            print("Please run 'python test_email.py' manually.")

if __name__ == "__main__":
    setup_email_variables() 