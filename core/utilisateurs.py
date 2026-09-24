"""
Gestion des utilisateurs - B-NDEKE Comptability One
- Authentification (login)
- Hash des mots de passe avec bcrypt
- CRUD utilisateurs + compatibilite UI
- Blocage de fonctionnalites par utilisateur (JSON)
- Protection du compte gestionnaire
"""
import json
import bcrypt
from database import get_connection


# ============================================================
# FONCTIONNALITES QUI PEUVENT ETRE BLOQUEES
# ============================================================
FONCTIONNALITES_BLOQUABLES = [
    "Tableau de bord",
    "Classes",
    "Frais",
    "Eleves",
    "Paiements",
    "Caisse",
    "Depenses",
    "Personnel",
    "Presences",
    "Presences personnel",
    "Dettes",
    "Recouvrement",
    "Rapports",
    "Etats financiers",
    "Export Excel",
    "Parametres",
]


# ============================================================
# HASH MOT DE PASSE
# ============================================================
def hasher_mot_de_passe(mot_de_passe):
    """Hash un mot de passe en clair avec bcrypt."""
    if isinstance(mot_de_passe, str):
        mot_de_passe = mot_de_passe.encode("utf-8")
    return bcrypt.hashpw(mot_de_passe, bcrypt.gensalt()).decode("utf-8")


def verifier_mot_de_passe(mot_de_passe_clair, hash_stocke):
    """Verifie qu'un mot de passe correspond au hash bcrypt."""
    try:
        if isinstance(mot_de_passe_clair, str):
            mot_de_passe_clair = mot_de_passe_clair.encode("utf-8")
        if isinstance(hash_stocke, str):
            hash_stocke = hash_stocke.encode("utf-8")
        return bcrypt.checkpw(mot_de_passe_clair, hash_stocke)
    except Exception:
        return False


# ============================================================
# AUTHENTIFICATION
# ============================================================
def authentifier(email, mot_de_passe):
    """
    Verifie les identifiants. Retourne (ok, utilisateur, message).
    """
    email = (email or "").strip().lower()
    if not email or not mot_de_passe:
        return False, None, "Email et mot de passe obligatoires."

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM utilisateurs
            WHERE LOWER(email) = ? AND actif = 1
        """, (email,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return False, None, "Email ou mot de passe incorrect."

        user = dict(row)
        if not verifier_mot_de_passe(mot_de_passe, user["mot_de_passe"]):
            return False, None, "Email ou mot de passe incorrect."

        return True, user, "Connexion reussie"
    except Exception as e:
        return False, None, f"Erreur : {e}"


# ============================================================
# PROTECTION DU COMPTE GESTIONNAIRE
# ============================================================
def est_gestionnaire(user):
    """True si l'utilisateur a le role gestionnaire."""
    if not user:
        return False
    role = (user.get("role") or "").lower()
    return role == "gestionnaire"


def est_admin(user):
    """True si l'utilisateur a le role admin."""
    if not user:
        return False
    role = (user.get("role") or "").lower()
    return role == "admin"


def est_protege(user):
    """
    True si le compte ne peut JAMAIS etre modifie ni supprime.
    Le compte gestionnaire est protege.
    """
    return est_gestionnaire(user)


# ============================================================
# FONCTIONNALITES BLOQUEES (JSON dans la colonne)
# ============================================================
def get_fonctionnalites_bloquees(user_id):
    """
    Retourne la liste des fonctionnalites bloquees pour cet utilisateur.
    Ne s'applique PAS aux gestionnaires (toujours vide pour eux).
    """
    if not user_id:
        return []
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fonctionnalites_bloquees, role
            FROM utilisateurs WHERE id = ?
        """, (user_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return []

        # Le gestionnaire n'a JAMAIS de blocage
        role = (row["role"] or "").lower()
        if role == "gestionnaire":
            return []

        data = row["fonctionnalites_bloquees"]
        if not data:
            return []

        try:
            liste = json.loads(data)
            if isinstance(liste, list):
                return [str(x) for x in liste]
        except Exception:
            pass
        return []
    except Exception as e:
        print(f"[UTILISATEURS] Erreur get_fonctionnalites_bloquees : {e}")
        return []


def set_fonctionnalites_bloquees(user_id, liste):
    """
    Definit la liste des fonctionnalites bloquees pour cet utilisateur.
    Impossible sur un gestionnaire.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Verifier que la cible n'est PAS gestionnaire
        cursor.execute("SELECT role FROM utilisateurs WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Utilisateur introuvable"

        if (row["role"] or "").lower() == "gestionnaire":
            conn.close()
            return False, "Le compte gestionnaire ne peut pas etre bloque."

        # Nettoyer la liste (garder uniquement les valides)
        liste_propre = [f for f in (liste or []) if f in FONCTIONNALITES_BLOQUABLES]
        data = json.dumps(liste_propre)

        cursor.execute("""
            UPDATE utilisateurs SET fonctionnalites_bloquees = ?
            WHERE id = ?
        """, (data, user_id))
        conn.commit()
        conn.close()
        return True, f"{len(liste_propre)} fonctionnalite(s) bloquee(s)"
    except Exception as e:
        return False, f"Erreur : {e}"


# ============================================================
# CRUD UTILISATEURS
# ============================================================
def lister_utilisateurs(actif=None):
    """Liste tous les utilisateurs."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT id, nom_complet, email, role, actif, date_creation,
                   fonctionnalites_bloquees
            FROM utilisateurs
            WHERE 1=1
        """
        params = []
        if actif is not None:
            query += " AND actif = ?"
            params.append(1 if actif else 0)
        query += " ORDER BY role, nom_complet"
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        # Parser le JSON pour chaque ligne
        for r in rows:
            try:
                r["bloques"] = json.loads(r.get("fonctionnalites_bloquees") or "[]")
            except Exception:
                r["bloques"] = []

        return rows
    except Exception as e:
        print(f"[UTILISATEURS] Erreur : {e}")
        return []


def get_utilisateur(user_id):
    """Retourne un utilisateur par id."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nom_complet, email, role, actif, date_creation,
                   fonctionnalites_bloquees
            FROM utilisateurs WHERE id = ?
        """, (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None


def get_utilisateur_par_email(email):
    """Retourne un utilisateur par email (avec hash pour admin)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM utilisateurs WHERE LOWER(email) = ?
        """, (email.strip().lower(),))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None


def email_existe(email):
    """Verifie si un email est deja utilise."""
    if not email:
        return False
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as n FROM utilisateurs WHERE LOWER(email) = ?
        """, (email.strip().lower(),))
        n = cursor.fetchone()["n"]
        conn.close()
        return n > 0
    except Exception:
        return False


def compter_admins():
    """Compte les utilisateurs avec le role admin et actifs."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as n FROM utilisateurs
            WHERE LOWER(role) = 'admin' AND actif = 1
        """)
        n = cursor.fetchone()["n"]
        conn.close()
        return n
    except Exception:
        return 0


def ajouter_utilisateur(nom_complet, email, mot_de_passe, role="comptable",
                        actif=True):
    """Cree un nouvel utilisateur."""
    nom_complet = (nom_complet or "").strip()
    email = (email or "").strip().lower()
    mot_de_passe = mot_de_passe or ""

    if not nom_complet or not email or not mot_de_passe:
        return False, "Tous les champs sont obligatoires."

    if role not in ["admin", "gestionnaire", "comptable", "caissier",
                    "directeur", "prefet"]:
        return False, f"Role invalide : {role}"

    try:
        conn = get_connection()
        cursor = conn.cursor()
        hash_mdp = hasher_mot_de_passe(mot_de_passe)
        cursor.execute("""
            INSERT INTO utilisateurs
                (nom_complet, email, mot_de_passe, role, actif,
                 fonctionnalites_bloquees)
            VALUES (?, ?, ?, ?, ?, '[]')
        """, (nom_complet, email, hash_mdp, role, 1 if actif else 0))
        conn.commit()
        conn.close()
        return True, "Utilisateur ajoute"
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, f"L'email '{email}' existe deja."
        return False, f"Erreur : {e}"


def modifier_utilisateur(user_id, nom_complet=None, email=None,
                          role=None, actif=None, mot_de_passe=None):
    """Modifie un utilisateur. mot_de_passe = None -> ne change pas."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM utilisateurs WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Utilisateur introuvable"

        # Protection du compte gestionnaire
        if (row["role"] or "").lower() == "gestionnaire":
            conn.close()
            return False, "Le compte gestionnaire est protege et ne peut pas etre modifie."

        nouveau_nom = nom_complet if nom_complet is not None else row["nom_complet"]
        nouvel_email = (email.strip().lower() if email else row["email"])
        nouveau_role = role if role is not None else row["role"]
        nouvel_actif = actif if actif is not None else row["actif"]

        if mot_de_passe:
            nouveau_mdp = hasher_mot_de_passe(mot_de_passe)
            cursor.execute("""
                UPDATE utilisateurs
                SET nom_complet = ?, email = ?, mot_de_passe = ?,
                    role = ?, actif = ?
                WHERE id = ?
            """, (nouveau_nom, nouvel_email, nouveau_mdp,
                  nouveau_role, nouvel_actif, user_id))
        else:
            cursor.execute("""
                UPDATE utilisateurs
                SET nom_complet = ?, email = ?, role = ?, actif = ?
                WHERE id = ?
            """, (nouveau_nom, nouvel_email, nouveau_role,
                  nouvel_actif, user_id))

        conn.commit()
        conn.close()
        return True, "Utilisateur modifie"
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, "Cet email est deja utilise."
        return False, f"Erreur : {e}"


def changer_mot_de_passe(user_id, nouveau_mot_de_passe):
    """Change le mot de passe d'un utilisateur."""
    if not nouveau_mot_de_passe or len(nouveau_mot_de_passe) < 4:
        return False, "Le mot de passe doit faire au moins 4 caracteres."

    try:
        conn = get_connection()
        cursor = conn.cursor()
        hash_mdp = hasher_mot_de_passe(nouveau_mot_de_passe)
        cursor.execute("""
            UPDATE utilisateurs SET mot_de_passe = ? WHERE id = ?
        """, (hash_mdp, user_id))
        conn.commit()
        conn.close()
        return True, "Mot de passe change"
    except Exception as e:
        return False, f"Erreur : {e}"


def changer_mot_de_passe_par_email(email, nouveau_mot_de_passe):
    """Change le mot de passe d'un utilisateur a partir de son email."""
    user = get_utilisateur_par_email(email)
    if not user:
        return False, f"Aucun utilisateur avec l'email '{email}'."
    return changer_mot_de_passe(user["id"], nouveau_mot_de_passe)


def supprimer_utilisateur(user_id):
    """Desactive un utilisateur (soft delete)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Protection du compte gestionnaire
        cursor.execute("SELECT role FROM utilisateurs WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row and (row["role"] or "").lower() == "gestionnaire":
            conn.close()
            return False, "Le compte gestionnaire est protege et ne peut pas etre supprime."

        cursor.execute("""
            UPDATE utilisateurs SET actif = 0 WHERE id = ?
        """, (user_id,))
        conn.commit()
        conn.close()
        return True, "Utilisateur desactive"
    except Exception as e:
        return False, f"Erreur : {e}"


def compter_utilisateurs():
    """Compte les utilisateurs actifs."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as n FROM utilisateurs WHERE actif = 1
        """)
        n = cursor.fetchone()["n"]
        conn.close()
        return n
    except Exception:
        return 0


def initialiser_admin_par_defaut():
    """
    Cree l'admin par defaut si aucun utilisateur n'existe.
    Email : admin@bndeke.com
    Mot de passe : admin123
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as n FROM utilisateurs")
        if cursor.fetchone()["n"] > 0:
            conn.close()
            return False

        hash_mdp = hasher_mot_de_passe("admin123")
        cursor.execute("""
            INSERT INTO utilisateurs
                (nom_complet, email, mot_de_passe, role, actif,
                 fonctionnalites_bloquees)
            VALUES (?, ?, ?, ?, 1, '[]')
        """, ("Administrateur", "admin@bndeke.com", hash_mdp, "admin"))

        conn.commit()
        conn.close()
        print("[INIT] Admin par defaut cree : admin@bndeke.com / admin123")
        return True
    except Exception as e:
        print(f"[UTILISATEURS] Erreur init : {e}")
        return False


# ============================================================
# ALIAS COMPATIBILITE
# ============================================================
def creer_admin_par_defaut():
    return initialiser_admin_par_defaut()


def creer_utilisateur(nom_complet, email, mot_de_passe, role="comptable"):
    return ajouter_utilisateur(nom_complet, email, mot_de_passe, role)


def changer_mot_de_passe_utilisateur(user_id, nouveau_mdp):
    return changer_mot_de_passe(user_id, nouveau_mdp)


def desactiver_utilisateur(user_id):
    return supprimer_utilisateur(user_id)


def reactiver_utilisateur(user_id):
    return modifier_utilisateur(user_id, actif=1)


def lister_tous_utilisateurs():
    return lister_utilisateurs(actif=None)


def lister_utilisateurs_actifs():
    return lister_utilisateurs(actif=True)