"""
Gestion des dettes des eleves (categories + report d'annee) - B-NDEKE
"""
from datetime import datetime
from database import get_connection


CATEGORIES = [
    "Scolarite",
    "Inscription",
    "Uniforme",
    "Cantine",
    "Examen",
    "Transport",
    "Fournitures",
    "Autre",
]


def ajouter_dette(eleve_id, annee_libelle, montant, motif="",
                  categorie="Scolarite", utilisateur_id=None):
    if montant <= 0:
        return False, "Le montant doit etre superieur a 0."
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dettes_eleves
                (eleve_id, annee_libelle, montant_initial, solde, motif,
                 categorie, utilisateur_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (eleve_id, annee_libelle, montant, montant, motif,
              categorie, utilisateur_id))
        conn.commit()
        conn.close()
        return True, "Dette enregistree"
    except Exception as e:
        return False, f"Erreur : {e}"


def lister_eleves_avec_dettes(statut=None, recherche=None):
    """Retourne une ligne par eleve avec les totaux agreges."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT
                e.id as eleve_id, e.matricule, e.nom, e.prenom, e.classe,
                COUNT(d.id) as nb_dettes,
                COALESCE(SUM(d.montant_initial), 0) as total_du,
                COALESCE(SUM(d.montant_paye), 0) as total_paye,
                COALESCE(SUM(d.solde), 0) as total_solde
            FROM eleves e
            JOIN dettes_eleves d ON d.eleve_id = e.id
            WHERE 1=1
        """
        params = []
        if statut == "en_cours":
            query += " AND d.statut = 'en_cours'"
        elif statut == "soldee":
            query += " AND d.statut = 'soldee'"
        if recherche:
            query += " AND (e.nom LIKE ? OR e.prenom LIKE ? OR e.matricule LIKE ?)"
            like = f"%{recherche}%"
            params.extend([like, like, like])
        query += """
            GROUP BY e.id
            HAVING total_du > 0
            ORDER BY total_solde DESC, e.nom, e.prenom
        """
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[DETTES] Erreur : {e}")
        return []


def detail_dettes_eleve(eleve_id):
    """Toutes les lignes de dettes d'un eleve."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM dettes_eleves
            WHERE eleve_id = ?
            ORDER BY
                CASE statut WHEN 'en_cours' THEN 1 WHEN 'soldee' THEN 2 ELSE 3 END,
                categorie, date_creation DESC
        """, (eleve_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []


def lister_toutes_dettes(statut=None, recherche=None):
    """Version plate (compat) - liste toutes les lignes."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT d.*, e.matricule, e.nom, e.prenom, e.classe
            FROM dettes_eleves d
            JOIN eleves e ON d.eleve_id = e.id
            WHERE 1=1
        """
        params = []
        if statut:
            query += " AND d.statut = ?"
            params.append(statut)
        if recherche:
            query += " AND (e.nom LIKE ? OR e.prenom LIKE ? OR e.matricule LIKE ?)"
            like = f"%{recherche}%"
            params.extend([like, like, like])
        query += " ORDER BY d.statut, e.classe, e.nom, e.prenom"
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[DETTES] Erreur : {e}")
        return []


def total_dettes_en_cours():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(solde), 0) as total
            FROM dettes_eleves WHERE statut = 'en_cours'
        """)
        total = cursor.fetchone()["total"]
        conn.close()
        return total
    except Exception:
        return 0


def compter_eleves_endettes():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT eleve_id) as n
            FROM dettes_eleves
            WHERE statut = 'en_cours' AND solde > 0
        """)
        n = cursor.fetchone()["n"]
        conn.close()
        return n
    except Exception:
        return 0


def total_recouvre_mois():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(montant), 0) as total
            FROM paiements_dettes
            WHERE strftime('%Y-%m', date_paiement) = strftime('%Y-%m', 'now')
        """)
        total = cursor.fetchone()["total"]
        conn.close()
        return total
    except Exception:
        return 0


def enregistrer_paiement_dette(dette_id, montant, mode_paiement="especes",
                                utilisateur_id=None):
    if montant <= 0:
        return False, "Montant invalide"
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT solde, montant_paye FROM dettes_eleves WHERE id = ?",
                       (dette_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Dette introuvable"
        solde = row["solde"]
        paye = row["montant_paye"] or 0

        if montant > solde:
            conn.close()
            return False, f"Le montant depasse le solde ({solde})."

        cursor.execute("SELECT COUNT(*) as n FROM paiements_dettes")
        n = cursor.fetchone()["n"] + 1
        numero = f"RPT-{datetime.now().strftime('%Y%m%d')}-{n:04d}"

        cursor.execute("""
            INSERT INTO paiements_dettes
                (dette_id, numero_recu, montant, mode_paiement, utilisateur_id)
            VALUES (?, ?, ?, ?, ?)
        """, (dette_id, numero, montant, mode_paiement, utilisateur_id))

        nouveau_paye = paye + montant
        nouveau_solde = solde - montant
        nouveau_statut = "soldee" if nouveau_solde <= 0 else "en_cours"

        cursor.execute("""
            UPDATE dettes_eleves
            SET montant_paye = ?, solde = ?, statut = ?
            WHERE id = ?
        """, (nouveau_paye, nouveau_solde, nouveau_statut, dette_id))

        conn.commit()
        conn.close()
        return True, f"Paiement enregistre. Recu : {numero}"
    except Exception as e:
        return False, f"Erreur : {e}"


def annuler_dette(dette_id, utilisateur_id=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE dettes_eleves SET statut = 'annulee' WHERE id = ?
        """, (dette_id,))
        conn.commit()
        conn.close()
        return True, "Dette annulee"
    except Exception as e:
        return False, f"Erreur : {e}"


def liste_eleves_pour_dette():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, matricule, nom, prenom, classe
            FROM eleves WHERE actif = 1
            ORDER BY classe, nom, prenom
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []