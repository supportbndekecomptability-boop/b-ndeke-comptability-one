"""
B-NDEKE Comptability One - Point d'entree
"""
import sys
from database import init_database
from core.utilisateurs import creer_admin_par_defaut, authentifier
from core.licence import licence_est_valide
from core.session import charger_session, sauvegarder_session
from core.updater import verifier_mise_a_jour
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


def _sauvegarde_cloud_si_besoin():
    """Envoie une sauvegarde cloud si active et derniere > 24h."""
    try:
        from core.backup_cloud import (
            sauvegarde_cloud_active, sauvegarder_dans_cloud,
        )
        from core.parametres import get_parametre
        from datetime import datetime, timedelta

        if not sauvegarde_cloud_active():
            return

        derniere = get_parametre("derniere_backup_cloud")
        if derniere:
            try:
                dt = datetime.strptime(derniere, "%d/%m/%Y %H:%M")
                if datetime.now() - dt < timedelta(hours=23):
                    return
            except Exception:
                pass

        print("[BACKUP] Envoi de la sauvegarde cloud...")
        ok, msg = sauvegarder_dans_cloud()
        print(f"[BACKUP] {msg}")
    except Exception as e:
        print(f"[BACKUP] Ignore : {e}")


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

    # 4. Verifier les mises a jour
    if not _verifier_mise_a_jour():
        return

    # 5. Sauvegarde cloud silencieuse (si active)
    _sauvegarde_cloud_si_besoin()

    # 6. AUTO-LOGIN (plus jamais de fenetre de connexion)
    utilisateur = charger_session()

    if not utilisateur:
        print("[INFO] Aucune session active. Connexion admin par defaut...")
        utilisateur = authentifier("admin@bndeke.com", "admin123")
        if utilisateur:
            sauvegarder_session(utilisateur)
        else:
            print("[ERREUR] Impossible de se connecter. Fermeture.")
            return

    # 7. Ouvrir le dashboard
    print(f"[SESSION] Connexion : {utilisateur.get('email', 'inconnu')}")
    dashboard = DashboardWindow(utilisateur)
    dashboard.mainloop()

    # 8. Fin de l'application
    print("[INFO] Application fermee.")


if __name__ == "__main__":
    main()