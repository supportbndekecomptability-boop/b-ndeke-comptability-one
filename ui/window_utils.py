"""
Utilitaire pour rendre toutes les fenetres adaptatives a l'ecran.
Evite les fenetres coupees sur les petits ecrans.
"""


def setup_adaptive_window(window, largeur_max=540, hauteur_max=720,
                            centre=True, marge_largeur=60, marge_hauteur=100,
                            resizable=False):
    """
    Adapte la taille et la position d'une fenetre Tkinter/CTk a l'ecran.

    - largeur_max / hauteur_max : taille desiree (sera reduite si trop grand)
    - marge_largeur / marge_hauteur : espace a laisser autour
    - centre : centrer la fenetre sur l'ecran
    - resizable : autoriser le redimensionnement
    """
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()

    largeur = min(largeur_max, screen_w - marge_largeur)
    hauteur = min(hauteur_max, screen_h - marge_hauteur)

    if centre:
        x = max(0, (screen_w - largeur) // 2)
        y = max(10, (screen_h - hauteur) // 2 - 20)
    else:
        x = 50
        y = 50

    window.geometry(f"{largeur}x{hauteur}+{x}+{y}")
    window.resizable(resizable, resizable)