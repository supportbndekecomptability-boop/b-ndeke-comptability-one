"""
Systeme de permissions par role - B-NDEKE Comptability One

Regles metier :
- Caissier       : entrees/sorties + annulation de SES operations.
                   Encaisse les dettes, ne peut PAS en creer.
                   Voit Classes, Eleves et Personnel en LECTURE SEULE
                   (pour copier les codes/matricules).
- Comptable      : superviseur du caissier. Voit, modifie, supprime
                   UNIQUEMENT les operations du caissier.
- Admin          : tout.
- Gestionnaire   : tout + bloquer/debloquer les fonctionnalites des autres.
- Directeur/Pre  : voient les etats financiers,
                   GERENT les bulletins et les presences (eleves + personnel),
                   exportent et impriment.
"""

# ===== LISTE DES ROLES =====
ROLES = [
    "admin",
    "gestionnaire",
    "comptable",
    "caissier",
    "directeur",
    "prefet",
]


# ===== ROLES ET MENUS ACCESSIBLES =====
MENUS_PAR_ROLE = {
    "admin": [
        "Tableau de bord", "Classes", "Frais", "Eleves", "Paiements",
        "Caisse", "Depenses", "Personnel", "Presences", "Presences personnel",
        "Dettes", "Bulletins", "Recouvrement", "Rapports",
        "Etats financiers", "Export Excel", "Parametres",
    ],
    "gestionnaire": [
        "Tableau de bord", "Classes", "Frais", "Eleves", "Paiements",
        "Caisse", "Depenses", "Personnel", "Presences", "Presences personnel",
        "Dettes", "Bulletins", "Recouvrement", "Rapports",
        "Etats financiers", "Export Excel", "Parametres",
    ],
    "comptable": [
        "Tableau de bord", "Paiements", "Caisse", "Dettes",
        "Rapports", "Etats financiers",
    ],
    # CAISSIER : acces lecture seule a Classes, Eleves et Personnel
    # pour trouver rapidement les matricules/codes
    "caissier": [
        "Caisse", "Paiements", "Dettes",
        "Classes", "Eleves", "Personnel",
    ],
    "directeur": [
        "Tableau de bord", "Bulletins", "Presences", "Presences personnel",
        "Rapports", "Etats financiers", "Export Excel",
    ],
    "prefet": [
        "Tableau de bord", "Bulletins", "Presences", "Presences personnel",
        "Rapports", "Etats financiers", "Export Excel",
    ],
}


# ===== PERMISSIONS DETAILLEES PAR ROLE =====
PERMISSIONS = {
    # ---------------------------------------------------------------
    # ADMIN : tout, sans exception
    # ---------------------------------------------------------------
    "admin": {
        "peut_tout_modifier": True,
        "peut_supprimer": True,
        "peut_supprimer_operations_caissier": True,
        "peut_gerer_utilisateurs": True,
        "peut_bloquer_utilisateurs": True,
        "peut_gerer_permissions": True,
        "peut_annuler_ses_operations": True,
        "peut_annuler_tout": True,
        "peut_voir_activite_caissier": True,
        "peut_modifier_operations_caissier": True,
        "peut_modifier_date": True,
        "peut_gerer_paiements": True,
        "peut_creer_dette": True,
        "peut_encaisser_dette": True,
        "peut_gerer_eleves": True,
        "peut_gerer_classes": True,
        "peut_gerer_frais": True,
        "peut_gerer_personnel": True,
        "peut_gerer_depenses": True,
        "peut_gerer_recouvrement": True,
        "peut_gerer_presences": True,
        "peut_gerer_presences_personnel": True,
        "peut_voir_presences": True,
        "peut_voir_presences_personnel": True,
        "peut_voir_etats_financiers": True,
        "peut_voir_bulletins": True,
        "peut_gerer_bulletins": True,
        "peut_modifier_frais_personnel": True,
        "peut_exporter": True,
        "peut_imprimer": True,
    },

    # ---------------------------------------------------------------
    # GESTIONNAIRE : tout + bloquer/debloquer
    # ---------------------------------------------------------------
    "gestionnaire": {
        "peut_tout_modifier": True,
        "peut_supprimer": True,
        "peut_supprimer_operations_caissier": True,
        "peut_gerer_utilisateurs": True,
        "peut_bloquer_utilisateurs": True,
        "peut_gerer_permissions": True,
        "peut_annuler_ses_operations": True,
        "peut_annuler_tout": True,
        "peut_voir_activite_caissier": True,
        "peut_modifier_operations_caissier": True,
        "peut_modifier_date": True,
        "peut_gerer_paiements": True,
        "peut_creer_dette": True,
        "peut_encaisser_dette": True,
        "peut_gerer_eleves": True,
        "peut_gerer_classes": True,
        "peut_gerer_frais": True,
        "peut_gerer_personnel": True,
        "peut_gerer_depenses": True,
        "peut_gerer_recouvrement": True,
        "peut_gerer_presences": True,
        "peut_gerer_presences_personnel": True,
        "peut_voir_presences": True,
        "peut_voir_presences_personnel": True,
        "peut_voir_etats_financiers": True,
        "peut_voir_bulletins": True,
        "peut_gerer_bulletins": True,
        "peut_modifier_frais_personnel": True,
        "peut_exporter": True,
        "peut_imprimer": True,
    },

    # ---------------------------------------------------------------
    # COMPTABLE : superviseur du caissier uniquement
    # ---------------------------------------------------------------
    "comptable": {
        # --- Superviseur du caissier ---
        "peut_voir_activite_caissier": True,
        "peut_modifier_operations_caissier": True,
        "peut_supprimer_operations_caissier": True,

        # --- Acces lecture ---
        "peut_voir_etats_financiers": True,
        "peut_voir_rapports": True,
        "peut_voir_paiements": True,
        "peut_voir_dettes": True,

        # --- Rien d'autre ---
        "peut_tout_modifier": False,
        "peut_supprimer": False,
        "peut_gerer_utilisateurs": False,
        "peut_bloquer_utilisateurs": False,
        "peut_gerer_permissions": False,
        "peut_annuler_ses_operations": False,
        "peut_annuler_tout": True,
        "peut_modifier_date": False,
        "peut_gerer_paiements": False,
        "peut_creer_dette": False,
        "peut_encaisser_dette": False,
        "peut_gerer_eleves": False,
        "peut_gerer_classes": False,
        "peut_gerer_frais": False,
        "peut_gerer_personnel": False,
        "peut_gerer_depenses": False,
        "peut_gerer_recouvrement": False,
        "peut_gerer_presences": False,
        "peut_gerer_presences_personnel": False,
        "peut_voir_presences": False,
        "peut_voir_presences_personnel": False,
        "peut_voir_bulletins": False,
        "peut_gerer_bulletins": False,
        "peut_modifier_frais_personnel": False,
        "peut_exporter": False,
        "peut_imprimer": True,
    },

    # ---------------------------------------------------------------
    # CAISSIER : entrees/sorties + annulation de SES operations.
    # Voit Classes, Eleves et Personnel en LECTURE SEULE (copier codes).
    # ---------------------------------------------------------------
    "caissier": {
        "peut_tout_modifier": False,
        "peut_supprimer": False,
        "peut_supprimer_operations_caissier": False,
        "peut_gerer_utilisateurs": False,
        "peut_bloquer_utilisateurs": False,
        "peut_gerer_permissions": False,
        "peut_annuler_ses_operations": True,
        "peut_annuler_tout": False,
        "peut_voir_activite_caissier": False,
        "peut_modifier_operations_caissier": False,
        "peut_modifier_date": False,
        "peut_gerer_paiements": True,
        "peut_creer_dette": False,
        "peut_encaisser_dette": True,

        # --- Lecture seule de Classes, Eleves et Personnel ---
        "peut_gerer_eleves": False,
        "peut_gerer_classes": False,
        "peut_gerer_frais": False,
        "peut_gerer_personnel": False,
        "peut_gerer_depenses": False,
        "peut_gerer_recouvrement": False,
        "peut_gerer_presences": False,
        "peut_gerer_presences_personnel": False,
        "peut_voir_presences": False,
        "peut_voir_presences_personnel": False,
        "peut_voir_etats_financiers": False,
        "peut_voir_bulletins": False,
        "peut_gerer_bulletins": False,
        "peut_modifier_frais_personnel": False,
        "peut_exporter": False,
        "peut_imprimer": True,
    },

    # ---------------------------------------------------------------
    # DIRECTEUR : etats financiers + bulletins + presences (gestion)
    # ---------------------------------------------------------------
    "directeur": {
        "peut_tout_modifier": False,
        "peut_supprimer": False,
        "peut_supprimer_operations_caissier": False,
        "peut_gerer_utilisateurs": False,
        "peut_bloquer_utilisateurs": False,
        "peut_gerer_permissions": False,
        "peut_annuler_ses_operations": False,
        "peut_annuler_tout": False,
        "peut_voir_activite_caissier": True,
        "peut_modifier_operations_caissier": False,
        "peut_modifier_date": False,
        "peut_gerer_paiements": False,
        "peut_creer_dette": False,
        "peut_encaisser_dette": False,
        "peut_gerer_eleves": False,
        "peut_gerer_classes": False,
        "peut_gerer_frais": False,
        "peut_gerer_personnel": False,
        "peut_gerer_depenses": False,
        "peut_gerer_recouvrement": False,
        "peut_gerer_presences": True,             # <-- GERE les presences
        "peut_gerer_presences_personnel": True,   # <-- GERE presences personnel
        "peut_voir_presences": True,
        "peut_voir_presences_personnel": True,
        "peut_voir_etats_financiers": True,
        "peut_voir_bulletins": True,
        "peut_gerer_bulletins": True,             # <-- GERE les bulletins
        "peut_modifier_frais_personnel": False,
        "peut_exporter": True,
        "peut_imprimer": True,
    },

    # ---------------------------------------------------------------
    # PREFET : identique au directeur
    # ---------------------------------------------------------------
    "prefet": {
        "peut_tout_modifier": False,
        "peut_supprimer": False,
        "peut_supprimer_operations_caissier": False,
        "peut_gerer_utilisateurs": False,
        "peut_bloquer_utilisateurs": False,
        "peut_gerer_permissions": False,
        "peut_annuler_ses_operations": False,
        "peut_annuler_tout": False,
        "peut_voir_activite_caissier": True,
        "peut_modifier_operations_caissier": False,
        "peut_modifier_date": False,
        "peut_gerer_paiements": False,
        "peut_creer_dette": False,
        "peut_encaisser_dette": False,
        "peut_gerer_eleves": False,
        "peut_gerer_classes": False,
        "peut_gerer_frais": False,
        "peut_gerer_personnel": False,
        "peut_gerer_depenses": False,
        "peut_gerer_recouvrement": False,
        "peut_gerer_presences": True,             # <-- GERE les presences
        "peut_gerer_presences_personnel": True,   # <-- GERE presences personnel
        "peut_voir_presences": True,
        "peut_voir_presences_personnel": True,
        "peut_voir_etats_financiers": True,
        "peut_voir_bulletins": True,
        "peut_gerer_bulletins": True,             # <-- GERE les bulletins
        "peut_modifier_frais_personnel": False,
        "peut_exporter": True,
        "peut_imprimer": True,
    },
}


# ===== FONCTIONS UTILITAIRES =====
def get_role(utilisateur):
    """Retourne le role de l'utilisateur (en minuscules)."""
    if not utilisateur:
        return "caissier"
    return (utilisateur.get("role") or "caissier").lower()


def menus_autorises(utilisateur):
    """Retourne la liste des menus accessibles pour ce role."""
    role = get_role(utilisateur)
    return MENUS_PAR_ROLE.get(role, MENUS_PAR_ROLE["caissier"])


def a_permission(utilisateur, permission):
    """Verifie si l'utilisateur a une permission donnee."""
    role = get_role(utilisateur)
    perms = PERMISSIONS.get(role, {})
    return bool(perms.get(permission, False))


def niveaux_autorises(utilisateur):
    """
    Retourne la liste des niveaux scolaires accessibles selon le role.
    - directeur : Maternelle + Primaire
    - prefet    : Secondaire
    - autres    : None (tous les niveaux)

    None = pas de restriction.
    """
    role = get_role(utilisateur)
    if role == "directeur":
        return ["Maternelle", "Primaire"]
    if role == "prefet":
        return ["Secondaire"]
    return None


def peut_acceder_page(utilisateur, nom_page):
    """Verifie si l'utilisateur peut acceder a une page donnee."""
    return nom_page in menus_autorises(utilisateur)


def role_label(role):
    """Retourne le label affichable du role."""
    labels = {
        "admin": "Administrateur",
        "gestionnaire": "Gestionnaire",
        "comptable": "Comptable",
        "caissier": "Caissier",
        "directeur": "Directeur",
        "prefet": "Prefet",
    }
    return labels.get(role.lower(), role)
