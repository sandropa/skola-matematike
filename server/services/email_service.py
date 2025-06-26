import smtplib
from email.message import EmailMessage
from fastapi import HTTPException

EMAIL_ADDRESS = "hrmenager2025@gmail.com"
EMAIL_PASSWORD = "fczv gsef gqyy oydb"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587

def send_invite_email(to_email: str, invite_id: str):
    link = f"http://localhost:5173/accept-invite/{invite_id}"

    msg = EmailMessage()
    msg['Subject'] = "Poziv za registraciju - Škola matematike"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(
        f"Pozvani ste da se registrujete kao predavač. Otvorite link: {link}"
    )

    msg.add_alternative(f"""\
<!DOCTYPE html>
<html lang="bs">
<head>
  <meta charset="UTF-8">
  <style>
    body {{
      font-family: 'Segoe UI', sans-serif;
      background-color: #f9fafb;
      color: #333;
      padding: 30px;
    }}
    .container {{
      max-width: 600px;
      margin: auto;
      background-color: #ffffff;
      padding: 40px;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    .button {{
      display: inline-block;
      padding: 14px 28px;
      background-color: #3f51b5;
      color: #ffffff !important;
      text-decoration: none;
      border-radius: 6px;
      font-weight: bold;
      margin-top: 20px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h2>Poziv za registraciju</h2>
    <p>Pozvani ste da kreirate predavački nalog na platformi <strong>Škola Matematike</strong>.</p>
    <p>Kliknite na dugme ispod kako biste započeli registraciju:</p>
    <a href="{link}" class="button">Prihvati poziv</a>
  </div>
</body>
</html>
""", subtype='html')

    _send_email(msg)


def send_reset_email(to_email: str, reset_link: str):
    msg = EmailMessage()
    msg['Subject'] = "Reset lozinke - Škola Matematike"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(
        f"Resetujte svoju lozinku klikom na: {reset_link}"
    )

    msg.add_alternative(f"""\
<!DOCTYPE html>
<html lang="bs">
<head>
  <meta charset="UTF-8">
  <style>
    body {{
      font-family: 'Segoe UI', sans-serif;
      background-color: #f4f6f9;
      padding: 30px;
      color: #333;
    }}
    .container {{
      max-width: 600px;
      margin: auto;
      background-color: white;
      padding: 40px;
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    .button {{
      display: inline-block;
      padding: 14px 28px;
      background-color: #e91e63;
      color: #ffffff !important;
      text-decoration: none;
      border-radius: 6px;
      font-weight: bold;
      margin-top: 20px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h2>Reset lozinke</h2>
    <p>Zatražen je reset Vaše lozinke na platformi <strong>Škola Matematike</strong>.</p>
    <p>Kliknite na dugme ispod kako biste postavili novu lozinku:</p>
    <a href="{reset_link}" class="button">Postavi novu lozinku</a>
  </div>
</body>
</html>
""", subtype='html')

    _send_email(msg)


def _send_email(msg: EmailMessage):
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Slanje emaila nije uspjelo: {str(e)}")
