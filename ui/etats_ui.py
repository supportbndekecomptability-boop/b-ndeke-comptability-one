"""
Interface Etats financiers SYSCOHADA
"""
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from config import COLOR_NAVY, COLOR_GOLD

from core.etats_financiers import (
    etat_journal, etat_grand_livre, etat_balance,
    etat_compte_resultat, etat_bilan, etat_tresorerie,
)
from services.etats_pdf import (
    pdf_journal, pdf_grand_livre, pdf_balance,
    pdf_compte_resultat, pdf_bilan, pdf_tresorerie,
)
from ui.pdf_viewer import PdfViewerWindow


class EtatsPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")

        self.utilisateur = utilisateur

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self._construire_interface()

    # ================== INTERFACE ==================
    def _construire_interface(self):
        ctk.CTkLabel(
            self.scroll,
            text="Etats financiers SYSCOHADA",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_NAVY,
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            self.scroll,
            text="Generez les etats financiers selon le referentiel OHADA / SYSCOHADA",
            font=("Segoe UI", 13),
            text_color="#666666",
        ).pack(anchor="w", pady=(0, 15))

        # ===== FILTRE DE PERIODE =====
        periode_frame = ctk.CTkFrame(self.scroll, fg_color="white", corner_radius=10)
        periode_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            periode_frame,
            text="Periode de l'exercice",
            font=("Segoe UI", 12, "bold"),
            text_color=COLOR_NAVY,
        ).pack(anchor="w", padx=15, pady=(12, 8))

        ligne_dates = ctk.CTkFrame(periode_frame, fg_color="transparent")
        ligne_dates.pack(fill="x", padx=15, pady=(0, 12))

        # Debut
        ctk.CTkLabel(
            ligne_dates, text="Du :",
            font=("Segoe UI", 11, "bold"),
            text_color="#333333",
        ).pack(side="left")

        self.entree_debut = ctk.CTkEntry(
            ligne_dates,
            font=("Segoe UI", 11),
            width=120, height=34,
            placeholder_text="AAAA-MM-JJ",
        )
        annee = datetime.now().year
        self.entree_debut.insert(0, f"{annee}-01-01")
        self.entree_debut.pack(side="left", padx=(5, 20))

        # Fin
        ctk.CTkLabel(
            ligne_dates, text="Au :",
            font=("Segoe UI", 11, "bold"),
            text_color="#333333",
        ).pack(side="left")

        self.entree_fin = ctk.CTkEntry(
            ligne_dates,
            font=("Segoe UI", 11),
            width=120, height=34,
            placeholder_text="AAAA-MM-JJ",
        )
        self.entree_fin.insert(0, f"{annee}-12-31")
        self.entree_fin.pack(side="left", padx=5)

        # Boutons rapides
        ctk.CTkButton(
            ligne_dates,
            text="Ce mois",
            font=("Segoe UI", 10),
            fg_color="#e0e0e0",
            text_color="#333333",
            hover_color="#c0c0c0",
            width=80, height=30,
            command=self._periode_mois_actuel,
        ).pack(side="left", padx=(20, 5))

        ctk.CTkButton(
            ligne_dates,
            text="Cette annee",
            font=("Segoe UI", 10),
            fg_color="#e0e0e0",
            text_color="#333333",
            hover_color="#c0c0c0",
            width=100, height=30,
            command=self._periode_annee_actuelle,
        ).pack(side="left", padx=5)

        # ===== GRILLE D'ETATS =====
        ctk.CTkLabel(
            self.scroll,
            text="Choisissez un etat financier",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_NAVY,
        ).pack(anchor="w", pady=(5, 10))

        grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        grid.pack(fill="x", expand=False)

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(2, weight=1)

        # Carte 1 : Journal
        self._creer_carte(
            grid, 0, 0,
            titre="Journal General",
            description="Toutes les ecritures comptables en ordre chronologique (debit / credit par piece).",
            couleur="#3498db",
            on_generer=self._generer_journal,
        )

        # Carte 2 : Grand livre
        self._creer_carte(
            grid, 0, 1,
            titre="Grand Livre",
            description="Detail de tous les mouvements, classe par compte comptable SYSCOHADA.",
            couleur="#9b59b6",
            on_generer=self._generer_grand_livre,
        )

        # Carte 3 : Balance
        self._creer_carte(
            grid, 0, 2,
            titre="Balance Generale",
            description="Balance a 6 colonnes : mouvements et soldes debiteurs / crediteurs.",
            couleur="#e67e22",
            on_generer=self._generer_balance,
        )

        # Carte 4 : Compte de resultat
        self._creer_carte(
            grid, 1, 0,
            titre="Compte de Resultat",
            description="Produits - Charges = Resultat net de l'exercice. Vue synthetique de la performance.",
            couleur="#27ae60",
            on_generer=self._generer_compte_resultat,
        )

        # Carte 5 : Bilan
        self._creer_carte(
            grid, 1, 1,
            titre="Bilan",
            description="Situation patrimoniale a la date de cloture : Actif et Passif (SYSCOHADA).",
            couleur="#e74c3c",
            on_generer=self._generer_bilan,
        )

        # Carte 6 : Tresorerie
        self._creer_carte(
            grid, 1, 2,
            titre="Etat de Tresorerie",
            description="Flux d'encaissements et de decaissements de la periode, solde de tresorerie.",
            couleur="#16a085",
            on_generer=self._generer_tresorerie,
        )

    def _creer_carte(self, parent, row, col, titre, description, couleur, on_generer):
        carte = ctk.CTkFrame(parent, fg_color="white", corner_radius=12,
                             border_width=2, border_color=couleur)
        carte.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        ctk.CTkLabel(
            carte, text=titre,
            font=("Segoe UI", 13, "bold"),
            text_color=couleur,
            wraplength=250,
        ).pack(pady=(15, 6), padx=10)

        ctk.CTkLabel(
            carte, text=description,
            font=("Segoe UI", 10),
            text_color="#666666",
            wraplength=250,
            justify="left",
        ).pack(padx=10, pady=(0, 10), fill="both", expand=True)

        ctk.CTkButton(
            carte,
            text="Generer",
            font=("Segoe UI", 12, "bold"),
            fg_color=couleur,
            hover_color=couleur,
            height=38,
            command=on_generer,
        ).pack(padx=10, pady=(0, 15), fill="x")

    # ================== PERIODES RAPIDES ==================
    def _periode_mois_actuel(self):
        now = datetime.now()
        debut = now.replace(day=1).strftime("%Y-%m-%d")
        fin = now.strftime("%Y-%m-%d")

        self.entree_debut.delete(0, "end")
        self.entree_debut.insert(0, debut)
        self.entree_fin.delete(0, "end")
        self.entree_fin.insert(0, fin)

    def _periode_annee_actuelle(self):
        annee = datetime.now().year
        self.entree_debut.delete(0, "end")
        self.entree_debut.insert(0, f"{annee}-01-01")
        self.entree_fin.delete(0, "end")
        self.entree_fin.insert(0, f"{annee}-12-31")

    def _get_periode(self):
        debut = self.entree_debut.get().strip()
        fin = self.entree_fin.get().strip()

        if not debut or not fin:
            messagebox.showerror("Erreur", "Veuillez saisir les 2 dates (debut et fin).")
            return None, None

        try:
            datetime.strptime(debut, "%Y-%m-%d")
            datetime.strptime(fin, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror(
                "Format invalide",
                "Format attendu : AAAA-MM-JJ\n\n"
                "Exemple : 2025-01-01"
            )
            return None, None

        return debut, fin

    # ================== GENERATION ==================
    def _generer_journal(self):
        debut, fin = self._get_periode()
        if not debut:
            return
        try:
            donnees = etat_journal(debut, fin)
            chemin = pdf_journal(donnees)
            PdfViewerWindow(self, chemin, titre="Journal General")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def _generer_grand_livre(self):
        debut, fin = self._get_periode()
        if not debut:
            return
        try:
            donnees = etat_grand_livre(debut, fin)
            chemin = pdf_grand_livre(donnees)
            PdfViewerWindow(self, chemin, titre="Grand Livre")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def _generer_balance(self):
        debut, fin = self._get_periode()
        if not debut:
            return
        try:
            donnees = etat_balance(debut, fin)
            chemin = pdf_balance(donnees)
            PdfViewerWindow(self, chemin, titre="Balance Generale")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def _generer_compte_resultat(self):
        debut, fin = self._get_periode()
        if not debut:
            return
        try:
            donnees = etat_compte_resultat(debut, fin)
            chemin = pdf_compte_resultat(donnees)
            PdfViewerWindow(self, chemin, titre="Compte de Resultat")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def _generer_bilan(self):
        debut, fin = self._get_periode()
        if not debut:
            return
        try:
            donnees = etat_bilan(debut, fin)
            chemin = pdf_bilan(donnees)
            PdfViewerWindow(self, chemin, titre="Bilan")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def _generer_tresorerie(self):
        debut, fin = self._get_periode()
        if not debut:
            return
        try:
            donnees = etat_tresorerie(debut, fin)
            chemin = pdf_tresorerie(donnees)
            PdfViewerWindow(self, chemin, titre="Etat de Tresorerie")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")