"""
Interface Caisse (Eleves + Personnel)
"""
import customtkinter as ctk
from config import COLOR_NAVY, COLOR_GOLD, format_montant
from core.paiements import (
    total_caisse_eleves, total_caisse_personnel,
    total_caisse_eleves_jour, total_caisse_personnel_jour,
    total_caisse_eleves_mois, total_caisse_personnel_mois,
)


class CaissePage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._construire_interface()

    def _construire_interface(self):
        # Titre
        ctk.CTkLabel(
            self,
            text="Caisse",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_NAVY,
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            self,
            text="Situation des encaissements et decaissements",
            font=("Segoe UI", 13),
            text_color="#666666",
        ).pack(anchor="w", pady=(0, 20))

        # ===== 2 GRANDES CARTES (CAISSE ELEVES + CAISSE PERSONNEL) =====
        cartes = ctk.CTkFrame(self, fg_color="transparent")
        cartes.pack(fill="x", pady=(0, 20))

        # Caisse Eleves
        carte_el = ctk.CTkFrame(cartes, fg_color="white", corner_radius=15, border_width=2,
                                border_color="#27ae60")
        carte_el.pack(side="left", expand=True, fill="both", padx=(0, 8))

        ctk.CTkLabel(
            carte_el,
            text="🎓  CAISSE ELEVES",
            font=("Segoe UI", 16, "bold"),
            text_color="#27ae60",
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            carte_el,
            text="Total encaisse (global)",
            font=("Segoe UI", 11),
            text_color="#888888",
        ).pack()

        ctk.CTkLabel(
            carte_el,
            text=format_montant(total_caisse_eleves()),
            font=("Segoe UI", 32, "bold"),
            text_color="#27ae60",
        ).pack(pady=(5, 20))

        # Détails
        details_el = ctk.CTkFrame(carte_el, fg_color="#F0FFF4", corner_radius=8)
        details_el.pack(fill="x", padx=15, pady=(0, 20))

        ctk.CTkLabel(
            details_el,
            text=f"Aujourd'hui : {format_montant(total_caisse_eleves_jour())}",
            font=("Segoe UI", 12, "bold"),
            text_color="#2d7a2d",
            anchor="w",
        ).pack(padx=15, pady=(10, 3), fill="x")

        ctk.CTkLabel(
            details_el,
            text=f"Ce mois : {format_montant(total_caisse_eleves_mois())}",
            font=("Segoe UI", 12, "bold"),
            text_color="#2d7a2d",
            anchor="w",
        ).pack(padx=15, pady=(0, 10), fill="x")

        # Caisse Personnel
        carte_pe = ctk.CTkFrame(cartes, fg_color="white", corner_radius=15, border_width=2,
                                border_color="#e67e22")
        carte_pe.pack(side="left", expand=True, fill="both", padx=(8, 0))

        ctk.CTkLabel(
            carte_pe,
            text="👨‍🏫  CAISSE PERSONNEL",
            font=("Segoe UI", 16, "bold"),
            text_color="#e67e22",
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            carte_pe,
            text="Total decaisse (global)",
            font=("Segoe UI", 11),
            text_color="#888888",
        ).pack()

        ctk.CTkLabel(
            carte_pe,
            text=format_montant(total_caisse_personnel()),
            font=("Segoe UI", 32, "bold"),
            text_color="#e67e22",
        ).pack(pady=(5, 20))

        details_pe = ctk.CTkFrame(carte_pe, fg_color="#FFF4E6", corner_radius=8)
        details_pe.pack(fill="x", padx=15, pady=(0, 20))

        ctk.CTkLabel(
            details_pe,
            text=f"Aujourd'hui : {format_montant(total_caisse_personnel_jour())}",
            font=("Segoe UI", 12, "bold"),
            text_color="#b35c00",
            anchor="w",
        ).pack(padx=15, pady=(10, 3), fill="x")

        ctk.CTkLabel(
            details_pe,
            text=f"Ce mois : {format_montant(total_caisse_personnel_mois())}",
            font=("Segoe UI", 12, "bold"),
            text_color="#b35c00",
            anchor="w",
        ).pack(padx=15, pady=(0, 10), fill="x")

        # ===== SOLDE NET =====
        carte_net = ctk.CTkFrame(self, fg_color=COLOR_NAVY, corner_radius=15)
        carte_net.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            carte_net,
            text="SOLDE NET DE CAISSE",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_GOLD,
        ).pack(pady=(20, 5))

        solde_net = total_caisse_eleves() - total_caisse_personnel()
        couleur_net = "#27ae60" if solde_net >= 0 else "#e74c3c"

        ctk.CTkLabel(
            carte_net,
            text="Recettes eleves - Decaissements personnel",
            font=("Segoe UI", 11),
            text_color="#cccccc",
        ).pack()

        ctk.CTkLabel(
            carte_net,
            text=format_montant(solde_net),
            font=("Segoe UI", 30, "bold"),
            text_color=couleur_net,
        ).pack(pady=(5, 20))