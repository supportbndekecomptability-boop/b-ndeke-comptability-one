"""
Gestion des eleves - avec separation frais scolaires / autres frais
"""
from database import get_connection


def generer_matricule():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM eleves")
    total = cursor.fetchone()["total"]
    conn.close()
    return f"BN{2025}{total + 1:04d}"


def ajouter_eleve(matricule, nom, prenom, classe, sexe=None,
                  date_naissance=None, nom_parent=None, telephone_parent=None,
                  frais_scolarite=0):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO eleves
                (matricule, nom, prenom, classe, sexe, date_naissance,
                 nom_parent, telephone_parent, frais_scolarite)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (matricule.strip().upper(), nom.strip().upper(), prenom.strip().capitalize(),
              classe.strip(), sexe, date_naissance, nom_parent, telephone_parent,
              float(frais_scolarite or 0)))
        conn.commit()
        return True, "Eleve ajoute avec succes"
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, f"Le matricule '{matricule}' existe deja"
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


def _total_par_motif(eleve_id, motif_like):
    """Retourne le total des paiements pour un motif (LIKE)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(montant), 0) as total
        FROM paiements_eleves
        WHERE eleve_id = ? AND LOWER(motif) LIKE ?
    """, (eleve_id, motif_like))
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return float(total)


def lister_eleves(recherche=""):
    """Liste tous les eleves avec separation frais scolaires / autres frais"""
    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT e.id, e.matricule, e.nom, e.prenom, e.classe, e.sexe,
               e.nom_parent, e.telephone_parent, e.date_inscription,
               COALESCE(e.frais_scolarite, 0) as frais_scolarite,
               -- Paiements FRAIS SCOLAIRES uniquement
               COALESCE(
                   (SELECT SUM(montant) FROM paiements_eleves
                    WHERE eleve_id = e.id
                      AND LOWER(motif) LIKE '%scolaire%'), 0
               ) as paye_scolaire,
               -- Paiements UNIFORME
               COALESCE(
                   (SELECT SUM(montant) FROM paiements_eleves
                    WHERE eleve_id = e.id
                      AND LOWER(motif) LIKE '%uniforme%'), 0
               ) as paye_uniforme,
               -- Paiements TRANSPORT
               COALESCE(
                   (SELECT SUM(montant) FROM paiements_eleves
                    WHERE eleve_id = e.id
                      AND LOWER(motif) LIKE '%transport%'), 0
               ) as paye_transport,
               -- Paiements CANTINE
               COALESCE(
                   (SELECT SUM(montant) FROM paiements_eleves
                    WHERE eleve_id = e.id
                      AND LOWER(motif) LIKE '%cantine%'), 0
               ) as paye_cantine,
               -- Paiements INSCRIPTION
               COALESCE(
                   (SELECT SUM(montant) FROM paiements_eleves
                    WHERE eleve_id = e.id
                      AND LOWER(motif) LIKE '%inscription%'), 0
               ) as paye_inscription
        FROM eleves e
        WHERE e.actif = 1
    """

    if recherche.strip():
        terme = f"%{recherche.strip()}%"
        cursor.execute(base_query + """
            AND (
                e.matricule LIKE ? OR
                e.nom LIKE ? OR
                e.prenom LIKE ? OR
                e.classe LIKE ?
            )
            ORDER BY e.classe, e.nom, e.prenom
        """, (terme, terme, terme, terme))
    else:
        cursor.execute(base_query + " ORDER BY e.classe, e.nom, e.prenom")

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Calculer le solde scolaire pour chaque eleve
    for r in rows:
        r["solde"] = r["frais_scolarite"] - r["paye_scolaire"]

    return rows


def get_eleve(eleve_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM eleves WHERE id = ?", (eleve_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def modifier_eleve(eleve_id, matricule, nom, prenom, classe, sexe=None,
                   date_naissance=None, nom_parent=None, telephone_parent=None,
                   frais_scolarite=0):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE eleves
            SET matricule = ?, nom = ?, prenom = ?, classe = ?,
                sexe = ?, date_naissance = ?, nom_parent = ?,
                telephone_parent = ?, frais_scolarite = ?
            WHERE id = ?
        """, (matricule.strip().upper(), nom.strip().upper(),
              prenom.strip().capitalize(), classe.strip(), sexe,
              date_naissance, nom_parent, telephone_parent,
              float(frais_scolarite or 0), eleve_id))
        conn.commit()
        return True, "Eleve modifie avec succes"
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, f"Le matricule '{matricule}' existe deja"
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


def supprimer_eleve(eleve_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE eleves SET actif = 0 WHERE id = ?", (eleve_id,))
        conn.commit()
        return True, "Eleve supprime avec succes"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


def compter_eleves():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM eleves WHERE actif = 1")
    total = cursor.fetchone()["total"]
    conn.close()
    return total


def lister_classes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT classe FROM eleves
        WHERE actif = 1
        ORDER BY classe
    """)
    classes = [r["classe"] for r in cursor.fetchall()]
    conn.close()
    return classes