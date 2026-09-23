"""
B-NDEKE Comptability One - Point d'entree
"""
import sys
from database import init_database
from core.utilisateurs import creer_admin_par_defaut, authentifier
from core.licence import licence_est_valide
from core.session import charger_session, supprimer_session, sauvegarder_session
from core.updater import verifier_mise_a_jour
from ui.login import LoginWindow
from ui.dashboard import DashboardWindow
from ui.activation_ui import ActivationWindow
from ui.update_ui import UpdateWindow


def _silence_dpi_error():
    def handler(exc_type, exc_value, exc_traceback):
        if "check_dpi_scaling" in str(exc_value):
            return
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    sys.excepthook = handler


def _verifier_licence():
    """Verifie la licence. Retourne (licence_ok, vient_d_etre_activee)."""
    ok, message, info = licence_est_valide()

    if ok:
        if info and info["jours_restants"] <= 30:
            print(f"[INFO] Licence expire dans {info['jours_restants']} jours")
        return True, False

    print(f"[LICENCE] {message}")
    activation = ActivationWindow()
    activation.mainloop()

    return activation.activation_reussie, True


def _verifier_mise_a_jour():
    """
    Verifie les mises a jour.
    Retourne True si l'appli peut continuer, False si l'utilisateur doit quitter.
    """
    maj = verifier_mise_a_jour()

    if not maj["ok"]:
        print("[UPDATE] Verification ignoree (hors ligne)")
        return True

    if maj["mise_a_jour_obligatoire"]:
        print(f"[UPDATE] Mise a jour obligatoire -> {maj['derniere_version']}")
        fenetre = UpdateWindow(maj, obligatoire=True)
        fenetre.mainloop()
        if not fenetre.mise_a_jour_effectuee:
            print("[UPDATE] Mise a jour refusee. Fermeture.")
            return False
        return True

    if maj["mise_a_jour_disponible"]:
        print(f"[UPDATE] Nouvelle version disponible : {maj['derniere_version']}")
        fenetre = UpdateWindow(maj, obligatoire=False)
        fenetre.mainloop()

    return True


def _ouvrir_dashboard(utilisateur):
    """
    Ouvre le dashboard pour un utilisateur donne.
    Retourne True si l'utilisateur a clique sur 'Se deconnecter',
    False s'il a ferme la fenetre par la croix.
    """
    dashboard = DashboardWindow(utilisateur)
    dashboard.mainloop()
    return getattr(dashboard, "deconnexion_demandee", False)


def main():
    _silence_dpi_error()

    # 1. Initialiser la base de donnees
    init_database()

    # 2. Verifier la licence
    licence_ok, just_activated = _verifier_licence()

    if not licence_ok:
        print("[INFO] Activation annulee. L'application va se fermer.")
        return

    # 3. Creer un admin par defaut si aucun utilisateur n'existe
    creer_admin_par_defaut()

    # 3.5 Verifier les mises a jour
    if not _verifier_mise_a_jour():
        return

    # 4. Si l'app vient d'etre activee -> AUTO-LOGIN avec l'admin
    if just_activated:
        print("[INFO] Activation reussie. Connexion automatique...")
        utilisateur = authentifier("admin@bndeke.com", "admin123")
        if utilisateur:
            sauvegarder_session(utilisateur)
            deconnexion = _ouvrir_dashboard(utilisateur)
            if not deconnexion:
                return
        else:
            return

    # 5. Reconnexion auto via session persistante
    utilisateur = charger_session()
    if utilisateur:
        print(f"[SESSION] Reconnexion automatique : {utilisateur['email']}")
        deconnexion = _ouvrir_dashboard(utilisateur)
        if not deconnexion:
            return

    # 6. Boucle login normale
    while True:
        login = LoginWindow()
        login.mainloop()

        if login.utilisateur_connecte is None:
            break

        deconnexion = _ouvrir_dashboard(login.utilisateur_connecte)
        if not deconnexion:
            break


if __name__ == "__main__":
    main()