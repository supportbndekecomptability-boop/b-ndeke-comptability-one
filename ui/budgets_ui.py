"""
Page Budgets - Parametres
3 grands budgets : PRIME, INVESTISSEMENT, FONCTIONNEMENT
Budget total : auto (frais eleves - insolvabilite) ou manuel (- insolvabilite aussi)
"""
import customtkinter as ctk
from tkinter import messagebox
from config import COLOR_NAVY, format_montant, CURRENCY_SYMBOL
from core.budgets import (
    get_budgets, set_mode_auto, set_budget_manuel,
    set_pourcentage_budget,
    set_pourcentage_sous_categorie, ajouter_sous_categorie,
    supprimer_sous_categorie, verifier_total_budgets,
    verifier_sous_categories, liste_budgets, vider_tout,
    calculer_budget_auto, calculer_budget_auto_brut,
    set_taux_insolvabilite, get_taux_insolvabilite,
)


class BudgetsPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")

        self.utilisateur = utilisateur or {}

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self.entrees_pct_budget = {}
        self.entrees_pct_sous = {}
        self.label_montants = {}
        self.label_montants_sous = {}

        self._construire()

    def _construire(self):
        ctk.CTkLabel(
            self.scroll, text="Repartition budgetaire",
            font=("Segoe UI", 20, "bold"),
            text_color=COLOR_NAVY,
        ).pack(anchor="w", pady=(5, 3))

        ctk.CTkLabel(
            self.scroll,
            text=(
                "Definissez votre budget annuel et repartissez-le entre les 3 grands "
                "postes. Chaque poste est divise en % du total, et chaque sous-categorie "
                "en % du poste parent."
            ),
            font=("Segoe UI", 10),
            text_color="#666666",
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(0, 15))

        # ===== BUDGET TOTAL =====
        cadre_total = ctk.CTkFrame(self.scroll, fg_color="#F0F7FF", corner_radius=10)
        cadre_total.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            cadre_total, text="BUDGET TOTAL ANNUEL",
            font=("Segoe UI", 12, "bold"),
            text_color=COLOR_NAVY,
        ).pack(anchor="w", padx=15, pady=(12, 3))

        ctk.CTkLabel(
            cadre_total,
            text="(le taux d'insolvabilite est deduit dans les 2 modes)",
            font=("Segoe UI", 9),
            text_color="#666666",
        ).pack(anchor="w", padx=15, pady=(0, 8))

        # Choix : auto ou manuel
        self.var_auto = ctk.StringVar(value="1")

        ligne_mode = ctk.CTkFrame(cadre_total, fg_color="transparent")
        ligne_mode.pack(fill="x", padx=15, pady=(0, 6))

        ctk.CTkRadioButton(
            ligne_mode,
            text="Calcul automatique (frais des eleves)",
            variable=self.var_auto, value="1",
            font=("Segoe UI", 11, "bold"),
            text_color=COLOR_NAVY,
            command=self._on_change_mode,
        ).pack(side="left", padx=(0, 20))

        ctk.CTkRadioButton(
            ligne_mode,
            text="Montant manuel",
            variable=self.var_auto, value="0",
            font=("Segoe UI", 11, "bold"),
            text_color=COLOR_NAVY,
            command=self._on_change_mode,
        ).pack(side="left")

        # Taux d'insolvabilite
        ligne_insolv = ctk.CTkFrame(cadre_total, fg_color="transparent")
        ligne_insolv.pack(fill="x", padx=15, pady=(8, 6))

        ctk.CTkLabel(
            ligne_insolv,
            text="Taux d'insolvabilite :",
            font=("Segoe UI", 11, "bold"),
            text_color="#333333",
        ).pack(side="left")

        self.entree_insolv = ctk.CTkEntry(
            ligne_insolv,
            font=("Segoe UI", 12, "bold"),
            height=32,
            width=70,
            placeholder_text="0",
        )
        self.entree_insolv.pack(side="left", padx=(8, 3))
        self.entree_insolv.bind("<KeyRelease>", lambda e: self._maj_totaux())
        self.entree_insolv.bind("<FocusOut>", lambda e: self._sauver_insolv())

        ctk.CTkLabel(
            ligne_insolv,
            text="%  (frais non recuperables)",
            font=("Segoe UI", 10),
            text_color="#666666",
        ).pack(side="left")

        # Montant calcule (net) - ligne
        ligne_auto = ctk.CTkFrame(cadre_total, fg_color="transparent")
        ligne_auto.pack(fill="x", padx=15, pady=(3, 3))

        ctk.CTkLabel(
            ligne_auto,
            text="Montant calcule (net) :",
            font=("Segoe UI", 11),
            text_color="#666666",
        ).pack(side="left")

        self.label_budget_auto = ctk.CTkLabel(
            ligne_auto,
            text="0",
            font=("Segoe UI", 13, "bold"),
            text_color="#27ae60",
        )
        self.label_budget_auto.pack(side="left", padx=(8, 0))

        self.label_insolv_detail = ctk.CTkLabel(
            ligne_auto,
            text="",
            font=("Segoe UI", 10, "italic"),
            text_color="#e67e22",
        )
        self.label_insolv_detail.pack(side="left", padx=(10, 0))

        ctk.CTkButton(
            ligne_auto,
            text="Actualiser",
            font=("Segoe UI", 9),
            fg_color="#e0e0e0", text_color="#333333",
            hover_color="#c0c0c0", height=26, width=80,
            command=self._actualiser_auto,
        ).pack(side="right")

        # Montant manuel
        ligne_total = ctk.CTkFrame(cadre_total, fg_color="transparent")
        ligne_total.pack(fill="x", padx=15, pady=(3, 12))

        ctk.CTkLabel(
            ligne_total,
            text=f"Montant manuel ({CURRENCY_SYMBOL}) :",
            font=("Segoe UI", 11, "bold"),
            text_color="#333333",
        ).pack(side="left")

        self.entree_budget_total = ctk.CTkEntry(
            ligne_total,
            font=("Segoe UI", 13, "bold"),
            height=38,
            width=200,
            placeholder_text="Ex: 10000000",
        )
        self.entree_budget_total.pack(side="left", padx=(8, 8))
        self.entree_budget_total.bind("<KeyRelease>", lambda e: self._maj_totaux())

        ctk.CTkButton(
            ligne_total,
            text="Appliquer",
            font=("Segoe UI", 11, "bold"),
            fg_color=COLOR_NAVY, hover_color="#1a3d75",
            height=38,
            command=self._enregistrer_budget_total,
        ).pack(side="left")

        ctk.CTkButton(
            ligne_total,
            text="Tout reinitialiser",
            font=("Segoe UI", 10),
            fg_color="#e74c3c", hover_color="#c0392b",
            height=38,
            command=self._reinitialiser_tout,
        ).pack(side="left", padx=(8, 0))

        # ===== 3 BLOCS BUDGETS =====
        for key, label, couleur in liste_budgets():
            self._construire_bloc_budget(key, label, couleur)

        # ===== VERIFICATION =====
        cadre_verif = ctk.CTkFrame(self.scroll, fg_color="#F5F5F5", corner_radius=10)
        cadre_verif.pack(fill="x", pady=(10, 5))

        self.label_verif = ctk.CTkLabel(
            cadre_verif, text="",
            font=("Segoe UI", 11, "bold"),
            text_color="#666666",
        )
        self.label_verif.pack(padx=15, pady=12, anchor="w")

        ctk.CTkButton(
            self.scroll,
            text="Sauvegarder tous les pourcentages",
            font=("Segoe UI", 12, "bold"),
            fg_color="#27ae60", hover_color="#229954",
            height=44,
            command=self._enregistrer_tous,
        ).pack(fill="x", pady=(5, 20))

        self._charger_valeurs()

    # =========================================================
    def _construire_bloc_budget(self, key, label, couleur):
        cadre = ctk.CTkFrame(self.scroll, fg_color="white", corner_radius=10,
                            border_width=2, border_color=couleur)
        cadre.pack(fill="x", pady=(0, 12))

        entete = ctk.CTkFrame(cadre, fg_color=couleur, corner_radius=8)
        entete.pack(fill="x", padx=8, pady=(8, 8))

        ctk.CTkLabel(
            entete, text=label,
            font=("Segoe UI", 13, "bold"),
            text_color="white",
        ).pack(side="left", padx=12, pady=8)

        self.label_montants[key] = ctk.CTkLabel(
            entete, text="",
            font=("Segoe UI", 12, "bold"),
            text_color="white",
        )
        self.label_montants[key].pack(side="right", padx=12, pady=8)

        ligne_pct = ctk.CTkFrame(cadre, fg_color="#FAFAFA", corner_radius=6)
        ligne_pct.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(
            ligne_pct,
            text="Pourcentage du budget total :",
            font=("Segoe UI", 11, "bold"),
            text_color="#333333",
        ).pack(side="left", padx=(12, 8), pady=10)

        e_pct = ctk.CTkEntry(
            ligne_pct,
            font=("Segoe UI", 12, "bold"),
            height=34,
            width=80,
        )
        e_pct.pack(side="left", pady=8)
        e_pct.bind("<KeyRelease>", lambda ev: self._maj_totaux())
        self.entrees_pct_budget[key] = e_pct

        ctk.CTkLabel(
            ligne_pct, text=" %",
            font=("Segoe UI", 12, "bold"),
            text_color=couleur,
        ).pack(side="left", padx=(4, 12))

        ctk.CTkLabel(
            cadre, text="Sous-categories (% du budget parent)",
            font=("Segoe UI", 10, "bold"),
            text_color="#666666",
        ).pack(anchor="w", padx=15, pady=(5, 3))

        self.entrees_pct_sous[key] = {}
        self.label_montants_sous[key] = {}

        data = get_budgets()
        sous_data = data.get(key, {}).get("sous_categories", {})

        for sous_nom in sous_data.keys():
            self._ajouter_ligne_sous(cadre, key, sous_nom, couleur)

        ctk.CTkButton(
            cadre,
            text="+ Ajouter une sous-categorie",
            font=("Segoe UI", 10),
            fg_color="#e0e0e0", text_color="#333333",
            hover_color="#c0c0c0",
            height=30,
            command=lambda k=key: self._ajouter_sous_categorie(k),
        ).pack(padx=15, pady=(8, 10), anchor="w")

        label_verif_sous = ctk.CTkLabel(
            cadre, text="",
            font=("Segoe UI", 10, "bold"),
            text_color="#888888",
        )
        label_verif_sous.pack(anchor="w", padx=15, pady=(0, 10))
        self.label_montants_sous[key]["__verif__"] = label_verif_sous

    def _ajouter_ligne_sous(self, parent, budget_key, nom, couleur):
        ligne = ctk.CTkFrame(parent, fg_color="#FAFAFA", corner_radius=4)
        ligne.pack(fill="x", padx=12, pady=2)

        ctk.CTkLabel(
            ligne, text=nom,
            font=("Segoe UI", 10),
            text_color="#333333",
            anchor="w",
        ).pack(side="left", padx=(10, 5), pady=6, fill="x", expand=True)

        label_m = ctk.CTkLabel(
            ligne, text="0",
            font=("Segoe UI", 10, "bold"),
            text_color=couleur,
            width=130, anchor="e",
        )
        label_m.pack(side="left", padx=(5, 5), pady=6)

        e_pct = ctk.CTkEntry(
            ligne,
            font=("Segoe UI", 10, "bold"),
            height=28,
            width=60,
        )
        e_pct.pack(side="left", padx=(5, 2), pady=4)
        e_pct.bind("<KeyRelease>", lambda ev, k=budget_key: self._maj_totaux())

        ctk.CTkLabel(
            ligne, text="%",
            font=("Segoe UI", 10, "bold"),
            text_color="#666666",
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            ligne, text="X",
            font=("Segoe UI", 10, "bold"),
            width=28, height=26,
            fg_color="#e74c3c", hover_color="#c0392b",
            command=lambda k=budget_key, n=nom: self._supprimer_sous(k, n),
        ).pack(side="right", padx=(2, 8), pady=4)

        self.entrees_pct_sous[budget_key][nom] = e_pct
        self.label_montants_sous[budget_key][nom] = label_m

    # =========================================================
    def _on_change_mode(self):
        try:
            if self.var_auto.get() == "1":
                self.entree_budget_total.configure(state="disabled")
            else:
                self.entree_budget_total.configure(state="normal")
        except Exception:
            pass
        self._maj_totaux()

    def _sauver_insolv(self):
        """Sauvegarde automatiquement le taux d'insolvabilite."""
        try:
            taux = float(self.entree_insolv.get().strip() or 0)
            if taux < 0:
                taux = 0
            if taux > 100:
                taux = 100
            set_taux_insolvabilite(taux)
            print(f"[BUDGET] Taux sauvegarde : {taux}%")
        except Exception as e:
            print(f"[BUDGET] Erreur sauvegarde taux : {e}")

    def _actualiser_auto(self):
        try:
            self._sauver_insolv()
            self._maj_totaux()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def _charger_valeurs(self):
        data = get_budgets()

        # Mode
        utiliser_auto = data.get("utiliser_auto", True)
        self.var_auto.set("1" if utiliser_auto else "0")

        # Taux
        taux = data.get("taux_insolvabilite", 0)
        self.entree_insolv.delete(0, "end")
        if taux > 0:
            self.entree_insolv.insert(0, str(int(taux)))

        # Montant manuel
        self.entree_budget_total.delete(0, "end")
        manuel = data.get("budget_total_manuel", 0)
        if manuel > 0:
            self.entree_budget_total.insert(0, str(int(manuel)))

        self._on_change_mode()

        # Les 3 budgets
        for key, _, _ in liste_budgets():
            b = data.get(key, {})
            self.entrees_pct_budget[key].delete(0, "end")
            self.entrees_pct_budget[key].insert(0, str(int(b.get("pourcentage", 0))))

            sous = b.get("sous_categories", {})
            for nom, info in sous.items():
                if nom in self.entrees_pct_sous.get(key, {}):
                    self.entrees_pct_sous[key][nom].delete(0, "end")
                    self.entrees_pct_sous[key][nom].insert(
                        0, str(int(info.get("pourcentage", 0)))
                    )

        self._maj_totaux()

    def _get_brut(self):
        """Retourne le montant brut (avant taux) selon le mode."""
        if self.var_auto.get() == "1":
            try:
                return calculer_budget_auto_brut()
            except Exception:
                return 0
        else:
            try:
                s = self.entree_budget_total.get().strip().replace(" ", "").replace(",", "")
                return float(s) if s else 0
            except Exception:
                return 0

    def _get_taux(self):
        try:
            taux = float(self.entree_insolv.get().strip() or 0)
        except Exception:
            taux = 0
        if taux < 0:
            taux = 0
        if taux > 100:
            taux = 100
        return taux

    def _get_budget_total(self):
        """Montant NET (brut - taux)."""
        brut = self._get_brut()
        taux = self._get_taux()
        return brut * (1 - taux / 100.0)

    def _maj_totaux(self):
        brut = self._get_brut()
        taux = self._get_taux()
        total = brut * (1 - taux / 100.0)

        # Mettre a jour le label net + detail
        try:
            self.label_budget_auto.configure(text=format_montant(total))
            if taux > 0 and brut > 0:
                deduction = brut * taux / 100.0
                self.label_insolv_detail.configure(
                    text=f"({format_montant(brut)} - {format_montant(deduction)})"
                )
            else:
                self.label_insolv_detail.configure(text="")
        except Exception:
            pass

        # Les 3 budgets
        total_pct = 0
        for key, _, _ in liste_budgets():
            try:
                pct = float(self.entrees_pct_budget[key].get().strip() or 0)
            except Exception:
                pct = 0
            total_pct += pct

            montant_parent = total * pct / 100.0

            if key in self.label_montants:
                self.label_montants[key].configure(
                    text=format_montant(montant_parent)
                )

            total_pct_sous = 0
            for nom, e_pct in self.entrees_pct_sous.get(key, {}).items():
                try:
                    pct_sous = float(e_pct.get().strip() or 0)
                except Exception:
                    pct_sous = 0
                total_pct_sous += pct_sous

                montant_sous = montant_parent * pct_sous / 100.0
                label = self.label_montants_sous.get(key, {}).get(nom)
                if label:
                    label.configure(text=format_montant(montant_sous))

            verif_label = self.label_montants_sous.get(key, {}).get("__verif__")
            if verif_label:
                if abs(total_pct_sous - 100) < 0.01 and total_pct_sous > 0:
                    verif_label.configure(
                        text=f"Sous-categories : {total_pct_sous:.0f}% OK",
                        text_color="#27ae60",
                    )
                elif total_pct_sous == 0:
                    verif_label.configure(
                        text="Sous-categories : --",
                        text_color="#999999",
                    )
                else:
                    verif_label.configure(
                        text=f"Sous-categories : {total_pct_sous:.0f}% (doit faire 100%)",
                        text_color="#e74c3c",
                    )

        if abs(total_pct - 100) < 0.01 and total_pct > 0:
            self.label_verif.configure(
                text=f"Total des 3 budgets : {total_pct:.0f}% - Repartition correcte",
                text_color="#27ae60",
            )
        elif total_pct == 0:
            self.label_verif.configure(
                text="Saisissez des pourcentages pour les 3 budgets.",
                text_color="#999999",
            )
        else:
            self.label_verif.configure(
                text=f"Total des 3 budgets : {total_pct:.0f}% (doit faire 100%)",
                text_color="#e74c3c",
            )

    # =========================================================
    def _enregistrer_budget_total(self):
        # 1. Sauvegarder le taux
        try:
            taux = float(self.entree_insolv.get().strip() or 0)
            set_taux_insolvabilite(taux)
        except Exception:
            pass

        # 2. Sauvegarder le mode + montant
        if self.var_auto.get() == "1":
            set_mode_auto(True)
            messagebox.showinfo(
                "Succes",
                "Mode automatique active.\n\n"
                "Le budget total est calcule depuis les frais des eleves\n"
                "(moins le taux d'insolvabilite)."
            )
        else:
            try:
                s = self.entree_budget_total.get().strip().replace(" ", "").replace(",", "")
                montant = float(s) if s else 0
            except Exception:
                messagebox.showerror("Erreur", "Montant invalide.")
                return
            if montant < 0:
                messagebox.showerror("Erreur", "Le montant doit etre positif.")
                return
            set_budget_manuel(montant)
            messagebox.showinfo(
                "Succes",
                f"Montant manuel enregistre : {format_montant(montant)}\n\n"
                f"Le taux d'insolvabilite ({taux}%) sera deduit."
            )
        self._maj_totaux()

    def _enregistrer_tous(self):
        total_pct = verifier_total_budgets()
        if abs(total_pct - 100) > 0.01:
            rep = messagebox.askyesno(
                "Attention",
                f"Le total des 3 budgets fait {total_pct:.0f}% (doit faire 100%).\n\n"
                f"Voulez-vous quand meme enregistrer ?"
            )
            if not rep:
                return

        # Taux
        try:
            taux = float(self.entree_insolv.get().strip() or 0)
            set_taux_insolvabilite(taux)
        except Exception:
            pass

        # Mode + budget total
        if self.var_auto.get() == "1":
            set_mode_auto(True)
        else:
            try:
                s = self.entree_budget_total.get().strip().replace(" ", "").replace(",", "")
                m = float(s) if s else 0
                set_budget_manuel(m)
            except Exception:
                pass

        for key, _, _ in liste_budgets():
            try:
                pct = float(self.entrees_pct_budget[key].get().strip() or 0)
            except Exception:
                pct = 0
            set_pourcentage_budget(key, pct)

            for nom, e_pct in self.entrees_pct_sous[key].items():
                try:
                    pct_sous = float(e_pct.get().strip() or 0)
                except Exception:
                    pct_sous = 0
                set_pourcentage_sous_categorie(key, nom, pct_sous)

        self._maj_totaux()
        messagebox.showinfo("Succes", "Tous les pourcentages ont ete enregistres.")

    def _ajouter_sous_categorie(self, budget_key):
        from tkinter import simpledialog

        nom = simpledialog.askstring(
            "Nouvelle sous-categorie",
            "Nom de la sous-categorie :",
            parent=self,
        )
        if not nom or not nom.strip():
            return

        nom = nom.strip()

        if ajouter_sous_categorie(budget_key, nom, 0):
            self._recharger_page()
        else:
            messagebox.showerror("Erreur", "Impossible d'ajouter la sous-categorie.")

    def _supprimer_sous(self, budget_key, nom):
        rep = messagebox.askyesno(
            "Confirmation",
            f"Supprimer la sous-categorie :\n\n{nom} ?"
        )
        if not rep:
            return

        if supprimer_sous_categorie(budget_key, nom):
            self._recharger_page()
        else:
            messagebox.showerror("Erreur", "Impossible de supprimer.")

    def _reinitialiser_tout(self):
        rep = messagebox.askyesno(
            "Confirmation",
            "Reinitialiser TOUT le budget ?\n\n"
            "Toutes les valeurs personnalisees seront perdues et "
            "remplacees par les valeurs par defaut."
        )
        if rep:
            vider_tout()
            self._recharger_page()
            messagebox.showinfo("Succes", "Budget reinitialise.")

    def _recharger_page(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self.entrees_pct_budget = {}
        self.entrees_pct_sous = {}
        self.label_montants = {}
        self.label_montants_sous = {}
        self._construire()