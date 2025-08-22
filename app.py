#!/usr/bin/env python3
"""
Simplified Flask application for AuthAI with focus on core routes.
This file focuses on making the home, login, and signup pages accessible.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from markupsafe import Markup
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')

# Simple csrf_token stub for templates that call it
@app.context_processor
def inject_csrf_token():
    def csrf_token():
        return ""
    return dict(csrf_token=csrf_token)

@app.route('/')
def index():
    """Home page with landing content."""
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        # For testing, just redirect to dashboard
        flash('Login functionality is in testing mode. Use the server.py for full login.', 'info')
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user signup."""
    if request.method == 'POST':
        # For testing, just redirect to login
        flash('Signup functionality is in testing mode. Use the server.py for full signup.', 'info')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard page."""
    return render_template('dashboard.html', username="Test User", email="test@example.com")

if __name__ == '__main__':
    logger.info("Starting simplified AuthAI application...")
    # Run with settings that avoid socket errors
    app.run(debug=True, threaded=False, use_reloader=False, port=5000)
