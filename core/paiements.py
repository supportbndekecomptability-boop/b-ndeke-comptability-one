"""
Gestion des paiements (Eleves + Personnel) de B-NDEKE Comptability One
"""
from datetime import datetime
from database import get_connection


# ============ NUMEROS AUTO ============
def generer_numero_recu():
    """Numero de recu pour paiement eleve : REC-2025-0001"""
    annee = datetime.now().year
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM paiements_eleves")
    total = cursor.fetchone()["total"]
    conn.close()
    return f"REC-{annee}-{total + 1:04d}"


def generer_numero_paie():
    """Numero de paie pour personnel : PAIE-2025-0001"""
    annee = datetime.now().year
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM paiements_personnel")
    total = cursor.fetchone()["total"]
    conn.close()
    return f"PAIE-{annee}-{total + 1:04d}"


# ============ PAIEMENTS ELEVES ============
def ajouter_paiement_eleve(eleve_id, montant, motif, mode_paiement, utilisateur_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        montant = float(montant)
        if montant <= 0:
            return False, "Le montant doit etre superieur a 0", None
        numero = generer_numero_recu()
        cursor.execute("""
            INSERT INTO paiements_eleves
                (numero_recu, eleve_id, montant, motif, mode_paiement, utilisateur_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (numero, eleve_id, montant, motif.strip(), mode_paiement, utilisateur_id))
        conn.commit()
        return True, f"Recu {numero}", numero
    except Exception as e:
        return False, f"Erreur : {str(e)}", None
    finally:
        conn.close()


def lister_paiements_eleves(recherche=""):
    conn = get_connection()
    cursor = conn.cursor()
    base = """
        SELECT p.id, p.numero_recu, p.montant, p.motif, p.mode_paiement,
               p.date_paiement, p.eleve_id,
               e.matricule, e.nom, e.prenom, e.classe
        FROM paiements_eleves p
        JOIN eleves e ON p.eleve_id = e.id
        WHERE 1=1
    """
    if recherche.strip():
        terme = f"%{recherche.strip()}%"
        cursor.execute(base + """
            AND (p.numero_recu LIKE ? OR e.matricule LIKE ?
                 OR e.nom LIKE ? OR e.prenom LIKE ? OR p.motif LIKE ?)
            ORDER BY p.date_paiement DESC, p.id DESC
        """, (terme, terme, terme, terme, terme))
    else:
        cursor.execute(base + " ORDER BY p.date_paiement DESC, p.id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def supprimer_paiement_eleve(pid):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM paiements_eleves WHERE id = ?", (pid,))
        conn.commit()
        return True, "Paiement supprime"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


# ============ PAIEMENTS PERSONNEL ============
def ajouter_paiement_personnel(personnel_id, montant, motif, mode_paiement,
                                utilisateur_id=None, montant_avance_deduit=0):
    """
    Enregistre une paie.
    - montant : montant TOTAL du salaire (ex: $400)
    - montant_avance_deduit : montant d'avance a deduire (ex: $100)
    Le net verse = montant - montant_avance_deduit
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        montant = float(montant)
        montant_avance_deduit = float(montant_avance_deduit or 0)

        if montant <= 0:
            return False, "Le montant doit etre superieur a 0", None

        if montant_avance_deduit < 0:
            return False, "Le montant de l'avance ne peut pas etre negatif", None

        if montant_avance_deduit > montant:
            return False, "L'avance depasse le montant du salaire", None

        numero = generer_numero_paie()
        cursor.execute("""
            INSERT INTO paiements_personnel
                (numero_paie, personnel_id, montant, motif, mode_paiement,
                 utilisateur_id, montant_avance_deduit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (numero, personnel_id, montant, motif.strip(), mode_paiement,
              utilisateur_id, montant_avance_deduit))
        conn.commit()
        return True, f"Paie {numero}", numero
    except Exception as e:
        return False, f"Erreur : {str(e)}", None
    finally:
        conn.close()


def lister_paiements_personnel(recherche=""):
    conn = get_connection()
    cursor = conn.cursor()
    base = """
        SELECT p.id, p.numero_paie, p.montant, p.motif, p.mode_paiement,
               COALESCE(p.montant_avance_deduit, 0) as montant_avance_deduit,
               p.date_paiement, p.personnel_id,
               e.code, e.nom, e.prenom, e.fonction
        FROM paiements_personnel p
        JOIN personnel e ON p.personnel_id = e.id
        WHERE 1=1
    """
    if recherche.strip():
        terme = f"%{recherche.strip()}%"
        cursor.execute(base + """
            AND (p.numero_paie LIKE ? OR e.code LIKE ?
                 OR e.nom LIKE ? OR e.prenom LIKE ? OR p.motif LIKE ?)
            ORDER BY p.date_paiement DESC, p.id DESC
        """, (terme, terme, terme, terme, terme))
    else:
        cursor.execute(base + " ORDER BY p.date_paiement DESC, p.id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def supprimer_paiement_personnel(pid):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM paiements_personnel WHERE id = ?", (pid,))
        conn.commit()
        return True, "Paie supprimee"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


# ============ TOTAUX / CAISSES ============
def total_caisse_eleves():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(SUM(montant), 0) as total FROM paiements_eleves")
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


def total_caisse_personnel():
    """Total verse REELLEMENT au personnel (net, apres deduction avances)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(montant - COALESCE(montant_avance_deduit, 0)), 0) as total
        FROM paiements_personnel
    """)
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


def total_caisse_eleves_jour():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(montant), 0) as total FROM paiements_eleves
        WHERE DATE(date_paiement) = DATE('now', 'localtime')
    """)
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


def total_caisse_personnel_jour():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(montant - COALESCE(montant_avance_deduit, 0)), 0) as total
        FROM paiements_personnel
        WHERE DATE(date_paiement) = DATE('now', 'localtime')
    """)
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


def total_caisse_eleves_mois():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(montant), 0) as total FROM paiements_eleves
        WHERE strftime('%Y-%m', date_paiement) = strftime('%Y-%m', 'now', 'localtime')
    """)
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


def total_caisse_personnel_mois():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(montant - COALESCE(montant_avance_deduit, 0)), 0) as total
        FROM paiements_personnel
        WHERE strftime('%Y-%m', date_paiement) = strftime('%Y-%m', 'now', 'localtime')
    """)
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


# ============ RECHERCHE RAPIDE ============
def rechercher_eleve_par_matricule(matricule):
    """Retourne un eleve + son solde"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*,
               COALESCE(e.frais_scolarite, 0) - COALESCE(
                   (SELECT SUM(montant) FROM paiements_eleves WHERE eleve_id = e.id), 0
               ) as solde
        FROM eleves e
        WHERE e.matricule = ? AND e.actif = 1
    """, (matricule.strip().upper(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def rechercher_personnel_par_code(code):
    """Retourne un personnel + son engagement total + solde a payer"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*,
               COALESCE(p.salaire_mensuel, 0) * COALESCE(p.duree_contrat_mois, 12)
                   as engagement_total,
               COALESCE(p.salaire_mensuel, 0) * COALESCE(p.duree_contrat_mois, 12)
               - COALESCE(
                   (SELECT SUM(montant) FROM paiements_personnel
                    WHERE personnel_id = p.id), 0
               ) as solde_a_payer,
               COALESCE(
                   (SELECT SUM(montant) FROM paiements_personnel
                    WHERE personnel_id = p.id), 0
               ) as total_paye
        FROM personnel p
        WHERE p.code = ? AND p.actif = 1
    """, (code.strip().upper(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def total_impayes_eleves():
    """Total des soldes impayes de tous les eleves"""
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