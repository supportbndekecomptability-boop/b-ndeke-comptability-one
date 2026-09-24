"""
Interface de gestion des presences des eleves
Avec filtre par classe, regroupement, et filtre par niveau (Directeur/Prefer).
Permissions :
- admin, gestionnaire, directeur, prefet : peuvent marquer presences
- comptable, caissier : lecture seule
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from config import COLOR_NAVY, COLOR_GOLD, format_montant
from ui.permissions_ui import peut, filtrer_eleves_par_niveau
from core.permissions import get_role, niveaux_autorises
from core.presences import (
    enregistrer_presence, presences_du_jour, presences_par_classe,
    compter_absences_semaine, ignorer_absence,
    statistiques_semaine, eleves_avec_absences_repetees, liste_classes,
)


class PresencesPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")

        self.utilisateur = utilisateur or {}
        self.date_courante = datetime.now().strftime("%Y-%m-%d")
        self.classe_filtre = "Toutes"

        self._construire_interface()
        self.rafraichir_tableau()

    # ================== PERMISSIONS ==================
    def _peut_gerer(self):
        return peut(self.utilisateur, "peut_gerer_presences")

    def _largeur_actions(self):
        return 280 if self._peut_gerer() else 0

    def _classes_autorisees(self):
        """Retourne le set des noms de classes accessibles selon le role."""
        niveaux = niveaux_autorises(self.utilisateur)
        if niveaux is None:
            return None
        try:
            from core.classes import lister_classes as lister_toutes
            return {c["nom"] for c in lister_toutes() if c.get("niveau") in niveaux}
        except Exception:
            return set()

    # ================== INTERFACE ==================
    def _construire_interface(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            top, text="Presences des eleves",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

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

            ctk.CTkLabel(carte, text=titre,
                         font=("Segoe UI", 11, "bold"),
                         text_color="#888888").pack(pady=(15, 3))
            ctk.CTkLabel(carte, text=valeur,
                         font=("Segoe UI", 20, "bold"),
                         text_color=couleur).pack(pady=(0, 15))

        # Barre de saisie
        barre = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        barre.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(barre, text="Date :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#666666").pack(side="left", padx=(15, 3), pady=12)

        self.entree_date = ctk.CTkEntry(
            barre, font=("Segoe UI", 11), width=110, height=32,
        )
        self.entree_date.insert(0, self.date_courante)
        self.entree_date.pack(side="left", padx=3, pady=12)

        ctk.CTkButton(
            barre, text="Charger",
            font=("Segoe UI", 10, "bold"),
            fg_color=COLOR_NAVY, hover_color="#1a3d75",
            height=32, width=80,
            command=self._charger_jour,
        ).pack(side="left", padx=3, pady=12)

        ctk.CTkLabel(barre, text="Classe :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#666666").pack(side="left", padx=(15, 3), pady=12)

        # ===== Liste des classes filtree par niveau autorise =====
        classes_ok = self._classes_autorisees()
        if classes_ok is None:
            self.classes_liste = ["Toutes"] + liste_classes()
        else:
            self.classes_liste = ["Toutes"] + [
                c for c in liste_classes() if c in classes_ok
            ]

        self.combo_classe = ctk.CTkComboBox(
            barre,
            values=self.classes_liste,
            font=("Segoe UI", 11),
            height=32,
            width=140,
            command=self._on_classe_change,
        )
        self.combo_classe.set("Toutes")
        self.combo_classe.pack(side="left", padx=3, pady=12)

        # Bouton "Tout present" : seulement si peut_gerer
        if self._peut_gerer():
            ctk.CTkButton(
                barre, text="Tout present",
                font=("Segoe UI", 10, "bold"),
                fg_color="#27ae60", hover_color="#229954",
                height=32, width=100,
                command=self._tout_present,
            ).pack(side="left", padx=3, pady=12)

        # Bouton Alertes : toujours visible
        ctk.CTkButton(
            barre, text="Alertes",
            font=("Segoe UI", 10, "bold"),
            fg_color="#e74c3c", hover_color="#c0392b",
            height=32, width=80,
            command=self._voir_alertes,
        ).pack(side="left", padx=3, pady=12)

        self.label_compteur = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 12), text_color="#666666",
        )
        self.label_compteur.pack(anchor="w", pady=(0, 10))

        self.tableau = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=10)
        self.tableau.pack(fill="both", expand=True)

    def _charger_jour(self):
        d = self.entree_date.get().strip()
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Erreur", "Format de date invalide (AAAA-MM-JJ).")
            return
        self.date_courante = d
        self.rafraichir_tableau()

    def _on_classe_change(self, valeur):
        self.classe_filtre = valeur
        self.rafraichir_tableau()

    def rafraichir_tableau(self):
        for w in self.tableau.winfo_children():
            w.destroy()

        # Charger selon le filtre de classe
        if self.classe_filtre == "Toutes":
            eleves = presences_par_classe(self.date_courante, None)
        else:
            eleves = presences_par_classe(self.date_courante, self.classe_filtre)

        # ===== FILTRE PAR NIVEAU (Directeur/Prefer) =====
        eleves = filtrer_eleves_par_niveau(eleves, self.utilisateur)

        self.label_compteur.configure(
            text=f"{len(eleves)} eleve(s) — Date : {self.date_courante} — "
                 f"Classe : {self.classe_filtre}"
        )

        if not eleves:
            ctk.CTkLabel(
                self.tableau,
                text="Aucun eleve. Ajoutez des eleves d'abord.",
                font=("Segoe UI", 12), text_color="#999999",
            ).pack(pady=40)
            return

        # ===== REGROUPER PAR CLASSE =====
        groupes = {}
        for e in eleves:
            cl = e.get("classe") or "Sans classe"
            groupes.setdefault(cl, []).append(e)

        # Afficher par classe
        for classe_nom in sorted(groupes.keys()):
            liste = groupes[classe_nom]

            # Titre de classe (en-tete colore)
            titre_classe = ctk.CTkFrame(
                self.tableau, fg_color=COLOR_NAVY, corner_radius=6
            )
            titre_classe.pack(fill="x", pady=(15, 3))

            ctk.CTkLabel(
                titre_classe,
                text=f"  CLASSE : {classe_nom}   ({len(liste)} eleve(s))",
                font=("Segoe UI", 12, "bold"),
                text_color=COLOR_GOLD,
                anchor="w",
            ).pack(side="left", padx=10, pady=8)

            # Stats rapides de la classe
            nb_presents = sum(1 for e in liste if e.get("statut") == "present")
            nb_absents = sum(1 for e in liste if e.get("statut") == "absent")
            nb_retards = sum(1 for e in liste if e.get("statut") == "retard")
            nb_non_saisis = sum(1 for e in liste if not e.get("statut"))

            ctk.CTkLabel(
                titre_classe,
                text=f"Presents: {nb_presents}  |  Absents: {nb_absents}  |  "
                     f"Retards: {nb_retards}  |  Non saisis: {nb_non_saisis}",
                font=("Segoe UI", 10, "bold"),
                text_color="white",
                anchor="e",
            ).pack(side="right", padx=15, pady=8)

            # Entete de tableau pour cette classe
            entete = ctk.CTkFrame(self.tableau, fg_color="#f0f0f0", corner_radius=4)
            entete.pack(fill="x", pady=(0, 3))

            for nom, larg in [
                ("Matricule", 110),
                ("Nom", 130),
                ("Prenom", 130),
                ("Statut", 140),
                ("Abs./sem.", 90),
            ]:
                ctk.CTkLabel(
                    entete, text=nom,
                    font=("Segoe UI", 10, "bold"),
                    text_color=COLOR_NAVY, width=larg, anchor="w",
                ).pack(side="left", padx=4, pady=8)

            if self._peut_gerer():
                ctk.CTkLabel(
                    entete, text="Actions",
                    font=("Segoe UI", 10, "bold"),
                    text_color=COLOR_NAVY, width=self._largeur_actions(),
                    anchor="center",
                ).pack(side="left", padx=4, pady=8)

            # Lignes de la classe
            for i, e in enumerate(liste):
                fond = "#ffffff" if i % 2 == 0 else "#fafafa"
                ligne = ctk.CTkFrame(self.tableau, fg_color=fond, corner_radius=4)
                ligne.pack(fill="x", pady=1)

                statut = e.get("statut")
                non_considere = e.get("non_considere", 0)
                couleur_statut = "#888888"
                texte_statut = "Non saisi"
                if statut == "present":
                    couleur_statut = "#27ae60"
                    texte_statut = "Present"
                elif statut == "absent":
                    if non_considere:
                        couleur_statut = "#999999"
                        texte_statut = "Absent (non cons.)"
                    else:
                        couleur_statut = "#e74c3c"
                        texte_statut = "Absent"
                elif statut == "retard":
                    couleur_statut = "#e67e22"
                    texte_statut = "Retard"

                nb_abs = compter_absences_semaine(e["eleve_id"], self.date_courante)
                couleur_nb = "#e74c3c" if nb_abs >= 3 else "#333333"

                valeurs = [
                    (e["matricule"], 110, "#333333", "normal"),
                    (e["nom"], 130, "#333333", "normal"),
                    (e["prenom"], 130, "#333333", "normal"),
                    (texte_statut, 140, couleur_statut, "bold"),
                    (str(nb_abs), 90, couleur_nb, "bold"),
                ]

                for val, larg, coul, poids in valeurs:
                    ctk.CTkLabel(
                        ligne, text=str(val),
                        font=("Segoe UI", 11, poids),
                        text_color=coul, width=larg, anchor="w",
                    ).pack(side="left", padx=4, pady=8)

                # ===== Actions conditionnelles =====
                if not self._peut_gerer():
                    continue

                actions = ctk.CTkFrame(ligne, fg_color="transparent",
                                        width=self._largeur_actions())
                actions.pack(side="left", padx=4)

                ctk.CTkButton(
                    actions, text="Present",
                    font=("Segoe UI", 10, "bold"),
                    width=75, height=28,
                    fg_color="#27ae60", hover_color="#229954",
                    command=lambda ee=e: self._marquer(ee, "present"),
                ).pack(side="left", padx=2)

                ctk.CTkButton(
                    actions, text="Absent",
                    font=("Segoe UI", 10, "bold"),
                    width=70, height=28,
                    fg_color="#e74c3c", hover_color="#c0392b",
                    command=lambda ee=e: self._marquer(ee, "absent"),
                ).pack(side="left", padx=2)

                ctk.CTkButton(
                    actions, text="Retard",
                    font=("Segoe UI", 10, "bold"),
                    width=70, height=28,
                    fg_color="#e67e22", hover_color="#d35400",
                    command=lambda ee=e: self._marquer(ee, "retard"),
                ).pack(side="left", padx=2)

                if statut == "absent" and e.get("presence_id"):
                    ctk.CTkButton(
                        actions, text="Ignorer",
                        font=("Segoe UI", 10, "bold"),
                        width=60, height=28,
                        fg_color="#999999", hover_color="#777777",
                        command=lambda ee=e: self._ignorer(ee),
                    ).pack(side="left", padx=2)

    def _marquer(self, eleve, statut):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse",
                                 "Vous n'avez pas la permission de gerer les presences.")
            return

        ok, msg, alerte = enregistrer_presence(
            eleve["eleve_id"],
            self.date_courante,
            statut,
            motif="",
            utilisateur_id=self.utilisateur.get("id"),
        )

        if not ok:
            messagebox.showerror("Erreur", msg)
            return

        if alerte:
            messagebox.showwarning(
                "Alerte absences",
                f"ATTENTION\n\n"
                f"L'eleve {alerte['eleve']} a "
                f"{alerte['nb_absences']} absences cette semaine.\n\n"
                f"Veuillez APPELER LES PARENTS immediatement.",
            )

        self.rafraichir_tableau()

    def _ignorer(self, eleve):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        pid = eleve.get("presence_id")
        if not pid:
            return
        rep = messagebox.askyesno(
            "Confirmation",
            f"Ignorer cette absence pour {eleve['nom']} {eleve['prenom']} ?\n\n"
            f"Elle ne sera pas comptee dans l'alerte."
        )
        if rep:
            ok, msg = ignorer_absence(pid, True)
            if ok:
                self.rafraichir_tableau()
            else:
                messagebox.showerror("Erreur", msg)

    def _tout_present(self):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return

        if self.classe_filtre == "Toutes":
            msg = f"Marquer TOUS les eleves presents pour le {self.date_courante} ?"
        else:
            msg = (f"Marquer TOUS les eleves de la classe {self.classe_filtre} "
                   f"presents pour le {self.date_courante} ?")

        rep = messagebox.askyesno("Confirmation", msg)
        if not rep:
            return

        if self.classe_filtre == "Toutes":
            eleves = presences_par_classe(self.date_courante, None)
        else:
            eleves = presences_par_classe(self.date_courante, self.classe_filtre)

        # ===== FILTRE PAR NIVEAU =====
        eleves = filtrer_eleves_par_niveau(eleves, self.utilisateur)

        for e in eleves:
            enregistrer_presence(
                e["eleve_id"], self.date_courante, "present",
                utilisateur_id=self.utilisateur.get("id"),
            )
        self.rafraichir_tableau()
        messagebox.showinfo("Succes", "Eleves marques presents.")

    def _voir_alertes(self):
        eleves = eleves_avec_absences_repetees(self.date_courante)

        # ===== FILTRE PAR NIVEAU =====
        eleves = filtrer_eleves_par_niveau(eleves, self.utilisateur)

        if not eleves:
            messagebox.showinfo(
                "Alertes",
                "Aucun eleve n'a 3 absences ou plus cette semaine."
            )
            return

        texte = "ELEVES AVEC 3 ABSENCES OU PLUS CETTE SEMAINE :\n\n"
        for e in eleves:
            texte += (f"- {e['nom']} {e['prenom']} ({e['classe']}) : "
                      f"{e['nb_absences']} absences\n")
        texte += "\nVeuillez appeler les parents."

        messagebox.showwarning("Alertes absences", texte)