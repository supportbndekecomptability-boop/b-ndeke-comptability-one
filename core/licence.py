# ===== INFOS CONTACT VENDEUR =====
VENDEUR_EMAIL = "supportbndekecomptability@gmail.com"
VENDEUR_NOM = "B-NDEKE Comptability One"


# ============================================================
# ENVOI D'EMAIL SILENCIEUX VERS LE VENDEUR
# ============================================================
def _envoyer_email_silencieux(sujet, corps):
    """
    Envoie un email silencieux vers VOTRE compte.
    Aucun affichage pour le client.
    """
    try:
        from config import (
            VENDEUR_EMAIL, VENDEUR_SMTP_PASSWORD,
            VENDEUR_SMTP_SERVER, VENDEUR_SMTP_PORT,
        )
    except Exception:
        return False, "Config vendeur introuvable"

    if not VENDEUR_EMAIL or VENDEUR_SMTP_PASSWORD.startswith("xxxx"):
        return False, "Email vendeur non configure"

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg["From"] = VENDEUR_EMAIL
        msg["To"] = VENDEUR_EMAIL
        msg["Subject"] = sujet
        msg.attach(MIMEText(corps, "plain", "utf-8"))

        server = smtplib.SMTP(VENDEUR_SMTP_SERVER, VENDEUR_SMTP_PORT, timeout=15)
        server.starttls()
        server.login(VENDEUR_EMAIL, VENDEUR_SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True, "Email envoye"
    except Exception as e:
        print(f"[Erreur email silencieux] {e}")
        return False, str(e)


def _get_info_machine():
    """Retourne les infos de la machine pour identification"""
    import platform
    import socket
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "inconnu"

    return {
        "nom_machine": hostname,
        "os": f"{platform.system()} {platform.release()}",
        "utilisateur": os.environ.get("USERNAME") or os.environ.get("USER", "inconnu"),
    }


def envoyer_demande_code(email_client):
    """
    Envoie la demande de code aupres du vendeur.
    Appelee quand le client clique sur 'Demander le code'.
    """
    info = _get_info_machine()

    sujet = f"[B-NDEKE] Nouvelle demande de code - {email_client}"

    corps = f"""
Bonjour B-NDEKE,

Un nouveau client demande une cle d'activation pour B-NDEKE Comptability One.

============================================================
INFORMATIONS DU CLIENT
============================================================
Email du client      : {email_client}
Date de la demande   : {datetime.now().strftime('%d/%m/%Y a %H:%M:%S')}

INFORMATIONS MACHINE
============================================================
Nom de l'ordinateur  : {info['nom_machine']}
Utilisateur Windows  : {info['utilisateur']}
Systeme d'exploitation : {info['os']}

============================================================
ACTION A FAIRE
============================================================
1. Generez une cle avec : python generer_licence.py
2. Envoyez-la par email au client : {email_client}
3. Le client la collera dans l'app pour activer

Cordialement,
B-NDEKE Comptability One
""".strip()

    return _envoyer_email_silencieux(sujet, corps)


def envoyer_confirmation_activation(email_client, nom_ecole, cle_utilisee, infos_ecole=None):
    """
    Envoie une confirmation silencieuse au vendeur apres activation reussie.
    Appelee apres que le client a rempli ses infos d'ecole.
    """
    info = _get_info_machine()

    sujet = f"[B-NDEKE] Activation reussie - {nom_ecole}"

    infos_ecole_texte = ""
    if infos_ecole:
        for k, v in infos_ecole.items():
            infos_ecole_texte += f"{k:<20} : {v}\n"

    corps = f"""
Bonjour B-NDEKE,

Un nouveau client vient d'activer B-NDEKE Comptability One.

============================================================
INFORMATIONS ECOLE
============================================================
Nom de l'ecole       : {nom_ecole}
{infos_ecole_texte}
============================================================
INFORMATIONS CLIENT
============================================================
Email du client      : {email_client}
Date d'activation    : {datetime.now().strftime('%d/%m/%Y a %H:%M:%S')}
Cle d'activation     : {cle_utilisee}

============================================================
INFORMATIONS MACHINE
============================================================
Nom de l'ordinateur  : {info['nom_machine']}
Utilisateur Windows  : {info['utilisateur']}
Systeme d'exploitation : {info['os']}

============================================================
STATUT
============================================================
Ce client est maintenant actif sur sa machine.
La cle sera valide jusqu'a expiration.

Cordialement,
B-NDEKE Comptability One
""".strip()

    return _envoyer_email_silencieux(sujet, corps)