import smtplib
from email.mime.text import MIMEText
import os

# Set environment variables
os.environ['EMAIL_QUEUE_PATH'] = 'D:/Internship/ChatApp/ChatApp/email_queue.pkl'
os.environ['EMAIL_SENDER'] = 'sp23bcs074@gmail.com'
os.environ['EMAIL_APP_PASSWORD'] = 'kxxhinyktvqtiouf'

from EmailEnqueue import EmailEnqueue

sender = os.environ.get('EMAIL_SENDER')
app_password = os.environ.get('EMAIL_APP_PASSWORD')

def send_welcome_email(receiver_email, user_password):  # NOW TAKES user_password!
    msg = MIMEText(f'''
Hello,

Welcome to DreamsChat! 
Your account has been successfully created.

Login Details:
    Email: {receiver_email}
    Password: {user_password}

Please change your password after first login.

Best regards,
Dreamschat Team 
''')
    msg["Subject"] = "Welcome to DreamsChat!"
    msg["From"] = sender
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender, app_password)
            server.send_message(msg)
        print(f"Email sent successfully to {receiver_email}")
        return True
    except Exception as e:
        print(f"Failed to send to {receiver_email}: {str(e)}")
        return False

def process_email_queue():
    enqueue = EmailEnqueue()
    queue_size = enqueue.get_queue_size()
    
    if queue_size == 0:
        print("Queue is empty - nothing to process")
        return
    
    print(f"Processing {queue_size} email(s) in queue...")
    
    sent_count = 0
    failed_count = 0
    
    while enqueue.get_queue_size() > 0:
        email_password = enqueue.email_dequeue()  # Gets (email, password) tuple
        
        if email_password:
            email, user_password = email_password  # Unpack tuple
            if send_welcome_email(email, user_password):  # Pass user_password!
                sent_count += 1
            else:
                enqueue.email_enqueue(email, user_password)  # Requeue both
                failed_count += 1
        else:
            break
    
    print(f"Summary: {sent_count} sent, {failed_count} failed (requeued)")

if __name__ == "__main__":
    process_email_queue()
