"""
Sauvegarde cloud CHIFFREE et OPT-IN - B-NDEKE Comptability One
L'ecole doit explicitement autoriser cette fonction.
Les donnees sont chiffrees et stockees sur le Drive B-NDEKE.
"""
import os
import json
import base64
import hashlib
import urllib.request
import urllib.parse
from datetime import datetime

from config import DB_PATH
from core.parametres import get_parametre, set_parametre

SERVEUR_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbxyJQnR-6JmxBXR1h3QxeXTrZb4J4AcveLgo6O7oeR892kxwWnD8Xj4E4yogXC4NDCM/exec"
)

CLE_SAUVEGARDE_CLOUD = "sauvegarde_cloud"
CLE_DERNIERE_BACKUP_CLOUD = "derniere_backup_cloud"
CLE_ACCEPTATION_CLOUD = "sauvegarde_cloud_acceptee"

_SECRET_CHIFFRE = "BNDEKE-BACKUP-SECRET-2026-V1"


def _xor_chiffre(data_bytes, cle):
    h = hashlib.sha256(cle.encode("utf-8")).digest()
    out = bytearray()
    for i, b in enumerate(data_bytes):
        out.append(b ^ h[i % len(h)])
    return bytes(out)


def _chiffrer_fichier(db_path, code):
    with open(db_path, "rb") as f:
        raw = f.read()
    chiffre = _xor_chiffre(raw, _SECRET_CHIFFRE + code)
    return base64.b64encode(chiffre).decode("ascii")


def _dechiffrer(content_b64, code):
    chiffre = base64.b64decode(content_b64)
    return _xor_chiffre(chiffre, _SECRET_CHIFFRE + code)


def activer_sauvegarde_cloud(actif):
    set_parametre(CLE_SAUVEGARDE_CLOUD, "1" if actif else "0")


def sauvegarde_cloud_active():
    return get_parametre(CLE_SAUVEGARDE_CLOUD) == "1"


def acceptation_cloud_faite():
    return get_parametre(CLE_ACCEPTATION_CLOUD) == "1"


def marquer_acceptation_cloud():
    set_parametre(CLE_ACCEPTATION_CLOUD, "1")


def get_derniere_backup_cloud():
    return get_parametre(CLE_DERNIERE_BACKUP_CLOUD) or "Jamais"


def sauvegarder_dans_cloud():
    """Envoie la base chiffree au serveur. Silencieux."""
    try:
        from core.licence import get_licence_stockee, _get_machine_id
        cle, email = get_licence_stockee()
        if not cle or not email:
            return False, "Pas de licence active"

        if not os.path.exists(DB_PATH):
            return False, "Base introuvable"

        try:
            from core.ecole import get_info_ecole
            nom_ecole = get_info_ecole().get("nom", "")
        except Exception:
            nom_ecole = ""

        content_b64 = _chiffrer_fichier(DB_PATH, cle)

        payload = {
            "action": "backup",
            "code": cle,
            "machine_id": _get_machine_id(),
            "nom_ecole": nom_ecole,
            "content_b64": content_b64,
            "date": datetime.now().strftime("%Y%m%d_%H%M%S"),
        }

        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            SERVEUR_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "B-NDEKE-App",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode("utf-8", errors="replace")

        try:
            data = json.loads(raw)
        except Exception:
            return False, f"Reponse invalide : {raw[:200]}"

        if data.get("ok"):
            set_parametre(
                CLE_DERNIERE_BACKUP_CLOUD,
                datetime.now().strftime("%d/%m/%Y %H:%M")
            )
            return True, data.get("message", "Sauvegarde cloud reussie.")
        return False, data.get("error", "Erreur inconnue")
    except Exception as e:
        return False, f"Erreur : {e}"


def lister_backups_cloud():
    """Retourne la liste des sauvegardes sur le serveur."""
    try:
        from core.licence import get_licence_stockee
        cle, _ = get_licence_stockee()
        if not cle:
            return []
        url = SERVEUR_URL + "?" + urllib.parse.urlencode({
            "action": "list",
            "code": cle,
        })
        req = urllib.request.Request(url, headers={"User-Agent": "B-NDEKE-App"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        if data.get("ok"):
            return data.get("backups", [])
    except Exception as e:
        print(f"[BACKUP] Erreur list : {e}")
    return []


def restaurer_depuis_cloud(file_id):
    """Telecharge et restaure un backup cloud."""
    try:
        from core.licence import get_licence_stockee
        from core.ecole import sauvegarder_base

        cle, _ = get_licence_stockee()
        if not cle:
            return False, "Pas de licence"

        url = SERVEUR_URL + "?" + urllib.parse.urlencode({
            "action": "restore",
            "file_id": file_id,
        })
        req = urllib.request.Request(url, headers={"User-Agent": "B-NDEKE-App"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8"))

        if not data.get("ok"):
            return False, data.get("error", "Erreur")

        content_b64 = data.get("content_b64", "")
        raw = _dechiffrer(content_b64, cle)

        # Sauvegarder la base actuelle avant d'ecraser
        sauvegarder_base()

        with open(DB_PATH, "wb") as f:
            f.write(raw)

        return True, "Base restauree. Redemarrez l'application."
    except Exception as e:
        return False, f"Erreur : {e}"