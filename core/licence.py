"""
Systeme de licence RENFORCE - B-NDEKE Comptability One
La cle est LIEE a l'email du client (anti-partage)
Limite : 3 machines par code (via serveur Google Sheets)
"""
import hmac
import hashlib
import os
import sys
import socket
import uuid
import platform
from datetime import datetime, timedelta

from database import get_connection


# ===== SECRET INTERNE =====
_SECRET = "BNDEKE2025COMPTABILITYONESECRETKEYv1"


# ===== HASH EMAIL =====
def _hash_email(email):
    email = email.strip().lower()
    h = hashlib.sha256(email.encode("utf-8")).hexdigest()[:8].upper()
    return h


# ===== DOSSIER PERSISTANT =====
def _get_dossier_persistant():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.path.expanduser("~/.config")
    dossier = os.path.join(base, "B-NDEKE")
    os.makedirs(dossier, exist_ok=True)
    return dossier


def _get_fichier_licence():
    return os.path.join(_get_dossier_persistant(), "licence.dat")


def _get_fichier_machine_id():
    return os.path.join(_get_dossier_persistant(), "machine_id.dat")


def _sauvegarder_dans_fichier(cle, email=None):
    try:
        with open(_get_fichier_licence(), "w", encoding="utf-8") as f:
            f.write(f"{cle.strip().upper()}\n{email or ''}")
        return True
    except Exception as e:
        print(f"[Erreur sauvegarde licence] {e}")
        return False


def _lire_fichier_licence():
    try:
        chemin = _get_fichier_licence()
        if os.path.exists(chemin):
            with open(chemin, "r", encoding="utf-8") as f:
                lignes = f.read().strip().split("\n")
                cle = lignes[0].strip() if len(lignes) > 0 and lignes[0] else None
                email = lignes[1].strip() if len(lignes) > 1 and lignes[1] else None
                return cle, email
    except Exception:
        pass
    return None, None


# ===== IDENTIFIANT UNIQUE DE MACHINE =====
def _get_machine_id():
    """
    Retourne un identifiant stable et unique pour cette machine.
    Stocke dans %APPDATA%\\B-NDEKE\\machine_id.dat pour rester identique
    meme si la config reseau change.
    """
    fichier = _get_fichier_machine_id()

    # Si deja genere, on le relit
    try:
        if os.path.exists(fichier):
            with open(fichier, "r", encoding="utf-8") as f:
                val = f.read().strip()
                if val:
                    return val
    except Exception:
        pass

    # Sinon on le genere
    parts = []
    try:
        parts.append(socket.gethostname())
    except Exception:
        parts.append("no-host")
    try:
        parts.append(str(uuid.getnode()))  # MAC address
    except Exception:
        parts.append("no-mac")
    parts.append(os.environ.get("USERNAME") or os.environ.get("USER", "user"))
    parts.append(platform.system())

    raw = "|".join(parts)
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16].upper()
    machine_id = f"{h[0:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"

    try:
        with open(fichier, "w", encoding="utf-8") as f:
            f.write(machine_id)
    except Exception:
        pass

    return machine_id


# ===== GENERATION DE CLE =====
def generer_cle(client_code, date_expiration, email_client):
    client_code = str(client_code).upper().replace("-", "").replace(" ", "")[:5]
    if len(client_code) < 3:
        client_code = client_code.ljust(3, "X")

    if isinstance(date_expiration, str):
        expiration = date_expiration
    else:
        expiration = date_expiration.strftime("%Y%m%d")

    sig = _signature(client_code, expiration, email_client)
    return f"BNDEKE-{client_code}-{expiration}-{sig}"


def _signature(client_code, expiration, email_client):
    email_hash = _hash_email(email_client)
    message = f"{client_code}-{expiration}-{email_hash}"
    sig = hmac.new(
        _SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:8].upper()
    return sig


# ===== VERIFICATION DE CLE =====
def verifier_cle(cle, email_client=None):
    if not cle:
        return False, "Aucune cle fournie", None

    cle = cle.strip().upper()
    parties = cle.split("-")
    if len(parties) != 4:
        return False, "Format de cle invalide", None

    prefixe, client_code, expiration, sig = parties
    if prefixe != "BNDEKE":
        return False, "Cle non reconnue", None

    if email_client is None:
        _, email_stocke = _lire_fichier_licence()
        if not email_stocke:
            try:
                from core.parametres import get_parametre
                email_stocke = get_parametre("licence_email")
            except Exception:
                pass
        email_client = email_stocke

    if not email_client:
        return False, "Email client introuvable pour verifier la licence", None

    sig_attendue = _signature(client_code, expiration, email_client)
    if not hmac.compare_digest(sig, sig_attendue):
        return False, (
            "CLE INVALIDE.\n\n"
            "Cette cle ne correspond PAS a votre email.\n"
            "Elle a ete generee pour un autre client.\n\n"
            "Contactez B-NDEKE pour obtenir votre propre cle.\n"
            "Email : supportbndekecomptability@gmail.com"
        ), None

    try:
        date_expiration = datetime.strptime(expiration, "%Y%m%d")
    except ValueError:
        return False, "Date d'expiration invalide", None

    maintenant = datetime.now()
    if maintenant > date_expiration:
        jours = (maintenant - date_expiration).days
        return False, (
            f"Licence expiree depuis {jours} jour(s)\n\n"
            f"Expiree le : {date_expiration.strftime('%d/%m/%Y')}\n\n"
            f"Contactez B-NDEKE pour renouveler.\n"
            f"Email : supportbndekecomptability@gmail.com"
        ), None

    jours_restants = (date_expiration - maintenant).days

    return True, (
        f"Licence valide\n\n"
        f"Client : {client_code}\n"
        f"Email : {email_client}\n"
        f"Expire le : {date_expiration.strftime('%d/%m/%Y')}\n"
        f"Jours restants : {jours_restants}"
    ), {
        "client_code": client_code,
        "email": email_client,
        "expiration": date_expiration,
        "jours_restants": jours_restants,
    }


# ===== GESTION LOCALE =====
def get_licence_stockee():
    cle, email = _lire_fichier_licence()
    if cle:
        return cle, email

    try:
        from core.parametres import get_parametre
        cle = get_parametre("licence_key")
        email = get_parametre("licence_email")
        if cle:
            _sauvegarder_dans_fichier(cle, email)
            return cle, email
    except Exception:
        pass

    return None, None


def enregistrer_licence(cle, email_client):
    cle = cle.strip().upper()
    _sauvegarder_dans_fichier(cle, email_client)
    try:
        from core.parametres import set_parametre
        set_parametre("licence_key", cle)
        set_parametre("licence_email", email_client)
    except Exception as e:
        print(f"[Erreur enregistrement BDD] {e}")


def get_date_activation():
    try:
        from core.parametres import get_parametre
        return get_parametre("licence_date_activation")
    except Exception:
        return None


def enregistrer_date_activation():
    try:
        from core.parametres import set_parametre, get_parametre
        if not get_parametre("licence_date_activation"):
            set_parametre("licence_date_activation",
                          datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    except Exception:
        pass


def licence_est_valide():
    cle, email = get_licence_stockee()
    if not cle:
        return False, "Aucune licence activee sur ce poste", None
    if not email:
        return False, "Aucun email associe a la licence", None
    return verifier_cle(cle, email)


# ============================================================
# ACTIVATION AVEC VERIFICATION SERVEUR (limite 3 machines)
# ============================================================
def activer_licence_avec_serveur(cle, email_client):
    """
    Fonction a appeler depuis l'UI a la place de 'enregistrer_licence'.
    Verifie la cle localement ET aupres du serveur (max 3 machines).

    Retourne (ok, message, info)
    """
    cle = (cle or "").strip().upper()
    email_client = (email_client or "").strip().lower()

    if not cle or not email_client:
        return False, "Cle et email obligatoires.", None

    # 1. Verification locale (signature + date)
    ok, msg, info = verifier_cle(cle, email_client)
    if not ok:
        return False, msg, None

    # 2. Verification aupres du serveur
    try:
        from core.activation_serveur import verifier_et_enregistrer
    except Exception as e:
        return False, f"Module serveur introuvable : {e}", None

    machine_id = _get_machine_id()
    print(f"[SERVEUR] Activation : code={cle} machine={machine_id}")

    ok_srv, status, msg_srv, count, max_m = verifier_et_enregistrer(
        cle, machine_id, email_client
    )

    # 3. Cas "limite atteinte"
    if status == "limit_reached":
        return False, (
            f"LIMITE DE MACHINES ATTEINTE\n\n"
            f"Cette licence est deja utilisee sur {count} machine(s) "
            f"sur {max_m} autorisees.\n\n"
            f"Vous ne pouvez pas activer une nouvelle machine avec ce code.\n\n"
            f"Contactez B-NDEKE pour augmenter votre nombre de machines :\n"
            f"supportbndekecomptability@gmail.com"
        ), None

    # 4. Autre erreur
    if not ok_srv:
        return False, (
            f"Impossible d'activer la licence.\n\n"
            f"{msg_srv}\n\n"
            f"Verifiez votre connexion Internet et reessayez."
        ), None

    # 5. OK -> enregistrer localement
    enregistrer_licence(cle, email_client)
    enregistrer_date_activation()

    if status == "already_activated":
        message_final = (
            f"Cette machine etait deja activee avec ce code.\n"
            f"Activation confirmee ({count}/{max_m} machines)."
        )
    else:
        message_final = (
            f"Activation reussie !\n"
            f"Cette machine est la {count}eme sur {max_m} autorisees."
        )

    return True, message_final, info


# ===== CONTACT VENDEUR =====
VENDEUR_EMAIL = "supportbndekecomptability@gmail.com"
VENDEUR_NOM = "B-NDEKE Comptability One"


# ============================================================
# ENVOI D'EMAIL
# ============================================================
def _envoyer_email_silencieux(sujet, corps):
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
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "inconnu"
    return {
        "nom_machine": hostname,
        "os": f"{platform.system()} {platform.release()}",
        "utilisateur": os.environ.get("USERNAME") or os.environ.get("USER", "inconnu"),
        "machine_id": _get_machine_id(),
    }


def _generer_code_client(email):
    base = email.split("@")[0].upper()
    base = "".join(c for c in base if c.isalnum())
    code = base[:5]
    if len(code) < 3:
        code = code.ljust(3, "X")
    return code


# ============================================================
# DEMANDE DE CODE
# ============================================================
def envoyer_demande_code(email_client):
    info = _get_info_machine()
    client_code = _generer_code_client(email_client)
    expiration = datetime.now() + timedelta(days=365)
    cle_generee = generer_cle(client_code, expiration, email_client)

    sujet = f"[B-NDEKE] CLE D'ACTIVATION pour {email_client}"

    corps = f"""
============================================================
   NOUVELLE DEMANDE D'ACTIVATION B-NDEKE
============================================================

    >>> CLE A ENVOYER AU CLIENT <<<

    {cle_generee}

============================================================

Cette cle fonctionne UNIQUEMENT avec l'email :
    {email_client}

Validite : {expiration.strftime('%d/%m/%Y')} (1 an)

============================================================
   ACTION A FAIRE
============================================================
1. Copiez la cle ci-dessus
2. Envoyez-la au client par WhatsApp, SMS ou email
3. Le client la collera dans l'app pour activer

============================================================
   INFORMATIONS CLIENT
============================================================
Email du client      : {email_client}
Code client          : {client_code}
Date de la demande   : {datetime.now().strftime('%d/%m/%Y a %H:%M:%S')}

INFORMATIONS MACHINE
============================================================
Nom de l'ordinateur  : {info['nom_machine']}
Machine ID           : {info['machine_id']}
Utilisateur Windows  : {info['utilisateur']}
Systeme d'exploitation : {info['os']}

============================================================
   B-NDEKE Comptability One
============================================================
""".strip()

    return _envoyer_email_silencieux(sujet, corps)


def envoyer_confirmation_activation(email_client, nom_ecole, cle_utilisee, infos_ecole=None):
    info = _get_info_machine()
    sujet = f"[B-NDEKE] Activation reussie - {nom_ecole}"

    infos_ecole_texte = ""
    if infos_ecole:
        for k, v in infos_ecole.items():
            infos_ecole_texte += f"{k:<20} : {v}\n"

    corps = f"""
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
Machine ID           : {info['machine_id']}
Utilisateur Windows  : {info['utilisateur']}
Systeme d'exploitation : {info['os']}

Cordialement,
B-NDEKE Comptability One
""".strip()

    return _envoyer_email_silencieux(sujet, corps)