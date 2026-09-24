"""
Interface Presences du personnel
Avec filtre par niveau : Directeur (Maternelle+Primaire), Prefet (Secondaire)
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from config import COLOR_NAVY, COLOR_GOLD, format_montant
from ui.permissions_ui import peut, filtrer_par_niveau
from core.permissions import get_role, niveaux_autorises
from core.presences_personnel import (
    enregistrer_presence, presences_par_fonction,
    compter_absences_semaine, ignorer_absence,
    statistiques_semaine, liste_fonctions,
    ajouter_retenue,
)


class PresencesPersonnelPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")
        self.utilisateur = utilisateur or {}
        self.date_courante = datetime.now().strftime("%Y-%m-%d")
        self.fonction_filtre = "Toutes"
        self._construire_interface()
        self.rafraichir_tableau()

    # ================== PERMISSIONS ==================
    def _peut_gerer(self):
        return peut(self.utilisateur, "peut_gerer_presences_personnel")

    def _largeur_actions(self):
        return 340 if self._peut_gerer() else 0

    def _construire_interface(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(top, text="Presences du personnel",
                     font=("Segoe UI", 22, "bold"),
                     text_color=COLOR_NAVY).pack(side="left")

        # Badge role
        if self._peut_gerer():
            info_role = "Vue : gestion des presences"
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

        # Badge niveaux autorises
        niveaux = niveaux_autorises(self.utilisateur)
        if niveaux:
            ctk.CTkLabel(
                top,
                text=" | ".join(niveaux),
                font=("Segoe UI", 10, "bold"),
                text_color="#8e44ad",
            ).pack(side="right", padx=(0, 15), pady=(8, 0))

        # Stats
        stats = statistiques_semaine()
        ligne_stats = ctk.CTkFrame(self, fg_color="transparent")
        ligne_stats.pack(fill="x", pady=(0, 15))
        for titre, valeur, couleur in [
            ("Presents (semaine)", str(stats["nb_presents"]), "#27ae60"),
            ("Absents (semaine)", str(stats["nb_absents"]), "#e74c3c"),
            ("Retards (semaine)", str(stats["nb_retards"]), "#e67e22"),
        ]:
            carte = ctk.CTkFrame(ligne_stats, fg_color="white", corner_radius=12)
            carte.pack(side="left", expand=True, fill="both", padx=6)
            ctk.CTkLabel(carte, text=titre, font=("Segoe UI", 11, "bold"),
                         text_color="#888888").pack(pady=(15, 3))
            ctk.CTkLabel(carte, text=valeur, font=("Segoe UI", 20, "bold"),
                         text_color=couleur).pack(pady=(0, 15))

        # Barre de saisie
        barre = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        barre.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(barre, text="Date :", font=("Segoe UI", 11, "bold"),
                     text_color="#666666").pack(side="left", padx=(15, 3), pady=12)
        self.entree_date = ctk.CTkEntry(barre, font=("Segoe UI", 11),
                                        width=110, height=32)
        self.entree_date.insert(0, self.date_courante)
        self.entree_date.pack(side="left", padx=3, pady=12)
        ctk.CTkButton(barre, text="Charger", font=("Segoe UI", 10, "bold"),
                      fg_color=COLOR_NAVY, hover_color="#1a3d75",
                      height=32, width=80,
                      command=self._charger_jour).pack(side="left", padx=3, pady=12)

        ctk.CTkLabel(barre, text="Fonction :", font=("Segoe UI", 11, "bold"),
                     text_color="#666666").pack(side="left", padx=(15, 3), pady=12)
        self.combo_fonction = ctk.CTkComboBox(
            barre, values=["Toutes"] + liste_fonctions(),
            font=("Segoe UI", 11), height=32, width=150,
            command=self._on_fonction_change)
        self.combo_fonction.set("Toutes")
        self.combo_fonction.pack(side="left", padx=3, pady=12)

        # Bouton "Tout present" : seulement si peut_gerer
        if self._peut_gerer():
            ctk.CTkButton(barre, text="Tout present", font=("Segoe UI", 10, "bold"),
                          fg_color="#27ae60", hover_color="#229954",
                          height=32, width=100,
                          command=self._tout_present).pack(side="left", padx=3, pady=12)

        self.label_compteur = ctk.CTkLabel(self, text="", font=("Segoe UI", 12),
                                           text_color="#666666")
        self.label_compteur.pack(anchor="w", pady=(0, 10))

        self.tableau = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=10)
        self.tableau.pack(fill="both", expand=True)

    def _charger_jour(self):
        d = self.entree_date.get().strip()
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Erreur", "Format invalide (AAAA-MM-JJ).")
            return
        self.date_courante = d
        self.rafraichir_tableau()

    def _on_fonction_change(self, valeur):
        self.fonction_filtre = valeur
        self.rafraichir_tableau()

    def rafraichir_tableau(self):
        for w in self.tableau.winfo_children():
            w.destroy()

        membres = presences_par_fonction(
            self.date_courante,
            None if self.fonction_filtre == "Toutes" else self.fonction_filtre)

        # ===== FILTRE PAR NIVEAU =====
        membres = filtrer_par_niveau(membres, self.utilisateur, cle_niveau="niveau")

        self.label_compteur.configure(
            text=f"{len(membres)} personne(s) - Date : {self.date_courante} - "
                 f"Fonction : {self.fonction_filtre}")

        if not membres:
            ctk.CTkLabel(self.tableau, text="Aucun personnel.",
                         font=("Segoe UI", 12),
                         text_color="#999999").pack(pady=40)
            return

        groupes = {}
        for m in membres:
            fn = m.get("fonction") or "Sans fonction"
            groupes.setdefault(fn, []).append(m)

        for fonction_nom in sorted(groupes.keys()):
            liste = groupes[fonction_nom]
            titre = ctk.CTkFrame(self.tableau, fg_color=COLOR_NAVY, corner_radius=6)
            titre.pack(fill="x", pady=(15, 3))
            ctk.CTkLabel(titre,
                         text=f"  FONCTION : {fonction_nom}   ({len(liste)})",
                         font=("Segoe UI", 12, "bold"),
                         text_color=COLOR_GOLD,
                         anchor="w").pack(side="left", padx=10, pady=8)

            entete = ctk.CTkFrame(self.tableau, fg_color="#f0f0f0", corner_radius=4)
            entete.pack(fill="x", pady=(0, 3))

            # Colonne "Niveau" ajoutee
            for nom, larg in [("Code", 90), ("Nom", 120), ("Prenom", 120),
                              ("Niveau", 90), ("Statut", 140), ("Abs./sem.", 90)]:
                ctk.CTkLabel(entete, text=nom, font=("Segoe UI", 10, "bold"),
                             text_color=COLOR_NAVY, width=larg,
                             anchor="w").pack(side="left", padx=4, pady=8)

            if self._peut_gerer():
                ctk.CTkLabel(entete, text="Actions", font=("Segoe UI", 10, "bold"),
                             text_color=COLOR_NAVY, width=self._largeur_actions(),
                             anchor="center").pack(side="left", padx=4, pady=8)

            for i, m in enumerate(liste):
                fond = "#ffffff" if i % 2 == 0 else "#fafafa"
                ligne = ctk.CTkFrame(self.tableau, fg_color=fond, corner_radius=4)
                ligne.pack(fill="x", pady=1)

                statut = m.get("statut")
                nc = m.get("non_considere", 0)
                couleur = "#888888"
                texte = "Non saisi"
                if statut == "present":
                    couleur, texte = "#27ae60", "Present"
                elif statut == "absent":
                    if nc:
                        couleur, texte = "#999999", "Absent (non cons.)"
                    else:
                        couleur, texte = "#e74c3c", "Absent"
                elif statut == "retard":
                    couleur, texte = "#e67e22", "Retard"

                nb = compter_absences_semaine(m["personnel_id"],
                                               self.date_courante)
                cn = "#e74c3c" if nb >= 3 else "#333333"

                # Niveau : couleur selon le type
                niveau = m.get("niveau") or "-"
                couleur_niveau = {
                    "Maternelle": "#e67e22",
                    "Primaire": "#27ae60",
                    "Secondaire": "#3498db",
                }.get(niveau, "#999999")

                valeurs = [
                    (m["code"], 90, "#333333", "normal"),
                    (m["nom"], 120, "#333333", "normal"),
                    (m["prenom"], 120, "#333333", "normal"),
                    (niveau, 90, couleur_niveau, "bold"),
                    (texte, 140, couleur, "bold"),
                    (str(nb), 90, cn, "bold"),
                ]

                for val, larg, coul, poids in valeurs:
                    ctk.CTkLabel(ligne, text=str(val),
                                 font=("Segoe UI", 11, poids),
                                 text_color=coul, width=larg,
                                 anchor="w").pack(side="left", padx=4, pady=8)

                # Actions conditionnelles
                if not self._peut_gerer():
                    continue

                actions = ctk.CTkFrame(ligne, fg_color="transparent",
                                       width=self._largeur_actions())
                actions.pack(side="left", padx=4)

                ctk.CTkButton(actions, text="Present",
                              font=("Segoe UI", 10, "bold"),
                              width=70, height=28, fg_color="#27ae60",
                              hover_color="#229954",
                              command=lambda mm=m: self._marquer(mm, "present")
                              ).pack(side="left", padx=2)
                ctk.CTkButton(actions, text="Absent",
                              font=("Segoe UI", 10, "bold"),
                              width=65, height=28, fg_color="#e74c3c",
                              hover_color="#c0392b",
                              command=lambda mm=m: self._marquer(mm, "absent")
                              ).pack(side="left", padx=2)
                ctk.CTkButton(actions, text="Retard",
                              font=("Segoe UI", 10, "bold"),
                              width=65, height=28, fg_color="#e67e22",
                              hover_color="#d35400",
                              command=lambda mm=m: self._marquer(mm, "retard")
                              ).pack(side="left", padx=2)

                if statut == "absent" and m.get("presence_id"):
                    ctk.CTkButton(actions, text="Retenue",
                                  font=("Segoe UI", 10, "bold"),
                                  width=75, height=28, fg_color="#9b59b6",
                                  hover_color="#8e44ad",
                                  command=lambda mm=m: self._retenue(mm)
                                  ).pack(side="left", padx=2)
                    ctk.CTkButton(actions, text="Ignorer",
                                  font=("Segoe UI", 10, "bold"),
                                  width=60, height=28, fg_color="#999999",
                                  hover_color="#777777",
                                  command=lambda mm=m: self._ignorer(mm)
                                  ).pack(side="left", padx=2)

    # ================== ACTIONS ==================
    def _marquer(self, membre, statut):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse",
                                 "Vous n'avez pas la permission de gerer les presences.")
            return
        ok, msg = enregistrer_presence(
            membre["personnel_id"], self.date_courante, statut,
            utilisateur_id=self.utilisateur.get("id"))
        if not ok:
            messagebox.showerror("Erreur", msg)
            return
        self.rafraichir_tableau()

    def _ignorer(self, membre):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        pid = membre.get("presence_id")
        if not pid:
            return
        if messagebox.askyesno(
            "Confirmation",
            f"Ignorer cette absence pour {membre['nom']} {membre['prenom']} ?"
        ):
            ignorer_absence(pid, True)
            self.rafraichir_tableau()

    def _retenue(self, membre):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        salaire = membre.get("salaire_mensuel", 0) or 0
        FormulaireRetenue(self, membre, salaire, self.date_courante,
                          self.utilisateur, on_save=self.rafraichir_tableau)

    def _tout_present(self):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        if not messagebox.askyesno("Confirmation",
                                    "Marquer tout le personnel present ?"):
            return
        membres = presences_par_fonction(
            self.date_courante,
            None if self.fonction_filtre == "Toutes" else self.fonction_filtre)
        # Filtrer aussi par niveau
        membres = filtrer_par_niveau(membres, self.utilisateur, cle_niveau="niveau")
        for m in membres:
            enregistrer_presence(m["personnel_id"], self.date_courante,
                                 "present",
                                 utilisateur_id=self.utilisateur.get("id"))
        self.rafraichir_tableau()


class FormulaireRetenue(ctk.CTkToplevel):
    def __init__(self, parent, membre, salaire, date_ref, utilisateur,
                 on_save=None):
        super().__init__(parent)
        self.membre = membre
        self.salaire = salaire
        self.date_ref = date_ref
        self.utilisateur = utilisateur
        self.on_save = on_save

        self.title(f"Retenue - {membre['nom']} {membre['prenom']}")
        self.geometry("480x480")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        x = (self.winfo_screenwidth() // 2) - 240
        y = max(20, (self.winfo_screenheight() // 2) - 240)
        self.geometry(f"480x480+{x}+{y}")

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

        ctk.CTkLabel(card, text="RETENUE SUR SALAIRE",
                     font=("Segoe UI", 15, "bold"),
                     text_color=COLOR_NAVY).pack(pady=(15, 5))
        ctk.CTkLabel(
            card,
            text=f"{self.membre['nom']} {self.membre['prenom']} "
                 f"({self.membre['code']})",
            font=("Segoe UI", 11), text_color="#666666").pack()
        ctk.CTkLabel(card,
                     text=f"Salaire mensuel : {format_montant(self.salaire)}",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#27ae60").pack(pady=(5, 15))

        ctk.CTkLabel(card, text="Type de retenue :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=30, pady=(5, 3), fill="x")
        self.var_type = ctk.StringVar(value="pourcentage")
        ligne_type = ctk.CTkFrame(card, fg_color="transparent")
        ligne_type.pack(fill="x", padx=30, pady=(0, 5))
        ctk.CTkRadioButton(ligne_type, text="Pourcentage (%)",
                           variable=self.var_type, value="pourcentage",
                           font=("Segoe UI", 11, "bold"),
                           command=self._maj_montant
                           ).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(ligne_type, text="Montant fixe",
                           variable=self.var_type, value="montant",
                           font=("Segoe UI", 11, "bold"),
                           command=self._maj_montant).pack(side="left")

        ctk.CTkLabel(card, text="Valeur :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=30, pady=(10, 3), fill="x")
        self.entree_valeur = ctk.CTkEntry(card,
                                          font=("Segoe UI", 13, "bold"),
                                          height=40, placeholder_text="0")
        self.entree_valeur.pack(padx=30, pady=(0, 5), fill="x")
        self.entree_valeur.bind("<KeyRelease>",
                                lambda e: self._maj_montant())

        self.label_apercu = ctk.CTkLabel(card,
                                          text="Montant calcule : --",
                                          font=("Segoe UI", 12, "bold"),
                                          text_color="#9b59b6")
        self.label_apercu.pack(pady=(5, 10))

        ctk.CTkLabel(card, text="Motif (optionnel) :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=30, pady=(5, 3), fill="x")
        self.entree_motif = ctk.CTkEntry(
            card, font=("Segoe UI", 11), height=36,
            placeholder_text="Ex: Absence non justifiee")
        self.entree_motif.pack(padx=30, pady=(0, 10), fill="x")

        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=30, pady=(5, 15))
        ctk.CTkButton(boutons, text="Annuler",
                      font=("Segoe UI", 12),
                      fg_color="#e74c3c", hover_color="#c0392b",
                      height=40, command=self.destroy
                      ).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(boutons, text="Appliquer",
                      font=("Segoe UI", 12, "bold"),
                      fg_color="#9b59b6", hover_color="#8e44ad",
                      height=40, command=self._enregistrer
                      ).pack(side="left", expand=True, fill="x", padx=(5, 0))

    def _maj_montant(self):
        try:
            s = self.entree_valeur.get().strip().replace(" ", "").replace(",", "")
            v = float(s) if s else 0
        except Exception:
            v = 0
        if self.var_type.get() == "pourcentage":
            m = self.salaire * v / 100.0
            self.label_apercu.configure(
                text=f"Montant calcule : {format_montant(m)} ({v}%)")
        else:
            self.label_apercu.configure(
                text=f"Montant calcule : {format_montant(v)}")

    def _enregistrer(self):
        try:
            s = self.entree_valeur.get().strip().replace(" ", "").replace(",", "")
            v = float(s) if s else 0
        except Exception:
            messagebox.showerror("Erreur", "Valeur invalide.")
            return
        if v <= 0:
            messagebox.showerror("Erreur", "Valeur > 0 obligatoire.")
            return
        if self.var_type.get() == "pourcentage":
            if v > 100:
                messagebox.showerror("Erreur", "Max 100 %.")
                return
            pct, montant = v, self.salaire * v / 100.0
        else:
            pct, montant = 0, v
        motif = self.entree_motif.get().strip() or "Absence"
        ok, msg = ajouter_retenue(
            self.membre["personnel_id"], self.date_ref,
            pourcentage=pct, montant_calcule=montant, motif=motif,
            utilisateur_id=self.utilisateur.get("id") if self.utilisateur else None)
        if ok:
            messagebox.showinfo(
                "Retenue",
                f"Retenue de {format_montant(montant)} enregistree.")
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Erreur", msg)