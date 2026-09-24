"""
Gestion du personnel de B-NDEKE Comptability One
Avec champ 'niveau' (Maternelle / Primaire / Secondaire) pour le filtrage
par role (Directeur = Maternelle + Primaire, Prefet = Secondaire).
"""
from database import get_connection


# Niveaux valides pour le personnel
NIVEAUX_PERSONNEL = ["Maternelle", "Primaire", "Secondaire", None]


def generer_code():
    """Genere un code personnel unique : PERS-0001, PERS-0002..."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM personnel")
    total = cursor.fetchone()["total"]
    conn.close()
    return f"PERS-{total + 1:04d}"


def ajouter_personnel(code, nom, prenom, fonction, sexe=None,
                      telephone=None, email=None, salaire_mensuel=0,
                      duree_contrat_mois=12, date_embauche=None,
                      niveau=None):
    """
    Ajoute un membre du personnel.
    niveau : 'Maternelle', 'Primaire', 'Secondaire' ou None
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO personnel
                (code, nom, prenom, fonction, sexe, telephone, email,
                 salaire_mensuel, duree_contrat_mois, date_embauche, niveau)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (code.strip().upper(), nom.strip().upper(), prenom.strip().capitalize(),
              fonction.strip(), sexe, telephone, email,
              float(salaire_mensuel or 0), int(duree_contrat_mois or 12),
              date_embauche, niveau))
        conn.commit()
        return True, "Personnel ajoute avec succes"
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, f"Le code '{code}' existe deja"
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


def lister_personnel(recherche=""):
    """Liste le personnel + engagement total + solde a payer + niveau
    Engagement total = salaire_mensuel x duree_contrat_mois
    Solde a payer = engagement total - total deja paye
    """
    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT p.id, p.code, p.nom, p.prenom, p.fonction, p.sexe,
               p.telephone, p.email, p.salaire_mensuel, p.duree_contrat_mois,
               p.date_embauche, p.niveau,
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
        WHERE p.actif = 1
    """

    if recherche.strip():
        terme = f"%{recherche.strip()}%"
        cursor.execute(base_query + """
            AND (p.code LIKE ? OR p.nom LIKE ? OR p.prenom LIKE ? OR p.fonction LIKE ?)
            ORDER BY p.nom, p.prenom
        """, (terme, terme, terme, terme))
    else:
        cursor.execute(base_query + " ORDER BY p.nom, p.prenom")

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_personnel(personnel_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM personnel WHERE id = ?", (personnel_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def modifier_personnel(personnel_id, code, nom, prenom, fonction, sexe=None,
                       telephone=None, email=None, salaire_mensuel=0,
                       duree_contrat_mois=12, date_embauche=None,
                       niveau=None):
    """
    Modifie un membre du personnel.
    niveau : 'Maternelle', 'Primaire', 'Secondaire' ou None
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE personnel
            SET code = ?, nom = ?, prenom = ?, fonction = ?, sexe = ?,
                telephone = ?, email = ?, salaire_mensuel = ?,
                duree_contrat_mois = ?, date_embauche = ?, niveau = ?
            WHERE id = ?
        """, (code.strip().upper(), nom.strip().upper(), prenom.strip().capitalize(),
              fonction.strip(), sexe, telephone, email,
              float(salaire_mensuel or 0), int(duree_contrat_mois or 12),
              date_embauche, niveau, personnel_id))
        conn.commit()
        return True, "Personnel modifie avec succes"
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, f"Le code '{code}' existe deja"
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


def supprimer_personnel(personnel_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE personnel SET actif = 0 WHERE id = ?", (personnel_id,))
        conn.commit()
        return True, "Personnel supprime avec succes"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


def compter_personnel():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM personnel WHERE actif = 1")
    total = cursor.fetchone()["total"]
    conn.close()
    return total


def rechercher_par_code(code):
    """Retourne un personnel par son code exact"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM personnel WHERE code = ? AND actif = 1",
                   (code.strip().upper(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def lister_personnel_par_niveaux(niveaux):
    """
    Retourne le personnel dont le niveau est dans la liste donnee.
    niveaux : liste ['Maternelle', 'Primaire'] ou None pour tout.
    """
    tous = lister_personnel()
    if niveaux is None:
        return tous
    return [p for p in tous if p.get("niveau") in niveaux]