"""
Systeme de mise a jour B-NDEKE Comptability One
Verifie une URL distante qui contient les infos de version.
"""
import json
import urllib.request
from datetime import datetime
from config import APP_VERSION

# URL du fichier version.json heberge sur GitHub
VERSION_URL = (
    "https://raw.githubusercontent.com/"
    "supportbndekecomptability-boop/b-ndeke-comptability-one/main/version.json"
)


def _parse_version(v):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except Exception:
        return (0, 0, 0)


def verifier_mise_a_jour():
    """
    Interroge VERSION_URL et retourne un dict :
    {
        'ok': bool,                       # la verif a-t-elle reussi ?
        'version_actuelle': str,
        'derniere_version': str,
        'mise_a_jour_disponible': bool,
        'mise_a_jour_obligatoire': bool,
        'message': str,
        'url_telechargement': str,
        'deadline': str or None,
    }
    """
    info = {
        "ok": False,
        "version_actuelle": APP_VERSION,
        "derniere_version": APP_VERSION,
        "mise_a_jour_disponible": False,
        "mise_a_jour_obligatoire": False,
        "message": "",
        "url_telechargement": "",
        "deadline": None,
    }

    try:
        req = urllib.request.Request(
            VERSION_URL, headers={"Cache-Control": "no-cache"}
        )
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"[UPDATE] Verification impossible (hors ligne ?) : {e}")
        return info

    info["ok"] = True
    derniere = data.get("latest", APP_VERSION)
    min_requis = data.get("min_required", APP_VERSION)
    deadline = data.get("deadline")
    url = data.get("download_url", "")

    info["derniere_version"] = derniere
    info["deadline"] = deadline
    info["url_telechargement"] = url

    actuelle = _parse_version(APP_VERSION)

    if _parse_version(derniere) > actuelle:
        info["mise_a_jour_disponible"] = True

    # Mise a jour obligatoire ?
    obligatoire = False

    if _parse_version(min_requis) > actuelle:
        obligatoire = True

    if deadline:
        try:
            if datetime.now() > datetime.fromisoformat(deadline):
                obligatoire = True
        except Exception:
            pass

    info["mise_a_jour_obligatoire"] = obligatoire

    if obligatoire:
        info["message"] = (
            f"Votre version ({APP_VERSION}) n'est plus supportee.\n"
            f"Vous devez installer la version {derniere} pour continuer."
        )
    elif info["mise_a_jour_disponible"]:
        info["message"] = (
            f"Une nouvelle version ({derniere}) est disponible.\n"
            f"Vous utilisez actuellement la version {APP_VERSION}."
        )

    return info