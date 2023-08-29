import smtplib
from email.message import EmailMessage


def sendMail(recipient, body_text, sender="draft"):
    message = EmailMessage()
    message.set_content(body_text)
    message['Subject'] = 'MLB Fantasy'
    message['From'] = sender + "@fantasy.zanzalaz.com"
    message['To'] = recipient

    smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
    smtp_server.ehlo()
    smtp_server.starttls()
    smtp_server.send_message(message)
    smtp_server.quit()
