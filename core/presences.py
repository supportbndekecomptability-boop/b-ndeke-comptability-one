"""
Gestion des presences des eleves - B-NDEKE Comptability One
"""
from datetime import datetime, timedelta
from database import get_connection


STATUTS = ["present", "absent", "retard"]


def _lundi_semaine(date=None):
    if date is None:
        date = datetime.now().date()
    elif isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d").date()
    return date - timedelta(days=date.weekday())


def _dimanche_semaine(date=None):
    lundi = _lundi_semaine(date)
    return lundi + timedelta(days=6)


def enregistrer_presence(eleve_id, date_presence, statut, motif="", utilisateur_id=None):
    if statut not in STATUTS:
        return False, f"Statut invalide : {statut}", None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT nom, prenom FROM eleves WHERE id = ?", (eleve_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Eleve introuvable", None
        nom_complet = f"{row['nom']} {row['prenom']}"

        cursor.execute("""
            INSERT INTO presences_eleves
                (eleve_id, date_presence, statut, motif, saisi_par)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(eleve_id, date_presence)
            DO UPDATE SET
                statut = excluded.statut,
                motif = excluded.motif,
                saisi_par = excluded.saisi_par,
                date_saisie = CURRENT_TIMESTAMP
        """, (eleve_id, date_presence, statut, motif, utilisateur_id))

        conn.commit()

        alerte = None
        if statut == "absent":
            nb = compter_absences_semaine(eleve_id, date_presence)
            if nb >= 3:
                alerte = {
                    "eleve": nom_complet,
                    "eleve_id": eleve_id,
                    "nb_absences": nb,
                }

        conn.close()
        return True, "Presence enregistree", alerte

    except Exception as e:
        return False, f"Erreur : {str(e)}", None


def compter_absences_semaine(eleve_id, date_ref=None):
    lundi = _lundi_semaine(date_ref)
    dimanche = lundi + timedelta(days=6)

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM presences_eleves
            WHERE eleve_id = ?
              AND statut = 'absent'
              AND non_considere = 0
              AND date_presence >= ?
              AND date_presence <= ?
        """, (eleve_id, lundi.isoformat(), dimanche.isoformat()))
        total = cursor.fetchone()["total"]
        conn.close()
        return total
    except Exception:
        return 0


def presences_du_jour(date_presence=None):
    if date_presence is None:
        date_presence = datetime.now().strftime("%Y-%m-%d")

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                e.id as eleve_id,
                e.matricule,
                e.nom,
                e.prenom,
                e.classe,
                p.statut,
                p.motif,
                p.non_considere,
                p.id as presence_id
            FROM eleves e
            LEFT JOIN presences_eleves p
                ON p.eleve_id = e.id AND p.date_presence = ?
            WHERE e.actif = 1
            ORDER BY e.classe, e.nom, e.prenom
        """, (date_presence,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[PRESENCES] Erreur : {e}")
        return []


def ignorer_absence(presence_id, ignorer=True):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE presences_eleves
            SET non_considere = ?
            WHERE id = ?
        """, (1 if ignorer else 0, presence_id))
        conn.commit()
        conn.close()
        return True, "Absence mise a jour"
    except Exception as e:
        return False, f"Erreur : {e}"


def statistiques_semaine(date_ref=None):
    lundi = _lundi_semaine(date_ref)
    dimanche = lundi + timedelta(days=6)

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(CASE WHEN statut = 'present' THEN 1 END) as nb_presents,
                COUNT(CASE WHEN statut = 'absent' AND non_considere = 0 THEN 1 END) as nb_absents,
                COUNT(CASE WHEN statut = 'retard' THEN 1 END) as nb_retards
            FROM presences_eleves
            WHERE date_presence >= ? AND date_presence <= ?
        """, (lundi.isoformat(), dimanche.isoformat()))
        row = cursor.fetchone()
        conn.close()

        return {
            "lundi": lundi,
            "dimanche": dimanche,
            "nb_presents": row["nb_presents"] or 0,
            "nb_absents": row["nb_absents"] or 0,
            "nb_retards": row["nb_retards"] or 0,
        }
    except Exception:
        return {
            "lundi": lundi, "dimanche": dimanche,
            "nb_presents": 0, "nb_absents": 0, "nb_retards": 0,
        }


def eleves_avec_absences_repetees(date_ref=None):
    lundi = _lundi_semaine(date_ref)
    dimanche = lundi + timedelta(days=6)

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                e.id, e.matricule, e.nom, e.prenom, e.classe,
                COUNT(*) as nb_absences
            FROM presences_eleves p
            JOIN eleves e ON p.eleve_id = e.id
            WHERE p.statut = 'absent'
              AND p.non_considere = 0
              AND p.date_presence >= ?
              AND p.date_presence <= ?
            GROUP BY e.id
            HAVING COUNT(*) >= 3
            ORDER BY nb_absences DESC, e.nom
        """, (lundi.isoformat(), dimanche.isoformat()))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []

        

def liste_classes():
    """Retourne la liste des classes existantes (triees)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT classe FROM eleves
            WHERE actif = 1 AND classe IS NOT NULL AND classe != ''
            ORDER BY classe
        """)
        rows = [r["classe"] for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []


def presences_par_classe(date_presence=None, classe=None):
    """
    Liste les eleves d'une classe (ou toutes) avec leur statut pour une date.
    """
    if date_presence is None:
        date_presence = datetime.now().strftime("%Y-%m-%d")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if classe:
            cursor.execute("""
                SELECT
                    e.id as eleve_id,
                    e.matricule,
                    e.nom,
                    e.prenom,
                    e.classe,
                    p.statut,
                    p.motif,
                    p.non_considere,
                    p.id as presence_id
                FROM eleves e
                LEFT JOIN presences_eleves p
                    ON p.eleve_id = e.id AND p.date_presence = ?
                WHERE e.actif = 1 AND e.classe = ?
                ORDER BY e.nom, e.prenom
            """, (date_presence, classe))
        else:
            cursor.execute("""
                SELECT
                    e.id as eleve_id,
                    e.matricule,
                    e.nom,
                    e.prenom,
                    e.classe,
                    p.statut,
                    p.motif,
                    p.non_considere,
                    p.id as presence_id
                FROM eleves e
                LEFT JOIN presences_eleves p
                    ON p.eleve_id = e.id AND p.date_presence = ?
                WHERE e.actif = 1
                ORDER BY e.classe, e.nom, e.prenom
            """, (date_presence,))

        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[PRESENCES] Erreur : {e}")
        return []