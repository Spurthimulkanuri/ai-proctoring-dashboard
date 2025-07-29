from dotenv import load_dotenv
load_dotenv()

from sib_api_v3_sdk.models.send_smtp_email import SendSmtpEmail
import os

def send_email(recipient, subject, html_body, attachments=None):
    sender = {
        "name": os.getenv("SENDER_NAME"),
        "email": os.getenv("SENDER_EMAIL")
    }

    # 🧪 ADD THIS DEBUG LINE
    print("SENDER DEBUG:", sender)

    smtp_email = SendSmtpEmail(
        to=[{"email": recipient}],
        sender=sender,
        subject=subject,
        html_content=html_body,
        attachment=attachments
    )

    # Rest of your Brevo send code...
if __name__ == "__main__":
    send_email(
        recipient="shivlachinki06@gmail.com",
        subject="Test Sender Debug",
        html_body="<h1>This is a test</h1>",
        attachments=[]
    )

