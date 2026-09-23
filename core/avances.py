"""
Gestion des avances sur salaire du personnel
"""
from datetime import datetime
from database import get_connection


def generer_numero_avance():
    """Numero auto : AV-2025-0001"""
    annee = datetime.now().year
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM avances_personnel")
    total = cursor.fetchone()["total"]
    conn.close()
    return f"AV-{annee}-{total + 1:04d}"


def ajouter_avance(personnel_id, montant, motif, utilisateur_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        montant = float(montant)
        if montant <= 0:
            return False, "Le montant doit etre superieur a 0", None

        numero = generer_numero_avance()

        cursor.execute("""
            INSERT INTO avances_personnel
                (numero_avance, personnel_id, montant, motif, utilisateur_id)
            VALUES (?, ?, ?, ?, ?)
        """, (numero, personnel_id, montant, motif.strip(), utilisateur_id))
        conn.commit()
        return True, f"Avance {numero} enregistree", numero
    except Exception as e:
        return False, f"Erreur : {str(e)}", None
    finally:
        conn.close()


def lister_avances(personnel_id=None, seulement_en_cours=False):
    """Liste les avances (filtre par employe si specifie)"""
    conn = get_connection()
    cursor = conn.cursor()

    base = """
        SELECT a.id, a.numero_avance, a.personnel_id, a.montant,
               a.montant_deduit, a.motif, a.date_avance,
               p.code, p.nom, p.prenom, p.fonction
        FROM avances_personnel a
        JOIN personnel p ON a.personnel_id = p.id
        WHERE 1=1
    """

    params = []

    if personnel_id is not None:
        base += " AND a.personnel_id = ?"
        params.append(personnel_id)

    if seulement_en_cours:
        base += " AND a.montant > a.montant_deduit"

    base += " ORDER BY a.date_avance DESC, a.id DESC"

    cursor.execute(base, params)
    rows = [dict(r) for r in cursor.fetchall()]

    # Calculer le reste
    for r in rows:
        r["reste"] = r["montant"] - r["montant_deduit"]
        r["en_cours"] = r["reste"] > 0.01

    conn.close()
    return rows


def total_avance_en_cours(personnel_id):
    """Total des avances restant a deduire pour un employe"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(montant - COALESCE(montant_deduit, 0)), 0) as total
        FROM avances_personnel
        WHERE personnel_id = ? AND montant > COALESCE(montant_deduit, 0)
    """, (personnel_id,))
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


def deduire_avances_personnel(personnel_id, montant_a_deduire):
    """
    Deduit un montant des avances en cours (FIFO = les plus anciennes en premier).
    Retourne (ok, montant_effectivement_deduit, message)
    """
    montant_a_deduire = float(montant_a_deduire)
    if montant_a_deduire <= 0:
        return True, 0, "Rien a deduire"

    conn = get_connection()
    cursor = conn.cursor()
    montant_restant = montant_a_deduire

    try:
        cursor.execute("""
            SELECT id, montant, COALESCE(montant_deduit, 0) as montant_deduit
            FROM avances_personnel
            WHERE personnel_id = ? AND montant > COALESCE(montant_deduit, 0)
            ORDER BY date_avance ASC, id ASC
        """, (personnel_id,))

        for row in cursor.fetchall():
            if montant_restant <= 0.01:
                break
            reste_avance = row["montant"] - row["montant_deduit"]
            a_deduire = min(reste_avance, montant_restant)

            cursor.execute("""
                UPDATE avances_personnel
                SET montant_deduit = COALESCE(montant_deduit, 0) + ?
                WHERE id = ?
            """, (a_deduire, row["id"]))

            montant_restant -= a_deduire

        conn.commit()
        effectif = montant_a_deduire - montant_restant
        return True, effectif, f"Deduit : {effectif:.2f}"

    except Exception as e:
        conn.rollback()
        return False, 0, f"Erreur : {str(e)}"
    finally:
        conn.close()


def supprimer_avance(avance_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM avances_personnel WHERE id = ?", (avance_id,))
        conn.commit()
        return True, "Avance supprimee"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


def get_avance(avance_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM avances_personnel WHERE id = ?", (avance_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["reste"] = d["montant"] - (d["montant_deduit"] or 0)
        return d
    return None