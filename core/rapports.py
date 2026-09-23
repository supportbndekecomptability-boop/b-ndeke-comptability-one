"""
Generation des donnees pour les rapports
"""
from datetime import datetime
from database import get_connection


def _connexion():
    return get_connection()


def donnees_rapport_mensuel(annee=None, mois=None):
    """Retourne un dict avec toutes les donnees du mois"""
    if annee is None or mois is None:
        maintenant = datetime.now()
        annee = maintenant.year
        mois = maintenant.month

    mois_str = f"{annee}-{mois:02d}"

    conn = _connexion()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(montant), 0) as total, COUNT(*) as nombre
        FROM paiements_eleves
        WHERE strftime('%Y-%m', date_paiement) = ?
    """, (mois_str,))
    row = cursor.fetchone()
    recettes_eleves = {"total": row["total"] or 0, "nombre": row["nombre"] or 0}

    cursor.execute("""
        SELECT COALESCE(SUM(montant), 0) as total, COUNT(*) as nombre
        FROM paiements_personnel
        WHERE strftime('%Y-%m', date_paiement) = ?
    """, (mois_str,))
    row = cursor.fetchone()
    depenses_personnel = {"total": row["total"] or 0, "nombre": row["nombre"] or 0}

    cursor.execute("""
        SELECT COALESCE(SUM(montant), 0) as total, COUNT(*) as nombre
        FROM depenses
        WHERE strftime('%Y-%m', date_depense) = ?
    """, (mois_str,))
    row = cursor.fetchone()
    depenses_generales = {"total": row["total"] or 0, "nombre": row["nombre"] or 0}

    cursor.execute("""
        SELECT categorie, SUM(montant) as total, COUNT(*) as nombre
        FROM depenses
        WHERE strftime('%Y-%m', date_depense) = ?
        GROUP BY categorie
        ORDER BY total DESC
    """, (mois_str,))
    depenses_par_categorie = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT p.nom, p.prenom, p.fonction, p.code,
               SUM(pp.montant) as total
        FROM paiements_personnel pp
        JOIN personnel p ON pp.personnel_id = p.id
        WHERE strftime('%Y-%m', pp.date_paiement) = ?
        GROUP BY p.id
        ORDER BY total DESC
    """, (mois_str,))
    paies_personnel = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT COUNT(*) as nombre,
               COALESCE(SUM(
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
    row = cursor.fetchone()
    impayes = {"nombre": row["nombre"] or 0, "total": row["total"] or 0}

    conn.close()

    recettes_totales = recettes_eleves["total"]
    depenses_totales = depenses_personnel["total"] + depenses_generales["total"]
    benefice = recettes_totales - depenses_totales

    return {
        "annee": annee,
        "mois": mois,
        "mois_str": mois_str,
        "date_generation": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "recettes_eleves": recettes_eleves,
        "depenses_personnel": depenses_personnel,
        "depenses_generales": depenses_generales,
        "depenses_par_categorie": depenses_par_categorie,
        "paies_personnel": paies_personnel,
        "impayes": impayes,
        "recettes_totales": recettes_totales,
        "depenses_totales": depenses_totales,
        "benefice": benefice,
    }


def donnees_rapport_impayes():
    """Retourne la liste detaillee des impayes"""
    conn = _connexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.matricule, e.nom, e.prenom, e.classe,
               COALESCE(e.frais_scolarite, 0) as frais,
               COALESCE((SELECT SUM(montant) FROM paiements_eleves
                         WHERE eleve_id = e.id), 0) as paye,
               COALESCE(e.frais_scolarite, 0) -
                   COALESCE((SELECT SUM(montant) FROM paiements_eleves
                             WHERE eleve_id = e.id), 0) as solde
        FROM eleves e
        WHERE e.actif = 1
        ORDER BY solde DESC
    """)
    eleves = [dict(r) for r in cursor.fetchall()]
    conn.close()

    eleves_impayes = [e for e in eleves if e["solde"] > 0]
    total_impaye = sum(e["solde"] for e in eleves_impayes)

    return {
        "date_generation": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "eleves": eleves_impayes,
        "nombre_impayes": len(eleves_impayes),
        "total_impaye": total_impaye,
    }


def donnees_rapport_dettes_personnel():
    """Retourne la liste des dettes envers le personnel"""
    conn = _connexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.code, p.nom, p.prenom, p.fonction,
               COALESCE(p.salaire_mensuel, 0) as salaire,
               COALESCE(p.duree_contrat_mois, 12) as duree,
               COALESCE(p.salaire_mensuel, 0) * COALESCE(p.duree_contrat_mois, 12) as engagement,
               COALESCE((SELECT SUM(montant) FROM paiements_personnel
                         WHERE personnel_id = p.id), 0) as paye
        FROM personnel p
        WHERE p.actif = 1
        ORDER BY p.nom
    """)
    personnel = [dict(r) for r in cursor.fetchall()]
    conn.close()

    for p in personnel:
        p["reste"] = p["engagement"] - p["paye"]

    dettes = [p for p in personnel if p["reste"] > 0]
    total_dette = sum(p["reste"] for p in dettes)

    return {
        "date_generation": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "personnel": dettes,
        "nombre": len(dettes),
        "total_dette": total_dette,
    }


def donnees_rapport_journalier(date_str=None):
    """Retourne les operations d'une journee"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    conn = _connexion()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.numero_recu, p.montant, p.motif, p.mode_paiement,
               p.date_paiement, e.matricule, e.nom, e.prenom, e.classe
        FROM paiements_eleves p
        JOIN eleves e ON p.eleve_id = e.id
        WHERE DATE(p.date_paiement) = ?
        ORDER BY p.date_paiement DESC
    """, (date_str,))
    paiements_eleves = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT pp.numero_paie, pp.montant, pp.motif, pp.mode_paiement,
               pp.date_paiement, e.code, e.nom, e.prenom, e.fonction
        FROM paiements_personnel pp
        JOIN personnel e ON pp.personnel_id = e.id
        WHERE DATE(pp.date_paiement) = ?
        ORDER BY pp.date_paiement DESC
    """, (date_str,))
    paiements_personnel = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT libelle, montant, categorie, date_depense
        FROM depenses
        WHERE DATE(date_depense) = ?
        ORDER BY date_depense DESC
    """, (date_str,))
    depenses = [dict(r) for r in cursor.fetchall()]

    conn.close()

    total_recettes = sum(p["montant"] for p in paiements_eleves)
    total_personnel = sum(p["montant"] for p in paiements_personnel)
    total_depenses = sum(d["montant"] for d in depenses)

    return {
        "date": date_str,
        "date_generation": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "paiements_eleves": paiements_eleves,
        "paiements_personnel": paiements_personnel,
        "depenses": depenses,
        "total_recettes": total_recettes,
        "total_personnel": total_personnel,
        "total_depenses": total_depenses,
        "solde_jour": total_recettes - total_personnel - total_depenses,
    }