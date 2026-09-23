"""
Client du serveur d'activation B-NDEKE (Google Sheets)
Verifie la limite de 3 machines par code
"""
import json
import urllib.request
import urllib.parse

SERVEUR_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbxyJQnR-6JmxBXR1h3QxeXTrZb4J4AcveLgo6O7oeR892kxwWnD8Xj4E4yogXC4NDCM/exec"
)


def verifier_et_enregistrer(cle, machine_id, email=""):
    """
    Contacte le serveur pour activer la machine avec ce code.
    Retourne (ok, status, message, count, max_machines)
    """
    params = {
        "action": "activate",
        "code": cle.strip().upper(),
        "machine_id": machine_id,
        "email": email or "",
    }
    url = SERVEUR_URL + "?" + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (B-NDEKE-App)",
                "Accept": "application/json",
                "Accept-Encoding": "identity",  # empeche Google de compresser en gzip
                "Cache-Control": "no-cache",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[SERVEUR] Erreur reseau : {e}")
        return False, "error", (
            f"Impossible de contacter le serveur d'activation.\n"
            f"Verifiez votre connexion Internet et reessayez.\n"
            f"(detail : {e})"
        ), 0, 3

    print(f"[SERVEUR] Reponse brute ({len(raw)} octets) : {raw[:200]}")

    if not raw or not raw.strip():
        return False, "error", (
            "Le serveur a repondu vide.\n"
            "Verifiez votre connexion Internet et reessayez."
        ), 0, 3

    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"[SERVEUR] JSON invalide : {raw[:500]}")
        return False, "error", (
            f"Reponse invalide du serveur.\n"
            f"(detail : {e})"
        ), 0, 3

    ok = bool(data.get("ok", False))
    status = data.get("status", "error")
    message = data.get("message", "")
    count = int(data.get("count", 0))
    max_m = int(data.get("max", 3))

    return ok, status, message, count, max_m