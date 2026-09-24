"""
Gestion des depenses de B-NDEKE Comptability One
Avec liaison aux sous-categories budgetaires.
"""
from datetime import datetime
from database import get_connection


def generer_numero_depense():
    annee = datetime.now().year
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM depenses")
    total = cursor.fetchone()["total"]
    conn.close()
    return f"DEP-{annee}-{total + 1:04d}"


def ajouter_depense(libelle, montant, categorie, utilisateur_id=None,
                    budget_sous_categorie=""):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        montant = float(montant)
        if montant <= 0:
            return False, "Le montant doit etre superieur a 0"
        cursor.execute("""
            INSERT INTO depenses
                (libelle, montant, categorie, utilisateur_id, budget_sous_categorie)
            VALUES (?, ?, ?, ?, ?)
        """, (libelle.strip(), montant, categorie.strip(), utilisateur_id,
              (budget_sous_categorie or "").strip()))
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
        SELECT id, libelle, montant, categorie, date_depense,
               utilisateur_id, COALESCE(budget_sous_categorie, '') as budget_sous_categorie
        FROM depenses
        WHERE 1=1
    """

    if recherche.strip():
        terme = f"%{recherche.strip()}%"
        cursor.execute(base + """
            AND (libelle LIKE ? OR categorie LIKE ? OR budget_sous_categorie LIKE ?)
            ORDER BY date_depense DESC, id DESC
        """, (terme, terme, terme))
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


def modifier_depense(depense_id, libelle, montant, categorie,
                     budget_sous_categorie=""):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE depenses
            SET libelle = ?, montant = ?, categorie = ?, budget_sous_categorie = ?
            WHERE id = ?
        """, (libelle.strip(), float(montant), categorie.strip(),
              (budget_sous_categorie or "").strip(), depense_id))
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


# ===== SUIVI BUDGETAIRE =====
def total_depenses_par_sous_categorie():
    """
    Retourne un dict :
    { "Papier et cahiers": 800000, "Fournitures scolaires": 400000, ... }
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COALESCE(budget_sous_categorie, '') as sous_cat,
                COALESCE(SUM(montant), 0) as total
            FROM depenses
            WHERE COALESCE(budget_sous_categorie, '') != ''
            GROUP BY budget_sous_categorie
        """)
        rows = cursor.fetchall()
        conn.close()
        return {r["sous_cat"]: float(r["total"] or 0) for r in rows}
    except Exception as e:
        print(f"[DEPENSES] Erreur calcul par sous-categorie : {e}")
        return {}


def suivi_budgetaire_complet():
    """
    Retourne le suivi budgetaire complet :
    prevu / reel / ecart par budget et par sous-categorie.
    """
    try:
        from core.budgets import get_budgets
        data = get_budgets()
        par_sous = total_depenses_par_sous_categorie()

        result = {}
        for key in ("prime", "investissement", "fonctionnement"):
            b = data.get(key, {})
            prevu = b.get("montant", 0)
            sous = {}
            total_reel = 0

            for nom, info in b.get("sous_categories", {}).items():
                p = info.get("montant", 0)
                r = par_sous.get(nom, 0)
                sous[nom] = {
                    "prevu": p,
                    "reel": r,
                    "ecart": p - r,
                }
                total_reel += r

            result[key] = {
                "prevu": prevu,
                "reel": total_reel,
                "ecart": prevu - total_reel,
                "sous_categories": sous,
            }

        return result
    except Exception as e:
        print(f"[DEPENSES] Erreur suivi budgetaire : {e}")
        return {}


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