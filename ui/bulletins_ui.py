"""
Interface Bulletins scolaires - Version simplifiee
Le module complet sera developpe dans une prochaine version.
Le pays de l'ecole est deja enregistre et sera utilise automatiquement.
"""
import customtkinter as ctk
from config import COLOR_NAVY, COLOR_GOLD
from core.permissions import a_permission, niveaux_autorises
from core.ecole import get_pays_ecole
from core.pays import get_systeme_label


class BulletinsPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")
        self.utilisateur = utilisateur or {}
        self._construire_interface()

    def _construire_interface(self):
        # ===== EN-TETE =====
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            top, text="Bulletins scolaires",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        niveaux = niveaux_autorises(self.utilisateur)
        if niveaux:
            ctk.CTkLabel(
                top, text=" | ".join(niveaux),
                font=("Segoe UI", 10, "bold"),
                text_color="#8e44ad",
            ).pack(side="left", padx=(15, 0), pady=(8, 0))

        # ===== CADRE PAYS ENREGISTRE =====
        pays = get_pays_ecole() or ""

        cadre_pays = ctk.CTkFrame(self, fg_color="#F0F7FF", corner_radius=12,
                                   border_width=2, border_color="#3498db")
        cadre_pays.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            cadre_pays,
            text="PAYS DE L'ETABLISSEMENT",
            font=("Segoe UI", 12, "bold"),
            text_color="#1565C0",
        ).pack(pady=(15, 5))

        if pays:
            ctk.CTkLabel(
                cadre_pays,
                text=pays,
                font=("Segoe UI", 22, "bold"),
                text_color=COLOR_NAVY,
            ).pack(pady=(0, 5))

            try:
                systeme = get_systeme_label(pays)
            except Exception:
                systeme = ""

            if systeme:
                ctk.CTkLabel(
                    cadre_pays,
                    text=f"Systeme educatif : {systeme}",
                    font=("Segoe UI", 11),
                    text_color="#666666",
                ).pack(pady=(0, 15))
            else:
                ctk.CTkFrame(cadre_pays, fg_color="transparent", height=10).pack()
        else:
            ctk.CTkLabel(
                cadre_pays,
                text="Aucun pays enregistre",
                font=("Segoe UI", 14, "italic"),
                text_color="#e74c3c",
            ).pack(pady=(5, 5))

            ctk.CTkLabel(
                cadre_pays,
                text="Allez dans Parametres > Informations Ecole pour choisir votre pays.",
                font=("Segoe UI", 11),
                text_color="#666666",
                justify="center",
            ).pack(pady=(0, 15))

        # ===== MESSAGE DEVELOPPEMENT FUTUR =====
        cadre_info = ctk.CTkFrame(self, fg_color="#FFF7E0", corner_radius=12,
                                   border_width=2, border_color="#e67e22")
        cadre_info.pack(fill="both", expand=True, pady=(0, 10))

        ctk.CTkLabel(
            cadre_info,
            text="MODULE EN COURS DE DEVELOPPEMENT",
            font=("Segoe UI", 16, "bold"),
            text_color="#e67e22",
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            cadre_info,
            text=(
                "Le module complet des bulletins sera disponible dans une\n"
                "prochaine version de l'application.\n\n"
                "Il permettra de :\n\n"
                "    - Saisir manuellement les matieres du programme national\n"
                "    - Enregistrer les notes par eleve et par periode\n"
                "    - Generer les bulletins en PDF\n"
                "    - Calculer les moyennes et les rangs automatiquement\n\n"
                "Le pays que vous avez enregistre sera automatiquement\n"
                "utilise pour adapter le format du bulletin\n"
                "(langue, bareme, mentions, mise en page)."
            ),
            font=("Segoe UI", 12),
            text_color="#8B6914",
            justify="center",
        ).pack(padx=30, pady=(0, 30))

        # ===== BOUTON PARAMETRES =====
        if a_permission(self.utilisateur, "peut_gerer_utilisateurs"):
            ctk.CTkButton(
                cadre_info,
                text="Modifier le pays dans Parametres",
                font=("Segoe UI", 12, "bold"),
                fg_color=COLOR_NAVY, hover_color="#1a3d75",
                height=40, width=280,
                command=self._aller_parametres,
            ).pack(pady=(0, 25))

    def _aller_parametres(self):
        """Ouvre la page Parametres."""
        try:
            parent = self.master
            while parent is not None:
                if hasattr(parent, "_changer_page"):
                    parent._changer_page("Parametres")
                    return
                parent = getattr(parent, "master", None)
        except Exception as e:
            print(f"[BULLETINS] Impossible d'ouvrir Parametres : {e}")