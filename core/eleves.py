"""
Gestion des eleves
- Separation frais scolaires / autres frais
- GENERATION AUTOMATIQUE des frais a l'inscription selon la classe
"""
from database import get_connection


def generer_matricule():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM eleves")
    total = cursor.fetchone()["total"]
    conn.close()
    return f"BN{2025}{total + 1:04d}"


def _get_classe_id_par_nom(nom_classe):
    """Retrouve l'id de la classe a partir de son nom."""
    if not nom_classe:
        return None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM classes WHERE nom = ? AND actif = 1",
                       (nom_classe.strip(),))
        row = cursor.fetchone()
        conn.close()
        return row["id"] if row else None
    except Exception:
        return None


def _generer_frais_apres_inscription(eleve_id, nom_classe, utilisateur_id=None):
    """Genere les frais eleves selon sa classe (silencieux, retourne (ok, msg))."""
    classe_id = _get_classe_id_par_nom(nom_classe)
    if not classe_id:
        return False, f"Classe '{nom_classe}' introuvable dans la structure."

    try:
        from core.frais import generer_frais_eleve
        ok, msg, nb = generer_frais_eleve(eleve_id, classe_id,
                                           utilisateur_id=utilisateur_id)
        return ok, msg
    except Exception as e:
        return False, f"Erreur generation frais : {e}"


def ajouter_eleve(matricule, nom, prenom, classe, sexe=None,
                  date_naissance=None, nom_parent=None, telephone_parent=None,
                  frais_scolarite=0, utilisateur_id=None):
    """
    Ajoute un eleve puis genere AUTOMATIQUEMENT ses frais
    selon les frais affectes a sa classe.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO eleves
                (matricule, nom, prenom, classe, sexe, date_naissance,
                 nom_parent, telephone_parent, frais_scolarite)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (matricule.strip().upper(), nom.strip().upper(),
              prenom.strip().capitalize(), classe.strip(), sexe,
              date_naissance, nom_parent, telephone_parent,
              float(frais_scolarite or 0)))

        eleve_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # ===== GENERATION AUTOMATIQUE DES FRAIS =====
        ok_f, msg_f = _generer_frais_apres_inscription(
            eleve_id, classe, utilisateur_id
        )

        if ok_f:
            return True, f"Eleve ajoute. {msg_f}"
        else:
            # Eleve cree, mais aucun frais affecte a la classe
            return True, (f"Eleve ajoute, MAIS aucun frais n'a ete genere.\n\n"
                          f"Raison : {msg_f}\n\n"
                          f"Allez dans 'Frais' pour affecter des frais "
                          f"a la classe '{classe}'.")
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        if "UNIQUE" in str(e):
            return False, f"Le matricule '{matricule}' existe deja"
        return False, f"Erreur : {str(e)}"


def _total_par_motif(eleve_id, motif_like):
    """Retourne le total des paiements pour un motif (LIKE)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(montant), 0) as total
        FROM paiements_eleves
        WHERE eleve_id = ? AND LOWER(motif) LIKE ?
    """, (eleve_id, motif_like))
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return float(total)


def lister_eleves(recherche=""):
    """Liste tous les eleves avec separation frais scolaires / autres frais.
    Inclut les totaux depuis frais_eleves (nouveau systeme).
    """
    conn = get_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT e.id, e.matricule, e.nom, e.prenom, e.classe, e.sexe,
               e.nom_parent, e.telephone_parent, e.date_inscription,
               COALESCE(e.frais_scolarite, 0) as frais_scolarite,
               -- Paiements FRAIS SCOLAIRES uniquement (ancien systeme)
               COALESCE(
                   (SELECT SUM(montant) FROM paiements_eleves
                    WHERE eleve_id = e.id
                      AND LOWER(motif) LIKE '%scolaire%'), 0
               ) as paye_scolaire,
               COALESCE(
                   (SELECT SUM(montant) FROM paiements_eleves
                    WHERE eleve_id = e.id
                      AND LOWER(motif) LIKE '%uniforme%'), 0
               ) as paye_uniforme,
               COALESCE(
                   (SELECT SUM(montant) FROM paiements_eleves
                    WHERE eleve_id = e.id
                      AND LOWER(motif) LIKE '%transport%'), 0
               ) as paye_transport,
               COALESCE(
                   (SELECT SUM(montant) FROM paiements_eleves
                    WHERE eleve_id = e.id
                      AND LOWER(motif) LIKE '%cantine%'), 0
               ) as paye_cantine,
               COALESCE(
                   (SELECT SUM(montant) FROM paiements_eleves
                    WHERE eleve_id = e.id
                      AND LOWER(motif) LIKE '%inscription%'), 0
               ) as paye_inscription,
               -- ===== TOTAUX VIA frais_eleves (nouveau systeme) =====
               COALESCE(
                   (SELECT SUM(montant_initial) FROM frais_eleves
                    WHERE eleve_id = e.id), 0
               ) as total_frais_du,
               COALESCE(
                   (SELECT SUM(montant_paye) FROM frais_eleves
                    WHERE eleve_id = e.id), 0
               ) as total_frais_paye,
               COALESCE(
                   (SELECT SUM(solde) FROM frais_eleves
                    WHERE eleve_id = e.id AND statut = 'en_cours'), 0
               ) as total_frais_solde
        FROM eleves e
        WHERE e.actif = 1
    """

    if recherche.strip():
        terme = f"%{recherche.strip()}%"
        cursor.execute(base_query + """
            AND (
                e.matricule LIKE ? OR
                e.nom LIKE ? OR
                e.prenom LIKE ? OR
                e.classe LIKE ?
            )
            ORDER BY e.classe, e.nom, e.prenom
        """, (terme, terme, terme, terme))
    else:
        cursor.execute(base_query + " ORDER BY e.classe, e.nom, e.prenom")

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Calculer le solde scolaire pour chaque eleve
    for r in rows:
        r["solde"] = r["frais_scolarite"] - r["paye_scolaire"]

    return rows


def get_eleve(eleve_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM eleves WHERE id = ?", (eleve_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def modifier_eleve(eleve_id, matricule, nom, prenom, classe, sexe=None,
                   date_naissance=None, nom_parent=None, telephone_parent=None,
                   frais_scolarite=0, utilisateur_id=None):
    """
    Modifie un eleve.
    Si la CLASSE a change -> regenere les frais.
    """
    # Recuperer la classe AVANT modification
    ancien = get_eleve(eleve_id)
    ancienne_classe = ancien["classe"] if ancien else None

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE eleves
            SET matricule = ?, nom = ?, prenom = ?, classe = ?,
                sexe = ?, date_naissance = ?, nom_parent = ?,
                telephone_parent = ?, frais_scolarite = ?
            WHERE id = ?
        """, (matricule.strip().upper(), nom.strip().upper(),
              prenom.strip().capitalize(), classe.strip(), sexe,
              date_naissance, nom_parent, telephone_parent,
              float(frais_scolarite or 0), eleve_id))
        conn.commit()
        conn.close()

        # Si la classe a change -> regenerer les frais
        message_sup = ""
        if ancienne_classe and ancienne_classe != classe.strip():
            ok_f, msg_f = _generer_frais_apres_inscription(
                eleve_id, classe, utilisateur_id
            )
            if ok_f:
                message_sup = f" Frais regeneres ({msg_f})."
            else:
                message_sup = (f" Classe changee mais frais non regeneres : "
                               f"{msg_f}")

        return True, "Eleve modifie avec succes." + message_sup
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        if "UNIQUE" in str(e):
            return False, f"Le matricule '{matricule}' existe deja"
        return False, f"Erreur : {str(e)}"


def supprimer_eleve(eleve_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE eleves SET actif = 0 WHERE id = ?", (eleve_id,))
        conn.commit()
        return True, "Eleve supprime avec succes"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


def compter_eleves():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM eleves WHERE actif = 1")
    total = cursor.fetchone()["total"]
    conn.close()
    return total


def lister_classes():
    """Liste les classes qui ont au moins un eleve actif (pour filtres)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT classe FROM eleves
        WHERE actif = 1
        ORDER BY classe
    """)
    classes = [r["classe"] for r in cursor.fetchall()]
    conn.close()
    return classes


def regenerer_frais_eleve(eleve_id, utilisateur_id=None):
    """Force la regeneration des frais d'un eleve (utilitaire)."""
    eleve = get_eleve(eleve_id)
    if not eleve:
        return False, "Eleve introuvable"
    return _generer_frais_apres_inscription(
        eleve_id, eleve["classe"], utilisateur_id
    )