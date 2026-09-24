"""
Gestion du catalogue de frais
+ affectation aux classes
+ frais par defaut par niveau/option
+ generation automatique des frais eleves
"""
from datetime import datetime
from database import get_connection


# ============================================================
# CATALOGUE DE FRAIS
# ============================================================
def ajouter_frais(nom, description="", montant_defaut=0,
                  categorie_budget="", dans_budget=False, ordre=0):
    if not nom or not nom.strip():
        return False, "Le nom du frais est obligatoire."
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO frais (nom, description, montant_defaut,
                               categorie_budget, dans_budget, ordre)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nom.strip(), description.strip() if description else "",
              float(montant_defaut or 0),
              categorie_budget.strip() if categorie_budget else "",
              1 if dans_budget else 0, int(ordre or 0)))
        conn.commit()
        conn.close()
        return True, "Frais ajoute"
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, f"Le frais '{nom}' existe deja."
        return False, f"Erreur : {e}"


def lister_frais(actif=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM frais WHERE 1=1"
        params = []
        if actif is not None:
            query += " AND actif = ?"
            params.append(1 if actif else 0)
        query += " ORDER BY ordre, nom"
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[FRAIS] Erreur : {e}")
        return []


def get_frais(frais_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM frais WHERE id = ?", (frais_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None


def modifier_frais(frais_id, nom=None, description=None, montant_defaut=None,
                    categorie_budget=None, dans_budget=None, actif=None,
                    ordre=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM frais WHERE id = ?", (frais_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Frais introuvable"

        nouveau_nom = nom if nom is not None else row["nom"]
        nouvelle_desc = description if description is not None else row["description"]
        nouveau_montant = montant_defaut if montant_defaut is not None else row["montant_defaut"]
        nouvelle_cat = categorie_budget if categorie_budget is not None else row["categorie_budget"]
        nouveau_dans_budget = dans_budget if dans_budget is not None else row["dans_budget"]
        nouvel_actif = actif if actif is not None else row["actif"]
        nouvel_ordre = ordre if ordre is not None else row["ordre"]

        cursor.execute("""
            UPDATE frais
            SET nom = ?, description = ?, montant_defaut = ?,
                categorie_budget = ?, dans_budget = ?, actif = ?, ordre = ?
            WHERE id = ?
        """, (nouveau_nom, nouvelle_desc, nouveau_montant,
              nouvelle_cat, nouveau_dans_budget, nouvel_actif,
              nouvel_ordre, frais_id))
        conn.commit()
        conn.close()
        return True, "Frais modifie"
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, "Un frais avec ce nom existe deja."
        return False, f"Erreur : {e}"


def supprimer_frais(frais_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM frais WHERE id = ?", (frais_id,))
        conn.commit()
        conn.close()
        return True, "Frais supprime"
    except Exception as e:
        return False, f"Erreur : {e}"


def lister_frais_dans_budget():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM frais
            WHERE dans_budget = 1 AND actif = 1
            ORDER BY ordre, nom
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []


def total_frais_dans_budget():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(montant_defaut), 0) as total
            FROM frais WHERE dans_budget = 1 AND actif = 1
        """)
        total = cursor.fetchone()["total"]
        conn.close()
        return total
    except Exception:
        return 0


# ============================================================
# AFFECTATION FRAIS <-> CLASSE
# ============================================================
def assigner_frais_classe(frais_id, classe_id, montant=0, obligatoire=True):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO frais_classes (frais_id, classe_id, montant, obligatoire)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(frais_id, classe_id)
            DO UPDATE SET
                montant = excluded.montant,
                obligatoire = excluded.obligatoire
        """, (frais_id, classe_id, float(montant or 0),
              1 if obligatoire else 0))
        conn.commit()
        conn.close()
        return True, "Frais affecte"
    except Exception as e:
        return False, f"Erreur : {e}"


def retirer_frais_classe(frais_id, classe_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM frais_classes WHERE frais_id = ? AND classe_id = ?
        """, (frais_id, classe_id))
        conn.commit()
        conn.close()
        return True, "Frais retire"
    except Exception as e:
        return False, f"Erreur : {e}"


def lister_frais_par_classe(classe_id):
    """Frais affectes a cette classe (avec montant specifique)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.id as frais_id, f.nom, f.description, f.montant_defaut,
                   f.categorie_budget, f.dans_budget, f.ordre,
                   fc.montant as montant_classe, fc.obligatoire
            FROM frais f
            JOIN frais_classes fc ON fc.frais_id = f.id
            WHERE fc.classe_id = ? AND f.actif = 1
            ORDER BY f.ordre, f.nom
        """, (classe_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[FRAIS] Erreur : {e}")
        return []


def total_frais_classe(classe_id):
    frais = lister_frais_par_classe(classe_id)
    total = 0
    for f in frais:
        montant = f.get("montant_classe") or f.get("montant_defaut") or 0
        total += montant
    return total


def compter_frais_par_classe(classe_id):
    return len(lister_frais_par_classe(classe_id))


# ============================================================
# FRAIS PAR DEFAUT (PAR NIVEAU / OPTION)
# ============================================================
def _cle_defaut(niveau, sous_type=None, option_nom=None):
    """
    Normalise la cle :
    - Maternelle/Primaire -> (niveau, None, None)
    - Secondaire Base -> ('Secondaire', 'base', None)
    - Secondaire Option -> ('Secondaire', 'option', nom_option)
    """
    if niveau != "Secondaire":
        return (niveau, None, None)
    if sous_type == "base":
        return ("Secondaire", "base", None)
    if sous_type == "option":
        return ("Secondaire", "option", option_nom)
    return (niveau, sous_type, option_nom)


def sauvegarder_defauts(niveau, sous_type, option_nom, lignes):
    """
    Sauvegarde les frais par defaut pour un niveau/option.
    - niveau : Maternelle / Primaire / Secondaire
    - sous_type : None / 'base' / 'option'
    - option_nom : nom de l'option (uniquement si Secondaire option)
    - lignes : [(frais_id, montant), ...]
    Remplace tous les defauts precedents pour cette cle.
    """
    cle = _cle_defaut(niveau, sous_type, option_nom)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Supprimer les anciens defauts pour cette cle
        cursor.execute("""
            DELETE FROM frais_defauts
            WHERE niveau = ? AND
                  COALESCE(sous_type, '') = COALESCE(?, '') AND
                  COALESCE(option_nom, '') = COALESCE(?, '')
        """, (cle[0], cle[1], cle[2]))

        # Inserer les nouveaux
        nb = 0
        for frais_id, montant in lignes:
            if montant > 0:
                cursor.execute("""
                    INSERT INTO frais_defauts
                        (niveau, sous_type, option_nom, frais_id, montant)
                    VALUES (?, ?, ?, ?, ?)
                """, (cle[0], cle[1], cle[2], frais_id, float(montant)))
                nb += 1

        conn.commit()
        conn.close()
        return True, f"{nb} frais sauvegardes comme defaut"
    except Exception as e:
        return False, f"Erreur : {e}"


def charger_defauts(niveau, sous_type=None, option_nom=None):
    """
    Retourne les frais par defaut pour ce niveau/option.
    Retourne {frais_id: montant, ...}
    """
    cle = _cle_defaut(niveau, sous_type, option_nom)

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT frais_id, montant FROM frais_defauts
            WHERE niveau = ? AND
                  COALESCE(sous_type, '') = COALESCE(?, '') AND
                  COALESCE(option_nom, '') = COALESCE(?, '')
        """, (cle[0], cle[1], cle[2]))
        rows = cursor.fetchall()
        conn.close()
        return {r["frais_id"]: r["montant"] for r in rows}
    except Exception as e:
        print(f"[FRAIS] Erreur chargement defauts : {e}")
        return {}


def a_des_defauts(niveau, sous_type=None, option_nom=None):
    """Verifie s'il existe des frais par defaut pour ce niveau."""
    return len(charger_defauts(niveau, sous_type, option_nom)) > 0


def description_cle(niveau, sous_type=None, option_nom=None):
    """Retourne une description lisible pour l'interface."""
    if niveau == "Secondaire":
        if sous_type == "base":
            return "Secondaire - Education de base"
        if sous_type == "option":
            return f"Secondaire - Option : {option_nom or '?'}"
    return niveau


# ============================================================
# GENERATION AUTOMATIQUE A L'INSCRIPTION
# ============================================================
def generer_frais_eleve(eleve_id, classe_id, annee_libelle=None,
                         utilisateur_id=None):
    """
    Genere automatiquement toutes les lignes de frais_eleves pour cet eleve,
    selon les frais affectes a sa classe.
    Retourne (ok, message, nb_frais_crees).
    """
    if annee_libelle is None:
        annee_libelle = f"{datetime.now().year}-{datetime.now().year + 1}"

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Frais affectes a la classe
        cursor.execute("""
            SELECT f.id as frais_id, f.nom, f.montant_defaut,
                   fc.montant as montant_classe
            FROM frais f
            JOIN frais_classes fc ON fc.frais_id = f.id
            WHERE fc.classe_id = ? AND f.actif = 1
            ORDER BY f.ordre, f.nom
        """, (classe_id,))
        frais = [dict(r) for r in cursor.fetchall()]

        if not frais:
            conn.close()
            return False, "Aucun frais affecte a cette classe.", 0

        # Supprimer les frais existants (eviter doublons)
        cursor.execute("DELETE FROM frais_eleves WHERE eleve_id = ?",
                       (eleve_id,))

        nb_crees = 0
        for f in frais:
            montant = f.get("montant_classe") or f.get("montant_defaut") or 0
            if montant <= 0:
                continue

            cursor.execute("""
                INSERT INTO frais_eleves
                    (eleve_id, frais_id, libelle, montant_initial,
                     montant_paye, solde, annee_libelle, statut, utilisateur_id)
                VALUES (?, ?, ?, ?, 0, ?, ?, 'en_cours', ?)
            """, (eleve_id, f["frais_id"], f["nom"], montant, montant,
                  annee_libelle, utilisateur_id))
            nb_crees += 1

        conn.commit()
        conn.close()

        if nb_crees == 0:
            return False, "Aucun frais avec un montant > 0.", 0

        return True, f"{nb_crees} frais generes", nb_crees
    except Exception as e:
        return False, f"Erreur : {e}", 0


def lister_frais_eleve(eleve_id):
    """Retourne tous les frais a payer d'un eleve."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fe.*, f.nom as frais_nom, f.categorie_budget, f.dans_budget
            FROM frais_eleves fe
            JOIN frais f ON fe.frais_id = f.id
            WHERE fe.eleve_id = ?
            ORDER BY
                CASE fe.statut WHEN 'en_cours' THEN 1 WHEN 'soldee' THEN 2 ELSE 3 END,
                f.ordre, fe.libelle
        """, (eleve_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[FRAIS] Erreur : {e}")
        return []


def total_frais_eleve(eleve_id):
    """Total general du, paye, solde restant."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COALESCE(SUM(montant_initial), 0) as total_du,
                COALESCE(SUM(montant_paye), 0) as total_paye,
                COALESCE(SUM(solde), 0) as total_solde
            FROM frais_eleves WHERE eleve_id = ?
        """, (eleve_id,))
        row = cursor.fetchone()
        conn.close()
        return {
            "total_du": row["total_du"] or 0,
            "total_paye": row["total_paye"] or 0,
            "total_solde": row["total_solde"] or 0,
        }
    except Exception:
        return {"total_du": 0, "total_paye": 0, "total_solde": 0}


def enregistrer_paiement_frais(frais_eleve_id, montant,
                                mode_paiement="especes",
                                utilisateur_id=None):
    """Enregistre un paiement sur une ligne de frais."""
    if montant <= 0:
        return False, "Montant invalide"
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT solde, montant_paye FROM frais_eleves WHERE id = ?",
                       (frais_eleve_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Frais introuvable"
        solde = row["solde"]
        paye = row["montant_paye"] or 0

        if montant > solde:
            conn.close()
            return False, f"Le montant depasse le solde ({solde})."

        cursor.execute("SELECT COUNT(*) as n FROM paiements_frais")
        n = cursor.fetchone()["n"] + 1
        numero = f"FRA-{datetime.now().strftime('%Y%m%d')}-{n:04d}"

        cursor.execute("""
            INSERT INTO paiements_frais
                (frais_eleve_id, numero_recu, montant, mode_paiement,
                 utilisateur_id)
            VALUES (?, ?, ?, ?, ?)
        """, (frais_eleve_id, numero, montant, mode_paiement, utilisateur_id))

        nouveau_paye = paye + montant
        nouveau_solde = solde - montant
        nouveau_statut = "soldee" if nouveau_solde <= 0 else "en_cours"

        cursor.execute("""
            UPDATE frais_eleves
            SET montant_paye = ?, solde = ?, statut = ?
            WHERE id = ?
        """, (nouveau_paye, nouveau_solde, nouveau_statut, frais_eleve_id))

        conn.commit()
        conn.close()
        return True, f"Paiement enregistre. Recu : {numero}"
    except Exception as e:
        return False, f"Erreur : {e}"


def initialiser_frais_par_defaut():
    """Cree une liste de frais de base si la table est vide."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as n FROM frais")
        if cursor.fetchone()["n"] > 0:
            conn.close()
            return False

        defauts = [
            ("Scolarite", "Frais de scolarite annuels", 0, "Scolarite", 1, 1),
            ("Inscription", "Frais d'inscription annuels", 0, "Scolarite", 1, 2),
            ("Uniforme", "Uniforme scolaire", 0, "Autres", 0, 3),
            ("Fournitures", "Fournitures scolaires", 0, "Autres", 0, 4),
            ("Cantine", "Service de cantine", 0, "Autres", 0, 5),
            ("Transport", "Service de transport", 0, "Autres", 0, 6),
            ("Examen", "Frais d'examen", 0, "Scolarite", 1, 7),
        ]
        for nom, desc, montant, cat, budget, ordre in defauts:
            cursor.execute("""
                INSERT INTO frais (nom, description, montant_defaut,
                                   categorie_budget, dans_budget, ordre)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nom, desc, montant, cat, budget, ordre))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[FRAIS] Erreur init : {e}")
        return False