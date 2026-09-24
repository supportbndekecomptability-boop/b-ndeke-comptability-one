"""
Gestion de la structure scolaire (classes/niveaux) - B-NDEKE
Les classes sont creees manuellement par l'ecole (admin/gestionnaire).
"""
from database import get_connection


NIVEAUX = ["Maternelle", "Primaire", "Secondaire"]
SOUS_TYPES_SECONDAIRE = ["base", "option"]


def ajouter_classe(niveau, nom, sous_type=None, ordre=0, description=""):
    """Ajoute une classe. sous_type uniquement pour le Secondaire."""
    if niveau not in NIVEAUX:
        return False, f"Niveau invalide : {niveau}"

    if niveau == "Secondaire":
        if sous_type not in SOUS_TYPES_SECONDAIRE:
            return False, "Sous-type secondaire requis (base ou option)"
    else:
        sous_type = None

    if not nom or not nom.strip():
        return False, "Le nom de la classe est obligatoire."

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO classes (niveau, sous_type, nom, ordre, description)
            VALUES (?, ?, ?, ?, ?)
        """, (niveau, sous_type, nom.strip(), int(ordre or 0),
              description.strip() if description else ""))
        conn.commit()
        conn.close()
        return True, "Classe ajoutee"
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, f"La classe '{nom}' existe deja dans {niveau}."
        return False, f"Erreur : {e}"


def lister_classes(niveau=None, actif=True):
    """Liste les classes. Si niveau=None -> toutes."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM classes WHERE 1=1"
        params = []
        if actif is not None:
            query += " AND actif = ?"
            params.append(1 if actif else 0)
        if niveau:
            query += " AND niveau = ?"
            params.append(niveau)
        query += " ORDER BY niveau, ordre, nom"
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[CLASSES] Erreur : {e}")
        return []


def lister_classes_par_niveau():
    """Retourne {niveau: [classes]} pour affichage groupe."""
    toutes = lister_classes()
    groupes = {}
    for c in toutes:
        groupes.setdefault(c["niveau"], []).append(c)
    return groupes


def compter_eleves_par_classe(nom_classe):
    """Compte les eleves actifs rattaches a cette classe."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as n FROM eleves
            WHERE classe = ? AND actif = 1
        """, (nom_classe,))
        n = cursor.fetchone()["n"]
        conn.close()
        return n
    except Exception:
        return 0


def modifier_classe(classe_id, nom=None, ordre=None, description=None,
                     actif=None, sous_type=None):
    """Modifie une classe existante."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM classes WHERE id = ?", (classe_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Classe introuvable"

        nouveau_nom = nom if nom is not None else row["nom"]
        nouvel_ordre = ordre if ordre is not None else row["ordre"]
        nouvelle_desc = description if description is not None else row["description"]
        nouvel_actif = actif if actif is not None else row["actif"]
        nouveau_sous_type = sous_type if sous_type is not None else row["sous_type"]

        cursor.execute("""
            UPDATE classes
            SET nom = ?, ordre = ?, description = ?, actif = ?, sous_type = ?
            WHERE id = ?
        """, (nouveau_nom, nouvel_ordre, nouvelle_desc,
              nouvel_actif, nouveau_sous_type, classe_id))
        conn.commit()
        conn.close()
        return True, "Classe modifiee"
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, "Une classe avec ce nom existe deja dans ce niveau."
        return False, f"Erreur : {e}"


def supprimer_classe(classe_id):
    """Supprime une classe UNIQUEMENT si aucun eleve n'y est rattache."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nom, niveau FROM classes WHERE id = ?", (classe_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Classe introuvable"

        nom = row["nom"]

        cursor.execute("""
            SELECT COUNT(*) as n FROM eleves
            WHERE classe = ? AND actif = 1
        """, (nom,))
        n = cursor.fetchone()["n"]
        if n > 0:
            conn.close()
            return False, (
                f"Impossible : {n} eleve(s) actif(s) rattache(s) "
                f"a la classe '{nom}'.\n\n"
                f"Desactivez la classe au lieu de la supprimer."
            )

        cursor.execute("DELETE FROM classes WHERE id = ?", (classe_id,))
        conn.commit()
        conn.close()
        return True, "Classe supprimee"
    except Exception as e:
        return False, f"Erreur : {e}"


def liste_noms_classes(actif=True):
    """Retourne la liste simple des noms de classes (pour dropdown)."""
    classes = lister_classes(actif=actif)
    return [c["nom"] for c in classes]