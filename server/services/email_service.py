import smtplib
from email.message import EmailMessage
from fastapi import HTTPException

EMAIL_ADDRESS = "hrmenager2025@gmail.com"
EMAIL_PASSWORD = "fczv gsef gqyy oydb"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587

def send_invite_email(to_email: str, invite_id: str):
    msg = EmailMessage()
    msg['Subject'] = "Invite za kreiranje predavačkog profila na Školi matematike"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(
        f"Pozdrav, Pozvani ste da se registrujete kao predavač na platformi Škola Matematike. "
        f"Kliknite na link ispod da biste kreirali svoj nalog:\n\n"
        f"http://localhost:5173/accept-invite/{invite_id}"
    )
    _send_email(msg)

def send_reset_email(to_email: str, reset_link: str):
    msg = EmailMessage()
    msg['Subject'] = "Reset lozinke - Škola matematike"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(
        f"Pozdrav, Primili smo zahtjev za resetovanje Vaše lozinke. "
        f"Kliknite na link:\n\n{reset_link}"
    )
    _send_email(msg)

def _send_email(msg: EmailMessage):
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Slanje emaila nije uspjelo: {str(e)}")
