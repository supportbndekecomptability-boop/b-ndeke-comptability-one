"""
Interface de gestion des FRAIS
- Onglet 1 : Catalogue (Scolarite, Inscription, Uniforme...)
- Onglet 2 : Affectation aux classes (montant par classe)
Permissions : admin et gestionnaire uniquement.
"""
import customtkinter as ctk
from tkinter import messagebox
from config import COLOR_NAVY, COLOR_GOLD, format_montant, CURRENCY_SYMBOL
from ui.window_utils import setup_adaptive_window
from ui.permissions_ui import peut
from core.permissions import get_role
from core.frais import (
    ajouter_frais, lister_frais, get_frais, modifier_frais,
    supprimer_frais, assigner_frais_classe, retirer_frais_classe,
    lister_frais_par_classe, total_frais_classe,
)
from core.classes import lister_classes, NIVEAUX


class FraisPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")
        self.utilisateur = utilisateur or {}
        self._construire_interface()
        self.rafraichir()

    # ================== PERMISSIONS ==================
    def _peut_gerer(self):
        return peut(self.utilisateur, "peut_gerer_frais")

    # ================== INTERFACE ==================
    def _construire_interface(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(top, text="Gestion des frais",
                     font=("Segoe UI", 22, "bold"),
                     text_color=COLOR_NAVY).pack(side="left")

        # Badge role
        if self._peut_gerer():
            info_role = "Vue : gestion des frais"
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

        # Bouton "+ Nouveau frais" : seulement si peut_gerer
        if self._peut_gerer():
            ctk.CTkButton(top, text="+ Nouveau frais",
                          font=("Segoe UI", 11, "bold"),
                          fg_color=COLOR_NAVY, hover_color="#1a3d75",
                          height=36, width=150,
                          command=self._nouveau_frais).pack(side="right", padx=(0, 15))

        # ===== ONGLETS =====
        onglets = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        onglets.pack(fill="x", pady=(0, 10))

        self.btn_catalogue = ctk.CTkButton(
            onglets, text="Catalogue des frais",
            font=("Segoe UI", 12, "bold"),
            fg_color=COLOR_NAVY, hover_color="#1a3d75",
            text_color="white", height=42, corner_radius=8,
            command=lambda: self._changer_onglet("catalogue"),
        )
        self.btn_catalogue.pack(side="left", expand=True, fill="x",
                                padx=(10, 5), pady=10)

        self.btn_affectation = ctk.CTkButton(
            onglets, text="Affectation par classe",
            font=("Segoe UI", 12, "bold"),
            fg_color="#e0e0e0", hover_color="#c0c0c0",
            text_color="#333333", height=42, corner_radius=8,
            command=lambda: self._changer_onglet("affectation"),
        )
        self.btn_affectation.pack(side="left", expand=True, fill="x",
                                   padx=(5, 10), pady=10)

        self.onglet_actuel = "catalogue"

        # ===== CONTENU =====
        self.contenu = ctk.CTkFrame(self, fg_color="transparent")
        self.contenu.pack(fill="both", expand=True)

        self.rafraichir()

    def _changer_onglet(self, onglet):
        self.onglet_actuel = onglet
        if onglet == "catalogue":
            self.btn_catalogue.configure(fg_color=COLOR_NAVY, text_color="white")
            self.btn_affectation.configure(fg_color="#e0e0e0", text_color="#333333")
        else:
            self.btn_catalogue.configure(fg_color="#e0e0e0", text_color="#333333")
            self.btn_affectation.configure(fg_color=COLOR_NAVY, text_color="white")
        self.rafraichir()

    def rafraichir(self):
        for w in self.contenu.winfo_children():
            w.destroy()

        if self.onglet_actuel == "catalogue":
            self._afficher_catalogue()
        else:
            self._afficher_affectation()

    # ================== ONGLET CATALOGUE ==================
    def _afficher_catalogue(self):
        frais_liste = lister_frais(actif=None)

        info = ctk.CTkFrame(self.contenu, fg_color="#E3F2FD", corner_radius=8)
        info.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            info,
            text=("Le catalogue contient tous les frais possibles. "
                  "Ensuite, affectez-les aux classes dans l'onglet "
                  "'Affectation par classe'.\n"
                  "Cochez 'Dans le budget' pour qu'un frais soit inclus dans "
                  "le calcul du budget annuel."),
            font=("Segoe UI", 10),
            text_color="#1565C0",
            justify="left", wraplength=900,
        ).pack(padx=15, pady=10, anchor="w")

        self.label_compteur = ctk.CTkLabel(self.contenu, text="",
                                            font=("Segoe UI", 12),
                                            text_color="#666666")
        self.label_compteur.pack(anchor="w", pady=(0, 10))
        self.label_compteur.configure(text=f"{len(frais_liste)} frais au catalogue")

        if not frais_liste:
            cadre = ctk.CTkFrame(self.contenu, fg_color="#FFF7E0", corner_radius=10)
            cadre.pack(fill="x", pady=20, padx=10)
            ctk.CTkLabel(
                cadre,
                text=("Aucun frais dans le catalogue.\n\n"
                      "Cliquez sur '+ Nouveau frais' pour en ajouter."),
                font=("Segoe UI", 12), text_color="#8B6914",
                justify="center",
            ).pack(pady=30)
            return

        tableau = ctk.CTkScrollableFrame(self.contenu, fg_color="white",
                                          corner_radius=10)
        tableau.pack(fill="both", expand=True)

        # Entete
        entete = ctk.CTkFrame(tableau, fg_color="#f0f0f0", corner_radius=4)
        entete.pack(fill="x", pady=(0, 3))
        for nom, larg in [
            ("Nom", 180), ("Description", 260), ("Montant def.", 130),
            ("Budget", 100), ("Ordre", 70), ("Statut", 100),
        ]:
            ctk.CTkLabel(entete, text=nom, font=("Segoe UI", 10, "bold"),
                         text_color=COLOR_NAVY, width=larg,
                         anchor="w").pack(side="left", padx=4, pady=8)

        # Actions uniquement si peut_gerer
        if self._peut_gerer():
            ctk.CTkLabel(entete, text="Actions", font=("Segoe UI", 10, "bold"),
                         text_color=COLOR_NAVY, width=200,
                         anchor="center").pack(side="left", padx=4, pady=8)

        for i, f in enumerate(frais_liste):
            fond = "#ffffff" if i % 2 == 0 else "#fafafa"
            ligne = ctk.CTkFrame(tableau, fg_color=fond, corner_radius=4)
            ligne.pack(fill="x", pady=1)

            actif = f.get("actif", 1)
            dans_budget = f.get("dans_budget", 0)

            couleur_nom = "#333333" if actif else "#999999"
            statut_txt = "Actif" if actif else "Desactive"
            couleur_statut = "#27ae60" if actif else "#999999"

            budget_txt = "Oui" if dans_budget else "Non"
            couleur_budget = "#27ae60" if dans_budget else "#999999"

            desc = f.get("description") or "-"
            if len(desc) > 40:
                desc = desc[:37] + "..."

            for val, larg, coul, poids in [
                (f["nom"], 180, couleur_nom, "bold"),
                (desc, 260, "#666666", "normal"),
                (format_montant(f.get("montant_defaut", 0)), 130, "#333333", "normal"),
                (budget_txt, 100, couleur_budget, "bold"),
                (str(f.get("ordre", 0)), 70, "#666666", "normal"),
                (statut_txt, 100, couleur_statut, "bold"),
            ]:
                ctk.CTkLabel(ligne, text=str(val), font=("Segoe UI", 11, poids),
                             text_color=coul, width=larg,
                             anchor="w").pack(side="left", padx=4, pady=8)

            # Actions conditionnelles
            if not self._peut_gerer():
                continue

            actions = ctk.CTkFrame(ligne, fg_color="transparent", width=200)
            actions.pack(side="left", padx=4)

            ctk.CTkButton(actions, text="Modifier",
                          font=("Segoe UI", 10, "bold"),
                          width=70, height=26,
                          fg_color="#3498db", hover_color="#2980b9",
                          command=lambda ff=f: self._modifier_frais(ff)
                          ).pack(side="left", padx=2)

            if actif:
                ctk.CTkButton(actions, text="Desactiver",
                              font=("Segoe UI", 10, "bold"),
                              width=75, height=26,
                              fg_color="#999999", hover_color="#777777",
                              command=lambda ff=f: self._toggle_actif(ff)
                              ).pack(side="left", padx=2)
            else:
                ctk.CTkButton(actions, text="Activer",
                              font=("Segoe UI", 10, "bold"),
                              width=65, height=26,
                              fg_color="#27ae60", hover_color="#229954",
                              command=lambda ff=f: self._toggle_actif(ff)
                              ).pack(side="left", padx=2)

            ctk.CTkButton(actions, text="X",
                          font=("Segoe UI", 11, "bold"),
                          width=34, height=26,
                          fg_color="#e74c3c", hover_color="#c0392b",
                          command=lambda ff=f: self._supprimer_frais(ff)
                          ).pack(side="left", padx=2)

    # ================== ACTIONS CATALOGUE ==================
    def _nouveau_frais(self):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse",
                                 "Vous n'avez pas la permission de gerer les frais.")
            return
        FormulaireFrais(self, self.utilisateur, on_save=self.rafraichir)

    def _modifier_frais(self, frais):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        FormulaireFrais(self, self.utilisateur, on_save=self.rafraichir,
                        frais_existant=frais)

    def _toggle_actif(self, frais):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        nouvel_actif = 0 if frais.get("actif") else 1
        ok, msg = modifier_frais(frais["id"], actif=nouvel_actif)
        if ok:
            self.rafraichir()
        else:
            messagebox.showerror("Erreur", msg)

    def _supprimer_frais(self, frais):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        rep = messagebox.askyesno(
            "Confirmation",
            f"Supprimer le frais '{frais['nom']}' ?\n\n"
            f"Attention : cela supprime aussi son affectation "
            f"a toutes les classes."
        )
        if not rep:
            return
        ok, msg = supprimer_frais(frais["id"])
        if ok:
            self.rafraichir()
        else:
            messagebox.showerror("Erreur", msg)

    # ================== ONGLET AFFECTATION ==================
    def _afficher_affectation(self):
        classes = lister_classes(actif=True)

        info = ctk.CTkFrame(self.contenu, fg_color="#FFF3CD", corner_radius=8)
        info.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            info,
            text=("Cliquez sur 'Gerer les frais' d'une classe pour lui "
                  "affecter des frais avec un montant specifique.\n"
                  "Ces frais seront automatiquement generes quand un eleve "
                  "est inscrit dans cette classe."),
            font=("Segoe UI", 10),
            text_color="#8B6914",
            justify="left", wraplength=900,
        ).pack(padx=15, pady=10, anchor="w")

        if not classes:
            cadre = ctk.CTkFrame(self.contenu, fg_color="#FFF7E0", corner_radius=10)
            cadre.pack(fill="x", pady=20, padx=10)
            ctk.CTkLabel(
                cadre,
                text=("Aucune classe creee.\n\n"
                      "Allez dans le menu 'Classes' pour creer vos classes "
                      "avant d'affecter des frais."),
                font=("Segoe UI", 12), text_color="#8B6914",
                justify="center",
            ).pack(pady=30)
            return

        tableau = ctk.CTkScrollableFrame(self.contenu, fg_color="white",
                                          corner_radius=10)
        tableau.pack(fill="both", expand=True)

        # Entete
        entete = ctk.CTkFrame(tableau, fg_color="#f0f0f0", corner_radius=4)
        entete.pack(fill="x", pady=(0, 3))
        for nom, larg in [
            ("Classe", 200), ("Niveau", 110), ("Sous-type", 140),
            ("Nb frais", 90), ("Total classe", 140),
        ]:
            ctk.CTkLabel(entete, text=nom, font=("Segoe UI", 10, "bold"),
                         text_color=COLOR_NAVY, width=larg,
                         anchor="w").pack(side="left", padx=4, pady=8)

        if self._peut_gerer():
            ctk.CTkLabel(entete, text="Actions", font=("Segoe UI", 10, "bold"),
                         text_color=COLOR_NAVY, width=170,
                         anchor="center").pack(side="left", padx=4, pady=8)

        # Grouper par niveau
        groupes = {}
        for c in classes:
            groupes.setdefault(c["niveau"], []).append(c)

        for niveau_nom in NIVEAUX:
            if niveau_nom not in groupes:
                continue
            titre = ctk.CTkFrame(tableau, fg_color=COLOR_NAVY, corner_radius=6)
            titre.pack(fill="x", pady=(15, 3))
            ctk.CTkLabel(titre, text=f"  {niveau_nom.upper()}",
                         font=("Segoe UI", 12, "bold"),
                         text_color=COLOR_GOLD,
                         anchor="w").pack(side="left", padx=10, pady=8)

            for c in groupes[niveau_nom]:
                nb = len(lister_frais_par_classe(c["id"]))
                total = total_frais_classe(c["id"])

                fond = "#ffffff" if nb % 2 == 0 else "#fafafa"
                ligne = ctk.CTkFrame(tableau, fg_color=fond, corner_radius=4)
                ligne.pack(fill="x", pady=1)

                sous_type = c.get("sous_type") or "-"
                if sous_type == "base":
                    sous_type_txt = "Education de base"
                elif sous_type == "option":
                    sous_type_txt = "Option"
                else:
                    sous_type_txt = "-"

                couleur_nb = "#e74c3c" if nb == 0 else "#27ae60"

                for val, larg, coul, poids in [
                    (c["nom"], 200, "#333333", "bold"),
                    (niveau_nom, 110, "#666666", "normal"),
                    (sous_type_txt, 140, "#666666", "normal"),
                    (str(nb), 90, couleur_nb, "bold"),
                    (format_montant(total) if total > 0 else "-",
                     140, "#0F2C5C", "bold"),
                ]:
                    ctk.CTkLabel(ligne, text=str(val),
                                 font=("Segoe UI", 11, poids),
                                 text_color=coul, width=larg,
                                 anchor="w").pack(side="left", padx=4, pady=8)

                if not self._peut_gerer():
                    continue

                actions = ctk.CTkFrame(ligne, fg_color="transparent", width=170)
                actions.pack(side="left", padx=4)

                ctk.CTkButton(actions, text="Gerer les frais",
                              font=("Segoe UI", 10, "bold"),
                              width=140, height=28,
                              fg_color=COLOR_NAVY, hover_color="#1a3d75",
                              command=lambda cc=c: self._ouvrir_gestion_classe(cc)
                              ).pack(side="left", padx=2)

    def _ouvrir_gestion_classe(self, classe):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        ModalFraisClasse(self, classe, self.utilisateur,
                         on_save=self.rafraichir)


# ============================================================
# FORMULAIRE FRAIS (catalogue) - inchange
# ============================================================
class FormulaireFrais(ctk.CTkToplevel):
    def __init__(self, parent, utilisateur, on_save=None, frais_existant=None):
        super().__init__(parent)
        self.utilisateur = utilisateur
        self.on_save = on_save
        self.frais_existant = frais_existant
        self.mode_edition = frais_existant is not None

        titre = "Modifier frais" if self.mode_edition else "Nouveau frais"
        self.title(titre)
        self.configure(fg_color="#F5F7FB")
        setup_adaptive_window(self, largeur_max=500, hauteur_max=600)

        self.bind("<Escape>", lambda e: self.destroy())
        self.transient(parent)
        self.after(100, self._activer_grab)
        self._construire()

    def _activer_grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _construire(self):
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=25, pady=(10, 15), side="bottom")

        ctk.CTkButton(boutons, text="Annuler",
                      font=("Segoe UI", 12),
                      fg_color="#e74c3c", hover_color="#c0392b",
                      height=40, command=self.destroy
                      ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        texte_btn = "Enregistrer les modifications" if self.mode_edition else "Ajouter le frais"
        ctk.CTkButton(boutons, text=texte_btn,
                      font=("Segoe UI", 12, "bold"),
                      fg_color=COLOR_NAVY, hover_color="#1a3d75",
                      height=40, command=self._enregistrer
                      ).pack(side="left", expand=True, fill="x", padx=(5, 0))

        titre = "MODIFIER FRAIS" if self.mode_edition else "NOUVEAU FRAIS"
        ctk.CTkLabel(card, text=titre,
                     font=("Segoe UI", 15, "bold"),
                     text_color=COLOR_NAVY).pack(pady=(15, 10))

        zone = ctk.CTkScrollableFrame(card, fg_color="transparent",
                                       corner_radius=0)
        zone.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(zone, text="Nom du frais *",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=20, pady=(5, 3), fill="x")
        self.entree_nom = ctk.CTkEntry(zone, height=38,
                                        placeholder_text="Ex: Scolarite, Inscription, Uniforme...")
        self.entree_nom.pack(padx=20, pady=(0, 10), fill="x")

        ctk.CTkLabel(zone, text="Description (optionnel)",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=20, pady=(5, 3), fill="x")
        self.entree_desc = ctk.CTkEntry(zone, height=38,
                                         placeholder_text="Ex: Frais de scolarite annuels")
        self.entree_desc.pack(padx=20, pady=(0, 10), fill="x")

        ctk.CTkLabel(zone, text=f"Montant par defaut ({CURRENCY_SYMBOL})",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=20, pady=(5, 3), fill="x")
        self.entree_montant = ctk.CTkEntry(zone, height=40,
                                            font=("Segoe UI", 13, "bold"),
                                            placeholder_text="0")
        self.entree_montant.pack(padx=20, pady=(0, 10), fill="x")

        ctk.CTkLabel(zone,
                     text="(Le montant reel est defini par classe dans l'onglet Affectation)",
                     font=("Segoe UI", 9), text_color="#888888",
                     anchor="w").pack(padx=20, pady=(0, 10), fill="x")

        ctk.CTkLabel(zone, text="Categorie budgetaire (optionnel)",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=20, pady=(5, 3), fill="x")
        self.entree_cat = ctk.CTkEntry(zone, height=36,
                                        placeholder_text="Ex: Scolarite, Autres...")
        self.entree_cat.pack(padx=20, pady=(0, 10), fill="x")

        self.var_budget = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            zone,
            text="Inclure dans le budget annuel",
            variable=self.var_budget,
            font=("Segoe UI", 12, "bold"),
            text_color="#8B6914",
            fg_color=COLOR_NAVY,
            hover_color="#1a3d75",
        ).pack(padx=20, pady=(5, 10), anchor="w")

        ctk.CTkLabel(zone, text="Ordre d'affichage",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=20, pady=(5, 3), fill="x")
        self.entree_ordre = ctk.CTkEntry(zone, height=36, placeholder_text="0")
        self.entree_ordre.pack(padx=20, pady=(0, 10), fill="x")

        if self.mode_edition:
            f = self.frais_existant
            self.entree_nom.insert(0, f.get("nom", ""))
            self.entree_desc.insert(0, f.get("description", "") or "")
            self.entree_montant.insert(0, str(int(f.get("montant_defaut", 0) or 0)))
            self.entree_cat.insert(0, f.get("categorie_budget", "") or "")
            self.var_budget.set(bool(f.get("dans_budget")))
            self.entree_ordre.insert(0, str(f.get("ordre", 0)))

    def _enregistrer(self):
        nom = self.entree_nom.get().strip()
        if not nom:
            messagebox.showerror("Erreur", "Le nom est obligatoire.")
            return

        desc = self.entree_desc.get().strip()
        cat = self.entree_cat.get().strip()

        try:
            montant = float(self.entree_montant.get().strip()
                            .replace(" ", "").replace(",", "") or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Montant invalide.")
            return

        try:
            ordre = int(self.entree_ordre.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Ordre doit etre un nombre entier.")
            return

        dans_budget = self.var_budget.get()

        if self.mode_edition:
            ok, msg = modifier_frais(
                self.frais_existant["id"],
                nom=nom, description=desc, montant_defaut=montant,
                categorie_budget=cat, dans_budget=dans_budget, ordre=ordre,
            )
        else:
            ok, msg = ajouter_frais(nom, desc, montant, cat,
                                     dans_budget, ordre)

        if ok:
            messagebox.showinfo("Succes", msg)
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Erreur", msg)


# ============================================================
# MODAL : GERER LES FRAIS D'UNE CLASSE - inchange
# ============================================================
class ModalFraisClasse(ctk.CTkToplevel):
    def __init__(self, parent, classe, utilisateur, on_save=None):
        super().__init__(parent)
        self.classe = classe
        self.utilisateur = utilisateur
        self.on_save = on_save

        self.title(f"Frais de la classe - {classe['nom']}")
        self.configure(fg_color="#F5F7FB")
        setup_adaptive_window(self, largeur_max=700, hauteur_max=600,
                               marge_hauteur=80)

        self.bind("<Escape>", lambda e: self.destroy())
        self.transient(parent)
        self.after(100, self._activer_grab)

        self._construire()
        self._rafraichir()

    def _activer_grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _construire(self):
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=20, pady=(5, 15), side="bottom")

        ctk.CTkButton(boutons, text="Fermer",
                      font=("Segoe UI", 12),
                      fg_color="#999999", hover_color="#777777",
                      height=38, width=120,
                      command=self.destroy
                      ).pack(side="right")

        ctk.CTkButton(boutons, text="Enregistrer les affectations",
                      font=("Segoe UI", 12, "bold"),
                      fg_color=COLOR_NAVY, hover_color="#1a3d75",
                      height=38,
                      command=self._enregistrer_tout
                      ).pack(side="left")

        ctk.CTkLabel(card,
                     text=f"FRAIS DE : {self.classe['nom']}",
                     font=("Segoe UI", 15, "bold"),
                     text_color=COLOR_NAVY).pack(pady=(15, 5))

        ctk.CTkLabel(card,
                     text=f"Niveau : {self.classe['niveau']}",
                     font=("Segoe UI", 11),
                     text_color="#666666").pack(pady=(0, 10))

        info = ctk.CTkFrame(card, fg_color="#E3F2FD", corner_radius=8)
        info.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(
            info,
            text=("Cochez les frais a appliquer a cette classe, puis "
                  "saisissez le MONTANT reel pour cette classe."),
            font=("Segoe UI", 10),
            text_color="#1565C0",
            justify="left", wraplength=620,
        ).pack(padx=15, pady=10, anchor="w")

        self.zone = ctk.CTkScrollableFrame(card, fg_color="#FAFAFA",
                                            corner_radius=8)
        self.zone.pack(fill="both", expand=True, padx=20, pady=(0, 5))

        self.label_total = ctk.CTkLabel(card, text="",
                                         font=("Segoe UI", 14, "bold"),
                                         text_color="#e74c3c")
        self.label_total.pack(pady=(5, 5))

        self.lignes = {}

    def _rafraichir(self):
        for w in self.zone.winfo_children():
            w.destroy()
        self.lignes = {}

        tous_frais = lister_frais(actif=True)
        affectes = lister_frais_par_classe(self.classe["id"])
        affectes_map = {a["frais_id"]: a for a in affectes}

        if not tous_frais:
            ctk.CTkLabel(self.zone,
                         text="Aucun frais dans le catalogue.\n"
                              "Ajoutez d'abord des frais dans l'onglet "
                              "'Catalogue'.",
                         font=("Segoe UI", 11),
                         text_color="#999999").pack(pady=40)
            self.label_total.configure(text="")
            return

        entete = ctk.CTkFrame(self.zone, fg_color="#ECECEC", corner_radius=4)
        entete.pack(fill="x", pady=(0, 3))
        for nom, larg in [
            ("Appliquer", 90), ("Nom du frais", 220),
            ("Montant def.", 110), ("Montant classe", 160),
            ("Budget", 90),
        ]:
            ctk.CTkLabel(entete, text=nom, font=("Segoe UI", 10, "bold"),
                         text_color=COLOR_NAVY, width=larg,
                         anchor="w").pack(side="left", padx=4, pady=8)

        for i, f in enumerate(tous_frais):
            fond = "#ffffff" if i % 2 == 0 else "#fafafa"
            ligne = ctk.CTkFrame(self.zone, fg_color=fond, corner_radius=4)
            ligne.pack(fill="x", pady=1)

            affecte = affectes_map.get(f["id"])

            var_check = ctk.BooleanVar(value=bool(affecte))
            cb = ctk.CTkCheckBox(
                ligne, text="", variable=var_check,
                width=30, fg_color=COLOR_NAVY, hover_color="#1a3d75",
                command=self._maj_total,
            )
            cb.pack(side="left", padx=(10, 5), pady=8)

            ctk.CTkLabel(ligne, text=f["nom"],
                         font=("Segoe UI", 11, "bold"),
                         text_color="#333333", width=220,
                         anchor="w").pack(side="left", padx=4, pady=8)

            ctk.CTkLabel(ligne,
                         text=format_montant(f.get("montant_defaut", 0)),
                         font=("Segoe UI", 10),
                         text_color="#666666", width=110,
                         anchor="w").pack(side="left", padx=4, pady=8)

            montant_init = ""
            if affecte and affecte.get("montant_classe"):
                montant_init = str(int(affecte["montant_classe"]))
            entree = ctk.CTkEntry(ligne, height=32, width=140,
                                   font=("Segoe UI", 11, "bold"),
                                   placeholder_text="0")
            if montant_init:
                entree.insert(0, montant_init)
            entree.pack(side="left", padx=4, pady=8)
            entree.bind("<KeyRelease>", lambda e: self._maj_total())

            dans_budget = "Oui" if f.get("dans_budget") else "Non"
            c_budget = "#27ae60" if f.get("dans_budget") else "#999999"
            ctk.CTkLabel(ligne, text=dans_budget,
                         font=("Segoe UI", 10, "bold"),
                         text_color=c_budget, width=90,
                         anchor="w").pack(side="left", padx=4, pady=8)

            self.lignes[f["id"]] = {
                "frais": f,
                "var_check": var_check,
                "entree": entree,
            }

        self._maj_total()

    def _maj_total(self):
        total = 0
        nb = 0
        for fid, l in self.lignes.items():
            if l["var_check"].get():
                try:
                    m = float(l["entree"].get().strip()
                              .replace(" ", "").replace(",", "") or 0)
                except ValueError:
                    m = 0
                total += m
                if m > 0:
                    nb += 1

        self.label_total.configure(
            text=f"Total pour cette classe : {format_montant(total)}  ({nb} frais)"
        )

    def _enregistrer_tout(self):
        erreurs = []
        for fid, l in self.lignes.items():
            frais = l["frais"]
            coche = l["var_check"].get()

            if coche:
                try:
                    m = float(l["entree"].get().strip()
                              .replace(" ", "").replace(",", "") or 0)
                except ValueError:
                    erreurs.append(f"{frais['nom']} : montant invalide")
                    continue

                if m <= 0:
                    erreurs.append(f"{frais['nom']} : montant > 0 obligatoire")
                    continue

                ok, msg = assigner_frais_classe(
                    frais["id"], self.classe["id"], m
                )
                if not ok:
                    erreurs.append(f"{frais['nom']} : {msg}")
            else:
                retirer_frais_classe(frais["id"], self.classe["id"])

        if erreurs:
            messagebox.showerror(
                "Erreurs",
                "Certaines affectations ont echoue :\n\n" + "\n".join(erreurs)
            )
        else:
            messagebox.showinfo("Succes",
                                "Affectations enregistrees avec succes.")
            if self.on_save:
                self.on_save()
            self.destroy()