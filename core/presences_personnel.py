"""
Gestion des presences du personnel - B-NDEKE Comptability One
Avec colonne 'niveau' pour le filtrage par role (Directeur/Prefer).
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


def enregistrer_presence(personnel_id, date_presence, statut,
                         motif="", utilisateur_id=None):
    if statut not in STATUTS:
        return False, f"Statut invalide : {statut}"
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO presences_personnel
                (personnel_id, date_presence, statut, motif, saisi_par)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(personnel_id, date_presence)
            DO UPDATE SET
                statut = excluded.statut,
                motif = excluded.motif,
                saisi_par = excluded.saisi_par,
                date_saisie = CURRENT_TIMESTAMP
        """, (personnel_id, date_presence, statut, motif, utilisateur_id))
        conn.commit()
        conn.close()
        return True, "Presence enregistree"
    except Exception as e:
        return False, f"Erreur : {e}"


def compter_absences_semaine(personnel_id, date_ref=None):
    lundi = _lundi_semaine(date_ref)
    dimanche = lundi + timedelta(days=6)
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM presences_personnel
            WHERE personnel_id = ?
              AND statut = 'absent'
              AND non_considere = 0
              AND date_presence >= ?
              AND date_presence <= ?
        """, (personnel_id, lundi.isoformat(), dimanche.isoformat()))
        total = cursor.fetchone()["total"]
        conn.close()
        return total
    except Exception:
        return 0


def presences_par_fonction(date_presence=None, fonction=None):
    if date_presence is None:
        date_presence = datetime.now().strftime("%Y-%m-%d")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if fonction:
            cursor.execute("""
                SELECT
                    p.id as personnel_id, p.code, p.nom, p.prenom, p.fonction,
                    p.niveau, p.salaire_mensuel,
                    pr.statut, pr.motif, pr.non_considere, pr.id as presence_id
                FROM personnel p
                LEFT JOIN presences_personnel pr
                    ON pr.personnel_id = p.id AND pr.date_presence = ?
                WHERE p.actif = 1 AND p.fonction = ?
                ORDER BY p.nom, p.prenom
            """, (date_presence, fonction))
        else:
            cursor.execute("""
                SELECT
                    p.id as personnel_id, p.code, p.nom, p.prenom, p.fonction,
                    p.niveau, p.salaire_mensuel,
                    pr.statut, pr.motif, pr.non_considere, pr.id as presence_id
                FROM personnel p
                LEFT JOIN presences_personnel pr
                    ON pr.personnel_id = p.id AND pr.date_presence = ?
                WHERE p.actif = 1
                ORDER BY p.fonction, p.nom, p.prenom
            """, (date_presence,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[PRESENCES] Erreur : {e}")
        return []


def liste_fonctions():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT fonction FROM personnel
            WHERE actif = 1 AND fonction IS NOT NULL AND fonction != ''
            ORDER BY fonction
        """)
        rows = [r["fonction"] for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []


def ignorer_absence(presence_id, ignorer=True):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE presences_personnel SET non_considere = ? WHERE id = ?
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
            FROM presences_personnel
            WHERE date_presence >= ? AND date_presence <= ?
        """, (lundi.isoformat(), dimanche.isoformat()))
        row = cursor.fetchone()
        conn.close()
        return {
            "nb_presents": row["nb_presents"] or 0,
            "nb_absents": row["nb_absents"] or 0,
            "nb_retards": row["nb_retards"] or 0,
        }
    except Exception:
        return {"nb_presents": 0, "nb_absents": 0, "nb_retards": 0}


def ajouter_retenue(personnel_id, date_retenue, pourcentage=0,
                    montant_calcule=0, motif="", utilisateur_id=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO retenues_personnel
                (personnel_id, date_retenue, pourcentage, montant_calcule,
                 motif, utilisateur_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (personnel_id, date_retenue, pourcentage, montant_calcule,
              motif, utilisateur_id))
        conn.commit()
        conn.close()
        return True, "Retenue enregistree"
    except Exception as e:
        return False, f"Erreur : {e}"


def lister_retenues_en_attente(personnel_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, date_retenue, pourcentage, montant_calcule, motif
            FROM retenues_personnel
            WHERE personnel_id = ? AND statut = 'en_attente'
            ORDER BY date_retenue
        """, (personnel_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []


def marquer_retenue_appliquee(retenue_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE retenues_personnel SET statut = 'appliquee' WHERE id = ?
        """, (retenue_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


# ============================================================
# NOUVEAU : statistiques filtrees par niveau
# ============================================================

def statistiques_semaine_par_niveaux(date_ref=None, niveaux=None):
    """
    Statistiques de la semaine, filtrees par niveaux autorises.
    niveaux : liste ['Maternelle', 'Primaire'] ou None pour tout.
    """
    lundi = _lundi_semaine(date_ref)
    dimanche = lundi + timedelta(days=6)

    if niveaux is None:
        return statistiques_semaine(date_ref)

    try:
        conn = get_connection()
        cursor = conn.cursor()
        placeholders = ",".join("?" * len(niveaux))
        cursor.execute(f"""
            SELECT
                COUNT(CASE WHEN pr.statut = 'present' THEN 1 END) as nb_presents,
                COUNT(CASE WHEN pr.statut = 'absent' AND pr.non_considere = 0 THEN 1 END) as nb_absents,
                COUNT(CASE WHEN pr.statut = 'retard' THEN 1 END) as nb_retards
            FROM presences_personnel pr
            JOIN personnel p ON p.id = pr.personnel_id
            WHERE pr.date_presence >= ? AND pr.date_presence <= ?
              AND p.niveau IN ({placeholders})
        """, (lundi.isoformat(), dimanche.isoformat(), *niveaux))
        row = cursor.fetchone()
        conn.close()
        return {
            "nb_presents": row["nb_presents"] or 0,
            "nb_absents": row["nb_absents"] or 0,
            "nb_retards": row["nb_retards"] or 0,
        }
    except Exception:
        return {"nb_presents": 0, "nb_absents": 0, "nb_retards": 0}