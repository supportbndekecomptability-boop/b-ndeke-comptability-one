"""
Gestion des utilisateurs de B-NDEKE Comptability One
"""
import bcrypt
from database import get_connection


def hasher_mot_de_passe(mot_de_passe: str) -> str:
    """Hache un mot de passe avec bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(mot_de_passe.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verifier_mot_de_passe(mot_de_passe: str, hash_stocke: str) -> bool:
    """Vérifie si le mot de passe correspond au hash"""
    try:
        return bcrypt.checkpw(
            mot_de_passe.encode("utf-8"),
            hash_stocke.encode("utf-8")
        )
    except Exception:
        return False


def creer_utilisateur(nom_complet: str, email: str, mot_de_passe: str, role: str = "comptable"):
    """Cree un nouvel utilisateur en base"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        mot_de_passe_hash = hasher_mot_de_passe(mot_de_passe)
        cursor.execute("""
            INSERT INTO utilisateurs (nom_complet, email, mot_de_passe, role)
            VALUES (?, ?, ?, ?)
        """, (nom_complet, email.lower().strip(), mot_de_passe_hash, role))
        conn.commit()
        return True, "Utilisateur cree avec succes"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


def authentifier(email: str, mot_de_passe: str):
    """Verifie les identifiants. Retourne le dict utilisateur ou None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nom_complet, email, mot_de_passe, role, actif
        FROM utilisateurs
        WHERE email = ? AND actif = 1
    """, (email.lower().strip(),))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    if verifier_mot_de_passe(mot_de_passe, row["mot_de_passe"]):
        return {
            "id": row["id"],
            "nom_complet": row["nom_complet"],
            "email": row["email"],
            "role": row["role"],
        }
    return None


def compter_utilisateurs() -> int:
    """Retourne le nombre d'utilisateurs"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM utilisateurs")
    total = cursor.fetchone()["total"]
    conn.close()
    return total


def creer_admin_par_defaut():
    """Cree un admin par defaut si aucun utilisateur n'existe"""
    if compter_utilisateurs() == 0:
        ok, msg = creer_utilisateur(
            nom_complet="Administrateur",
            email="admin@bndeke.com",
            mot_de_passe="admin123",
            role="admin"
        )
        if ok:
            print("[OK] Admin par defaut cree : admin@bndeke.com / admin123")
        return ok
    return False

    

# ============================================================
# GESTION DES UTILISATEURS (pour le module Parametres)
# ============================================================
def lister_utilisateurs():
    """Liste tous les utilisateurs actifs"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nom_complet, email, role, date_creation
        FROM utilisateurs
        WHERE actif = 1
        ORDER BY nom_complet
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_utilisateur(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM utilisateurs WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def supprimer_utilisateur(user_id):
    """Desactive un utilisateur (soft delete)"""
    # Verifier qu'on ne supprime pas le dernier admin
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role FROM utilisateurs WHERE id = ? AND actif = 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False, "Utilisateur introuvable"

    if row["role"] == "admin" and compter_admins() <= 1:
        return False, "Impossible de supprimer le dernier administrateur"

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE utilisateurs SET actif = 0 WHERE id = ?", (user_id,))
        conn.commit()
        return True, "Utilisateur supprime"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def modifier_utilisateur(user_id, nom_complet, role, nouveau_mdp=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if nouveau_mdp:
            cursor.execute("""
                UPDATE utilisateurs
                SET nom_complet = ?, role = ?, mot_de_passe = ?
                WHERE id = ?
            """, (nom_complet, role,
                  hasher_mot_de_passe(nouveau_mdp), user_id))
        else:
            cursor.execute("""
                UPDATE utilisateurs
                SET nom_complet = ?, role = ?
                WHERE id = ?
            """, (nom_complet, role, user_id))
        conn.commit()
        return True, "Utilisateur modifie"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def compter_admins():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM utilisateurs WHERE role='admin' AND actif=1")
    total = cursor.fetchone()["total"]
    conn.close()
    return total


def email_existe(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM utilisateurs WHERE email = ?", (email.lower().strip(),))
    row = cursor.fetchone()
    conn.close()
    return row is not None