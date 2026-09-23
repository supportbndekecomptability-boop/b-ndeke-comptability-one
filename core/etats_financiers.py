"""
Etats financiers SYSCOHADA adaptes a une ecole
Mapping automatique des operations de l'ecole vers le plan comptable SYSCOHADA
"""
from datetime import datetime
from database import get_connection


# ============================================================
# PLAN COMPTABLE SYSCOHADA (adapte aux ecoles)
# ============================================================
PLAN_COMPTABLE = {
    "101": "Capital social",
    "106": "Reserves",
    "110": "Report a nouveau",
    "130": "Resultat net de l'exercice",
    "162": "Emprunts et dettes assimilees",
    "231": "Materiel scolaire",
    "244": "Mobilier de bureau",
    "245": "Materiel informatique",
    "401": "Fournisseurs",
    "411": "Eleves (creances)",
    "421": "Personnel - Avances versees",
    "422": "Personnel - Remunerations dues",
    "431": "Securite sociale",
    "447": "Etat, impots et taxes",
    "521": "Banque",
    "531": "Cheques postaux",
    "571": "Caisse",
    "601": "Achats de fournitures",
    "605": "Autres achats",
    "613": "Locations",
    "614": "Charges locatives",
    "622": "Remunerations intermediaires",
    "624": "Entretien et reparations",
    "626": "Assurances",
    "627": "Publicite",
    "628": "Frais de telecommunication",
    "631": "Frais bancaires",
    "632": "Frais de transport",
    "641": "Impots et taxes",
    "661": "Remunerations du personnel",
    "664": "Charges sociales",
    "701": "Frais de scolarite",
    "702": "Frais d'inscription",
    "706": "Services vendus (uniforme, transport...)",
    "707": "Produits annexes (cantine, etc.)",
    "758": "Produits divers",
    "871": "Subventions d'exploitation",
}

# Mapping : categorie de depense -> compte SYSCOHADA
MAPPING_DEPENSES = {
    "Loyer": "613",
    "Electricite": "605",
    "Eau": "605",
    "Internet": "628",
    "Fournitures scolaires": "601",
    "Entretien": "624",
    "Transport": "632",
    "Carburant": "605",
    "Telephone": "628",
    "Publicite": "627",
    "Frais bancaires": "631",
    "Mobilier": "244",
    "Informatique": "245",
    "Cantine": "605",
    "Securite": "622",
    "Assurance": "626",
    "Autre": "605",
}

# Mapping : motif de paiement eleve -> compte SYSCOHADA
MAPPING_RECETTES = {
    "Frais scolaires": "701",
    "Frais d'inscription": "702",
    "Frais de reinscription": "702",
    "Uniforme": "706",
    "Fournitures scolaires": "706",
    "Transport": "706",
    "Cantine": "707",
    "Autre": "758",
}

# Mapping : motif de paiement personnel -> compte SYSCOHADA
MAPPING_PERSONNEL = {
    "Salaire mensuel": "661",
    "Prime": "661",
    "Heures supplementaires": "661",
    "Indemnite": "661",
    "Autre": "661",
}


# ============================================================
# COLLECTE DES ECRITURES
# ============================================================
def _collecter_ecritures(date_debut=None, date_fin=None):
    """
    Recupere toutes les operations de l'ecole et les convertit
    en ecritures comptables SYSCOHADA.
    """
    conn = get_connection()
    cursor = conn.cursor()

    ecritures = []

    # Filtres de date
    filtre_eleves = ""
    filtre_personnel = ""
    filtre_depenses = ""
    filtre_avances = ""
    params_eleves = []
    params_personnel = []
    params_depenses = []
    params_avances = []

    if date_debut:
        filtre_eleves += " AND DATE(p.date_paiement) >= ?"
        params_eleves.append(date_debut)
        filtre_personnel += " AND DATE(p.date_paiement) >= ?"
        params_personnel.append(date_debut)
        filtre_depenses += " AND DATE(d.date_depense) >= ?"
        params_depenses.append(date_debut)
        filtre_avances += " AND DATE(a.date_avance) >= ?"
        params_avances.append(date_debut)

    if date_fin:
        filtre_eleves += " AND DATE(p.date_paiement) <= ?"
        params_eleves.append(date_fin)
        filtre_personnel += " AND DATE(p.date_paiement) <= ?"
        params_personnel.append(date_fin)
        filtre_depenses += " AND DATE(d.date_depense) <= ?"
        params_depenses.append(date_fin)
        filtre_avances += " AND DATE(a.date_avance) <= ?"
        params_avances.append(date_fin)

    # ===== PAIEMENTS ELEVES =====
    cursor.execute(f"""
        SELECT p.numero_recu, p.date_paiement, p.montant, p.motif, p.mode_paiement,
               e.matricule, e.nom, e.prenom
        FROM paiements_eleves p
        JOIN eleves e ON p.eleve_id = e.id
        WHERE 1=1 {filtre_eleves}
        ORDER BY p.date_paiement
    """, params_eleves)

    for row in cursor.fetchall():
        compte_produit = MAPPING_RECETTES.get(row["motif"], "758")
        compte_tresorerie = _compte_tresorerie(row["mode_paiement"])
        libelle = f"Recu {row['numero_recu']} - {row['nom']} {row['prenom']}"

        ecritures.append({
            "date": row["date_paiement"][:10],
            "journal": "CAISSE" if "esp" in row["mode_paiement"].lower() else "BANQUE",
            "piece": row["numero_recu"],
            "libelle": libelle,
            "lignes": [
                {"compte": compte_tresorerie, "debit": row["montant"], "credit": 0},
                {"compte": compte_produit, "debit": 0, "credit": row["montant"]},
            ]
        })

    # ===== PAIEMENTS PERSONNEL (avec split avance) =====
    cursor.execute(f"""
        SELECT p.numero_paie, p.date_paiement, p.montant, p.motif, p.mode_paiement,
               COALESCE(p.montant_avance_deduit, 0) as montant_avance_deduit,
               e.code, e.nom, e.prenom
        FROM paiements_personnel p
        JOIN personnel e ON p.personnel_id = e.id
        WHERE 1=1 {filtre_personnel}
        ORDER BY p.date_paiement
    """, params_personnel)

    for row in cursor.fetchall():
        compte_charge = MAPPING_PERSONNEL.get(row["motif"], "661")
        compte_tresorerie = _compte_tresorerie(row["mode_paiement"])
        libelle = f"Paie {row['numero_paie']} - {row['nom']} {row['prenom']}"

        montant_total = row["montant"]
        montant_deduit = row["montant_avance_deduit"] or 0
        montant_net = montant_total - montant_deduit

        # Ecriture : charge totale (debit 661)
        lignes = [
            {"compte": compte_charge, "debit": montant_total, "credit": 0},
        ]

        # Deduction d'avance : credite 421 (recuperation de la creance)
        if montant_deduit > 0.01:
            lignes.append({"compte": "421", "debit": 0, "credit": montant_deduit})

        # Net verse en tresorerie
        if montant_net > 0.01:
            lignes.append({"compte": compte_tresorerie, "debit": 0, "credit": montant_net})

        ecritures.append({
            "date": row["date_paiement"][:10],
            "journal": "CAISSE" if "esp" in row["mode_paiement"].lower() else "BANQUE",
            "piece": row["numero_paie"],
            "libelle": libelle,
            "lignes": lignes,
        })

    # ===== AVANCES SUR SALAIRE =====
    cursor.execute(f"""
        SELECT a.numero_avance, a.date_avance, a.montant,
               p.code, p.nom, p.prenom
        FROM avances_personnel a
        JOIN personnel p ON a.personnel_id = p.id
        WHERE 1=1 {filtre_avances}
        ORDER BY a.date_avance
    """, params_avances)

    for row in cursor.fetchall():
        libelle = f"Avance {row['numero_avance']} - {row['nom']} {row['prenom']}"

        ecritures.append({
            "date": row["date_avance"][:10],
            "journal": "CAISSE",
            "piece": row["numero_avance"],
            "libelle": libelle,
            "lignes": [
                {"compte": "421", "debit": row["montant"], "credit": 0},
                {"compte": "571", "debit": 0, "credit": row["montant"]},
            ]
        })

    # ===== DEPENSES =====
    cursor.execute(f"""
        SELECT d.id, d.date_depense, d.montant, d.categorie, d.libelle
        FROM depenses d
        WHERE 1=1 {filtre_depenses}
        ORDER BY d.date_depense
    """, params_depenses)

    for row in cursor.fetchall():
        compte_charge = MAPPING_DEPENSES.get(row["categorie"], "605")
        libelle = f"Depense {row['categorie']} - {row['libelle']}"
        piece = f"DEP{row['id']:04d}"

        ecritures.append({
            "date": row["date_depense"][:10],
            "journal": "CAISSE",
            "piece": piece,
            "libelle": libelle,
            "lignes": [
                {"compte": compte_charge, "debit": row["montant"], "credit": 0},
                {"compte": "571", "debit": 0, "credit": row["montant"]},
            ]
        })

    conn.close()

    ecritures.sort(key=lambda x: x["date"])
    return ecritures


def _compte_tresorerie(mode_paiement):
    """Determine le compte de tresorerie selon le mode"""
    if "esp" in mode_paiement.lower():
        return "571"
    elif "banque" in mode_paiement.lower() or "virement" in mode_paiement.lower():
        return "521"
    elif "cheque" in mode_paiement.lower():
        return "521"
    elif "mobile" in mode_paiement.lower():
        return "521"
    else:
        return "571"


# ============================================================
# 1. JOURNAL GENERAL
# ============================================================
def etat_journal(date_debut=None, date_fin=None):
    """Retourne le journal general chronologique"""
    ecritures = _collecter_ecritures(date_debut, date_fin)

    lignes = []
    for e in ecritures:
        for i, ligne in enumerate(e["lignes"]):
            lignes.append({
                "date": e["date"],
                "journal": e["journal"],
                "piece": e["piece"],
                "libelle": e["libelle"] if i == 0 else "",
                "compte": ligne["compte"],
                "intitule": PLAN_COMPTABLE.get(ligne["compte"], "Autre"),
                "debit": ligne["debit"],
                "credit": ligne["credit"],
            })

    total_debit = sum(l["debit"] for l in lignes)
    total_credit = sum(l["credit"] for l in lignes)

    return {
        "titre": "JOURNAL GENERAL",
        "date_debut": date_debut or "Origine",
        "date_fin": date_fin or datetime.now().strftime("%d/%m/%Y"),
        "lignes": lignes,
        "total_debit": total_debit,
        "total_credit": total_credit,
    }


# ============================================================
# 2. GRAND LIVRE
# ============================================================
def etat_grand_livre(date_debut=None, date_fin=None):
    """Retourne le grand livre (detail par compte)"""
    ecritures = _collecter_ecritures(date_debut, date_fin)

    comptes = {}

    for e in ecritures:
        for ligne in e["lignes"]:
            c = ligne["compte"]
            if c not in comptes:
                comptes[c] = {
                    "compte": c,
                    "intitule": PLAN_COMPTABLE.get(c, "Autre"),
                    "mouvements": [],
                    "total_debit": 0,
                    "total_credit": 0,
                }

            comptes[c]["mouvements"].append({
                "date": e["date"],
                "libelle": e["libelle"],
                "debit": ligne["debit"],
                "credit": ligne["credit"],
                "solde": 0,
            })
            comptes[c]["total_debit"] += ligne["debit"]
            comptes[c]["total_credit"] += ligne["credit"]

    resultat = []
    for c, data in sorted(comptes.items()):
        solde = 0
        for mvt in data["mouvements"]:
            solde += mvt["debit"] - mvt["credit"]
            mvt["solde"] = solde

        data["solde_final"] = data["total_debit"] - data["total_credit"]
        resultat.append(data)

    return {
        "titre": "GRAND LIVRE",
        "date_debut": date_debut or "Origine",
        "date_fin": date_fin or datetime.now().strftime("%d/%m/%Y"),
        "comptes": resultat,
    }


# ============================================================
# 3. BALANCE GENERALE
# ============================================================
def etat_balance(date_debut=None, date_fin=None):
    """Retourne la balance generale a 6 colonnes"""
    ecritures = _collecter_ecritures(date_debut, date_fin)

    comptes = {}

    for e in ecritures:
        for ligne in e["lignes"]:
            c = ligne["compte"]
            if c not in comptes:
                comptes[c] = {
                    "compte": c,
                    "intitule": PLAN_COMPTABLE.get(c, "Autre"),
                    "total_debit": 0,
                    "total_credit": 0,
                }
            comptes[c]["total_debit"] += ligne["debit"]
            comptes[c]["total_credit"] += ligne["credit"]

    lignes = []
    for c, data in sorted(comptes.items()):
        solde_debiteur = max(0, data["total_debit"] - data["total_credit"])
        solde_crediteur = max(0, data["total_credit"] - data["total_debit"])

        lignes.append({
            "compte": c,
            "intitule": data["intitule"],
            "mvt_debit": data["total_debit"],
            "mvt_credit": data["total_credit"],
            "solde_debit": solde_debiteur,
            "solde_credit": solde_crediteur,
        })

    total_debit = sum(l["mvt_debit"] for l in lignes)
    total_credit = sum(l["mvt_credit"] for l in lignes)
    total_solde_deb = sum(l["solde_debit"] for l in lignes)
    total_solde_cred = sum(l["solde_credit"] for l in lignes)

    return {
        "titre": "BALANCE GENERALE",
        "date_debut": date_debut or "Origine",
        "date_fin": date_fin or datetime.now().strftime("%d/%m/%Y"),
        "lignes": lignes,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "total_solde_debit": total_solde_deb,
        "total_solde_credit": total_solde_cred,
    }


# ============================================================
# 4. COMPTE DE RESULTAT
# ============================================================
def etat_compte_resultat(date_debut=None, date_fin=None):
    """Compte de resultat simplifie SYSCOHADA"""
    ecritures = _collecter_ecritures(date_debut, date_fin)

    produits = {}
    charges = {}

    for e in ecritures:
        for ligne in e["lignes"]:
            c = ligne["compte"]
            if c.startswith("7"):
                if c not in produits:
                    produits[c] = {
                        "compte": c,
                        "intitule": PLAN_COMPTABLE.get(c, "Autre"),
                        "montant": 0,
                    }
                produits[c]["montant"] += ligne["credit"] - ligne["debit"]
            elif c.startswith("6"):
                if c not in charges:
                    charges[c] = {
                        "compte": c,
                        "intitule": PLAN_COMPTABLE.get(c, "Autre"),
                        "montant": 0,
                    }
                charges[c]["montant"] += ligne["debit"] - ligne["credit"]

    liste_produits = sorted(produits.values(), key=lambda x: x["compte"])
    liste_charges = sorted(charges.values(), key=lambda x: x["compte"])

    total_produits = sum(p["montant"] for p in liste_produits)
    total_charges = sum(c["montant"] for c in liste_charges)
    resultat = total_produits - total_charges

    return {
        "titre": "COMPTE DE RESULTAT",
        "date_debut": date_debut or "Origine",
        "date_fin": date_fin or datetime.now().strftime("%d/%m/%Y"),
        "produits": liste_produits,
        "charges": liste_charges,
        "total_produits": total_produits,
        "total_charges": total_charges,
        "resultat_net": resultat,
    }


# ============================================================
# 5. BILAN SIMPLIFIE
# ============================================================
def etat_bilan(date_debut=None, date_fin=None):
    """Bilan simplifie (Actif / Passif) selon SYSCOHADA"""
    ecritures = _collecter_ecritures(date_debut, date_fin)

    comptes = {}
    for e in ecritures:
        for ligne in e["lignes"]:
            c = ligne["compte"]
            if c not in comptes:
                comptes[c] = {"debit": 0, "credit": 0}
            comptes[c]["debit"] += ligne["debit"]
            comptes[c]["credit"] += ligne["credit"]

    # Calcul du resultat
    total_produits = sum(
        v["credit"] - v["debit"]
        for k, v in comptes.items() if k.startswith("7")
    )
    total_charges = sum(
        v["debit"] - v["credit"]
        for k, v in comptes.items() if k.startswith("6")
    )
    resultat = total_produits - total_charges

    # ===== ACTIF =====
    actif = []

    # Classe 2 : Immobilisations
    for c in sorted(comptes):
        if c.startswith("2"):
            solde = comptes[c]["debit"] - comptes[c]["credit"]
            if abs(solde) > 0.01:
                actif.append({
                    "compte": c,
                    "intitule": PLAN_COMPTABLE.get(c, "Autre"),
                    "montant": solde,
                })

    # 411 Eleves (a recevoir) - impayes
    eleves_a_recevoir = _calculer_impayes()
    if eleves_a_recevoir > 0.01:
        actif.append({
            "compte": "411",
            "intitule": "Eleves (a recevoir)",
            "montant": eleves_a_recevoir,
        })

    # 421 Personnel - Avances versees (creance sur les employes)
    avances_en_cours = _calculer_avances_en_cours()
    if avances_en_cours > 0.01:
        actif.append({
            "compte": "421",
            "intitule": "Personnel - Avances versees",
            "montant": avances_en_cours,
        })

    # Autres creances (classe 4 debitrice, hors 411 et 421)
    for c in sorted(comptes):
        if c.startswith("4") and c not in ("411", "421"):
            solde = comptes[c]["debit"] - comptes[c]["credit"]
            if solde > 0.01:
                actif.append({
                    "compte": c,
                    "intitule": PLAN_COMPTABLE.get(c, "Autre"),
                    "montant": solde,
                })

    # Classe 5 : Tresorerie
    tresorerie = 0
    for c in sorted(comptes):
        if c.startswith("5"):
            solde = comptes[c]["debit"] - comptes[c]["credit"]
            if abs(solde) > 0.01:
                actif.append({
                    "compte": c,
                    "intitule": PLAN_COMPTABLE.get(c, "Autre"),
                    "montant": solde,
                })
            tresorerie += solde

    total_actif = sum(a["montant"] for a in actif)

    # ===== PASSIF =====
    passif = []

    # Classe 1 : Capitaux propres et emprunts
    for c in sorted(comptes):
        if c.startswith("1"):
            solde = comptes[c]["credit"] - comptes[c]["debit"]
            if abs(solde) > 0.01:
                passif.append({
                    "compte": c,
                    "intitule": PLAN_COMPTABLE.get(c, "Autre"),
                    "montant": solde,
                })

    # Resultat de l'exercice
    if abs(resultat) > 0.01:
        passif.append({
            "compte": "130",
            "intitule": "Resultat net de l'exercice",
            "montant": resultat,
        })

    # 422 Personnel - Engagements contractuels a payer (dettes)
    dettes_personnel = _calculer_dettes_personnel()
    if dettes_personnel > 0.01:
        passif.append({
            "compte": "422",
            "intitule": "Personnel - Engagements a payer",
            "montant": dettes_personnel,
        })

    # Autres dettes (classe 4 creditrice, hors 422)
    for c in sorted(comptes):
        if c.startswith("4") and c != "422":
            solde = comptes[c]["credit"] - comptes[c]["debit"]
            if solde > 0.01:
                passif.append({
                    "compte": c,
                    "intitule": PLAN_COMPTABLE.get(c, "Autre"),
                    "montant": solde,
                })

    total_passif = sum(p["montant"] for p in passif)

    return {
        "titre": "BILAN",
        "date_debut": date_debut or "Origine",
        "date_fin": date_fin or datetime.now().strftime("%d/%m/%Y"),
        "actif": actif,
        "passif": passif,
        "total_actif": total_actif,
        "total_passif": total_passif,
        "resultat": resultat,
    }


def _calculer_impayes():
    """Calcule le total des impayes (creances eleves)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(
            CASE
                WHEN COALESCE(e.frais_scolarite, 0) -
                     COALESCE((SELECT SUM(montant) FROM paiements_eleves
                               WHERE eleve_id = e.id), 0) > 0
                THEN COALESCE(e.frais_scolarite, 0) -
                     COALESCE((SELECT SUM(montant) FROM paiements_eleves
                               WHERE eleve_id = e.id), 0)
                ELSE 0
            END
        ), 0) as total
        FROM eleves e
        WHERE e.actif = 1
    """)
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


def _calculer_avances_en_cours():
    """Calcule le total des avances non encore deduites"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(montant - COALESCE(montant_deduit, 0)), 0) as total
        FROM avances_personnel
        WHERE montant > COALESCE(montant_deduit, 0)
    """)
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


def _calculer_dettes_personnel():
    """Calcule le total des engagements envers le personnel non payes"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(
            COALESCE(p.salaire_mensuel, 0) * COALESCE(p.duree_contrat_mois, 12) -
            COALESCE((SELECT SUM(montant) FROM paiements_personnel
                      WHERE personnel_id = p.id), 0)
        ), 0) as total
        FROM personnel p
        WHERE p.actif = 1
          AND COALESCE(p.salaire_mensuel, 0) * COALESCE(p.duree_contrat_mois, 12) >
              COALESCE((SELECT SUM(montant) FROM paiements_personnel
                        WHERE personnel_id = p.id), 0)
    """)
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


# ============================================================
# 6. ETAT DE TRESORERIE
# ============================================================
def etat_tresorerie(date_debut=None, date_fin=None):
    """Etat des flux de tresorerie"""
    ecritures = _collecter_ecritures(date_debut, date_fin)

    encaissements = []
    decaissements = []

    for e in ecritures:
        for ligne in e["lignes"]:
            c = ligne["compte"]
            if c in ("571", "521", "531"):
                if ligne["debit"] > 0:
                    encaissements.append({
                        "date": e["date"],
                        "libelle": e["libelle"],
                        "montant": ligne["debit"],
                        "compte": c,
                    })
                elif ligne["credit"] > 0:
                    decaissements.append({
                        "date": e["date"],
                        "libelle": e["libelle"],
                        "montant": ligne["credit"],
                        "compte": c,
                    })

    total_entrees = sum(e["montant"] for e in encaissements)
    total_sorties = sum(d["montant"] for d in decaissements)

    return {
        "titre": "ETAT DE TRESORERIE",
        "date_debut": date_debut or "Origine",
        "date_fin": date_fin or datetime.now().strftime("%d/%m/%Y"),
        "encaissements": encaissements,
        "decaissements": decaissements,
        "total_entrees": total_entrees,
        "total_sorties": total_sorties,
        "solde": total_entrees - total_sorties,
    }