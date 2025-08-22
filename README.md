# AuthAI - Face Authentication System

AuthAI is a secure face authentication system built with Python, Flask, and modern web technologies.

## Features

- User registration and authentication
- Face scanning and recognition
- Permission management
- Profile management
- Activity logging
- Security features

## Setup Instructions

### Prerequisites

- Python 3.8+
- MongoDB
- A Gmail account (for sending emails)

### Installation

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: 
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Start MongoDB service
6. Run the application: `python server.py`

### Setting up Email Functionality

The application uses Gmail to send permission emails. To enable this feature:

1. **Create a Gmail App Password**:
   - Go to your [Google Account](https://myaccount.google.com/)
   - Select "Security" from the left menu
   - Under "Signing in to Google", select "2-Step Verification" (enable it if not already enabled)
   - Scroll down to "App passwords" and select it
   - Select "Mail" as the app and "Other" as the device
   - Enter "AuthAI" as the name and click "Generate"
   - Copy the 16-character password that appears

2. **Set Environment Variables**:
   - Set the `EMAIL_USERNAME` environment variable to your Gmail address
   - Set the `EMAIL_PASSWORD` environment variable to the App Password you generated

   Windows:
   ```
   set EMAIL_USERNAME=your.email@gmail.com
   set EMAIL_PASSWORD=your-app-password
   ```

   Linux/Mac:
   ```
   export EMAIL_USERNAME=your.email@gmail.com
   export EMAIL_PASSWORD=your-app-password
   ```

3. **Test Email Functionality**:
   - Run `python test_email.py` to test that emails are being sent correctly

## Usage Flow

1. **Home Page**: View information about AuthAI
2. **Sign Up**: Create a new account with name, email and password
3. **Login**: Authenticate with email and password
4. **Face Scan**: Register your face for authentication
5. **Face Recognition**: Verify your identity using face recognition
6. **Dashboard**: View your profile and recent activities
7. **Settings**: Update your profile settings
8. **Logout**: Securely log out of the system

## Technologies

- **Backend**: Python, Flask
- **Database**: MongoDB
- **Frontend**: HTML, CSS, JavaScript, TailwindCSS
- **Face Recognition**: OpenCV
- **Security**: Bcrypt for password hashing, CSRF protection

## License

This project is licensed under the MIT License.

## Project Structure

```
authai/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── templates/
│   ├── home.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   └── face_scan.html
├── face_match.py
├── server.py
└── requirements.txt
```

## Security Features

- Face recognition using deep learning
- Anti-spoofing detection
- Secure password hashing
- Session management
- Activity logging
- MongoDB for secure data storage

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments

- VGGFace model for face recognition
- OpenCV for image processing
- Flask for the web framework
- MongoDB for data storage 