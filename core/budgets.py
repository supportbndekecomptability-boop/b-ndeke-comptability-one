"""
Gestion du budget annuel - B-NDEKE Comptability One
Budget total = montant (auto ou manuel) moins le taux d'insolvabilite.
"""
import os
import json
from config import DATA_DIR
from database import get_connection

FICHIER_BUDGETS = os.path.join(DATA_DIR, "budgets.json")


# ============================================================
# STRUCTURE PAR DEFAUT
# ============================================================
STRUCTURE_DEFAUT = {
    "utiliser_auto": True,
    "budget_total_manuel": 0,
    "taux_insolvabilite": 0,
    "prime": {
        "pourcentage": 20,
        "sous_categories": {
            "Primes enseignants": 70,
            "Primes personnel administratif": 30,
        },
    },
    "investissement": {
        "pourcentage": 30,
        "sous_categories": {
            "Epargne": 30,
            "Impot banque": 10,
            "Construction": 25,
            "Mobilier": 15,
            "Achat terrain": 10,
            "Remboursement dette": 10,
        },
    },
    "fonctionnement": {
        "pourcentage": 50,
        "sous_categories": {
            "Fournitures scolaires (stylos, craies, markers)": 30,
            "Papier et cahiers": 15,
            "Manuels scolaires": 20,
            "Transport": 15,
            "Enveloppes et cartes travailleur": 10,
            "Autres": 10,
        },
    },
}


def _charger():
    try:
        if os.path.exists(FICHIER_BUDGETS):
            with open(FICHIER_BUDGETS, "r", encoding="utf-8") as f:
                data = json.load(f)
            return _fusionner(data)
    except Exception as e:
        print(f"[BUDGET] Erreur chargement : {e}")

    return json.loads(json.dumps(STRUCTURE_DEFAUT))


def _fusionner(data):
    result = json.loads(json.dumps(STRUCTURE_DEFAUT))

    if "utiliser_auto" in data:
        result["utiliser_auto"] = bool(data["utiliser_auto"])
    if "budget_total_manuel" in data:
        result["budget_total_manuel"] = float(data["budget_total_manuel"] or 0)
    if "taux_insolvabilite" in data:
        result["taux_insolvabilite"] = float(data["taux_insolvabilite"] or 0)

    for key in ("prime", "investissement", "fonctionnement"):
        if key in data and isinstance(data[key], dict):
            result[key]["pourcentage"] = float(
                data[key].get("pourcentage", result[key]["pourcentage"]) or 0
            )
            if "sous_categories" in data[key] and isinstance(data[key]["sous_categories"], dict):
                result[key]["sous_categories"] = {
                    k: float(v or 0)
                    for k, v in data[key]["sous_categories"].items()
                }
    return result


def _sauvegarder(data):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(FICHIER_BUDGETS, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[BUDGET] Erreur sauvegarde : {e}")
        return False


# ============================================================
# CALCUL AUTOMATIQUE DU BUDGET TOTAL
# ============================================================
def calculer_budget_auto_brut():
    """Retourne le total brut des frais des eleves (sans deduction)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(COALESCE(frais_scolarite, 0)), 0) as total
            FROM eleves
            WHERE actif = 1
        """)
        row = cursor.fetchone()
        conn.close()
        return float(row["total"] or 0)
    except Exception as e:
        print(f"[BUDGET] Erreur calcul auto brut : {e}")
        return 0


def _appliquer_taux(brut, taux):
    """Applique le taux d'insolvabilite a un montant brut."""
    try:
        taux = float(taux or 0)
    except Exception:
        taux = 0
    if taux < 0:
        taux = 0
    if taux > 100:
        taux = 100
    return brut * (1 - taux / 100.0)


def calculer_budget_auto():
    """Retourne le net apres taux (mode auto)."""
    brut = calculer_budget_auto_brut()
    taux = get_taux_insolvabilite()
    return _appliquer_taux(brut, taux)


def set_taux_insolvabilite(taux):
    """Enregistre le taux d'insolvabilite (en %)."""
    try:
        taux = float(taux or 0)
    except Exception:
        return False
    if taux < 0:
        taux = 0
    if taux > 100:
        taux = 100

    data = _charger()
    data["taux_insolvabilite"] = taux
    return _sauvegarder(data)


def get_taux_insolvabilite():
    data = _charger()
    return float(data.get("taux_insolvabilite", 0) or 0)


# ============================================================
# API PUBLIQUE
# ============================================================
def get_budgets():
    """
    Retourne la structure complete avec les montants calcules.
    Le taux d'insolvabilite est applique DANS LES 2 MODES
    (auto et manuel).
    """
    data = _charger()

    taux_insolv = float(data.get("taux_insolvabilite", 0) or 0)
    if taux_insolv < 0:
        taux_insolv = 0
    if taux_insolv > 100:
        taux_insolv = 100

    utiliser_auto = data.get("utiliser_auto", True)

    if utiliser_auto:
        # Mode auto : frais eleves bruts - taux
        montant_brut = calculer_budget_auto_brut()
    else:
        # Mode manuel : montant saisi - taux aussi
        montant_brut = float(data.get("budget_total_manuel", 0) or 0)

    deduction = montant_brut * taux_insolv / 100.0
    total = montant_brut - deduction

    result = {
        "budget_total": total,
        "budget_total_auto": _appliquer_taux(calculer_budget_auto_brut(), taux_insolv),
        "budget_total_brut": montant_brut,
        "budget_total_manuel": float(data.get("budget_total_manuel", 0) or 0),
        "utiliser_auto": utiliser_auto,
        "taux_insolvabilite": taux_insolv,
        "deduction_insolvabilite": deduction,
        "prime": _enrichir(data["prime"], total),
        "investissement": _enrichir(data["investissement"], total),
        "fonctionnement": _enrichir(data["fonctionnement"], total),
    }
    return result


def _enrichir(budget, total):
    pct = float(budget.get("pourcentage", 0) or 0)
    montant_parent = total * pct / 100.0

    sous = {}
    for nom, pct_sous in budget.get("sous_categories", {}).items():
        pct_sous = float(pct_sous or 0)
        sous[nom] = {
            "pourcentage": pct_sous,
            "montant": montant_parent * pct_sous / 100.0,
        }

    return {
        "pourcentage": pct,
        "montant": montant_parent,
        "sous_categories": sous,
    }


def set_mode_auto(utiliser_auto):
    data = _charger()
    data["utiliser_auto"] = bool(utiliser_auto)
    return _sauvegarder(data)


def set_budget_manuel(montant):
    data = _charger()
    data["budget_total_manuel"] = float(montant or 0)
    data["utiliser_auto"] = False
    return _sauvegarder(data)


def set_pourcentage_budget(budget_key, pourcentage):
    if budget_key not in ("prime", "investissement", "fonctionnement"):
        return False
    data = _charger()
    data[budget_key]["pourcentage"] = float(pourcentage or 0)
    return _sauvegarder(data)


def set_pourcentage_sous_categorie(budget_key, sous_nom, pourcentage):
    if budget_key not in ("prime", "investissement", "fonctionnement"):
        return False
    data = _charger()
    if sous_nom not in data[budget_key]["sous_categories"]:
        return False
    data[budget_key]["sous_categories"][sous_nom] = float(pourcentage or 0)
    return _sauvegarder(data)


def ajouter_sous_categorie(budget_key, nom, pourcentage=0):
    if budget_key not in ("prime", "investissement", "fonctionnement"):
        return False
    data = _charger()
    data[budget_key]["sous_categories"][nom] = float(pourcentage or 0)
    return _sauvegarder(data)


def supprimer_sous_categorie(budget_key, nom):
    if budget_key not in ("prime", "investissement", "fonctionnement"):
        return False
    data = _charger()
    if nom in data[budget_key]["sous_categories"]:
        del data[budget_key]["sous_categories"][nom]
        return _sauvegarder(data)
    return False


def vider_tout():
    return _sauvegarder(json.loads(json.dumps(STRUCTURE_DEFAUT)))


# ============================================================
# VERIFICATIONS
# ============================================================
def verifier_total_budgets():
    data = _charger()
    total = (
        float(data["prime"]["pourcentage"] or 0)
        + float(data["investissement"]["pourcentage"] or 0)
        + float(data["fonctionnement"]["pourcentage"] or 0)
    )
    return total


def verifier_sous_categories(budget_key):
    data = _charger()
    if budget_key not in ("prime", "investissement", "fonctionnement"):
        return 0
    total = sum(
        float(v or 0) for v in data[budget_key]["sous_categories"].values()
    )
    return total


# ============================================================
# UTILITAIRES
# ============================================================
def liste_budgets():
    return [
        ("prime", "PRIME", "#8e44ad"),
        ("investissement", "INVESTISSEMENT", "#3498db"),
        ("fonctionnement", "FONCTIONNEMENT", "#e67e22"),
    ]


def get_montant_budget(budget_key):
    b = get_budgets()
    if budget_key in b:
        return b[budget_key]["montant"]
    return 0


def get_toutes_sous_categories():
    b = get_budgets()
    result = []
    for key, label, _ in liste_budgets():
        for nom in b.get(key, {}).get("sous_categories", {}).keys():
            result.append({
                "budget": key,
                "budget_label": label,
                "nom": nom,
            })
    return result