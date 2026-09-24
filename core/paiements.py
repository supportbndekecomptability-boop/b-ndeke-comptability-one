"""
Gestion des paiements (Eleves + Personnel) de B-NDEKE Comptability One
"""
from datetime import datetime
from database import get_connection


# ============ NUMEROS AUTO ============
def generer_numero_recu():
    """Numero de recu pour paiement eleve : REC-2025-0001"""
    annee = datetime.now().year
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM paiements_eleves")
    total = cursor.fetchone()["total"]
    conn.close()
    return f"REC-{annee}-{total + 1:04d}"


def generer_numero_paie():
    """Numero de paie pour personnel : PAIE-2025-0001"""
    annee = datetime.now().year
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM paiements_personnel")
    total = cursor.fetchone()["total"]
    conn.close()
    return f"PAIE-{annee}-{total + 1:04d}"


# ============ DETTES ELEVES ============
def dettes_en_cours_eleve(eleve_id):
    """Retourne toutes les dettes en cours d'un eleve (ancienne d'abord)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, eleve_id, annee_libelle, categorie, montant_initial,
               montant_paye, solde, motif, statut, date_creation
        FROM dettes_eleves
        WHERE eleve_id = ? AND statut = 'en_cours' AND solde > 0
        ORDER BY date_creation ASC, id ASC
    """, (eleve_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def total_dettes_eleve(eleve_id):
    """Somme des soldes de dettes en cours d'un eleve."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(solde), 0) as total
        FROM dettes_eleves
        WHERE eleve_id = ? AND statut = 'en_cours' AND solde > 0
    """, (eleve_id,))
    total = cursor.fetchone()["total"]
    conn.close()
    return total


def _affecter_paiement_aux_dettes(cursor, eleve_id, montant,
                                    mode_paiement, utilisateur_id,
                                    date_operation=None):
    """
    Affecte le montant (dans l'ordre) aux dettes en cours de l'eleve.
    Retourne (montant_affecte, detail_liste, reste).
    detail_liste = [{'categorie': 'Scolarite', 'montant': 5000, 'dette_id': 3}, ...]
    """
    cursor.execute("""
        SELECT id, categorie, solde
        FROM dettes_eleves
        WHERE eleve_id = ? AND statut = 'en_cours' AND solde > 0
        ORDER BY date_creation ASC, id ASC
    """, (eleve_id,))
    dettes = [dict(r) for r in cursor.fetchall()]

    reste = float(montant)
    affecte_total = 0.0
    details = []

    if not date_operation:
        date_operation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for d in dettes:
        if reste <= 0:
            break
        solde = d["solde"] or 0
        if solde <= 0:
            continue
        montant_a_affecter = min(reste, solde)

        # Enregistrer le paiement de dette
        numero_recu = f"REC-DET-{datetime.now().strftime('%Y%m%d%H%M%S')}-{d['id']}"
        cursor.execute("""
            INSERT INTO paiements_dettes
                (dette_id, numero_recu, montant, mode_paiement,
                 utilisateur_id, date_paiement)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (d["id"], numero_recu, montant_a_affecter,
              mode_paiement, utilisateur_id, date_operation))

        # Mettre a jour la dette
        cursor.execute("SELECT montant_paye FROM dettes_eleves WHERE id = ?",
                       (d["id"],))
        row = cursor.fetchone()
        paye_actuel = (row["montant_paye"] if row else 0) or 0
        nouveau_paye = paye_actuel + montant_a_affecter
        nouveau_solde = solde - montant_a_affecter
        nouveau_statut = "soldee" if nouveau_solde <= 0 else "en_cours"

        cursor.execute("""
            UPDATE dettes_eleves
            SET montant_paye = ?, solde = ?, statut = ?
            WHERE id = ?
        """, (nouveau_paye, nouveau_solde, nouveau_statut, d["id"]))

        details.append({
            "dette_id": d["id"],
            "categorie": d["categorie"],
            "montant": montant_a_affecter,
            "ancien_solde": solde,
            "nouveau_solde": nouveau_solde,
        })
        affecte_total += montant_a_affecter
        reste -= montant_a_affecter

    return affecte_total, details, reste


# ============ PAIEMENTS ELEVES ============
def ajouter_paiement_eleve(eleve_id, montant, motif, mode_paiement,
                            utilisateur_id=None, affecter_dettes=True,
                            date_operation=None):
    """
    Enregistre un paiement eleve.
    - affecter_dettes=True  -> le montant est D'ABORD affecte aux dettes en cours
    - affecter_dettes=False -> paiement normal (scolarite uniquement)
    - date_operation : 'AAAA-MM-JJ' ou 'AAAA-MM-JJ HH:MM:SS'
                       Si None -> date du jour
    Retourne (ok, message, numero_recu, details_dettes).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        montant = float(montant)
        if montant <= 0:
            return False, "Le montant doit etre superieur a 0", None, []

        # Date d'operation
        if not date_operation:
            date_operation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif len(date_operation) == 10:
            date_operation = date_operation + " " + datetime.now().strftime("%H:%M:%S")

        # 1) Affecter d'abord aux dettes en cours (si demande)
        if affecter_dettes:
            affecte, details, reste = _affecter_paiement_aux_dettes(
                cursor, eleve_id, montant, mode_paiement, utilisateur_id,
                date_operation=date_operation,
            )
        else:
            affecte, details, reste = 0, [], montant

        # 2) Numero de recu
        cursor.execute("SELECT COUNT(*) as total FROM paiements_eleves")
        total = cursor.fetchone()["total"]
        annee = datetime.now().year
        numero = f"REC-{annee}-{total + 1:04d}"

        # 3) Motif enrichi
        motif_final = motif.strip()
        if details:
            detail_txt = " | ".join(
                f"{d['categorie']}: {int(d['montant'])}" for d in details
            )
            motif_final = f"{motif_final} (Dettes: {detail_txt})"

        # 4) Enregistrer le paiement global
        cursor.execute("""
            INSERT INTO paiements_eleves
                (numero_recu, eleve_id, montant, motif, mode_paiement,
                 utilisateur_id, date_paiement)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (numero, eleve_id, montant, motif_final, mode_paiement,
              utilisateur_id, date_operation))

        conn.commit()

        # 5) Message
        if details:
            lignes = "\n".join(
                f"  - {d['categorie']} : {int(d['montant'])} "
                f"(reste {int(d['nouveau_solde'])})"
                for d in details
            )
            msg = (f"Recu {numero}\n\n"
                   f"Affecte aux dettes : {int(affecte)} FCFA\n{lignes}")
            if reste > 0:
                msg += f"\n\nReste affecte a la scolarite : {int(reste)} FCFA"
        else:
            msg = f"Recu {numero}"

        return True, msg, numero, details

    except Exception as e:
        conn.rollback()
        return False, f"Erreur : {str(e)}", None, []
    finally:
        conn.close()


def modifier_paiement_eleve(pid, montant=None, motif=None,
                              mode_paiement=None, date_operation=None):
    """
    Modifie un paiement eleve existant.
    Chaque parametre a None = pas de changement.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM paiements_eleves WHERE id = ?", (pid,))
        row = cursor.fetchone()
        if not row:
            return False, "Paiement introuvable"

        nouveau_montant = montant if montant is not None else row["montant"]
        nouveau_motif = motif if motif is not None else row["motif"]
        nouveau_mode = mode_paiement if mode_paiement is not None else row["mode_paiement"]
        nouvelle_date = date_operation if date_operation else row["date_paiement"]

        if nouveau_montant <= 0:
            return False, "Le montant doit etre superieur a 0."

        if len(nouvelle_date) == 10:
            nouvelle_date = nouvelle_date + " " + datetime.now().strftime("%H:%M:%S")

        cursor.execute("""
            UPDATE paiements_eleves
            SET montant = ?, motif = ?, mode_paiement = ?, date_paiement = ?
            WHERE id = ?
        """, (nouveau_montant, nouveau_motif, nouveau_mode, nouvelle_date, pid))

        conn.commit()
        return True, "Paiement modifie"
    except Exception as e:
        conn.rollback()
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


def lister_paiements_eleves(recherche=""):
    conn = get_connection()
    cursor = conn.cursor()
    base = """
        SELECT p.id, p.numero_recu, p.montant, p.motif, p.mode_paiement,
               p.date_paiement, p.eleve_id,
               e.matricule, e.nom, e.prenom, e.classe
        FROM paiements_eleves p
        JOIN eleves e ON p.eleve_id = e.id
        WHERE 1=1
    """
    if recherche.strip():
        terme = f"%{recherche.strip()}%"
        cursor.execute(base + """
            AND (p.numero_recu LIKE ? OR e.matricule LIKE ?
                 OR e.nom LIKE ? OR e.prenom LIKE ? OR p.motif LIKE ?)
            ORDER BY p.date_paiement DESC, p.id DESC
        """, (terme, terme, terme, terme, terme))
    else:
        cursor.execute(base + " ORDER BY p.date_paiement DESC, p.id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def supprimer_paiement_eleve(pid):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM paiements_eleves WHERE id = ?", (pid,))
        conn.commit()
        return True, "Paiement supprime"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


# ============ PAIEMENTS PERSONNEL ============
def ajouter_paiement_personnel(personnel_id, montant, motif, mode_paiement,
                                utilisateur_id=None, montant_avance_deduit=0,
                                date_operation=None):
    """
    Enregistre une paie.
    - montant : montant TOTAL du salaire (ex: $400)
    - montant_avance_deduit : montant d'avance a deduire (ex: $100)
    - date_operation : 'AAAA-MM-JJ' ou 'AAAA-MM-JJ HH:MM:SS'
    Le net verse = montant - montant_avance_deduit
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        montant = float(montant)
        montant_avance_deduit = float(montant_avance_deduit or 0)

        if montant <= 0:
            return False, "Le montant doit etre superieur a 0", None

        if montant_avance_deduit < 0:
            return False, "Le montant de l'avance ne peut pas etre negatif", None

        if montant_avance_deduit > montant:
            return False, "L'avance depasse le montant du salaire", None

        if not date_operation:
            date_operation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif len(date_operation) == 10:
            date_operation = date_operation + " " + datetime.now().strftime("%H:%M:%S")

        numero = generer_numero_paie()
        cursor.execute("""
            INSERT INTO paiements_personnel
                (numero_paie, personnel_id, montant, motif, mode_paiement,
                 utilisateur_id, montant_avance_deduit, date_paiement)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (numero, personnel_id, montant, motif.strip(), mode_paiement,
              utilisateur_id, montant_avance_deduit, date_operation))
        conn.commit()
        return True, f"Paie {numero}", numero
    except Exception as e:
        return False, f"Erreur : {str(e)}", None
    finally:
        conn.close()


def modifier_paiement_personnel(pid, montant=None, motif=None,
                                  mode_paiement=None, date_operation=None):
    """Modifie une paie existante."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM paiements_personnel WHERE id = ?", (pid,))
        row = cursor.fetchone()
        if not row:
            return False, "Paie introuvable"

        nouveau_montant = montant if montant is not None else row["montant"]
        nouveau_motif = motif if motif is not None else row["motif"]
        nouveau_mode = mode_paiement if mode_paiement is not None else row["mode_paiement"]
        nouvelle_date = date_operation if date_operation else row["date_paiement"]

        if nouveau_montant <= 0:
            return False, "Le montant doit etre superieur a 0."

        if len(nouvelle_date) == 10:
            nouvelle_date = nouvelle_date + " " + datetime.now().strftime("%H:%M:%S")

        cursor.execute("""
            UPDATE paiements_personnel
            SET montant = ?, motif = ?, mode_paiement = ?, date_paiement = ?
            WHERE id = ?
        """, (nouveau_montant, nouveau_motif, nouveau_mode, nouvelle_date, pid))

        conn.commit()
        return True, "Paie modifiee"
    except Exception as e:
        conn.rollback()
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


def lister_paiements_personnel(recherche=""):
    conn = get_connection()
    cursor = conn.cursor()
    base = """
        SELECT p.id, p.numero_paie, p.montant, p.motif, p.mode_paiement,
               COALESCE(p.montant_avance_deduit, 0) as montant_avance_deduit,
               p.date_paiement, p.personnel_id,
               e.code, e.nom, e.prenom, e.fonction
        FROM paiements_personnel p
        JOIN personnel e ON p.personnel_id = e.id
        WHERE 1=1
    """
    if recherche.strip():
        terme = f"%{recherche.strip()}%"
        cursor.execute(base + """
            AND (p.numero_paie LIKE ? OR e.code LIKE ?
                 OR e.nom LIKE ? OR e.prenom LIKE ? OR p.motif LIKE ?)
            ORDER BY p.date_paiement DESC, p.id DESC
        """, (terme, terme, terme, terme, terme))
    else:
        cursor.execute(base + " ORDER BY p.date_paiement DESC, p.id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def supprimer_paiement_personnel(pid):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM paiements_personnel WHERE id = ?", (pid,))
        conn.commit()
        return True, "Paie supprimee"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


# ============ TOTAUX / CAISSES ============
def total_caisse_eleves():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(SUM(montant), 0) as total FROM paiements_eleves")
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


def total_caisse_personnel():
    """Total verse REELLEMENT au personnel (net, apres deduction avances)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(montant - COALESCE(montant_avance_deduit, 0)), 0) as total
        FROM paiements_personnel
    """)
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


def total_caisse_eleves_jour():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(montant), 0) as total FROM paiements_eleves
        WHERE DATE(date_paiement) = DATE('now', 'localtime')
    """)
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


def total_caisse_personnel_jour():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(montant - COALESCE(montant_avance_deduit, 0)), 0) as total
        FROM paiements_personnel
        WHERE DATE(date_paiement) = DATE('now', 'localtime')
    """)
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


def total_caisse_eleves_mois():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(montant), 0) as total FROM paiements_eleves
        WHERE strftime('%Y-%m', date_paiement) = strftime('%Y-%m', 'now', 'localtime')
    """)
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


def total_caisse_personnel_mois():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(montant - COALESCE(montant_avance_deduit, 0)), 0) as total
        FROM paiements_personnel
        WHERE strftime('%Y-%m', date_paiement) = strftime('%Y-%m', 'now', 'localtime')
    """)
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total


# ============ RECHERCHE RAPIDE ============
def rechercher_eleve_par_matricule(matricule):
    """Retourne un eleve + son solde scolarite + son total dettes."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*,
               COALESCE(e.frais_scolarite, 0) - COALESCE(
                   (SELECT SUM(montant) FROM paiements_eleves WHERE eleve_id = e.id), 0
               ) as solde,
               COALESCE(
                   (SELECT SUM(solde) FROM dettes_eleves
                    WHERE eleve_id = e.id AND statut = 'en_cours'), 0
               ) as total_dettes
        FROM eleves e
        WHERE e.matricule = ? AND e.actif = 1
    """, (matricule.strip().upper(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def rechercher_personnel_par_code(code):
    """Retourne un personnel + son engagement total + solde a payer"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*,
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
        WHERE p.code = ? AND p.actif = 1
    """, (code.strip().upper(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def total_impayes_eleves():
    """Total des soldes impayes (scolarite) + total dettes en cours."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(
            CASE
                WHEN COALESCE(e.frais_scolarite, 0) -
                     COALESCE((SELECT SUM(montant) FROM paiements_eleves
                               WHERE eleve_id = e.id), 0) > 0
                THEN COALESCE(e.frais_scolarite, 0) -
                     COALESCE((SELECT SUM(montant) FROM paiements_eleves
                               WHERE eleve_id = e.id), 0)
                ELSE 0
            END
        ), 0) as total
        FROM eleves e
        WHERE e.actif = 1
    """)
    total = cursor.fetchone()["total"] or 0
    conn.close()
    return total