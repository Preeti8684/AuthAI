@echo off
echo ===== AuthAI Server Launcher with Email Setup =====
echo.

REM Set email credentials
set EMAIL_USERNAME=kpreeti09050@gmail.com
set EMAIL_PASSWORD=kanika26

echo Email environment variables set:
echo USERNAME: %EMAIL_USERNAME%
echo.
echo IMPORTANT: If emails fail, you need a Gmail App Password
echo Visit: https://myaccount.google.com/security to create one
echo.

echo Starting server with fixed settings...
python run_fixed_server.py

pause 