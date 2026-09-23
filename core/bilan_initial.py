"""
Bilan initial - Comptes Syscohada simplifie
Le comptable choisit les comptes qu'il utilise, saisit les montants.
Les comptes non utilises n'apparaissent pas.
"""
import json
from core.parametres import get_parametre, set_parametre

CLE_BILAN_INIT = "bilan_init_data"

# ===== COMPTES D'ACTIF (Classes 2, 3, 4, 5) =====
COMPTES_ACTIF = [
    ("20", "Immobilisations incorporelles"),
    ("21", "Immobilisations corporelles"),
    ("22", "Terrains"),
    ("23", "Batiments"),
    ("24", "Materiel"),
    ("25", "Mobilier et agencements"),
    ("26", "Titres de participation"),
    ("27", "Autres immobilisations financieres"),
    ("28", "Amortissements (a deduire)"),
    ("31", "Matieres premieres"),
    ("32", "Autres approvisionnements"),
    ("33", "Autres stocks"),
    ("41", "Eleves (creances)"),
    ("42", "Personnel (avances)"),
    ("43", "Organismes sociaux (creances)"),
    ("44", "Etat (creances)"),
    ("45", "Autres debiteurs"),
    ("46", "Creances diverses"),
    ("47", "Comptes transitoires"),
    ("51", "Titres de placement"),
    ("52", "Banque"),
    ("53", "Etablissements financiers"),
    ("57", "Caisse"),
    ("58", "Regies d'avances"),
]

# ===== COMPTES DE PASSIF (Classes 1 et 4) =====
COMPTES_PASSIF = [
    ("10", "Capital"),
    ("11", "Reserves"),
    ("12", "Report a nouveau"),
    ("13", "Resultat net"),
    ("14", "Subventions d'investissement"),
    ("15", "Provisions reglementees"),
    ("16", "Emprunts"),
    ("17", "Dettes de credit-bail"),
    ("18", "Dettes liees a des participations"),
    ("19", "Provisions pour risques"),
    ("40", "Fournisseurs"),
    ("42", "Personnel (salaires a payer)"),
    ("43", "Organismes sociaux (dettes)"),
    ("44", "Etat (impots a payer)"),
    ("45", "Autres dettes"),
    ("46", "Crediteurs divers"),
]


def _charger_data():
    try:
        raw = get_parametre(CLE_BILAN_INIT)
        if raw:
            data = json.loads(raw)
            if "actif" not in data:
                data["actif"] = {}
            if "passif" not in data:
                data["passif"] = {}
            return data
    except Exception:
        pass
    return {"actif": {}, "passif": {}}


def _sauvegarder_data(data):
    set_parametre(CLE_BILAN_INIT, json.dumps(data))


def get_bilan_initial():
    """Retourne dict {'actif': {code: montant}, 'passif': {code: montant}}"""
    return _charger_data()


def ajouter_compte(cote, code, montant):
    """cote = 'actif' ou 'passif'. code = '57', montant = float."""
    if cote not in ("actif", "passif"):
        return False, "Cote invalide"
    try:
        m = float(str(montant).replace(" ", "").replace(",", "."))
    except Exception:
        return False, "Montant invalide"
    if m < 0:
        return False, "Montant negatif interdit"

    data = _charger_data()
    data[cote][str(code)] = m
    _sauvegarder_data(data)
    return True, "Compte enregistre"


def supprimer_compte(cote, code):
    data = _charger_data()
    if cote in data and str(code) in data[cote]:
        del data[cote][str(code)]
        _sauvegarder_data(data)
        return True
    return False


def total_actif():
    data = _charger_data()
    return sum(float(v) for v in data.get("actif", {}).values())


def total_passif():
    data = _charger_data()
    return sum(float(v) for v in data.get("passif", {}).values())


def capitaux_propres():
    """Total Actif - Total Passif"""
    return total_actif() - total_passif()


def liste_comptes_actif():
    return COMPTES_ACTIF


def liste_comptes_passif():
    return COMPTES_PASSIF


def get_libelle(code):
    code = str(code)
    for c, lib in COMPTES_ACTIF + COMPTES_PASSIF:
        if c == code:
            return lib
    return code


def vider_bilan_initial():
    _sauvegarder_data({"actif": {}, "passif": {}})