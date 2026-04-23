import os
import smtplib
import ssl
from email.message import EmailMessage

def test_smtp():
    msg = EmailMessage()
    msg.set_content('This is a diagnostic test to verify SMTP credentials for info@cresdynamics.com.')
    msg['Subject'] = 'OCH SMTP Diagnostic'
    msg['From'] = 'info@cresdynamics.com'
    msg['To'] = 'info@cresdynamics.com'

    print("Attempting to connect to mail.privateemail.com on port 465 (SSL)...")
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("mail.privateemail.com", 465, context=context) as server:
            print("Connected. Attempting login...")
            server.login("info@cresdynamics.com", os.environ.get('MAIL_PASSWORD', ''))
            print("Login successful. Sending test email...")
            server.send_message(msg)
            print("✅ SMTP verification SUCCESSFUL!")
            return True
    except Exception as e:
        print(f"❌ SMTP verification FAILED: {e}")
        return False

if __name__ == "__main__":
    test_smtp()
