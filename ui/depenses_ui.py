"""
Interface de gestion des depenses
Avec liaison aux sous-categories budgetaires et creation a la volee.
Permissions : admin et gestionnaire uniquement (comptable, caissier, directeur, prefet
              n'ont pas acces a cette page).
"""
import customtkinter as ctk
from tkinter import messagebox, simpledialog
from config import COLOR_NAVY, COLOR_GOLD, format_montant, CURRENCY_SYMBOL
from ui.scroll_frame import HorizontalScrollFrame
from ui.permissions_ui import peut
from core.depenses import (
    ajouter_depense, lister_depenses, modifier_depense,
    supprimer_depense, get_depense, total_depenses,
    total_depenses_jour, total_depenses_mois, CATEGORIES,
    total_depenses_par_sous_categorie,
)
from core.budgets import (
    liste_budgets, get_budgets,
    ajouter_sous_categorie,
)


class DepensesPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")

        self.utilisateur = utilisateur or {}
        self._construire_interface()
        self.rafraichir_tableau()

    # ================== PERMISSIONS ==================
    def _peut_gerer(self):
        return peut(self.utilisateur, "peut_gerer_depenses")

    # ================== INTERFACE ==================
    def _construire_interface(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            top, text="Gestion des depenses",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        # Badge role
        if self._peut_gerer():
            info_role = "Vue : gestion des depenses"
            couleur_role = "#27ae60"
        else:
            info_role = "Vue : lecture seule"
            couleur_role = "#e67e22"

        ctk.CTkLabel(
            top,
            text=info_role,
            font=("Segoe UI", 10, "italic"),
            text_color=couleur_role,
        ).pack(side="right", pady=(8, 0))

        # Bouton "+ Nouvelle depense" : seulement si peut_gerer_depenses
        if self._peut_gerer():
            ctk.CTkButton(
                top, text="+ Nouvelle depense",
                font=("Segoe UI", 13, "bold"),
                fg_color=COLOR_NAVY, hover_color="#1a3d75",
                height=40, command=self._ouvrir_formulaire,
            ).pack(side="right", padx=(0, 15))

        # Cartes KPI
        cartes = ctk.CTkFrame(self, fg_color="transparent")
        cartes.pack(fill="x", pady=(0, 15))

        try:
            total_gen = total_depenses()
            total_jour = total_depenses_jour()
            total_mois = total_depenses_mois()
            nb_total = len(lister_depenses())
        except Exception:
            total_gen = total_jour = total_mois = 0
            nb_total = 0

        for titre, valeur, couleur in [
            ("Total general", format_montant(total_gen), "#e74c3c"),
            ("Aujourd'hui", format_montant(total_jour), "#e67e22"),
            ("Ce mois", format_montant(total_mois), "#c0392b"),
            ("Nombre depenses", str(nb_total), COLOR_NAVY),
        ]:
            carte = ctk.CTkFrame(cartes, fg_color="white", corner_radius=12)
            carte.pack(side="left", expand=True, fill="both", padx=6)

            ctk.CTkLabel(carte, text=titre,
                         font=("Segoe UI", 11, "bold"),
                         text_color="#888888").pack(pady=(15, 3))

            ctk.CTkLabel(carte, text=valeur,
                         font=("Segoe UI", 18, "bold"),
                         text_color=couleur).pack(pady=(0, 15))

        # Recherche
        recherche_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        recherche_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(recherche_frame, text="Recherche :",
                     font=("Segoe UI", 12, "bold"),
                     text_color="#666666").pack(side="left", padx=(15, 5), pady=12)

        self.entree_recherche = ctk.CTkEntry(
            recherche_frame,
            placeholder_text="Libelle, categorie ou budget...",
            font=("Segoe UI", 13),
            border_width=0, fg_color="white", height=35,
        )
        self.entree_recherche.pack(side="left", fill="x", expand=True, padx=5, pady=12)
        self.entree_recherche.bind("<KeyRelease>", lambda e: self.rafraichir_tableau())

        ctk.CTkButton(recherche_frame, text="Effacer",
                      font=("Segoe UI", 11),
                      fg_color="#e0e0e0", text_color="#333333",
                      hover_color="#c0c0c0", width=80, height=32,
                      command=self._effacer_recherche).pack(side="right", padx=15, pady=12)

        # Astuce
        info_frame = ctk.CTkFrame(self, fg_color="#FFF7E0", corner_radius=6)
        info_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            info_frame,
            text="Astuce : liez chaque depense a une sous-categorie budget "
                 "(ex: FONCTIONNEMENT > Papier et cahiers) pour suivre "
                 "l'ecart prevu/reel. Le depassement est autorise mais signale.",
            font=("Segoe UI", 11),
            text_color="#8B6914",
            wraplength=900,
            justify="left",
        ).pack(padx=15, pady=6, anchor="w")

        self.label_compteur = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 12), text_color="#666666",
        )
        self.label_compteur.pack(anchor="w", pady=(0, 10))

        # Tableau
        self.tableau = HorizontalScrollFrame(self, fg_color="white", corner_radius=10)
        self.tableau.pack(fill="both", expand=True)

        self._creer_entete()

    def _creer_entete(self):
        entete = ctk.CTkFrame(self.tableau.interior, fg_color="#f0f0f0", corner_radius=6)
        entete.pack(fill="x", pady=(0, 5))

        colonnes = [
            ("Date", 130),
            ("Categorie", 140),
            ("Libelle", 220),
            ("Budget", 180),
            ("Montant", 110),
        ]

        for nom, largeur in colonnes:
            ctk.CTkLabel(entete, text=nom,
                         font=("Segoe UI", 12, "bold"),
                         text_color=COLOR_NAVY, width=largeur,
                         anchor="w").pack(side="left", padx=5, pady=12)

        # Colonne Actions uniquement si peut_gerer
        if self._peut_gerer():
            ctk.CTkLabel(entete, text="Actions",
                         font=("Segoe UI", 12, "bold"),
                         text_color=COLOR_NAVY, width=90,
                         anchor="center").pack(side="right", padx=5, pady=12)

    def _effacer_recherche(self):
        self.entree_recherche.delete(0, "end")
        self.rafraichir_tableau()

    # ================== TABLEAU ==================
    def rafraichir_tableau(self):
        self.tableau.clear()
        self._creer_entete()

        recherche = self.entree_recherche.get()
        depenses = lister_depenses(recherche)

        self.label_compteur.configure(text=f"{len(depenses)} depense(s)")

        if not depenses:
            ctk.CTkLabel(self.tableau.interior,
                         text="Aucune depense enregistree. Cliquez sur '+ Nouvelle depense'.",
                         font=("Segoe UI", 13),
                         text_color="#999999").pack(pady=40)
            return

        for i, d in enumerate(depenses):
            fond = "#ffffff" if i % 2 == 0 else "#fafafa"
            ligne = ctk.CTkFrame(self.tableau.interior, fg_color=fond, corner_radius=4)
            ligne.pack(fill="x", pady=1)

            try:
                date_str = d["date_depense"][:16].replace("T", " ")
            except Exception:
                date_str = str(d.get("date_depense", ""))[:16]

            sous_cat = d.get("budget_sous_categorie", "") or ""
            if sous_cat:
                couleur_budget = "#9b59b6"
                texte_budget = sous_cat
            else:
                couleur_budget = "#cccccc"
                texte_budget = "(non lie)"

            valeurs = [
                (date_str, 130, "#333333", "normal"),
                (d["categorie"], 140, "#8e44ad", "bold"),
                (d["libelle"], 220, "#333333", "normal"),
                (texte_budget, 180, couleur_budget, "bold"),
                (format_montant(d["montant"]), 110, "#e74c3c", "bold"),
            ]

            for valeur, largeur, couleur, poids in valeurs:
                ctk.CTkLabel(ligne, text=str(valeur),
                             font=("Segoe UI", 12, poids),
                             text_color=couleur,
                             width=largeur, anchor="w").pack(side="left", padx=5, pady=10)

            # Actions conditionnelles
            if not self._peut_gerer():
                continue

            actions = ctk.CTkFrame(ligne, fg_color="transparent", width=90)
            actions.pack(side="right", padx=5)

            ctk.CTkButton(actions, text="M",
                          font=("Segoe UI", 12, "bold"),
                          width=36, height=28,
                          fg_color="#3498db", hover_color="#2980b9",
                          command=lambda dd=d: self._modifier(dd)).pack(side="left", padx=2)

            ctk.CTkButton(actions, text="X",
                          font=("Segoe UI", 12, "bold"),
                          width=36, height=28,
                          fg_color="#e74c3c", hover_color="#c0392b",
                          command=lambda dd=d: self._supprimer(dd)).pack(side="left", padx=2)

    # ================== ACTIONS ==================
    def _ouvrir_formulaire(self, depense=None):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse",
                                 "Vous n'avez pas la permission de gerer les depenses.")
            return
        FormulaireDepense(self, depense=depense,
                          utilisateur=self.utilisateur,
                          on_save=self._recharger_complet)

    def _recharger_complet(self):
        for w in self.winfo_children():
            w.destroy()
        self._construire_interface()
        self.rafraichir_tableau()

    def _modifier(self, d):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        complet = get_depense(d["id"])
        self._ouvrir_formulaire(complet)

    def _supprimer(self, d):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        rep = messagebox.askyesno(
            "Confirmation",
            f"Voulez-vous vraiment supprimer cette depense ?\n\n"
            f"Categorie : {d['categorie']}\n"
            f"Libelle : {d['libelle']}\n"
            f"Montant : {format_montant(d['montant'])}"
        )
        if rep:
            ok, msg = supprimer_depense(d["id"])
            if ok:
                self._recharger_complet()
            else:
                messagebox.showerror("Erreur", msg)


# ============================================================
# FORMULAIRE
# ============================================================
class FormulaireDepense(ctk.CTkToplevel):
    def __init__(self, parent, depense=None, utilisateur=None, on_save=None):
        super().__init__(parent)

        self.depense = depense
        self.utilisateur = utilisateur
        self.on_save = on_save

        self.sous_categories_par_budget = {}
        self.budget_sous_cat_details = {}

        titre = "Modifier une depense" if depense else "Nouvelle depense"
        self.title(titre)

        largeur = 560
        hauteur = min(800, self.winfo_screenheight() - 60)
        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        x = (self.winfo_screenwidth() // 2) - (largeur // 2)
        y = max(10, (self.winfo_screenheight() // 2) - (hauteur // 2))
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")

        self.bind("<Escape>", lambda e: self.destroy())

        self.transient(parent)
        self.after(100, self._activer_grab)

        self._charger_sous_categories()
        self._construire_interface()

    def _activer_grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _charger_sous_categories(self):
        self.sous_categories_par_budget = {}
        self.budget_sous_cat_details = {}
        try:
            data = get_budgets()
            par_sous = total_depenses_par_sous_categorie()

            for key, label, _ in liste_budgets():
                b = data.get(key, {})
                sous_dict = b.get("sous_categories", {})

                self.sous_categories_par_budget[key] = {
                    "label": label,
                    "sous": list(sous_dict.keys()),
                }

                for nom, info in sous_dict.items():
                    prevu = info.get("montant", 0)
                    reel = par_sous.get(nom, 0)
                    self.budget_sous_cat_details[nom] = {
                        "budget": key,
                        "budget_label": label,
                        "prevu": prevu,
                        "reel": reel,
                        "ecart": prevu - reel,
                    }
        except Exception as e:
            print(f"[DEPENSES] Erreur chargement sous-cat : {e}")

    def _construire_interface(self):
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        ligne_titre = ctk.CTkFrame(card, fg_color="transparent")
        ligne_titre.pack(fill="x", padx=15, pady=(10, 5))

        titre = "Modifier une depense" if self.depense else "Nouvelle depense"
        ctk.CTkLabel(ligne_titre, text=titre,
                     font=("Segoe UI", 17, "bold"),
                     text_color=COLOR_NAVY).pack(side="left")

        ctk.CTkButton(ligne_titre, text="X",
                      font=("Segoe UI", 14, "bold"),
                      width=32, height=32,
                      fg_color="#e74c3c", hover_color="#c0392b",
                      command=self.destroy).pack(side="right")

        zone = ctk.CTkScrollableFrame(card, fg_color="transparent", corner_radius=0)
        zone.pack(fill="both", expand=True, padx=5, pady=5)

        self.champs = {}

        ctk.CTkLabel(zone, text="Categorie *",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w").pack(padx=10, pady=(6, 3), fill="x")

        self.combo_categorie = ctk.CTkComboBox(
            zone, values=CATEGORIES,
            font=("Segoe UI", 11), height=36,
        )
        if self.depense and self.depense["categorie"] in CATEGORIES:
            self.combo_categorie.set(self.depense["categorie"])
        else:
            self.combo_categorie.set(CATEGORIES[0])
        self.combo_categorie.pack(padx=10, pady=(0, 6), fill="x")

        ctk.CTkLabel(zone, text="Libelle * (description)",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w").pack(padx=10, pady=(6, 3), fill="x")

        self.entree_libelle = ctk.CTkEntry(
            zone, font=("Segoe UI", 12), height=36,
            placeholder_text="Ex: Achat cahiers pour 5eme",
        )
        if self.depense:
            self.entree_libelle.insert(0, self.depense["libelle"])
        self.entree_libelle.pack(padx=10, pady=(0, 6), fill="x")

        ctk.CTkLabel(zone, text=f"Montant ({CURRENCY_SYMBOL}) *",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w").pack(padx=10, pady=(6, 3), fill="x")

        self.entree_montant = ctk.CTkEntry(
            zone, font=("Segoe UI", 13, "bold"), height=40,
            placeholder_text="0",
        )
        if self.depense:
            self.entree_montant.insert(0, str(int(self.depense["montant"])))
        self.entree_montant.pack(padx=10, pady=(0, 6), fill="x")
        self.entree_montant.bind("<KeyRelease>", lambda e: self._maj_alerte())

        rapides = ctk.CTkFrame(zone, fg_color="transparent")
        rapides.pack(padx=10, pady=(0, 8), fill="x")

        ctk.CTkLabel(rapides, text="Rapide :",
                     font=("Segoe UI", 9),
                     text_color="#888888").pack(side="left", padx=(0, 4))

        for m in [50, 100, 500, 1000]:
            ctk.CTkButton(rapides, text=f"+{m}",
                          font=("Segoe UI", 9),
                          fg_color="#e0e0e0", text_color="#333333",
                          hover_color="#c0c0c0", width=50, height=26,
                          command=lambda mm=m: self._ajouter_montant(mm)).pack(side="left", padx=2)

        sep = ctk.CTkFrame(zone, fg_color="#e0e0e0", height=1)
        sep.pack(fill="x", padx=10, pady=(10, 6))

        ctk.CTkLabel(zone, text="SUIVI BUDGETAIRE",
                     font=("Segoe UI", 10, "bold"),
                     text_color="#8e44ad", anchor="w").pack(padx=10, pady=(0, 4), fill="x")

        ctk.CTkLabel(
            zone,
            text="Liez la depense a une sous-categorie pour suivre le budget.",
            font=("Segoe UI", 9),
            text_color="#999999",
        ).pack(padx=10, pady=(0, 6), anchor="w", fill="x")

        ctk.CTkLabel(zone, text="Budget principal",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w").pack(padx=10, pady=(4, 3), fill="x")

        budgets_labels = ["(Aucun)"] + [b["label"] for b in self.sous_categories_par_budget.values()]

        self.combo_budget = ctk.CTkComboBox(
            zone,
            values=budgets_labels,
            font=("Segoe UI", 11),
            height=36,
            command=self._on_budget_change,
        )
        self.combo_budget.set("(Aucun)")
        self.combo_budget.pack(padx=10, pady=(0, 6), fill="x")

        ctk.CTkLabel(zone, text="Sous-categorie",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w").pack(padx=10, pady=(4, 3), fill="x")

        ligne_sous = ctk.CTkFrame(zone, fg_color="transparent")
        ligne_sous.pack(padx=10, pady=(0, 6), fill="x")

        self.combo_sous = ctk.CTkComboBox(
            ligne_sous,
            values=["(Choisir d'abord un budget)"],
            font=("Segoe UI", 11),
            height=36,
            command=self._on_sous_change,
        )
        self.combo_sous.set("(Choisir d'abord un budget)")
        self.combo_sous.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            ligne_sous, text="+",
            font=("Segoe UI", 14, "bold"),
            fg_color="#8e44ad", hover_color="#7d3c98",
            width=42, height=36,
            command=self._creer_sous_categorie,
        ).pack(side="left", padx=(5, 0))

        cadre_info = ctk.CTkFrame(zone, fg_color="#F0F7FF", corner_radius=8)
        cadre_info.pack(fill="x", padx=10, pady=(5, 8))

        self.label_budget_info = ctk.CTkLabel(
            cadre_info,
            text="Selectionnez un budget pour voir les montants.",
            font=("Segoe UI", 10),
            text_color="#666666",
            justify="left",
            anchor="w",
        )
        self.label_budget_info.pack(padx=12, pady=8, fill="x")

        if self.depense:
            sous_cat_actuelle = (self.depense.get("budget_sous_categorie") or "").strip()
            if sous_cat_actuelle:
                self._selectionner_sous_categorie(sous_cat_actuelle)

        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=15, pady=(5, 12))

        ctk.CTkButton(boutons, text="Annuler (Echap)",
                      font=("Segoe UI", 12, "bold"),
                      fg_color="#e74c3c", text_color="white",
                      hover_color="#c0392b", height=42,
                      command=self.destroy).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(boutons, text="Enregistrer",
                      font=("Segoe UI", 12, "bold"),
                      fg_color=COLOR_NAVY, hover_color="#1a3d75",
                      height=42, command=self._enregistrer).pack(side="left", expand=True, fill="x", padx=(5, 0))

    def _on_budget_change(self, valeur):
        if valeur == "(Aucun)":
            self.combo_sous.configure(values=["(Choisir d'abord un budget)"])
            self.combo_sous.set("(Choisir d'abord un budget)")
            self.label_budget_info.configure(text="Selectionnez un budget pour voir les montants.")
            return

        for key, info in self.sous_categories_par_budget.items():
            if info["label"] == valeur:
                if info["sous"]:
                    self.combo_sous.configure(values=info["sous"])
                    self.combo_sous.set(info["sous"][0])
                    self._on_sous_change(info["sous"][0])
                else:
                    self.combo_sous.configure(values=["(Aucune sous-categorie)"])
                    self.combo_sous.set("(Aucune sous-categorie)")
                    self.label_budget_info.configure(
                        text="Aucune sous-categorie dans ce budget.\n"
                             "Cliquez sur + pour en creer une."
                    )
                return

    def _on_sous_change(self, valeur):
        if valeur in ("(Choisir d'abord un budget)", "(Aucune sous-categorie)"):
            return

        details = self.budget_sous_cat_details.get(valeur)
        if not details:
            return

        prevu = details["prevu"]
        reel = details["reel"]

        try:
            m_str = self.entree_montant.get().strip().replace(" ", "").replace(",", "")
            montant_saisi = float(m_str) if m_str else 0
        except Exception:
            montant_saisi = 0

        nouveau_reel = reel + montant_saisi
        nouvel_ecart = prevu - nouveau_reel

        couleur_ecart = "#27ae60" if nouvel_ecart >= 0 else "#e74c3c"
        avertissement = ""
        if nouvel_ecart < 0:
            avertissement = "\nDEPASSEMENT DE BUDGET !"

        texte = (
            f"Budget : {details['budget_label']}  >  {valeur}\n"
            f"Prevu     : {format_montant(prevu)}\n"
            f"Deja dep. : {format_montant(reel)}\n"
            f"Cette dep.: {format_montant(montant_saisi)}\n"
            f"Reste     : {format_montant(nouvel_ecart)}{avertissement}"
        )

        self.label_budget_info.configure(text=texte, text_color=couleur_ecart)

    def _maj_alerte(self):
        sous = self.combo_sous.get().strip()
        if sous not in ("(Choisir d'abord un budget)", "(Aucune sous-categorie)"):
            self._on_sous_change(sous)

    def _selectionner_sous_categorie(self, sous_cat):
        for key, info in self.sous_categories_par_budget.items():
            if sous_cat in info["sous"]:
                self.combo_budget.set(info["label"])
                self.combo_sous.configure(values=info["sous"])
                self.combo_sous.set(sous_cat)
                self._on_sous_change(sous_cat)
                return

    def _creer_sous_categorie(self):
        budget_label = self.combo_budget.get().strip()
        if budget_label == "(Aucun)":
            messagebox.showwarning(
                "Attention",
                "Choisissez d'abord un budget principal\n"
                "(PRIME, INVESTISSEMENT ou FONCTIONNEMENT)."
            )
            return

        budget_key = None
        for key, info in self.sous_categories_par_budget.items():
            if info["label"] == budget_label:
                budget_key = key
                break

        if not budget_key:
            messagebox.showerror("Erreur", "Budget introuvable.")
            return

        nom = simpledialog.askstring(
            "Nouvelle sous-categorie",
            f"Nom de la nouvelle sous-categorie\n(dans {budget_label}) :",
            parent=self,
        )
        if not nom or not nom.strip():
            return

        nom = nom.strip()

        pct_str = simpledialog.askstring(
            "Pourcentage",
            f"Pourcentage de '{nom}'\n(par rapport au budget {budget_label}) :",
            initialvalue="0",
            parent=self,
        )
        try:
            pct = float(pct_str) if pct_str else 0
        except Exception:
            pct = 0

        if ajouter_sous_categorie(budget_key, nom, pct):
            messagebox.showinfo(
                "Succes",
                f"Sous-categorie '{nom}' creee dans {budget_label}.\n\n"
                f"Elle est maintenant disponible partout\n"
                f"(Parametres > Budgets, Suivi budgetaire, etc.)"
            )
            self._charger_sous_categories()
            budgets_labels = ["(Aucun)"] + [
                b["label"] for b in self.sous_categories_par_budget.values()
            ]
            self.combo_budget.configure(values=budgets_labels)
            self._on_budget_change(budget_label)
            self.combo_sous.set(nom)
            self._on_sous_change(nom)
        else:
            messagebox.showerror("Erreur", "Impossible de creer la sous-categorie.")

    def _ajouter_montant(self, m):
        actuel = self.entree_montant.get().strip()
        try:
            v = float(actuel) if actuel else 0
        except ValueError:
            v = 0
        self.entree_montant.delete(0, "end")
        self.entree_montant.insert(0, str(int(v + m)))
        self._maj_alerte()

    def _enregistrer(self):
        categorie = self.combo_categorie.get().strip()
        libelle = self.entree_libelle.get().strip()

        montant_str = self.entree_montant.get().strip().replace(" ", "").replace(",", "")
        try:
            montant = float(montant_str) if montant_str else 0
        except ValueError:
            messagebox.showerror("Erreur", "Le montant doit etre un nombre.")
            return

        if not categorie or not libelle:
            messagebox.showerror("Champs obligatoires",
                                 "Veuillez remplir la categorie et le libelle.")
            return

        if montant <= 0:
            messagebox.showerror("Erreur", "Le montant doit etre superieur a 0.")
            return

        budget = self.combo_budget.get().strip()
        sous_cat = self.combo_sous.get().strip()

        if budget == "(Aucun)" or sous_cat in ("(Choisir d'abord un budget)",
                                                 "(Aucune sous-categorie)"):
            sous_cat = ""

        if sous_cat:
            details = self.budget_sous_cat_details.get(sous_cat)
            if details:
                prevu = details["prevu"]
                reel = details["reel"]

                if self.depense and self.depense.get("budget_sous_categorie") == sous_cat:
                    reel -= self.depense["montant"]

                nouveau_reel = reel + montant
                if nouveau_reel > prevu and prevu > 0:
                    depassement = nouveau_reel - prevu
                    rep = messagebox.askyesno(
                        "Depassement de budget",
                        f"Cette depense va depasser le budget prevu.\n\n"
                        f"Sous-categorie : {sous_cat}\n"
                        f"Prevu     : {format_montant(prevu)}\n"
                        f"Apres dep.: {format_montant(nouveau_reel)}\n"
                        f"Depassement : {format_montant(depassement)}\n\n"
                        f"Voulez-vous continuer ?"
                    )
                    if not rep:
                        return

        user_id = self.utilisateur["id"] if self.utilisateur else None

        if self.depense:
            ok, msg = modifier_depense(
                self.depense["id"], libelle, montant, categorie, sous_cat
            )
        else:
            ok, msg = ajouter_depense(
                libelle, montant, categorie, user_id, sous_cat
            )

        if ok:
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Erreur", msg)