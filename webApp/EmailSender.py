import smtplib
from email.message import EmailMessage
import threading
from Schema import *
from datetime import date, datetime, timedelta
from flask import current_app as app
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email import encoders
from pathlib import Path
import os



class EmailSender:
    """
    Sends Email to receipient using Multithreading.
    """
    def __init__(self, mode="no-reply"):
        if mode == "examsofficer":
            self.senderEmail = "examsofficer@ateamacademy.co.uk"
            self.sendPassword = os.environ.get("MAIL_EXAMS_PASSWORD", "")
        else:
            self.senderEmail = "no-reply@ateamacad.co.uk"
            self.sendPassword = os.environ.get("MAIL_NOREPLY_PASSWORD", "")
        self.servername = 'smtp.ionos.co.uk'
        self.serverPort = 587
        self.msg = EmailMessage()
        self.msg['From']=self.senderEmail

    def setEmail(self, text, subtype="html"):
        """
        Sets the content of the email message.

            Parameters:
                    text: The main content of the email
        """
        # self.msg.set_content("")
        self.msg.add_alternative(text, subtype=subtype)

    def setSubject(self, text):
        """
        Sets the subject of the email message.

            Parameters:
                    text: The subject of the email
        """
        self.msg['Subject'] = text
    
    def setReceipient(self, email):
        """
        Sets the email address of recipient.

            Parameters:
                    text: The recipient email address.
        """
        self.msg['Bcc'] = 'safwaan@ateamacademy.co.uk'
        self.msg['To'] = email
        
    def setFiles(self, files):
        for path in files:
            part = MIMEBase('application', "octet-stream")
            with open(path, 'rb') as file:
                part = MIMEApplication(file.read(),_subtype="pdf")
            part.add_header('Content-Disposition','attachment', filename=os.path.basename(path))
            self.msg.attach(part)


    def send(self, email, subject, message, files=None, subtype="html"):
        """
        Connects to email server using smtplib and sets appropriate values.

            Parameters:
                    email (string): email address of receipient
                    subject (string): subject of email
                    message (string): Main message of email

            Returns:
                    Status Code (int): Status code 400 for error, nothing for no error.
        """
        try:
            self.setEmail(message, subtype)
            self.setSubject(subject)
            self.setReceipient(email)
            self.setFiles(files if files is not None else [])
            self.connect()
            
            with app.app_context():
                if isinstance(email, list): 
                    db.session.add(log(role = "admin", message=" An email with the subject '" + subject + "' was sent to " + ", ".join(str(element) for element in email), date=datetime.utcnow()))
                else: 
                    db.session.add(log(role = "admin", message=" An email with the subject '" + subject + "' was sent to " + email, date=datetime.utcnow()))

                db.session.commit()

            return [200, 'The message was sent']
        except smtplib.SMTPRecipientsRefused as e:
            with app.app_context():
                if email == "" or email == []:
                    email = "NO EMAIL SUPPLIED"
                    
                if isinstance(email, list): 
                    db.session.add(log(role = "admin", message=" An email with the subject '" + subject + "' could not be sent to " + ", ".join(str(element) for element in email) + " because of " + str(e), date=datetime.utcnow()))
                else: 
                    db.session.add(log(role = "admin", message=" An email with the subject '" + subject + "' could not be sent to " + email + " because of " + str(e), date=datetime.utcnow()))

                db.session.commit()
            print(e)
            return 400
        except Exception as e:
            with app.app_context():
                if email == "" or email == []:
                    email = "NO EMAIL SUPPLIED"
                    
                if isinstance(email, list): 
                    db.session.add(log(role="admin", message=" An email with the subject '" + subject + "' could not be sent to " + ", ".join(str(element) for element in email) + " because of " + str(e), date=datetime.utcnow()))
                else: 
                    db.session.add(log(role="admin", message=" An email with the subject '" + subject + "' could not be sent to " + email + " because of " + str(e), date=datetime.utcnow()))

                db.session.commit()
            print(e)
            return 400
        

    def connect(self):
        """
        Sends email to recipient after establishing connection
        """
        server = smtplib.SMTP(self.servername, self.serverPort)
        server.starttls()
        server.login(self.senderEmail, self.sendPassword)
        server.send_message(self.msg)
        self.msg.clear()
        server.quit()

    def sendThreaded(self, email, subject, message):
        """
        Creates a new thread per email sent.

            Parameters:
                    email (string): email address of recipient
                    subject (string): subject of email
                    message (string): Main message of email
        """
        thread = threading.Thread(target=self.send, args=(email, subject, message))
        thread.start()

# if __name__ == "__main__":
#     sender = EmailSender()
#     sender.sendThreaded("asafwaan03@gmail.com", "test email", "this is a test please ignore")