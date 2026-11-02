import smtplib
from email.message import EmailMessage
from app.core.config import settings

def send_offer_email(offer, recipient: str | None = None) -> tuple[bool, str]:
    target = recipient or settings.smtp_to
    if not settings.smtp_host or not settings.smtp_from or not target:
        return False, "SMTP non configuré"
    msg = EmailMessage()
    msg["Subject"] = f"[JobRadar] {offer.title} – {offer.match_score}/100"
    msg["From"] = settings.smtp_from
    msg["To"] = target
    msg.set_content(
        f"{offer.title}\n{offer.company} – {offer.location}\n"
        f"Score : {offer.match_score}/100\n\n{offer.match_explanation}\n\n"
        f"Voir l'offre : {offer.source_url}"
    )
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
        return True, ""
    except Exception as exc:
        return False, str(exc)
