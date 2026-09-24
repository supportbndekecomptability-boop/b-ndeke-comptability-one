"""
Interface Dettes eleves - vue par eleve + detail par categorie
Fenetres adaptatives aux petits ecrans
Avec permissions par role :
- Caissier     : encaisse uniquement (pas de creation, pas d'annulation)
- Comptable    : voit les dettes du caissier, peut annuler
- Admin/Gest.  : tout (creer, encaisser, annuler)
- Directeur    : pas d'acces
"""
import customtkinter as ctk
from tkinter import messagebox
from config import COLOR_NAVY, COLOR_GOLD, format_montant
from ui.window_utils import setup_adaptive_window
from ui.permissions_ui import peut
from core.dettes import (
    CATEGORIES,
    ajouter_dette, lister_eleves_avec_dettes, detail_dettes_eleve,
    total_dettes_en_cours, compter_eleves_endettes, total_recouvre_mois,
    enregistrer_paiement_dette, annuler_dette,
    liste_eleves_pour_dette,
)
from core.permissions import get_role


class DettesPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")
        self.utilisateur = utilisateur or {}
        self.recherche = ""
        self.filtre_statut = "En cours"
        self._construire_interface()
        self.rafraichir_tableau()

    # ================== PERMISSIONS ==================
    def _peut_creer(self):
        """Creer une dette : admin, gestionnaire uniquement."""
        return peut(self.utilisateur, "peut_creer_dette")

    def _peut_encaisser(self):
        """Encaisser un paiement de dette : caissier, admin, gestionnaire."""
        return peut(self.utilisateur, "peut_encaisser_dette")

    def _peut_annuler(self):
        """Annuler une dette : comptable, admin, gestionnaire."""
        return (peut(self.utilisateur, "peut_supprimer_operations_caissier")
                or peut(self.utilisateur, "peut_supprimer"))

    # ================== INTERFACE ==================
    def _construire_interface(self):
        # ===== Titre + Badge role =====
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(top, text="Dettes eleves",
                     font=("Segoe UI", 22, "bold"),
                     text_color=COLOR_NAVY).pack(side="left")

        # Bouton "+ Nouvelle dette" : seulement si peut_creer
        if self._peut_creer():
            ctk.CTkButton(top, text="+ Nouvelle dette",
                          font=("Segoe UI", 11, "bold"),
                          fg_color=COLOR_NAVY, hover_color="#1a3d75",
                          height=36, width=150,
                          command=self._nouvelle_dette).pack(side="right")

        # Badge role
        role = get_role(self.utilisateur)
        if role == "caissier":
            info_role = "Vue : encaissement uniquement"
            couleur_role = "#3498db"
        elif role == "comptable":
            info_role = "Vue : dettes des caissiers (modification possible)"
            couleur_role = "#e67e22"
        else:
            info_role = "Vue : toutes les dettes"
            couleur_role = "#27ae60"

        ctk.CTkLabel(
            top,
            text=info_role,
            font=("Segoe UI", 10, "italic"),
            text_color=couleur_role,
        ).pack(side="right", padx=(0, 15), pady=(8, 0))

        # ===== Stats =====
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.pack(fill="x", pady=(0, 15))
        for titre, valeur, couleur in [
            ("Total dettes en cours", format_montant(total_dettes_en_cours()), "#e74c3c"),
            ("Eleves endettes", str(compter_eleves_endettes()), "#e67e22"),
            ("Recouvre ce mois", format_montant(total_recouvre_mois()), "#27ae60"),
        ]:
            carte = ctk.CTkFrame(stats, fg_color="white", corner_radius=12)
            carte.pack(side="left", expand=True, fill="both", padx=6)
            ctk.CTkLabel(carte, text=titre, font=("Segoe UI", 11, "bold"),
                         text_color="#888888").pack(pady=(15, 3))
            ctk.CTkLabel(carte, text=valeur, font=("Segoe UI", 20, "bold"),
                         text_color=couleur).pack(pady=(0, 15))

        # ===== Barre de recherche =====
        barre = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        barre.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(barre, text="Recherche :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#666666").pack(side="left", padx=(15, 3), pady=12)
        self.entree_recherche = ctk.CTkEntry(
            barre, font=("Segoe UI", 11), width=200, height=32,
            placeholder_text="Nom, prenom ou matricule...",
        )
        self.entree_recherche.pack(side="left", padx=3, pady=12)
        self.entree_recherche.bind("<Return>", lambda e: self._rechercher())

        ctk.CTkButton(barre, text="Chercher",
                      font=("Segoe UI", 10, "bold"),
                      fg_color=COLOR_NAVY, hover_color="#1a3d75",
                      height=32, width=80,
                      command=self._rechercher).pack(side="left", padx=3, pady=12)

        ctk.CTkLabel(barre, text="Statut :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#666666").pack(side="left", padx=(20, 3), pady=12)
        self.combo_statut = ctk.CTkComboBox(
            barre, values=["En cours", "Soldees", "Toutes"],
            font=("Segoe UI", 11), height=32, width=130,
            command=self._on_statut_change,
        )
        self.combo_statut.set("En cours")
        self.combo_statut.pack(side="left", padx=3, pady=12)

        self.label_compteur = ctk.CTkLabel(self, text="",
                                            font=("Segoe UI", 12),
                                            text_color="#666666")
        self.label_compteur.pack(anchor="w", pady=(0, 10))

        self.tableau = ctk.CTkScrollableFrame(self, fg_color="white",
                                              corner_radius=10)
        self.tableau.pack(fill="both", expand=True)

    def _on_statut_change(self, valeur):
        self.filtre_statut = valeur
        self.rafraichir_tableau()

    def _rechercher(self):
        self.recherche = self.entree_recherche.get().strip()
        self.rafraichir_tableau()

    def rafraichir_tableau(self):
        for w in self.tableau.winfo_children():
            w.destroy()

        statut_map = {"En cours": "en_cours", "Soldees": "soldee", "Toutes": None}
        eleves = lister_eleves_avec_dettes(
            statut=statut_map.get(self.filtre_statut),
            recherche=self.recherche or None,
        )

        self.label_compteur.configure(
            text=f"{len(eleves)} eleve(s) endette(s) - Statut : {self.filtre_statut}")

        if not eleves:
            ctk.CTkLabel(self.tableau,
                         text="Aucun eleve endette.",
                         font=("Segoe UI", 12),
                         text_color="#999999").pack(pady=40)
            return

        entete = ctk.CTkFrame(self.tableau, fg_color="#f0f0f0", corner_radius=4)
        entete.pack(fill="x", pady=(0, 3))
        for nom, larg in [
            ("Matricule", 100), ("Nom", 110), ("Prenom", 110), ("Classe", 80),
            ("Nb dettes", 90), ("Total du", 120), ("Total paye", 120),
            ("Solde restant", 130),
        ]:
            ctk.CTkLabel(entete, text=nom, font=("Segoe UI", 10, "bold"),
                         text_color=COLOR_NAVY, width=larg,
                         anchor="w").pack(side="left", padx=4, pady=8)
        ctk.CTkLabel(entete, text="Actions", font=("Segoe UI", 10, "bold"),
                     text_color=COLOR_NAVY, width=180,
                     anchor="center").pack(side="left", padx=4, pady=8)

        for i, e in enumerate(eleves):
            fond = "#ffffff" if i % 2 == 0 else "#fafafa"
            ligne = ctk.CTkFrame(self.tableau, fg_color=fond, corner_radius=4)
            ligne.pack(fill="x", pady=1)

            solde = e.get("total_solde", 0)
            couleur_solde = "#e74c3c" if solde > 0 else "#27ae60"

            for val, larg, coul, poids in [
                (e.get("matricule", ""), 100, "#333333", "normal"),
                (e.get("nom", ""), 110, "#333333", "normal"),
                (e.get("prenom", ""), 110, "#333333", "normal"),
                (e.get("classe", ""), 80, "#333333", "normal"),
                (str(e.get("nb_dettes", 0)), 90, "#666666", "normal"),
                (format_montant(e.get("total_du", 0)), 120, "#333333", "normal"),
                (format_montant(e.get("total_paye", 0)), 120, "#27ae60", "normal"),
                (format_montant(solde), 130, couleur_solde, "bold"),
            ]:
                ctk.CTkLabel(ligne, text=str(val),
                             font=("Segoe UI", 11, poids),
                             text_color=coul, width=larg,
                             anchor="w").pack(side="left", padx=4, pady=8)

            actions = ctk.CTkFrame(ligne, fg_color="transparent", width=180)
            actions.pack(side="left", padx=4)

            # Le bouton "Voir / Payer" est visible pour tout le monde :
            # - caissier → encaisser
            # - comptable → voir et annuler
            # - admin/gestionnaire → tout
            ctk.CTkButton(actions, text="Voir / Payer",
                          font=("Segoe UI", 10, "bold"),
                          width=110, height=28,
                          fg_color=COLOR_NAVY, hover_color="#1a3d75",
                          command=lambda ee=e: self._ouvrir_detail(ee)
                          ).pack(side="left", padx=2)

    def _nouvelle_dette(self):
        if not self._peut_creer():
            messagebox.showerror("Acces refuse",
                                 "Vous n'avez pas la permission de creer une dette.")
            return
        FormulaireNouvelleDette(self, self.utilisateur,
                                on_save=self.rafraichir_tableau)

    def _ouvrir_detail(self, eleve):
        ModalDetailEleve(self, eleve, self.utilisateur,
                         on_save=self.rafraichir_tableau,
                         parent_page=self)


# ============================================================
# NOUVELLE DETTE
# ============================================================
class FormulaireNouvelleDette(ctk.CTkToplevel):
    def __init__(self, parent, utilisateur, on_save=None,
                 eleve_pre_selectionne=None):
        super().__init__(parent)
        self.utilisateur = utilisateur
        self.on_save = on_save
        self.eleve_pre_selectionne = eleve_pre_selectionne

        self.title("Nouvelle dette")
        self.configure(fg_color="#F5F7FB")
        setup_adaptive_window(self, largeur_max=500, hauteur_max=640)

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
        boutons.pack(fill="x", padx=30, pady=(10, 15), side="bottom")
        ctk.CTkButton(boutons, text="Annuler",
                      font=("Segoe UI", 12),
                      fg_color="#e74c3c", hover_color="#c0392b",
                      height=40, command=self.destroy
                      ).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(boutons, text="Enregistrer",
                      font=("Segoe UI", 12, "bold"),
                      fg_color=COLOR_NAVY, hover_color="#1a3d75",
                      height=40, command=self._enregistrer
                      ).pack(side="left", expand=True, fill="x", padx=(5, 0))

        ctk.CTkLabel(card, text="NOUVELLE DETTE",
                     font=("Segoe UI", 15, "bold"),
                     text_color=COLOR_NAVY).pack(pady=(15, 10))

        zone = ctk.CTkScrollableFrame(card, fg_color="transparent", corner_radius=0)
        zone.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(zone, text="Rechercher un eleve :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=25, pady=(5, 3), fill="x")
        self.entree_recherche = ctk.CTkEntry(zone, height=36,
                                              placeholder_text="Nom, prenom, matricule...")
        self.entree_recherche.pack(padx=25, pady=(0, 5), fill="x")
        self.entree_recherche.bind("<KeyRelease>", lambda e: self._filtrer())

        self.combo_eleve = ctk.CTkComboBox(zone, values=["-- Aucun --"],
                                            font=("Segoe UI", 11), height=36)
        self.combo_eleve.pack(padx=25, pady=(0, 10), fill="x")
        self.combo_eleve.set("-- Aucun --")

        ctk.CTkLabel(zone, text="Categorie :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=25, pady=(5, 3), fill="x")
        self.combo_categorie = ctk.CTkComboBox(zone, values=CATEGORIES,
                                                font=("Segoe UI", 11), height=36)
        self.combo_categorie.set("Scolarite")
        self.combo_categorie.pack(padx=25, pady=(0, 10), fill="x")

        ctk.CTkLabel(zone, text="Annee (ex: 2024-2025) :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=25, pady=(5, 3), fill="x")
        self.entree_annee = ctk.CTkEntry(zone, height=36,
                                          placeholder_text="2024-2025")
        self.entree_annee.pack(padx=25, pady=(0, 10), fill="x")

        ctk.CTkLabel(zone, text="Montant du :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=25, pady=(5, 3), fill="x")
        self.entree_montant = ctk.CTkEntry(zone, height=40,
                                            font=("Segoe UI", 13, "bold"),
                                            placeholder_text="0")
        self.entree_montant.pack(padx=25, pady=(0, 10), fill="x")

        ctk.CTkLabel(zone, text="Motif (optionnel) :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=25, pady=(5, 3), fill="x")
        self.entree_motif = ctk.CTkEntry(zone, height=36,
                                          placeholder_text="Ex: Reste scolarite 3eme tranche")
        self.entree_motif.pack(padx=25, pady=(0, 10), fill="x")

        self.eleves = liste_eleves_pour_dette()
        self.map_eleve = {}
        self._filtrer()

        if self.eleve_pre_selectionne:
            for label, e in self.map_eleve.items():
                if e["id"] == self.eleve_pre_selectionne.get("eleve_id") or \
                   e["id"] == self.eleve_pre_selectionne.get("id"):
                    self.combo_eleve.set(label)
                    self.entree_recherche.insert(0, e["matricule"])
                    self._filtrer()
                    self.combo_eleve.set(label)
                    break

    def _filtrer(self):
        q = self.entree_recherche.get().strip().lower()
        if not q:
            filtres = self.eleves[:50]
        else:
            filtres = [e for e in self.eleves
                       if q in (e["nom"] + " " + e["prenom"] + " " +
                                e["matricule"]).lower()][:50]

        values = []
        self.map_eleve = {}
        for e in filtres:
            label = f"{e['matricule']} - {e['nom']} {e['prenom']} ({e['classe']})"
            values.append(label)
            self.map_eleve[label] = e
        if not values:
            values = ["-- Aucun --"]
        self.combo_eleve.configure(values=values)
        if self.combo_eleve.get() not in values:
            self.combo_eleve.set(values[0])

    def _enregistrer(self):
        selection = self.combo_eleve.get()
        if selection not in self.map_eleve:
            messagebox.showerror("Erreur", "Selectionnez un eleve.")
            return
        eleve = self.map_eleve[selection]

        annee = self.entree_annee.get().strip()
        if not annee:
            messagebox.showerror("Erreur", "Renseignez l'annee.")
            return

        try:
            montant = float(self.entree_montant.get().strip()
                            .replace(" ", "").replace(",", ""))
        except Exception:
            messagebox.showerror("Erreur", "Montant invalide.")
            return

        if montant <= 0:
            messagebox.showerror("Erreur", "Montant > 0 obligatoire.")
            return

        motif = self.entree_motif.get().strip() or f"Report {annee}"
        categorie = self.combo_categorie.get()

        ok, msg = ajouter_dette(
            eleve["id"], annee, montant, motif, categorie,
            utilisateur_id=self.utilisateur.get("id") if self.utilisateur else None,
        )
        if ok:
            messagebox.showinfo("Dette enregistree", msg)
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Erreur", msg)


# ============================================================
# MODAL DETAIL PAR ELEVE (avec permissions)
# ============================================================
class ModalDetailEleve(ctk.CTkToplevel):
    def __init__(self, parent, eleve, utilisateur, on_save=None,
                 parent_page=None):
        super().__init__(parent)
        self.eleve = eleve
        self.utilisateur = utilisateur
        self.on_save = on_save
        self.parent_page = parent_page

        nom = f"{eleve['nom']} {eleve['prenom']}"
        self.title(f"Detail dettes - {nom}")
        self.configure(fg_color="#F5F7FB")
        setup_adaptive_window(self, largeur_max=920, hauteur_max=600)

        self.bind("<Escape>", lambda e: self.destroy())
        self.transient(parent)
        self.after(100, self._activer_grab)

        self._construire()
        self._rafraichir()

    # ================== PERMISSIONS ==================
    def _peut_creer(self):
        return peut(self.utilisateur, "peut_creer_dette")

    def _peut_encaisser(self):
        return peut(self.utilisateur, "peut_encaisser_dette")

    def _peut_annuler(self):
        return (peut(self.utilisateur, "peut_supprimer_operations_caissier")
                or peut(self.utilisateur, "peut_supprimer"))

    def _activer_grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _construire(self):
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        # ===== BOUTONS DU BAS =====
        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=20, pady=(5, 15), side="bottom")

        # Bouton "Ajouter une categorie" : seulement si peut_creer_dette
        if self._peut_creer():
            ctk.CTkButton(boutons, text="Ajouter une categorie",
                          font=("Segoe UI", 11, "bold"),
                          fg_color=COLOR_NAVY, hover_color="#1a3d75",
                          height=38, width=180,
                          command=self._ajouter_categorie
                          ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(boutons, text="Fermer",
                      font=("Segoe UI", 11),
                      fg_color="#999999", hover_color="#777777",
                      height=38, width=120,
                      command=self.destroy
                      ).pack(side="right")

        # ===== EN-TETE =====
        entete = ctk.CTkFrame(card, fg_color="transparent")
        entete.pack(fill="x", padx=20, pady=(15, 5))

        ctk.CTkLabel(
            entete,
            text=f"{self.eleve['nom']} {self.eleve['prenom']}",
            font=("Segoe UI", 18, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        ctk.CTkLabel(
            entete,
            text=f"  {self.eleve['matricule']}  -  {self.eleve['classe']}",
            font=("Segoe UI", 12),
            text_color="#666666",
        ).pack(side="left")

        # ===== STATS =====
        self.cadre_stats = ctk.CTkFrame(card, fg_color="transparent")
        self.cadre_stats.pack(fill="x", padx=20, pady=(10, 15))

        ctk.CTkLabel(card, text="Detail par categorie",
                     font=("Segoe UI", 13, "bold"),
                     text_color=COLOR_NAVY, anchor="w"
                     ).pack(fill="x", padx=20, pady=(5, 5))

        self.tableau = ctk.CTkScrollableFrame(card, fg_color="#FAFAFA",
                                              corner_radius=8)
        self.tableau.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    def _rafraichir(self):
        for w in self.cadre_stats.winfo_children():
            w.destroy()

        dettes = detail_dettes_eleve(self.eleve["eleve_id"])
        total_du = sum(d["montant_initial"] for d in dettes)
        total_paye = sum(d["montant_paye"] for d in dettes)
        total_solde = sum(d["solde"] for d in dettes)

        for titre, valeur, couleur in [
            ("Total du", format_montant(total_du), "#333333"),
            ("Total paye", format_montant(total_paye), "#27ae60"),
            ("Solde restant", format_montant(total_solde),
             "#e74c3c" if total_solde > 0 else "#27ae60"),
        ]:
            c = ctk.CTkFrame(self.cadre_stats, fg_color="#F5F7FB", corner_radius=10)
            c.pack(side="left", expand=True, fill="both", padx=6)
            ctk.CTkLabel(c, text=titre, font=("Segoe UI", 10, "bold"),
                         text_color="#888888").pack(pady=(10, 2))
            ctk.CTkLabel(c, text=valeur, font=("Segoe UI", 16, "bold"),
                         text_color=couleur).pack(pady=(0, 10))

        for w in self.tableau.winfo_children():
            w.destroy()

        if not dettes:
            ctk.CTkLabel(self.tableau, text="Aucune dette pour cet eleve.",
                         font=("Segoe UI", 11),
                         text_color="#999999").pack(pady=30)
            return

        # Colonne Actions : combien de boutons visibles ?
        nb_actions = 0
        if self._peut_encaisser():
            nb_actions += 1
        if self._peut_annuler():
            nb_actions += 1
        largeur_actions = 140 if nb_actions == 2 else (85 if nb_actions == 1 else 0)

        entete = ctk.CTkFrame(self.tableau, fg_color="#ECECEC", corner_radius=4)
        entete.pack(fill="x", pady=(0, 3))
        for nom, larg in [
            ("Categorie", 120), ("Annee", 100), ("Motif", 200),
            ("Montant du", 110), ("Paye", 110), ("Solde", 110), ("Statut", 90),
        ]:
            ctk.CTkLabel(entete, text=nom, font=("Segoe UI", 10, "bold"),
                         text_color=COLOR_NAVY, width=larg,
                         anchor="w").pack(side="left", padx=4, pady=8)

        if nb_actions > 0:
            ctk.CTkLabel(entete, text="Actions", font=("Segoe UI", 10, "bold"),
                         text_color=COLOR_NAVY, width=largeur_actions,
                         anchor="center").pack(side="left", padx=4, pady=8)

        for i, d in enumerate(dettes):
            fond = "#ffffff" if i % 2 == 0 else "#FAFAFA"
            ligne = ctk.CTkFrame(self.tableau, fg_color=fond, corner_radius=4)
            ligne.pack(fill="x", pady=1)

            statut = d.get("statut", "en_cours")
            couleur = {"en_cours": "#e74c3c",
                       "soldee": "#27ae60",
                       "annulee": "#999999"}.get(statut, "#333333")
            texte = {"en_cours": "En cours",
                     "soldee": "Soldee",
                     "annulee": "Annulee"}.get(statut, statut)

            for val, larg, coul, poids in [
                (d.get("categorie", ""), 120, "#333333", "bold"),
                (d.get("annee_libelle", ""), 100, "#666666", "normal"),
                (d.get("motif", "") or "", 200, "#666666", "normal"),
                (format_montant(d.get("montant_initial", 0)), 110, "#333333", "normal"),
                (format_montant(d.get("montant_paye", 0)), 110, "#27ae60", "normal"),
                (format_montant(d.get("solde", 0)), 110, couleur, "bold"),
                (texte, 90, couleur, "bold"),
            ]:
                ctk.CTkLabel(ligne, text=str(val),
                             font=("Segoe UI", 11, poids),
                             text_color=coul, width=larg,
                             anchor="w").pack(side="left", padx=4, pady=8)

            if nb_actions == 0:
                continue

            actions = ctk.CTkFrame(ligne, fg_color="transparent",
                                    width=largeur_actions)
            actions.pack(side="left", padx=4)

            if statut == "en_cours":
                # Bouton "Payer" : visible si peut_encaisser_dette
                if self._peut_encaisser():
                    ctk.CTkButton(actions, text="Payer",
                                  font=("Segoe UI", 10, "bold"),
                                  width=70, height=26,
                                  fg_color="#27ae60", hover_color="#229954",
                                  command=lambda dd=d: self._payer(dd)
                                  ).pack(side="left", padx=2)

                # Bouton "Annuler" : visible si peut_annuler
                if self._peut_annuler():
                    ctk.CTkButton(actions, text="Annuler",
                                  font=("Segoe UI", 10, "bold"),
                                  width=60, height=26,
                                  fg_color="#999999", hover_color="#777777",
                                  command=lambda dd=d: self._annuler(dd)
                                  ).pack(side="left", padx=2)

    def _payer(self, dette):
        if not self._peut_encaisser():
            messagebox.showerror("Acces refuse",
                                 "Vous n'avez pas la permission d'encaisser.")
            return
        FormulairePaiementDette(self, dette, self.utilisateur,
                                on_save=self._rafraichir)

    def _annuler(self, dette):
        if not self._peut_annuler():
            messagebox.showerror("Acces refuse",
                                 "Vous n'avez pas la permission d'annuler.")
            return
        if messagebox.askyesno(
            "Confirmation",
            f"Annuler la dette '{dette.get('categorie','')}' "
            f"({format_montant(dette['solde'])}) ?"
        ):
            ok, msg = annuler_dette(dette["id"], self.utilisateur.get("id"))
            if ok:
                self._rafraichir()
                if self.on_save:
                    self.on_save()
            else:
                messagebox.showerror("Erreur", msg)

    def _ajouter_categorie(self):
        if not self._peut_creer():
            messagebox.showerror("Acces refuse",
                                 "Vous n'avez pas la permission de creer.")
            return
        FormulaireNouvelleDette(self, self.utilisateur,
                                on_save=self._rafraichir_et_parent,
                                eleve_pre_selectionne=self.eleve)

    def _rafraichir_et_parent(self):
        self._rafraichir()
        if self.on_save:
            self.on_save()


# ============================================================
# PAIEMENT D'UNE DETTE (une categorie)
# ============================================================
class FormulairePaiementDette(ctk.CTkToplevel):
    def __init__(self, parent, dette, utilisateur, on_save=None):
        super().__init__(parent)
        self.dette = dette
        self.utilisateur = utilisateur
        self.on_save = on_save

        self.title(f"Paiement - {dette.get('categorie','')}")
        self.configure(fg_color="#F5F7FB")
        setup_adaptive_window(self, largeur_max=480, hauteur_max=500)

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
        boutons.pack(fill="x", padx=30, pady=(15, 15), side="bottom")
        ctk.CTkButton(boutons, text="Annuler",
                      font=("Segoe UI", 12),
                      fg_color="#e74c3c", hover_color="#c0392b",
                      height=40, command=self.destroy
                      ).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(boutons, text="Encaisser",
                      font=("Segoe UI", 12, "bold"),
                      fg_color="#27ae60", hover_color="#229954",
                      height=40, command=self._enregistrer
                      ).pack(side="left", expand=True, fill="x", padx=(5, 0))

        ctk.CTkLabel(card, text="PAIEMENT",
                     font=("Segoe UI", 15, "bold"),
                     text_color=COLOR_NAVY).pack(pady=(15, 5))
        ctk.CTkLabel(card,
                     text=f"Categorie : {self.dette.get('categorie','')}",
                     font=("Segoe UI", 12, "bold"),
                     text_color="#333333").pack()
        ctk.CTkLabel(card,
                     text=f"Annee : {self.dette.get('annee_libelle', '')}",
                     font=("Segoe UI", 11), text_color="#666666").pack()
        ctk.CTkLabel(card,
                     text=f"Motif : {self.dette.get('motif', '') or '-'}",
                     font=("Segoe UI", 10), text_color="#888888").pack(pady=(0, 5))
        ctk.CTkLabel(card,
                     text=f"Solde restant : {format_montant(self.dette['solde'])}",
                     font=("Segoe UI", 13, "bold"),
                     text_color="#e74c3c").pack(pady=(5, 15))

        zone = ctk.CTkScrollableFrame(card, fg_color="transparent", corner_radius=0)
        zone.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(zone, text="Montant a payer :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=25, pady=(5, 3), fill="x")
        self.entree_montant = ctk.CTkEntry(zone, height=40,
                                            font=("Segoe UI", 13, "bold"),
                                            placeholder_text="0")
        self.entree_montant.pack(padx=25, pady=(0, 8), fill="x")

        ctk.CTkButton(zone,
                      text=f"Payer le solde total ({format_montant(self.dette['solde'])})",
                      font=("Segoe UI", 10, "bold"),
                      fg_color="#e0e0e0", text_color="#333333",
                      hover_color="#c0c0c0", height=30,
                      command=self._remplir_solde).pack(padx=25, pady=(0, 10), fill="x")

        ctk.CTkLabel(zone, text="Mode de paiement :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=25, pady=(5, 3), fill="x")
        self.combo_mode = ctk.CTkComboBox(
            zone, values=["especes", "mobile_money", "banque", "cheque"],
            font=("Segoe UI", 11), height=36)
        self.combo_mode.set("especes")
        self.combo_mode.pack(padx=25, pady=(0, 10), fill="x")

    def _remplir_solde(self):
        self.entree_montant.delete(0, "end")
        self.entree_montant.insert(0, str(int(self.dette["solde"])))

    def _enregistrer(self):
        try:
            montant = float(self.entree_montant.get().strip()
                            .replace(" ", "").replace(",", ""))
        except Exception:
            messagebox.showerror("Erreur", "Montant invalide.")
            return
        if montant <= 0:
            messagebox.showerror("Erreur", "Montant > 0 obligatoire.")
            return

        ok, msg = enregistrer_paiement_dette(
            self.dette["id"], montant, self.combo_mode.get(),
            utilisateur_id=self.utilisateur.get("id") if self.utilisateur else None,
        )
        if ok:
            messagebox.showinfo("Paiement", msg)
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Erreur", msg)