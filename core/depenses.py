"""
Gestion des depenses de B-NDEKE Comptability One
"""
from datetime import datetime
from database import get_connection


def generer_numero_depense():
    """Numero auto : DEP-2025-0001"""
    annee = datetime.now().year
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM depenses")
    total = cursor.fetchone()["total"]
    conn.close()
    return f"DEP-{annee}-{total + 1:04d}"


def ajouter_depense(libelle, montant, categorie, utilisateur_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        montant = float(montant)
        if montant <= 0:
            return False, "Le montant doit etre superieur a 0"
        cursor.execute("""
            INSERT INTO depenses (libelle, montant, categorie, utilisateur_id)
            VALUES (?, ?, ?, ?)
        """, (libelle.strip(), montant, categorie.strip(), utilisateur_id))
        conn.commit()
        return True, "Depense enregistree avec succes"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


def lister_depenses(recherche=""):
    conn = get_connection()
    cursor = conn.cursor()

    base = """
        SELECT id, libelle, montant, categorie, date_depense, utilisateur_id
        FROM depenses
        WHERE 1=1
    """

    if recherche.strip():
        terme = f"%{recherche.strip()}%"
        cursor.execute(base + """
            AND (libelle LIKE ? OR categorie LIKE ?)
            ORDER BY date_depense DESC, id DESC
        """, (terme, terme))
    else:
        cursor.execute(base + " ORDER BY date_depense DESC, id DESC")

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_depense(depense_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM depenses WHERE id = ?", (depense_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def modifier_depense(depense_id, libelle, montant, categorie):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE depenses
            SET libelle = ?, montant = ?, categorie = ?
            WHERE id = ?
        """, (libelle.strip(), float(montant), categorie.strip(), depense_id))
        conn.commit()
        return True, "Depense modifiee avec succes"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


def supprimer_depense(depense_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM depenses WHERE id = ?", (depense_id,))
        conn.commit()
        return True, "Depense supprimee avec succes"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


# ===== TOTAUX =====
def total_depenses():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(SUM(montant), 0) as total FROM depenses")
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


def total_depenses_jour():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(montant), 0) as total FROM depenses
        WHERE DATE(date_depense) = DATE('now', 'localtime')
    """)
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


def total_depenses_mois():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(montant), 0) as total FROM depenses
        WHERE strftime('%Y-%m', date_depense) = strftime('%Y-%m', 'now', 'localtime')
    """)
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


def compter_depenses():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM depenses")
    total = cursor.fetchone()["total"]
    conn.close()
    return total


# Categories suggerees
CATEGORIES = [
    "Loyer",
    "Electricite",
    "Eau",
    "Internet",
    "Fournitures scolaires",
    "Entretien",
    "Transport",
    "Carburant",
    "Telephone",
    "Publicite",
    "Frais bancaires",
    "Mobilier",
    "Informatique",
    "Cantine",
    "Securite",
    "Assurance",
    "Autre",
]