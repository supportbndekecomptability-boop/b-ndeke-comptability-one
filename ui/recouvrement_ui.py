"""
Interface de recouvrement
Affiche les eleves qui n'ont PAS encore paye au moins X
"""
import customtkinter as ctk
from tkinter import messagebox
from config import COLOR_NAVY, format_montant, CURRENCY_SYMBOL
from core.recouvrement import (
    lister_eleves_a_recouvrer, lister_classes_disponibles,
    stats_recouvrement,
)
from services.recouvrement_pdf import generer_liste_recouvrement
from ui.pdf_viewer import PdfViewerWindow
from ui.scroll_frame import HorizontalScrollFrame


class RecouvrementPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")

        self.utilisateur = utilisateur
        self.resultats = []

        self._construire_interface()
        self._charger()

    def _construire_interface(self):
        # En-tete
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            top,
            text="Recouvrement des impayes",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        ctk.CTkButton(
            top,
            text="Imprimer la liste",
            font=("Segoe UI", 12, "bold"),
            fg_color="#27ae60",
            hover_color="#229954",
            height=40,
            command=self._imprimer,
        ).pack(side="right")

        # ===== EXPLICATION =====
        info_frame = ctk.CTkFrame(self, fg_color="#FFF7E0", corner_radius=8)
        info_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            info_frame,
            text="Cette page affiche les eleves qui N'ONT PAS ENCORE PAYE "
                 "au moins le montant saisi. Utile pour aller faire le "
                 "recouvrement chez les parents.",
            font=("Segoe UI", 11),
            text_color="#8B6914",
            justify="left",
        ).pack(padx=15, pady=8, anchor="w")

        # ===== FILTRES =====
        filtre_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        filtre_frame.pack(fill="x", pady=(0, 10))

        ligne_filtre = ctk.CTkFrame(filtre_frame, fg_color="transparent")
        ligne_filtre.pack(fill="x", padx=15, pady=(12, 8))

        # Montant minimum paye
        ctk.CTkLabel(
            ligne_filtre,
            text="Eleves n'ayant pas paye au moins :",
            font=("Segoe UI", 12, "bold"),
            text_color="#333333",
        ).pack(side="left", padx=(0, 8))

        self.entree_montant = ctk.CTkEntry(
            ligne_filtre,
            font=("Segoe UI", 13, "bold"),
            width=140,
            height=36,
            placeholder_text="Ex: 300",
        )
        self.entree_montant.pack(side="left", padx=(0, 5))

        ctk.CTkLabel(
            ligne_filtre,
            text=CURRENCY_SYMBOL,
            font=("Segoe UI", 13, "bold"),
            text_color="#666666",
        ).pack(side="left", padx=(0, 20))

        # Classe
        ctk.CTkLabel(
            ligne_filtre,
            text="Classe :",
            font=("Segoe UI", 12, "bold"),
            text_color="#333333",
        ).pack(side="left", padx=(0, 8))

        classes = ["Toutes"] + lister_classes_disponibles()
        self.combo_classe = ctk.CTkComboBox(
            ligne_filtre,
            values=classes,
            font=("Segoe UI", 12),
            width=180,
            height=36,
        )
        self.combo_classe.set("Toutes")
        self.combo_classe.pack(side="left", padx=(0, 20))

        ctk.CTkButton(
            ligne_filtre,
            text="Rechercher",
            font=("Segoe UI", 12, "bold"),
            fg_color=COLOR_NAVY,
            hover_color="#1a3d75",
            width=110,
            height=36,
            command=self._charger,
        ).pack(side="left")

        ctk.CTkButton(
            ligne_filtre,
            text="Reinitialiser",
            font=("Segoe UI", 11),
            fg_color="#e0e0e0",
            text_color="#333333",
            hover_color="#c0c0c0",
            width=110,
            height=36,
            command=self._reinitialiser,
        ).pack(side="left", padx=(8, 0))

        # ===== STATS =====
        self.frame_stats = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_stats.pack(fill="x", pady=(0, 10))

        # ===== TABLEAU =====
        self.tableau = HorizontalScrollFrame(self, fg_color="white",
                                             corner_radius=10)
        self.tableau.pack(fill="both", expand=True)
        self.tableau_frame = self.tableau.interior

    def _creer_entete(self):
        entete = ctk.CTkFrame(self.tableau_frame, fg_color="#f0f0f0",
                              corner_radius=6)
        entete.pack(fill="x", pady=(0, 5))

        colonnes = [
            ("N°", 40),
            ("Matricule", 100),
            ("Nom", 130),
            ("Prenom", 130),
            ("Classe", 100),
            ("Parent", 140),
            ("Telephone", 120),
            ("Frais", 90),
            ("Deja paye", 100),
            ("Reste a payer", 110),
        ]

        for nom, larg in colonnes:
            ctk.CTkLabel(
                entete,
                text=nom,
                font=("Segoe UI", 11, "bold"),
                text_color=COLOR_NAVY,
                width=larg,
                anchor="w",
            ).pack(side="left", padx=4, pady=10)

    def _charger(self):
        # Recuperer les filtres
        try:
            montant_min = float(self.entree_montant.get().strip() or "0")
        except ValueError:
            montant_min = 0

        classe_sel = self.combo_classe.get().strip()
        classe = None if classe_sel == "Toutes" else classe_sel

        # Charger
        self.resultats = lister_eleves_a_recouvrer(
            montant_min_paye=montant_min, classe=classe
        )

        self._afficher_stats(montant_min, classe)
        self._afficher_tableau()

    def _reinitialiser(self):
        self.entree_montant.delete(0, "end")
        self.entree_montant.insert(0, "0")
        self.combo_classe.set("Toutes")
        self._charger()

    def _afficher_stats(self, montant_min, classe):
        for w in self.frame_stats.winfo_children():
            w.destroy()

        stats = stats_recouvrement(montant_min, classe)

        cartes = [
            ("Eleves concernes", str(stats["nombre"]), "#e74c3c"),
            ("Total deja paye", format_montant(stats["total_paye"]), "#27ae60"),
            ("Manquant a atteindre", format_montant(stats["total_manquant"]), "#e67e22"),
            ("Total des soldes", format_montant(stats["total_du"]), "#c0392b"),
        ]

        for titre, valeur, couleur in cartes:
            carte = ctk.CTkFrame(self.frame_stats, fg_color="white",
                                 corner_radius=12)
            carte.pack(side="left", expand=True, fill="both", padx=6)

            ctk.CTkLabel(
                carte, text=titre,
                font=("Segoe UI", 11, "bold"),
                text_color="#888888",
            ).pack(pady=(15, 3))

            ctk.CTkLabel(
                carte, text=valeur,
                font=("Segoe UI", 18, "bold"),
                text_color=couleur,
            ).pack(pady=(0, 15))

    def _afficher_tableau(self):
        self.tableau.clear()
        self._creer_entete()

        if not self.resultats:
            ctk.CTkLabel(
                self.tableau_frame,
                text="Aucun eleve ne correspond aux criteres.",
                font=("Segoe UI", 13),
                text_color="#999999",
            ).pack(pady=40)
            return

        for i, e in enumerate(self.resultats):
            fond = "#ffffff" if i % 2 == 0 else "#fafafa"
            ligne = ctk.CTkFrame(self.tableau_frame, fg_color=fond,
                                 corner_radius=4)
            ligne.pack(fill="x", pady=1)

            valeurs = [
                (str(i + 1), 40, "#666666", "normal"),
                (e["matricule"], 100, "#0066CC", "bold"),
                (e["nom"], 130, "#333333", "normal"),
                (e["prenom"], 130, "#333333", "normal"),
                (e["classe"], 100, "#333333", "normal"),
                (e.get("nom_parent") or "-", 140, "#333333", "normal"),
                (e.get("telephone_parent") or "-", 120, "#333333", "normal"),
                (format_montant(e["frais_totaux"]), 90, "#333333", "normal"),
                (format_montant(e["total_paye"]), 100, "#27ae60", "normal"),
                (format_montant(e["solde"]), 110, "#e74c3c", "bold"),
            ]

            for valeur, larg, coul, poids in valeurs:
                ctk.CTkLabel(
                    ligne, text=str(valeur),
                    font=("Segoe UI", 11, poids),
                    text_color=coul,
                    width=larg,
                    anchor="w",
                ).pack(side="left", padx=4, pady=8)

    def _imprimer(self):
        if not self.resultats:
            messagebox.showwarning(
                "Aucune donnee",
                "Il n'y a aucun eleve a recouvrer avec ces filtres."
            )
            return

        try:
            montant_min = float(self.entree_montant.get().strip() or "0")
        except ValueError:
            montant_min = 0

        classe_sel = self.combo_classe.get().strip()
        classe = None if classe_sel == "Toutes" else classe_sel

        rep = messagebox.askyesno(
            "Confirmation",
            f"Imprimer la liste de recouvrement ?\n\n"
            f"Nombre d'eleves : {len(self.resultats)}\n"
            f"Total des soldes : "
            f"{format_montant(sum(e['solde'] for e in self.resultats))}\n\n"
            f"Cette liste sera imprimee pour le recouvrement."
        )

        if not rep:
            return

        try:
            chemin = generer_liste_recouvrement(
                self.resultats, montant_min_paye=montant_min, classe=classe
            )
            PdfViewerWindow(self.master, chemin,
                            titre="Liste de recouvrement")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur",
                                 f"Impossible de generer le PDF :\n{e}")