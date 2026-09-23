"""
B-NDEKE Comptability One - Point d'entree
"""
from database import init_database
from core.utilisateurs import creer_admin_par_defaut
from ui.login import LoginWindow
from ui.dashboard import DashboardWindow


def main():
    # 1. Initialiser la base de donnees
    init_database()

    # 2. Creer un admin par defaut si aucun utilisateur n'existe
    creer_admin_par_defaut()

    # 3. Boucle : login -> dashboard -> (deconnexion = relance login)
    while True:
        # Afficher le login
        login = LoginWindow()
        login.mainloop()

        # Si aucun utilisateur connecte -> fenetre fermee, on quitte
        if login.utilisateur_connecte is None:
            break

        # Afficher le dashboard
        dashboard = DashboardWindow(login.utilisateur_connecte)
        dashboard.mainloop()

        # Boucle : si on revient ici, l'utilisateur s'est deconnecte -> relancer login


if __name__ == "__main__":
    main()