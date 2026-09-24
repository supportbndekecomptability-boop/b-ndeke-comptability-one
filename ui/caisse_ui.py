"""
Interface Caisse (Eleves + Personnel)
Avec filtrage des totaux selon le role de l'utilisateur.
"""
import customtkinter as ctk
from config import COLOR_NAVY, COLOR_GOLD, format_montant
from core.paiements import (
    total_caisse_eleves, total_caisse_personnel,
    total_caisse_eleves_jour, total_caisse_personnel_jour,
    total_caisse_eleves_mois, total_caisse_personnel_mois,
)
from core.permissions import get_role


class CaissePage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")
        self.utilisateur = utilisateur or {}
        self._construire_interface()

    # ================== TOTAUX FILTRES ==================
    def _totaux(self):
        """
        Retourne les totaux filtres selon le role :
        - caissier : uniquement SES operations
        - comptable : uniquement les operations des caissiers
        - admin / gestionnaire / directeur / prefet : tout
        """
        role = get_role(self.utilisateur)

        # Sans filtre
        if role in ("admin", "gestionnaire", "directeur", "prefet"):
            return {
                "eleves": total_caisse_eleves(),
                "eleves_jour": total_caisse_eleves_jour(),
                "eleves_mois": total_caisse_eleves_mois(),
                "personnel": total_caisse_personnel(),
                "personnel_jour": total_caisse_personnel_jour(),
                "personnel_mois": total_caisse_personnel_mois(),
            }

        # Filtre pour caissier / comptable
        try:
            from database import get_connection
            c = get_connection()
            cur = c.cursor()

            if role == "caissier":
                uid = self.utilisateur.get("id")
                if not uid:
                    raise Exception("ID caissier introuvable")
                where_el = f"WHERE utilisateur_id = {uid}"
                where_pe = f"WHERE utilisateur_id = {uid}"
            elif role == "comptable":
                sous_req = "(SELECT id FROM utilisateurs WHERE LOWER(role)='caissier')"
                where_el = f"WHERE utilisateur_id IN {sous_req}"
                where_pe = f"WHERE utilisateur_id IN {sous_req}"
            else:
                raise Exception(f"Role inconnu : {role}")

            def _sum(table, where, extra=""):
                suffix = f" AND {extra}" if extra else ""
                cur.execute(
                    f"SELECT COALESCE(SUM(montant), 0) AS t "
                    f"FROM {table} {where}{suffix}"
                )
                return cur.fetchone()["t"] or 0

            totaux = {
                "eleves": _sum("paiements_eleves", where_el),
                "eleves_jour": _sum("paiements_eleves", where_el,
                                    "date(date_paiement) = date('now')"),
                "eleves_mois": _sum("paiements_eleves", where_el,
                                    "strftime('%Y-%m', date_paiement) = strftime('%Y-%m', 'now')"),
                "personnel": _sum("paiements_personnel", where_pe),
                "personnel_jour": _sum("paiements_personnel", where_pe,
                                       "date(date_paiement) = date('now')"),
                "personnel_mois": _sum("paiements_personnel", where_pe,
                                       "strftime('%Y-%m', date_paiement) = strftime('%Y-%m', 'now')"),
            }
            c.close()
            return totaux

        except Exception as e:
            print(f"[CAISSE] Filtrage impossible ({e}) - affichage global")
            return {
                "eleves": total_caisse_eleves(),
                "eleves_jour": total_caisse_eleves_jour(),
                "eleves_mois": total_caisse_eleves_mois(),
                "personnel": total_caisse_personnel(),
                "personnel_jour": total_caisse_personnel_jour(),
                "personnel_mois": total_caisse_personnel_mois(),
            }

    # ================== INTERFACE ==================
    def _construire_interface(self):
        # Badge role
        role = get_role(self.utilisateur)
        if role == "caissier":
            info_role = "Vue : vos propres operations uniquement"
            couleur_role = "#3498db"
        elif role == "comptable":
            info_role = "Vue : operations des caissiers uniquement"
            couleur_role = "#e67e22"
        else:
            info_role = "Vue : toutes les operations"
            couleur_role = "#27ae60"

        # Titre + badge
        ligne_titre = ctk.CTkFrame(self, fg_color="transparent")
        ligne_titre.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(
            ligne_titre,
            text="Caisse",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        ctk.CTkLabel(
            ligne_titre,
            text=info_role,
            font=("Segoe UI", 10, "italic"),
            text_color=couleur_role,
        ).pack(side="right", pady=(8, 0))

        ctk.CTkLabel(
            self,
            text="Situation des encaissements et decaissements",
            font=("Segoe UI", 13),
            text_color="#666666",
        ).pack(anchor="w", pady=(0, 20))

        # Recuperer les totaux filtres
        t = self._totaux()

        # ===== 2 GRANDES CARTES =====
        cartes = ctk.CTkFrame(self, fg_color="transparent")
        cartes.pack(fill="x", pady=(0, 20))

        # --- Caisse Eleves ---
        carte_el = ctk.CTkFrame(cartes, fg_color="white", corner_radius=15,
                                border_width=2, border_color="#27ae60")
        carte_el.pack(side="left", expand=True, fill="both", padx=(0, 8))

        ctk.CTkLabel(
            carte_el,
            text="CAISSE ELEVES",
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
            text=format_montant(t["eleves"]),
            font=("Segoe UI", 32, "bold"),
            text_color="#27ae60",
        ).pack(pady=(5, 20))

        details_el = ctk.CTkFrame(carte_el, fg_color="#F0FFF4", corner_radius=8)
        details_el.pack(fill="x", padx=15, pady=(0, 20))

        ctk.CTkLabel(
            details_el,
            text=f"Aujourd'hui : {format_montant(t['eleves_jour'])}",
            font=("Segoe UI", 12, "bold"),
            text_color="#2d7a2d",
            anchor="w",
        ).pack(padx=15, pady=(10, 3), fill="x")

        ctk.CTkLabel(
            details_el,
            text=f"Ce mois : {format_montant(t['eleves_mois'])}",
            font=("Segoe UI", 12, "bold"),
            text_color="#2d7a2d",
            anchor="w",
        ).pack(padx=15, pady=(0, 10), fill="x")

        # --- Caisse Personnel ---
        carte_pe = ctk.CTkFrame(cartes, fg_color="white", corner_radius=15,
                                border_width=2, border_color="#e67e22")
        carte_pe.pack(side="left", expand=True, fill="both", padx=(8, 0))

        ctk.CTkLabel(
            carte_pe,
            text="CAISSE PERSONNEL",
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
            text=format_montant(t["personnel"]),
            font=("Segoe UI", 32, "bold"),
            text_color="#e67e22",
        ).pack(pady=(5, 20))

        details_pe = ctk.CTkFrame(carte_pe, fg_color="#FFF4E6", corner_radius=8)
        details_pe.pack(fill="x", padx=15, pady=(0, 20))

        ctk.CTkLabel(
            details_pe,
            text=f"Aujourd'hui : {format_montant(t['personnel_jour'])}",
            font=("Segoe UI", 12, "bold"),
            text_color="#b35c00",
            anchor="w",
        ).pack(padx=15, pady=(10, 3), fill="x")

        ctk.CTkLabel(
            details_pe,
            text=f"Ce mois : {format_montant(t['personnel_mois'])}",
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

        solde_net = t["eleves"] - t["personnel"]
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