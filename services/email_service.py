"""
Service d'envoi d'email - lit la config depuis la base de donnees
"""
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from core.parametres import get_config_email
from config import ECOLE_NOM


def envoyer_rapport_email(destinataires, sujet, message, chemins_pdf=None):
    """
    Envoie un email avec pieces jointes PDF.
    Lit la configuration depuis la base de donnees.
    """
    if isinstance(destinataires, str):
        destinataires = [destinataires]

    if not destinataires:
        return False, "Aucun destinataire specifie"

    config = get_config_email()

    if not config["user"] or not config["password"]:
        return False, ("Email non configure.\n\n"
                       "Cliquez sur 'Configurer l'email' dans la page Rapports.")

    msg = MIMEMultipart()
    msg["From"] = f"{config['from_name']} <{config['user']}>"
    msg["To"] = ", ".join(destinataires)
    msg["Subject"] = sujet

    corps = f"""{message}

--
{ECOLE_NOM}
Rapport genere automatiquement par B-NDEKE Comptability One
"""
    msg.attach(MIMEText(corps, "plain", "utf-8"))

    if chemins_pdf:
        for chemin in chemins_pdf:
            if not os.path.exists(chemin):
                continue
            try:
                with open(chemin, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                nom_fichier = os.path.basename(chemin)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename=\"{nom_fichier}\"",
                )
                msg.attach(part)
            except Exception as e:
                return False, f"Erreur lecture fichier {chemin} : {e}"

    try:
        server = smtplib.SMTP(config["server"], config["port"], timeout=30)
        server.starttls()
        server.login(config["user"], config["password"])
        server.send_message(msg)
        server.quit()
        return True, f"Email envoye avec succes a {len(destinataires)} destinataire(s)"
    except smtplib.SMTPAuthenticationError:
        return False, ("Erreur d'authentification SMTP.\n\n"
                       "Pour Gmail :\n"
                       "1. Activez la validation en 2 etapes\n"
                       "2. Generez un 'Mot de passe d'application'\n"
                       "3. Collez-le dans le champ Mot de passe")
    except smtplib.SMTPException as e:
        return False, f"Erreur SMTP : {e}"
    except Exception as e:
        return False, f"Erreur inattendue : {e}"


def tester_configuration():
    """Teste la connexion SMTP sans envoyer d'email"""
    config = get_config_email()

    if not config["user"] or not config["password"]:
        return False, "Email non configure. Cliquez sur 'Configurer l'email'."

    try:
        server = smtplib.SMTP(config["server"], config["port"], timeout=15)
        server.starttls()
        server.login(config["user"], config["password"])
        server.quit()
        return True, f"Configuration valide pour {config['user']}"
    except smtplib.SMTPAuthenticationError:
        return False, "Identifiants incorrects. Verifiez l'email et le mot de passe d'application."
    except Exception as e:
        return False, f"Erreur : {e}"