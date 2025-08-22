# Fixing Email Delivery Error in AuthAI

If you're seeing the "Email Delivery Failed" error message after face recognition, follow these steps to fix it:

## Step 1: Create a Gmail App Password

The application needs a special password to send emails through Gmail. This is different from your regular Gmail password.

1. Go to your [Google Account security settings](https://myaccount.google.com/security)
2. Make sure 2-Step Verification is enabled
3. Scroll down to "App passwords"
4. Select "Mail" as the app and "Windows Computer" as the device (or whatever is appropriate)
5. Click "Generate"
6. Google will display a 16-character password - copy this

## Step 2: Set Environment Variables

You need to set environment variables to store your email credentials securely:

### In Windows PowerShell:
```powershell
$env:EMAIL_USERNAME="your.email@gmail.com"
$env:EMAIL_PASSWORD="your-16-char-app-password"
```

### In Windows Command Prompt:
```cmd
set EMAIL_USERNAME=your.email@gmail.com
set EMAIL_PASSWORD=your-16-char-app-password
```

### In the same terminal window, run the application:
```
python server.py
```

## Step 3: Test Your Email Configuration

To check if your email setup is working correctly:

1. Open a new terminal window
2. Run the test script:
```
python test_email.py
```
3. When prompted, press "n" to send a test email to yourself
4. If successful, you'll see "Test email sent successfully!"

## Still Having Issues?

If you're still experiencing problems:

1. Check that you've entered the correct email address
2. Make sure you're using the 16-character App Password, not your regular Gmail password
3. Verify that 2-Step Verification is enabled on your Google account
4. Check your internet connection
5. Make sure no firewall is blocking the SMTP connection to Gmail
6. Try running the application with debug mode:
```powershell
$env:FLASK_DEBUG=1
python server.py
```

This will show more detailed error messages that can help diagnose the issue. 