import smtplib
import ssl
from email.message import EmailMessage
import os

def test_smtp():
    # Use environment variables if possible, or fall back to known working values
    host = "mail.privateemail.com"
    port = 465
    user = os.environ.get('MAIL_USERNAME', "info@cresdynamics.com")
    password = os.environ.get('MAIL_PASSWORD', "CresDynamics@2026")
    
    msg = EmailMessage()
    msg.set_content(f'This is a diagnostic test to verify SMTP credentials for {user}.')
    msg['Subject'] = 'OCH SMTP Diagnostic Clean'
    msg['From'] = user
    msg['To'] = user

    print(f"Attempting to connect to {host} on port {port} (SSL)...")
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as server:
            print("Connected. Attempting login...")
            server.login(user, password)
            print("Login successful. Sending test email...")
            server.send_message(msg)
            print("SMTP verification SUCCESSFUL!")
            return True
    except Exception as e:
        print(f"SMTP verification FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    test_smtp()
