"""
Gestion des informations de l'ecole + sauvegarde de la base
"""
import os
import shutil
from datetime import datetime
from core.parametres import get_parametre, set_parametre
from config import DATA_DIR, DB_PATH

# Cles de parametres
CLE_ECOLE_NOM = "ecole_nom"
CLE_ECOLE_ADRESSE = "ecole_adresse"
CLE_ECOLE_TELEPHONE = "ecole_telephone"
CLE_ECOLE_EMAIL = "ecole_email"
CLE_ECOLE_LOGO = "ecole_logo"
CLE_SAUVEGARDE_AUTO = "sauvegarde_auto"
CLE_DERNIERE_SAUVEGARDE = "derniere_sauvegarde"

# Dossiers
LOGOS_DIR = os.path.join(DATA_DIR, "logos")
BACKUPS_DIR = os.path.join(DATA_DIR, "backups")
os.makedirs(LOGOS_DIR, exist_ok=True)
os.makedirs(BACKUPS_DIR, exist_ok=True)


# ============================================================
# INFO ECOLE
# ============================================================
def get_info_ecole():
    """Retourne un dict avec les infos de l'ecole"""
    return {
        "nom": get_parametre(CLE_ECOLE_NOM) or "Ecole B-NDEKE",
        "adresse": get_parametre(CLE_ECOLE_ADRESSE) or "",
        "telephone": get_parametre(CLE_ECOLE_TELEPHONE) or "",
        "email": get_parametre(CLE_ECOLE_EMAIL) or "",
        "logo": get_parametre(CLE_ECOLE_LOGO) or "",
    }


def set_info_ecole(nom, adresse, telephone, email):
    set_parametre(CLE_ECOLE_NOM, nom.strip())
    set_parametre(CLE_ECOLE_ADRESSE, adresse.strip())
    set_parametre(CLE_ECOLE_TELEPHONE, telephone.strip())
    set_parametre(CLE_ECOLE_EMAIL, email.strip())


def set_logo(chemin_source):
    """Copie le logo dans data/logos/ et enregistre son chemin"""
    if not chemin_source or not os.path.exists(chemin_source):
        return False, "Fichier introuvable"

    ext = os.path.splitext(chemin_source)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".gif", ".bmp"):
        return False, "Format non supporte (PNG, JPG, GIF, BMP)"

    try:
        # Supprimer les anciens logos
        for f in os.listdir(LOGOS_DIR):
            try:
                os.remove(os.path.join(LOGOS_DIR, f))
            except Exception:
                pass

        dest = os.path.join(LOGOS_DIR, f"logo{ext}")
        shutil.copy2(chemin_source, dest)
        set_parametre(CLE_ECOLE_LOGO, dest)
        return True, "Logo enregistre"
    except Exception as e:
        return False, f"Erreur : {e}"


def get_logo_path():
    """Retourne le chemin du logo s'il existe"""
    chemin = get_parametre(CLE_ECOLE_LOGO)
    if chemin and os.path.exists(chemin):
        return chemin
    return None


def supprimer_logo():
    chemin = get_parametre(CLE_ECOLE_LOGO)
    if chemin and os.path.exists(chemin):
        try:
            os.remove(chemin)
        except Exception:
            pass
    set_parametre(CLE_ECOLE_LOGO, "")


# ============================================================
# SAUVEGARDE
# ============================================================
def sauvegarder_base():
    """Cree une copie horodatee de la base"""
    try:
        if not os.path.exists(DB_PATH):
            return False, "Base introuvable"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom = f"b_ndeke_{timestamp}.db"
        dest = os.path.join(BACKUPS_DIR, nom)

        shutil.copy2(DB_PATH, dest)
        set_parametre(CLE_DERNIERE_SAUVEGARDE,
                      datetime.now().strftime("%d/%m/%Y %H:%M"))

        return True, dest
    except Exception as e:
        return False, str(e)


def lister_sauvegardes():
    """Liste les fichiers de sauvegarde tries du plus recent au plus ancien"""
    if not os.path.exists(BACKUPS_DIR):
        return []

    fichiers = []
    for f in os.listdir(BACKUPS_DIR):
        if f.endswith(".db"):
            chemin = os.path.join(BACKUPS_DIR, f)
            fichiers.append({
                "nom": f,
                "chemin": chemin,
                "taille": os.path.getsize(chemin),
                "date": datetime.fromtimestamp(os.path.getmtime(chemin)),
            })

    return sorted(fichiers, key=lambda x: x["date"], reverse=True)


def restaurer_sauvegarde(chemin_backup):
    """Restaure une sauvegarde (ecrase la base actuelle)"""
    try:
        if not os.path.exists(chemin_backup):
            return False, "Fichier introuvable"
        shutil.copy2(chemin_backup, DB_PATH)
        return True, "Base restauree. Redemarrez l'application pour appliquer."
    except Exception as e:
        return False, f"Erreur : {e}"


def supprimer_sauvegarde(chemin_backup):
    try:
        if os.path.exists(chemin_backup):
            os.remove(chemin_backup)
        return True, "Sauvegarde supprimee"
    except Exception as e:
        return False, str(e)


def get_sauvegarde_auto():
    """True si la sauvegarde auto est activee"""
    return get_parametre(CLE_SAUVEGARDE_AUTO) == "1"


def set_sauvegarde_auto(active):
    set_parametre(CLE_SAUVEGARDE_AUTO, "1" if active else "0")


def get_derniere_sauvegarde():
    return get_parametre(CLE_DERNIERE_SAUVEGARDE) or "Jamais"


def nettoyer_vieilles_sauvegardes(max_a_garder=20):
    """Ne garde que les N dernieres sauvegardes"""
    fichiers = lister_sauvegardes()
    for f in fichiers[max_a_garder:]:
        try:
            os.remove(f["chemin"])
        except Exception:
            pass


def get_dossier_backups():
    return BACKUPS_DIR

    

def get_info_ecole_pour_pdf():
    """Retourne un dict avec les infos ecole pour les PDFs (avec chemin logo)"""
    info = get_info_ecole()
    info["logo_path"] = get_logo_path()  # None si pas de logo
    return info

# ============================================================
# PAYS DE L'ECOLE (stocke dans parametres clé/valeur)
# ============================================================
def get_pays_ecole():
    """Retourne le pays enregistre par l'ecole."""
    try:
        from core.parametres import get_parametre
        return get_parametre("ecole_pays") or ""
    except Exception:
        return ""


def set_pays_ecole(pays):
    """Enregistre le pays de l'ecole."""
    try:
        from core.parametres import set_parametre
        set_parametre("ecole_pays", pays or "")
        return True, "Pays enregistre"
    except Exception as e:
        return False, f"Erreur : {e}"
