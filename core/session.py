"""
Gestion de la session persistante B-NDEKE Comptability One
Permet a l'utilisateur de rester connecte entre les lancements.
"""
import os
import json
import hashlib
from datetime import datetime, timedelta

# Duree de validite de la session (en jours). 0 = illimite.
DUREE_SESSION_JOURS = 365

FICHIER_SESSION = os.path.join(
    os.environ.get("APPDATA", "."), "B-NDEKE", "session.dat"
)


def _dossier_session():
    dossier = os.path.dirname(FICHIER_SESSION)
    os.makedirs(dossier, exist_ok=True)
    return dossier


def _token_utilisateur(user):
    base = f"{user['id']}|{user['email']}|B-NDEKE-SECRET"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def sauvegarder_session(user):
    """Sauvegarde la session apres connexion reussie."""
    try:
        _dossier_session()
        expire = None
        if DUREE_SESSION_JOURS > 0:
            expire = (datetime.now() + timedelta(days=DUREE_SESSION_JOURS)).isoformat()

        data = {
            "user_id": user["id"],
            "email": user["email"],
            "nom_complet": user["nom_complet"],
            "role": user["role"],
            "token": _token_utilisateur(user),
            "expire": expire,
            "cree": datetime.now().isoformat(),
        }
        with open(FICHIER_SESSION, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[SESSION] Erreur sauvegarde : {e}")
        return False


def charger_session():
    """Charge la session si elle est valide, sinon None."""
    if not os.path.exists(FICHIER_SESSION):
        return None

    try:
        with open(FICHIER_SESSION, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        supprimer_session()
        return None

    expire = data.get("expire")
    if expire:
        try:
            if datetime.now() > datetime.fromisoformat(expire):
                supprimer_session()
                return None
        except Exception:
            supprimer_session()
            return None

    user = {
        "id": data.get("user_id"),
        "email": data.get("email"),
        "nom_complet": data.get("nom_complet"),
        "role": data.get("role"),
    }
    if not all(user.values()):
        supprimer_session()
        return None

    if data.get("token") != _token_utilisateur(user):
        supprimer_session()
        return None

    return user


def supprimer_session():
    """Supprime la session (deconnexion)."""
    try:
        if os.path.exists(FICHIER_SESSION):
            os.remove(FICHIER_SESSION)
        return True
    except Exception:
        return False


def session_existe():
    return os.path.exists(FICHIER_SESSION)