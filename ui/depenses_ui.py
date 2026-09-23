"""
Interface de gestion des depenses
"""
import customtkinter as ctk
from tkinter import messagebox
from config import COLOR_NAVY, COLOR_GOLD, format_montant, CURRENCY_SYMBOL
from ui.scroll_frame import HorizontalScrollFrame
from core.depenses import (
    ajouter_depense, lister_depenses, modifier_depense,
    supprimer_depense, get_depense, total_depenses,
    total_depenses_jour, total_depenses_mois, CATEGORIES
)


class DepensesPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")

        self.utilisateur = utilisateur
        self._construire_interface()
        self.rafraichir_tableau()

    # ================== INTERFACE ==================
    def _construire_interface(self):
        # Ligne haut
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            top, text="Gestion des depenses",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        ctk.CTkButton(
            top, text="+ Nouvelle depense",
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_NAVY, hover_color="#1a3d75",
            height=40, command=self._ouvrir_formulaire,
        ).pack(side="right")

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
            placeholder_text="Libelle ou categorie...",
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

        # Compteur
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
            ("Date", 140),
            ("Categorie", 160),
            ("Libelle", 260),
            ("Montant", 130),
            ("Actions", 90),
        ]

        for nom, largeur in colonnes:
            ctk.CTkLabel(entete, text=nom,
                         font=("Segoe UI", 12, "bold"),
                         text_color=COLOR_NAVY, width=largeur,
                         anchor="w").pack(side="left", padx=5, pady=12)

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

            valeurs = [
                (date_str, 140, "#333333", "normal"),
                (d["categorie"], 160, "#8e44ad", "bold"),
                (d["libelle"], 260, "#333333", "normal"),
                (format_montant(d["montant"]), 130, "#e74c3c", "bold"),
            ]

            for valeur, largeur, couleur, poids in valeurs:
                ctk.CTkLabel(ligne, text=str(valeur),
                             font=("Segoe UI", 12, poids),
                             text_color=couleur,
                             width=largeur, anchor="w").pack(side="left", padx=5, pady=10)

            actions = ctk.CTkFrame(ligne, fg_color="transparent", width=90)
            actions.pack(side="left", padx=5)

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
        FormulaireDepense(self, depense=depense,
                          utilisateur=self.utilisateur,
                          on_save=self._recharger_complet)

    def _recharger_complet(self):
        """Recharge tout : cartes KPI + tableau"""
        for w in self.winfo_children():
            w.destroy()
        self._construire_interface()
        self.rafraichir_tableau()

    def _modifier(self, d):
        complet = get_depense(d["id"])
        self._ouvrir_formulaire(complet)

    def _supprimer(self, d):
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

        titre = "Modifier une depense" if depense else "Nouvelle depense"
        self.title(titre)

        largeur = 500
        hauteur = 560
        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        x = (self.winfo_screenwidth() // 2) - (largeur // 2)
        y = 40
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")

        self.bind("<Escape>", lambda e: self.destroy())

        self.transient(parent)
        self.after(100, self._activer_grab)

        self._construire_interface()

    def _activer_grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _construire_interface(self):
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        ligne_titre = ctk.CTkFrame(card, fg_color="transparent")
        ligne_titre.pack(fill="x", padx=15, pady=(12, 5))

        titre = "Modifier une depense" if self.depense else "Nouvelle depense"
        ctk.CTkLabel(ligne_titre, text=titre,
                     font=("Segoe UI", 18, "bold"),
                     text_color=COLOR_NAVY).pack(side="left")

        ctk.CTkButton(ligne_titre, text="X",
                      font=("Segoe UI", 14, "bold"),
                      width=32, height=32,
                      fg_color="#e74c3c", hover_color="#c0392b",
                      command=self.destroy).pack(side="right")

        zone = ctk.CTkScrollableFrame(card, fg_color="transparent", corner_radius=0)
        zone.pack(fill="both", expand=True, padx=5, pady=5)

        self.champs = {}

        # Categorie
        ctk.CTkLabel(zone, text="Categorie *",
                     font=("Segoe UI", 12, "bold"),
                     text_color="#333333", anchor="w").pack(padx=10, pady=(8, 4), fill="x")

        self.combo_categorie = ctk.CTkComboBox(
            zone, values=CATEGORIES,
            font=("Segoe UI", 12), height=38,
        )
        if self.depense and self.depense["categorie"] in CATEGORIES:
            self.combo_categorie.set(self.depense["categorie"])
        else:
            self.combo_categorie.set(CATEGORIES[0])
        self.combo_categorie.pack(padx=10, pady=(0, 6), fill="x")

        # Libelle
        ctk.CTkLabel(zone, text="Libelle * (description)",
                     font=("Segoe UI", 12, "bold"),
                     text_color="#333333", anchor="w").pack(padx=10, pady=(8, 4), fill="x")

        self.entree_libelle = ctk.CTkEntry(
            zone, font=("Segoe UI", 13), height=38,
            placeholder_text="Ex: Facture electricite mars 2025",
        )
        if self.depense:
            self.entree_libelle.insert(0, self.depense["libelle"])
        self.entree_libelle.pack(padx=10, pady=(0, 6), fill="x")

        # Montant
        ctk.CTkLabel(zone, text=f"Montant ({CURRENCY_SYMBOL}) *",
                     font=("Segoe UI", 12, "bold"),
                     text_color="#333333", anchor="w").pack(padx=10, pady=(8, 4), fill="x")

        self.entree_montant = ctk.CTkEntry(
            zone, font=("Segoe UI", 14, "bold"), height=42,
            placeholder_text="0",
        )
        if self.depense:
            self.entree_montant.insert(0, str(int(self.depense["montant"])))
        self.entree_montant.pack(padx=10, pady=(0, 6), fill="x")

        # Boutons rapides montant
        rapides = ctk.CTkFrame(zone, fg_color="transparent")
        rapides.pack(padx=10, pady=(0, 8), fill="x")

        ctk.CTkLabel(rapides, text="Rapide :",
                     font=("Segoe UI", 10),
                     text_color="#888888").pack(side="left", padx=(0, 4))

        for m in [50, 100, 500, 1000]:
            ctk.CTkButton(rapides, text=f"+{m}",
                          font=("Segoe UI", 10),
                          fg_color="#e0e0e0", text_color="#333333",
                          hover_color="#c0c0c0", width=55, height=28,
                          command=lambda mm=m: self._ajouter_montant(mm)).pack(side="left", padx=2)

        # Boutons
        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=15, pady=(5, 12))

        ctk.CTkButton(boutons, text="Annuler (Echap)",
                      font=("Segoe UI", 13, "bold"),
                      fg_color="#e74c3c", text_color="white",
                      hover_color="#c0392b", height=42,
                      command=self.destroy).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(boutons, text="Enregistrer",
                      font=("Segoe UI", 13, "bold"),
                      fg_color=COLOR_NAVY, hover_color="#1a3d75",
                      height=42, command=self._enregistrer).pack(side="left", expand=True, fill="x", padx=(5, 0))

    def _ajouter_montant(self, m):
        actuel = self.entree_montant.get().strip()
        try:
            v = float(actuel) if actuel else 0
        except ValueError:
            v = 0
        self.entree_montant.delete(0, "end")
        self.entree_montant.insert(0, str(int(v + m)))

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

        user_id = self.utilisateur["id"] if self.utilisateur else None

        if self.depense:
            ok, msg = modifier_depense(self.depense["id"], libelle, montant, categorie)
        else:
            ok, msg = ajouter_depense(libelle, montant, categorie, user_id)

        if ok:
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Erreur", msg)