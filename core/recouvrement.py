"""
Gestion du recouvrement des impayes
Affiche les eleves qui N'ONT PAS encore paye au moins X
"""
from datetime import datetime
from database import get_connection


def lister_eleves_a_recouvrer(montant_min_paye=0, classe=None,
                                seulement_avec_parent=True):
    """
    Retourne la liste des eleves qui N'ONT PAS encore paye
    au moins `montant_min_paye`.

    - montant_min_paye = 0  -> affiche TOUS les eleves avec un solde > 0
    - montant_min_paye = X  -> affiche les eleves qui ont paye MOINS de X

    Exemple : montant_min_paye = 300
    -> Affiche ceux qui ont paye < 300 (donc encore en retard)
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            e.id,
            e.matricule,
            e.nom,
            e.prenom,
            e.classe,
            e.sexe,
            e.nom_parent,
            e.telephone_parent,
            COALESCE(e.frais_scolarite, 0) as frais_totaux,
            COALESCE(
                (SELECT SUM(montant) FROM paiements_eleves
                 WHERE eleve_id = e.id), 0
            ) as total_paye
        FROM eleves e
        WHERE e.actif = 1
    """

    params = []

    if classe:
        query += " AND e.classe = ?"
        params.append(classe)

    if seulement_avec_parent:
        query += " AND (e.nom_parent IS NOT NULL AND e.nom_parent != '')"

    query += " ORDER BY e.classe, e.nom, e.prenom"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    seuil = float(montant_min_paye or 0)

    resultats = []
    for r in rows:
        frais = float(r["frais_totaux"] or 0)
        paye = float(r["total_paye"] or 0)
        solde = frais - paye

        # ===== FILTRE =====
        if seuil > 0:
            # Cas 1 : seuil saisi -> eleves qui ont paye MOINS que le seuil
            if paye >= seuil:
                continue
        else:
            # Cas 2 : seuil = 0 -> eleves qui ont encore un solde a payer
            if solde <= 0.01:
                continue

        resultats.append({
            "id": r["id"],
            "matricule": r["matricule"],
            "nom": r["nom"],
            "prenom": r["prenom"],
            "classe": r["classe"],
            "sexe": r["sexe"],
            "nom_parent": r["nom_parent"],
            "telephone_parent": r["telephone_parent"],
            "frais_totaux": frais,
            "total_paye": paye,
            "solde": solde,
            "manquant": max(0, seuil - paye) if seuil > 0 else solde,
        })

    # Trier par montant paye croissant (les moins payes en premier)
    resultats.sort(key=lambda x: x["total_paye"])
    return resultats


def lister_classes_disponibles():
    """Retourne la liste des classes qui ont au moins un eleve"""
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


def stats_recouvrement(montant_min_paye=0, classe=None):
    """Retourne les statistiques du recouvrement"""
    eleves = lister_eleves_a_recouvrer(montant_min_paye, classe)

    if not eleves:
        return {
            "nombre": 0,
            "total_du": 0,
            "total_paye": 0,
            "moyenne": 0,
            "max": 0,
            "min": 0,
            "total_manquant": 0,
        }

    total_du = sum(e["solde"] for e in eleves)
    total_paye = sum(e["total_paye"] for e in eleves)
    total_manquant = sum(e["manquant"] for e in eleves)
    soldes = [e["solde"] for e in eleves]

    return {
        "nombre": len(eleves),
        "total_du": total_du,
        "total_paye": total_paye,
        "moyenne": total_du / len(eleves),
        "max": max(soldes),
        "min": min(soldes),
        "total_manquant": total_manquant,
    }