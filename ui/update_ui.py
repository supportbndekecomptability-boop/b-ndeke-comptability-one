"""
Fenetre de notification / blocage pour les mises a jour
"""
import webbrowser
import customtkinter as ctk
from config import COLOR_NAVY, COLOR_GOLD, COLOR_BG


class UpdateWindow(ctk.CTk):
    def __init__(self, info, obligatoire=False):
        super().__init__()

        self.info = info
        self.obligatoire = obligatoire
        self.mise_a_jour_effectuee = False

        titre = "Mise a jour requise" if obligatoire else "Mise a jour disponible"
        self.title(f"B-NDEKE - {titre}")
        self.geometry("560x420")
        self.configure(fg_color=COLOR_BG)
        self.resizable(False, False)

        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 280
        y = (self.winfo_screenheight() // 2) - 210
        self.geometry(f"560x420+{x}+{y}")

        # Bloquer la fermeture si obligatoire
        if obligatoire:
            self.protocol("WM_DELETE_WINDOW", lambda: None)

        self._construire()

    def _construire(self):
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=20)
        card.pack(expand=True, padx=30, pady=30, fill="both")

        ctk.CTkLabel(
            card, text="B-NDEKE",
            font=("Segoe UI", 28, "bold"),
            text_color=COLOR_NAVY,
        ).pack(pady=(25, 0))

        ctk.CTkLabel(
            card, text="Comptability One",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_GOLD,
        ).pack(pady=(0, 20))

        titre = "Mise a jour obligatoire" if self.obligatoire else "Mise a jour disponible"
        couleur_titre = "#e74c3c" if self.obligatoire else COLOR_NAVY

        ctk.CTkLabel(
            card, text=titre,
            font=("Segoe UI", 16, "bold"),
            text_color=couleur_titre,
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            card,
            text=self.info.get("message", ""),
            font=("Segoe UI", 11),
            text_color="#444444",
            justify="center",
        ).pack(pady=(0, 8), padx=20)

        ctk.CTkLabel(
            card,
            text=f"Version actuelle : {self.info.get('version_actuelle')}   →   "
                 f"Nouvelle version : {self.info.get('derniere_version')}",
            font=("Segoe UI", 10),
            text_color="#888888",
        ).pack(pady=(0, 15))

        ctk.CTkButton(
            card,
            text="Telecharger la mise a jour",
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_NAVY,
            hover_color="#1a3d75",
            height=45,
            command=self._telecharger,
        ).pack(padx=40, pady=(5, 10), fill="x")

        if self.obligatoire:
            ctk.CTkLabel(
                card,
                text="L'application ne peut pas demarrer sans cette mise a jour.",
                font=("Segoe UI", 10),
                text_color="#e74c3c",
                wraplength=400,
            ).pack(pady=(0, 5))

            ctk.CTkButton(
                card,
                text="Quitter",
                font=("Segoe UI", 11),
                fg_color="#999999",
                hover_color="#777777",
                height=32,
                command=self.destroy,
            ).pack(padx=40, pady=(0, 20), fill="x")
        else:
            ctk.CTkButton(
                card,
                text="Plus tard",
                font=("Segoe UI", 11),
                fg_color="#999999",
                hover_color="#777777",
                height=32,
                command=self.destroy,
            ).pack(padx=40, pady=(0, 20), fill="x")

    def _telecharger(self):
        url = self.info.get("url_telechargement", "")
        if url:
            webbrowser.open(url)
        self.mise_a_jour_effectuee = True
        if self.obligatoire:
            self.destroy()
        else:
            self.destroy()