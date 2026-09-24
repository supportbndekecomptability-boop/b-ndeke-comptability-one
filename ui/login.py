"""
Ecran de connexion de B-NDEKE Comptability One
"""
import customtkinter as ctk
from config import COLOR_NAVY, COLOR_GOLD, COLOR_BG
from core.utilisateurs import authentifier
from core.session import sauvegarder_session


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.utilisateur_connecte = None

        self.title("B-NDEKE Comptability One - Connexion")
        self.geometry("500x600")
        self.configure(fg_color=COLOR_BG)
        self.resizable(False, False)

        # Centrer la fenetre
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 250
        y = (self.winfo_screenheight() // 2) - 300
        self.geometry(f"500x600+{x}+{y}")

        self._construire_interface()

    def _construire_interface(self):
        # Carte centrale
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=20)
        card.pack(expand=True, padx=40, pady=40, fill="both")

        # Logo
        ctk.CTkLabel(
            card,
            text="B-NDEKE",
            font=("Segoe UI", 36, "bold"),
            text_color=COLOR_NAVY,
        ).pack(pady=(40, 0))

        ctk.CTkLabel(
            card,
            text="Comptability One",
            font=("Segoe UI", 18, "bold"),
            text_color=COLOR_GOLD,
        ).pack(pady=(0, 30))

        ctk.CTkLabel(
            card,
            text="Connexion a votre espace",
            font=("Segoe UI", 13),
            text_color="#666666",
        ).pack(pady=(0, 20))

        # Email
        ctk.CTkLabel(
            card,
            text="Adresse email",
            font=("Segoe UI", 12, "bold"),
            text_color="#333333",
            anchor="w",
        ).pack(padx=40, pady=(10, 5), fill="x")

        self.entree_email = ctk.CTkEntry(
            card,
            placeholder_text="exemple@bndeke.com",
            height=40,
            font=("Segoe UI", 13),
        )
        self.entree_email.pack(padx=40, pady=(0, 15), fill="x")

        # Mot de passe
        ctk.CTkLabel(
            card,
            text="Mot de passe",
            font=("Segoe UI", 12, "bold"),
            text_color="#333333",
            anchor="w",
        ).pack(padx=40, pady=(5, 5), fill="x")

        self.entree_mdp = ctk.CTkEntry(
            card,
            placeholder_text="********",
            show="*",
            height=40,
            font=("Segoe UI", 13),
        )
        self.entree_mdp.pack(padx=40, pady=(0, 10), fill="x")

        # Message d'erreur
        self.label_message = ctk.CTkLabel(
            card,
            text="",
            font=("Segoe UI", 12),
            text_color="red",
        )
        self.label_message.pack(pady=(0, 10))

        # Bouton connexion
        ctk.CTkButton(
            card,
            text="Se connecter",
            font=("Segoe UI", 14, "bold"),
            fg_color=COLOR_NAVY,
            hover_color="#1a3d75",
            height=45,
            command=self._se_connecter,
        ).pack(padx=40, pady=(10, 20), fill="x")

        # Lier la touche Entree
        self.entree_mdp.bind("<Return>", lambda e: self._se_connecter())

    def _se_connecter(self):
        email = self.entree_email.get().strip()
        mot_de_passe = self.entree_mdp.get()

        if not email or not mot_de_passe:
            self.label_message.configure(text="Veuillez remplir tous les champs.")
            return

        # authentifier() retourne (ok, user_dict, message)
        resultat = authentifier(email, mot_de_passe)

        if isinstance(resultat, tuple) and len(resultat) >= 2:
            ok, utilisateur = resultat[0], resultat[1]
            message = resultat[2] if len(resultat) >= 3 else ""
        else:
            ok = False
            utilisateur = None
            message = "Reponse invalide du serveur."

        if ok and isinstance(utilisateur, dict):
            self.utilisateur_connecte = utilisateur
            sauvegarder_session(utilisateur)
            self.destroy()
        else:
            # Afficher le vrai message d'erreur si possible
            self.label_message.configure(
                text=message or "Email ou mot de passe incorrect."
            )
            self.entree_mdp.delete(0, "end")