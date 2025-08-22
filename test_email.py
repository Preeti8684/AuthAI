import os
import smtplib
import getpass
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_connection():
    """Test the SMTP connection to Gmail and send a test email."""
    
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
    body = """
    This is a test email from AuthAI.
    
    If you're receiving this email, your email configuration is working correctly!
    
    You can now use the email-based permission functionality in AuthAI.
    """
    
    message.attach(MIMEText(body, "plain"))
    
    server = None
    try:
        print("\nConnecting to Gmail SMTP server...")
        # Create secure connection with Gmail's SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.set_debuglevel(1)  # Enable debugging output
        server.starttls()  # Secure the connection
        
        print("Logging in to your Gmail account...")
        server.login(email_username, email_password)
        
        print(f"Sending test email to {recipient}...")
        server.send_message(message)
        
        print("\n✅ SUCCESS! Test email sent successfully.")
        print("Your email configuration is working correctly.")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print("\n❌ ERROR: Authentication failed.")
        print("Gmail rejected your username or password.")
        print("\nIMPORTANT: Gmail requires an App Password, not your regular account password!")
        print("\nTo create an App Password:")
        print("1. Go to your Google Account at https://myaccount.google.com/")
        print("2. Select 'Security' from the left menu")
        print("3. Under 'Signing in to Google', select '2-Step Verification' (enable it if not already)")
        print("4. Scroll down to 'App passwords' and select it")
        print("5. Select 'Mail' as the app and 'Other' as the device")
        print("6. Enter 'AuthAI' as the name and click 'Generate'")
        print("7. Copy the 16-character password that appears")
        return False
        
    except smtplib.SMTPConnectError as e:
        print("\n❌ ERROR: Connection to Gmail server failed.")
        print(f"Error details: {str(e)}")
        print("\nPossible reasons:")
        print("- Your internet connection might be down")
        print("- Gmail SMTP server might be temporarily unavailable")
        print("- Your ISP might be blocking outgoing SMTP connections")
        return False
        
    except socket.error as e:
        print(f"\n❌ ERROR: Socket error occurred: {str(e)}")
        print("This is likely a network connectivity issue.")
        print("Please check your internet connection and try again.")
        return False
        
    except Exception as e:
        print("\n❌ ERROR: Failed to send test email.")
        print(f"Error details: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        # Provide troubleshooting advice
        print("\nTroubleshooting tips:")
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
    print("===== AuthAI Email Configuration Test =====\n")
    test_gmail_connection()
