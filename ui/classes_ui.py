"""
Interface de gestion des classes (structure scolaire)
- L'ecole cree ses classes + affecte les frais directement
- Bouton "Charger defaut" / case "Enregistrer comme defaut" par niveau
- Filtre par niveau + groupement visuel
- Pas de mention Budget dans le formulaire (gere dans Parametres)
- Permissions par role : le caissier voit en lecture seule
"""
import customtkinter as ctk
from tkinter import messagebox
from config import COLOR_NAVY, COLOR_GOLD, format_montant, CURRENCY_SYMBOL
from core.classes import (
    NIVEAUX, SOUS_TYPES_SECONDAIRE,
    ajouter_classe, lister_classes, modifier_classe,
    supprimer_classe, compter_eleves_par_classe,
)
from core.frais import (
    lister_frais, lister_frais_par_classe,
    assigner_frais_classe, retirer_frais_classe, total_frais_classe,
    charger_defauts, sauvegarder_defauts, a_des_defauts, description_cle,
)
from ui.permissions_ui import peut


class ClassesPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")
        self.utilisateur = utilisateur or {}
        self.filtre_niveau = "Tous"
        self._construire_interface()
        self.rafraichir_tableau()

    # ================== PERMISSIONS ==================
    def _peut_gerer(self):
        return peut(self.utilisateur, "peut_gerer_classes")

    def _peut_supprimer(self):
        return peut(self.utilisateur, "peut_supprimer")

    def _nb_actions(self):
        n = 0
        if self._peut_gerer():
            n += 2   # Modifier + Activer/Desactiver
        if self._peut_supprimer():
            n += 1   # X
        return n

    def _largeur_actions(self):
        largeur = 0
        if self._peut_gerer():
            largeur += 74 + 79   # Modifier + Desactiver
        if self._peut_supprimer():
            largeur += 38
        return largeur + 12 if largeur > 0 else 60

    # ================== INTERFACE ==================
    def _construire_interface(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(top, text="Classes",
                     font=("Segoe UI", 22, "bold"),
                     text_color=COLOR_NAVY).pack(side="left")

        # Bouton "+ Nouvelle classe" : seulement si peut_gerer_classes
        if self._peut_gerer():
            ctk.CTkButton(top, text="+ Nouvelle classe",
                          font=("Segoe UI", 11, "bold"),
                          fg_color=COLOR_NAVY, hover_color="#1a3d75",
                          height=36, width=160,
                          command=self._nouvelle_classe).pack(side="right")

        barre = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        barre.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(barre, text="Niveau :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#666666").pack(side="left",
                                                 padx=(15, 3), pady=12)

        self.combo_niveau = ctk.CTkComboBox(
            barre, values=["Tous"] + NIVEAUX,
            font=("Segoe UI", 11), height=32, width=150,
            command=self._on_filtre_change,
        )
        self.combo_niveau.set("Tous")
        self.combo_niveau.pack(side="left", padx=3, pady=12)

        ctk.CTkButton(barre, text="Rafraichir",
                      font=("Segoe UI", 10, "bold"),
                      fg_color="#e0e0e0", text_color="#333333",
                      hover_color="#c0c0c0",
                      height=32, width=100,
                      command=self.rafraichir_tableau
                      ).pack(side="right", padx=15, pady=12)

        # Astuce dynamique
        if self._peut_gerer():
            astuce = ("Astuce : 'Modifier' permet d'affecter les frais "
                      "et de desactiver une classe")
        else:
            astuce = "Consultation uniquement (lecture seule pour votre role)"

        cadre_astuce = ctk.CTkFrame(self, fg_color="#FFF7E0", corner_radius=6)
        cadre_astuce.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            cadre_astuce,
            text=astuce,
            font=("Segoe UI", 11),
            text_color="#8B6914",
        ).pack(padx=15, pady=6, anchor="w")

        self.label_compteur = ctk.CTkLabel(self, text="",
                                            font=("Segoe UI", 12),
                                            text_color="#666666")
        self.label_compteur.pack(anchor="w", pady=(0, 10))

        self.tableau = ctk.CTkScrollableFrame(self, fg_color="white",
                                              corner_radius=10)
        self.tableau.pack(fill="both", expand=True)

    def _on_filtre_change(self, valeur):
        self.filtre_niveau = valeur
        self.rafraichir_tableau()

    def rafraichir_tableau(self):
        for w in self.tableau.winfo_children():
            w.destroy()

        niveau = None if self.filtre_niveau == "Tous" else self.filtre_niveau
        classes = lister_classes(niveau=niveau, actif=None)

        self.label_compteur.configure(
            text=f"{len(classes)} classe(s) - Filtre : {self.filtre_niveau}")

        if not classes:
            cadre = ctk.CTkFrame(self.tableau, fg_color="#FFF7E0",
                                  corner_radius=10)
            cadre.pack(fill="x", pady=20, padx=10)

            if self._peut_gerer():
                texte = ("Aucune classe pour le moment.\n\n"
                         "Cliquez sur '+ Nouvelle classe' pour creer "
                         "les classes de votre ecole\n"
                         "et definir les FRAIS a payer pour chacune.")
            else:
                texte = ("Aucune classe pour le moment.\n\n"
                         "Contactez un administrateur pour creer les classes.")

            ctk.CTkLabel(
                cadre,
                text=texte,
                font=("Segoe UI", 12),
                text_color="#8B6914",
                justify="center",
            ).pack(pady=30)

            if self._peut_gerer():
                ctk.CTkButton(
                    cadre,
                    text="+ Creer la premiere classe",
                    font=("Segoe UI", 12, "bold"),
                    fg_color=COLOR_NAVY, hover_color="#1a3d75",
                    height=40, width=220,
                    command=self._nouvelle_classe,
                ).pack(pady=(0, 25))
            return

        groupes = {}
        for c in classes:
            groupes.setdefault(c["niveau"], []).append(c)

        for niveau_nom in NIVEAUX:
            if niveau_nom not in groupes:
                continue
            liste = groupes[niveau_nom]

            titre = ctk.CTkFrame(self.tableau, fg_color=COLOR_NAVY,
                                 corner_radius=6)
            titre.pack(fill="x", pady=(15, 3))

            ctk.CTkLabel(
                titre,
                text=f"  {niveau_nom.upper()}   ({len(liste)} classe(s))",
                font=("Segoe UI", 13, "bold"),
                text_color=COLOR_GOLD,
                anchor="w",
            ).pack(side="left", padx=10, pady=10)

            entete = ctk.CTkFrame(self.tableau, fg_color="#f0f0f0",
                                   corner_radius=4)
            entete.pack(fill="x", pady=(0, 3))

            for nom, larg in [
                ("Nom", 200),
                ("Sous-type", 110),
                ("Ordre", 60),
                ("Eleves", 80),
                ("Nb frais", 90),
                ("Total frais", 130),
                ("Statut", 100),
            ]:
                ctk.CTkLabel(entete, text=nom,
                             font=("Segoe UI", 10, "bold"),
                             text_color=COLOR_NAVY,
                             width=larg, anchor="w"
                             ).pack(side="left", padx=4, pady=8)

            # En-tete Actions : seulement si au moins une action possible
            if self._nb_actions() > 0:
                ctk.CTkLabel(entete, text="Actions",
                             font=("Segoe UI", 10, "bold"),
                             text_color=COLOR_NAVY,
                             width=self._largeur_actions(),
                             anchor="center").pack(side="left", padx=4, pady=8)

            for i, c in enumerate(liste):
                fond = "#ffffff" if i % 2 == 0 else "#fafafa"
                ligne = ctk.CTkFrame(self.tableau, fg_color=fond,
                                      corner_radius=4)
                ligne.pack(fill="x", pady=1)

                actif = c.get("actif", 1)
                nb_eleves = compter_eleves_par_classe(c["nom"])
                frais_classe = lister_frais_par_classe(c["id"])
                nb_frais = len(frais_classe)
                total_frais = total_frais_classe(c["id"])

                sous_type = c.get("sous_type") or "-"
                if sous_type == "base":
                    sous_type_txt = "Educ. base"
                elif sous_type == "option":
                    sous_type_txt = "Option"
                else:
                    sous_type_txt = "-"

                couleur_statut = "#27ae60" if actif else "#999999"
                statut_txt = "Active" if actif else "Desactivee"
                couleur_nom = "#333333" if actif else "#999999"
                couleur_nb_frais = "#e74c3c" if nb_frais == 0 else "#27ae60"
                couleur_total = "#e74c3c" if total_frais == 0 else "#0F2C5C"

                ctk.CTkLabel(ligne, text=c["nom"],
                             font=("Segoe UI", 11, "bold"),
                             text_color=couleur_nom,
                             width=200, anchor="w"
                             ).pack(side="left", padx=4, pady=8)

                ctk.CTkLabel(ligne, text=sous_type_txt,
                             font=("Segoe UI", 10),
                             text_color="#666666",
                             width=110, anchor="w"
                             ).pack(side="left", padx=4, pady=8)

                ctk.CTkLabel(ligne, text=str(c.get("ordre", 0)),
                             font=("Segoe UI", 10),
                             text_color="#666666",
                             width=60, anchor="w"
                             ).pack(side="left", padx=4, pady=8)

                couleur_nb_eleves = "#e74c3c" if nb_eleves > 0 else "#666666"
                ctk.CTkLabel(ligne, text=str(nb_eleves),
                             font=("Segoe UI", 11, "bold"),
                             text_color=couleur_nb_eleves,
                             width=80, anchor="w"
                             ).pack(side="left", padx=4, pady=8)

                ctk.CTkLabel(ligne, text=str(nb_frais),
                             font=("Segoe UI", 11, "bold"),
                             text_color=couleur_nb_frais,
                             width=90, anchor="w"
                             ).pack(side="left", padx=4, pady=8)

                ctk.CTkLabel(ligne,
                             text=format_montant(total_frais) if total_frais > 0 else "-",
                             font=("Segoe UI", 11, "bold"),
                             text_color=couleur_total,
                             width=130, anchor="w"
                             ).pack(side="left", padx=4, pady=8)

                ctk.CTkLabel(ligne, text=statut_txt,
                             font=("Segoe UI", 10, "bold"),
                             text_color=couleur_statut,
                             width=100, anchor="w"
                             ).pack(side="left", padx=4, pady=8)

                # ===== Actions conditionnelles =====
                if self._nb_actions() == 0:
                    continue

                actions = ctk.CTkFrame(ligne, fg_color="transparent",
                                        width=self._largeur_actions())
                actions.pack(side="left", padx=4)

                if self._peut_gerer():
                    ctk.CTkButton(actions, text="Modifier",
                                  font=("Segoe UI", 10, "bold"),
                                  width=70, height=26,
                                  fg_color="#3498db", hover_color="#2980b9",
                                  command=lambda cc=c: self._modifier(cc)
                                  ).pack(side="left", padx=2)

                    if actif:
                        ctk.CTkButton(actions, text="Desactiver",
                                      font=("Segoe UI", 10, "bold"),
                                      width=75, height=26,
                                      fg_color="#999999", hover_color="#777777",
                                      command=lambda cc=c: self._toggle_actif(cc)
                                      ).pack(side="left", padx=2)
                    else:
                        ctk.CTkButton(actions, text="Activer",
                                      font=("Segoe UI", 10, "bold"),
                                      width=65, height=26,
                                      fg_color="#27ae60", hover_color="#229954",
                                      command=lambda cc=c: self._toggle_actif(cc)
                                      ).pack(side="left", padx=2)

                if self._peut_supprimer():
                    ctk.CTkButton(actions, text="X",
                                  font=("Segoe UI", 11, "bold"),
                                  width=34, height=26,
                                  fg_color="#e74c3c", hover_color="#c0392b",
                                  command=lambda cc=c: self._supprimer(cc)
                                  ).pack(side="left", padx=2)

    # ================== ACTIONS ==================
    def _nouvelle_classe(self):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse",
                                 "Vous n'avez pas la permission de gerer les classes.")
            return
        FormulaireClasse(self, self.utilisateur,
                         on_save=self.rafraichir_tableau)

    def _modifier(self, classe):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        FormulaireClasse(self, self.utilisateur,
                         on_save=self.rafraichir_tableau,
                         classe_existante=classe)

    def _toggle_actif(self, classe):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        nouvel_actif = 0 if classe.get("actif") else 1
        ok, msg = modifier_classe(classe["id"], actif=nouvel_actif)
        if ok:
            self.rafraichir_tableau()
        else:
            messagebox.showerror("Erreur", msg)

    def _supprimer(self, classe):
        if not self._peut_supprimer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return

        nb = compter_eleves_par_classe(classe["nom"])
        if nb > 0:
            messagebox.showerror(
                "Impossible",
                f"{nb} eleve(s) sont rattaches a la classe "
                f"'{classe['nom']}'.\n\n"
                f"Desactivez la classe au lieu de la supprimer."
            )
            return

        rep = messagebox.askyesno(
            "Confirmation",
            f"Supprimer la classe '{classe['nom']}' "
            f"({classe['niveau']}) ?\n\n"
            f"Cela supprime aussi les frais affectes a cette classe."
        )
        if not rep:
            return

        ok, msg = supprimer_classe(classe["id"])
        if ok:
            self.rafraichir_tableau()
        else:
            messagebox.showerror("Erreur", msg)


# ============================================================
# FORMULAIRE CLASSE (INCHANGE)
# ============================================================
class FormulaireClasse(ctk.CTkToplevel):
    def __init__(self, parent, utilisateur, on_save=None,
                 classe_existante=None):
        super().__init__(parent)
        self.utilisateur = utilisateur
        self.on_save = on_save
        self.classe_existante = classe_existante
        self.mode_edition = classe_existante is not None

        if self.mode_edition:
            self.title("Modifier classe")
        else:
            self.title("Nouvelle classe")

        self.configure(fg_color="#F5F7FB")

        largeur = 640
        hauteur = 720
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        if hauteur > screen_h - 80:
            hauteur = screen_h - 80
        if largeur > screen_w - 40:
            largeur = screen_w - 40

        x = max(0, (screen_w - largeur) // 2)
        y = max(20, (screen_h - hauteur) // 2)
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")
        self.resizable(False, False)

        self.bind("<Escape>", lambda e: self.destroy())
        self.transient(parent)

        self.etat_frais = {}
        self.lignes_frais = {}

        self._construire()

        self.after(50, self._activer_grab)
        self.after(100, self.lift)

    def _activer_grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _construire(self):
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        card.grid_rowconfigure(0, weight=0)
        card.grid_rowconfigure(1, weight=0)
        card.grid_rowconfigure(2, weight=1)
        card.grid_rowconfigure(3, weight=0)
        card.grid_columnconfigure(0, weight=1)

        titre = "MODIFIER CLASSE" if self.mode_edition else "NOUVELLE CLASSE"
        ctk.CTkLabel(card, text=titre,
                     font=("Segoe UI", 15, "bold"),
                     text_color=COLOR_NAVY
                     ).grid(row=0, column=0, pady=(15, 5), sticky="ew")

        ctk.CTkLabel(card,
                     text="Infos de la classe + frais a payer",
                     font=("Segoe UI", 10),
                     text_color="#888888"
                     ).grid(row=1, column=0, pady=(0, 5), sticky="ew")

        zone = ctk.CTkScrollableFrame(card, fg_color="transparent",
                                       corner_radius=0)
        zone.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.grid(row=3, column=0, sticky="ew", padx=30, pady=(10, 15))

        ctk.CTkButton(boutons, text="Annuler",
                      font=("Segoe UI", 12),
                      fg_color="#e74c3c", hover_color="#c0392b",
                      height=40, command=self.destroy
                      ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        texte_btn = ("Enregistrer les modifications" if self.mode_edition
                     else "Creer la classe")
        ctk.CTkButton(boutons, text=texte_btn,
                      font=("Segoe UI", 12, "bold"),
                      fg_color=COLOR_NAVY, hover_color="#1a3d75",
                      height=40, command=self._enregistrer
                      ).pack(side="left", expand=True, fill="x", padx=(5, 0))

        ctk.CTkLabel(zone, text="Niveau *",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=25, pady=(5, 3), fill="x")

        self.combo_niveau = ctk.CTkComboBox(
            zone, values=NIVEAUX,
            font=("Segoe UI", 12), height=38,
            command=self._on_niveau_change,
        )
        self.combo_niveau.set("Primaire")
        self.combo_niveau.pack(padx=25, pady=(0, 10), fill="x")

        self.frame_sous_type = ctk.CTkFrame(zone, fg_color="transparent")

        ctk.CTkLabel(self.frame_sous_type,
                     text="Type de secondaire *",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=25, pady=(5, 3), fill="x")

        self.combo_sous_type = ctk.CTkComboBox(
            self.frame_sous_type,
            values=["Education de base", "Option"],
            font=("Segoe UI", 12), height=38,
            command=self._on_sous_type_change,
        )
        self.combo_sous_type.set("Education de base")
        self.combo_sous_type.pack(padx=25, pady=(0, 10), fill="x")

        ctk.CTkLabel(zone, text="Nom de la classe *",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=25, pady=(5, 3), fill="x")

        self.entree_nom = ctk.CTkEntry(
            zone, height=38,
            placeholder_text="Ex: Petite section, 1ere annee A, 7eme B, Sciences",
        )
        self.entree_nom.pack(padx=25, pady=(0, 10), fill="x")
        self.entree_nom.bind("<KeyRelease>", lambda e: self._maj_info_defauts())

        self.label_aide = ctk.CTkLabel(
            zone, text="", font=("Segoe UI", 10),
            text_color="#888888",
            justify="left", wraplength=520,
        )
        self.label_aide.pack(padx=25, pady=(0, 10), anchor="w")

        ctk.CTkLabel(zone, text="Ordre d'affichage",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=25, pady=(5, 3), fill="x")

        self.entree_ordre = ctk.CTkEntry(zone, height=36,
                                          placeholder_text="0, 1, 2, ...")
        self.entree_ordre.pack(padx=25, pady=(0, 10), fill="x")

        ctk.CTkLabel(zone, text="Description (optionnel)",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w"
                     ).pack(padx=25, pady=(5, 3), fill="x")

        self.entree_desc = ctk.CTkEntry(zone, height=36,
                                         placeholder_text="Ex: Classe de 25 eleves")
        self.entree_desc.pack(padx=25, pady=(0, 10), fill="x")

        separateur = ctk.CTkFrame(zone, fg_color=COLOR_NAVY, height=3,
                                   corner_radius=2)
        separateur.pack(fill="x", padx=25, pady=(20, 10))

        ligne_entete_frais = ctk.CTkFrame(zone, fg_color="transparent")
        ligne_entete_frais.pack(fill="x", padx=25, pady=(5, 5))

        ctk.CTkLabel(ligne_entete_frais,
                     text="FRAIS A PAYER",
                     font=("Segoe UI", 12, "bold"),
                     text_color=COLOR_NAVY, anchor="w"
                     ).pack(side="left")

        self.btn_charger = ctk.CTkButton(
            ligne_entete_frais,
            text="Charger les defauts",
            font=("Segoe UI", 10, "bold"),
            fg_color="#3498db", hover_color="#2980b9",
            height=30, width=170,
            command=self._charger_defauts,
        )
        self.btn_charger.pack(side="right")

        self.label_defaut = ctk.CTkLabel(
            zone, text="", font=("Segoe UI", 9),
            text_color="#888888", justify="left",
            wraplength=550, anchor="w",
        )
        self.label_defaut.pack(fill="x", padx=25, pady=(0, 8))

        tous_frais = lister_frais(actif=True)

        if not tous_frais:
            cadre = ctk.CTkFrame(zone, fg_color="#FFF3CD", corner_radius=8)
            cadre.pack(fill="x", padx=25, pady=(0, 10))
            ctk.CTkLabel(
                cadre,
                text=("Aucun frais dans le catalogue.\n\n"
                      "Allez dans le menu 'Frais' pour ajouter des frais "
                      "(Scolarite, Inscription, Uniforme...) avant d'en "
                      "affecter a cette classe."),
                font=("Segoe UI", 10, "bold"),
                text_color="#8B6914",
                justify="left", wraplength=480,
            ).pack(padx=15, pady=12, anchor="w")
        else:
            affectations = {}
            if self.mode_edition:
                liste_aff = lister_frais_par_classe(self.classe_existante["id"])
                affectations = {a["frais_id"]: a for a in liste_aff}

            for i, f in enumerate(tous_frais):
                ligne = ctk.CTkFrame(zone, fg_color="#FAFAFA",
                                      corner_radius=6)
                ligne.pack(fill="x", padx=25, pady=2)

                affecte = affectations.get(f["id"])
                etat_initial = bool(affecte)

                btn_toggle = ctk.CTkButton(
                    ligne,
                    text="[X]" if etat_initial else "[ ]",
                    font=("Segoe UI", 12, "bold"),
                    width=40, height=28,
                    fg_color="#27ae60" if etat_initial else "#e0e0e0",
                    text_color="white" if etat_initial else "#666666",
                    hover_color="#229954" if etat_initial else "#c0c0c0",
                )
                btn_toggle.pack(side="left", padx=(10, 5), pady=8)
                btn_toggle.configure(
                    command=lambda fid=f["id"]: self._toggle_frais(fid)
                )

                self.etat_frais[f["id"]] = etat_initial

                ctk.CTkLabel(ligne, text=f["nom"],
                             font=("Segoe UI", 11, "bold"),
                             text_color="#333333",
                             width=200, anchor="w"
                             ).pack(side="left", padx=4, pady=8)

                entree = ctk.CTkEntry(ligne, height=32, width=130,
                                       font=("Segoe UI", 11, "bold"),
                                       placeholder_text="0")
                init = ""
                if affecte and affecte.get("montant_classe"):
                    init = str(int(affecte["montant_classe"]))
                elif f.get("montant_defaut"):
                    init = str(int(f["montant_defaut"]))
                if init:
                    entree.insert(0, init)
                entree.pack(side="left", padx=4, pady=8)
                entree.bind("<KeyRelease>", lambda e: self._maj_total())

                ctk.CTkLabel(ligne, text=CURRENCY_SYMBOL,
                             font=("Segoe UI", 10, "bold"),
                             text_color="#666666",
                             width=30).pack(side="left", padx=(2, 5))

                self.lignes_frais[f["id"]] = {
                    "frais": f,
                    "btn_toggle": btn_toggle,
                    "entree": entree,
                }

            self.label_total = ctk.CTkLabel(zone, text="",
                                             font=("Segoe UI", 13, "bold"),
                                             text_color="#e74c3c")
            self.label_total.pack(padx=25, pady=(10, 5), anchor="w")

        ligne_def = ctk.CTkFrame(zone, fg_color="#FFF3E0", corner_radius=8)
        ligne_def.pack(fill="x", padx=25, pady=(15, 15))

        self.etat_sauver_defaut = False
        self.btn_sauver_defaut = ctk.CTkButton(
            ligne_def,
            text="[ ] Enregistrer comme DEFAUT du niveau",
            font=("Segoe UI", 10, "bold"),
            width=380, height=36,
            fg_color="#e0e0e0", text_color="#8B6914",
            hover_color="#c0c0c0",
            command=self._toggle_sauver_defaut,
        )
        self.btn_sauver_defaut.pack(padx=15, pady=10, anchor="w")

        ctk.CTkLabel(
            ligne_def,
            text="(Ces frais seront proposes automatiquement pour les "
                 "prochaines classes du meme niveau)",
            font=("Segoe UI", 9), text_color="#888888",
            justify="left", wraplength=520,
        ).pack(padx=15, pady=(0, 10), anchor="w")

        if self.mode_edition:
            self._pre_remplir()

        self._on_niveau_change(self.combo_niveau.get())

    def _toggle_frais(self, frais_id):
        nouvel_etat = not self.etat_frais.get(frais_id, False)
        self.etat_frais[frais_id] = nouvel_etat

        ligne = self.lignes_frais.get(frais_id)
        if not ligne:
            return
        btn = ligne["btn_toggle"]
        if nouvel_etat:
            btn.configure(text="[X]", fg_color="#27ae60",
                          text_color="white", hover_color="#229954")
        else:
            btn.configure(text="[ ]", fg_color="#e0e0e0",
                          text_color="#666666", hover_color="#c0c0c0")
        self._maj_total()

    def _toggle_sauver_defaut(self):
        self.etat_sauver_defaut = not self.etat_sauver_defaut
        if self.etat_sauver_defaut:
            self.btn_sauver_defaut.configure(
                text="[X] Enregistrer comme DEFAUT du niveau",
                fg_color="#e67e22", text_color="white",
                hover_color="#d35400",
            )
        else:
            self.btn_sauver_defaut.configure(
                text="[ ] Enregistrer comme DEFAUT du niveau",
                fg_color="#e0e0e0", text_color="#8B6914",
                hover_color="#c0c0c0",
            )

    def _on_niveau_change(self, valeur):
        if valeur == "Secondaire":
            self.frame_sous_type.pack(fill="x", padx=0, pady=0,
                                       before=self.entree_nom.master
                                       if False else None)
            self.frame_sous_type.pack(fill="x", padx=0, pady=0)
            self.label_aide.configure(
                text=("Secondaire :\n"
                      "  - Education de base : 7eme A, 7eme B, 8eme A, 8eme B\n"
                      "  - Option : Sciences, Commerciale, Litteraire, ...")
            )
        else:
            self.frame_sous_type.pack_forget()
            if valeur == "Maternelle":
                self.label_aide.configure(
                    text="Maternelle : Petite section, Moyenne section, "
                         "Grande section (ou personnalise)"
                )
            else:
                self.label_aide.configure(
                    text="Primaire : 1ere annee, 2eme annee, ... "
                         "(vous pouvez faire A, B, C...)"
                )
        self._maj_info_defauts()

    def _on_sous_type_change(self, valeur):
        self._maj_info_defauts()

    def _maj_info_defauts(self):
        if not hasattr(self, "label_defaut"):
            return

        niveau = self.combo_niveau.get()
        sous_type = None
        option_nom = None

        if niveau == "Secondaire":
            st = self.combo_sous_type.get()
            sous_type = "base" if st == "Education de base" else "option"
            if sous_type == "option":
                option_nom = self.entree_nom.get().strip() or "?"

        desc = description_cle(niveau, sous_type, option_nom)

        if a_des_defauts(niveau, sous_type, option_nom):
            self.label_defaut.configure(
                text=f"Defaut existant pour : {desc}  -  "
                     f"Cliquez sur 'Charger les defauts'",
                text_color="#1565C0",
            )
            self.btn_charger.configure(state="normal")
        else:
            self.label_defaut.configure(
                text=f"Aucun defaut pour : {desc}  -  "
                     f"Remplissez + cochez 'Enregistrer comme defaut'",
                text_color="#888888",
            )
            self.btn_charger.configure(state="disabled")

    def _charger_defauts(self):
        niveau = self.combo_niveau.get()
        sous_type = None
        option_nom = None

        if niveau == "Secondaire":
            st = self.combo_sous_type.get()
            sous_type = "base" if st == "Education de base" else "option"
            if sous_type == "option":
                option_nom = self.entree_nom.get().strip() or None
                if not option_nom:
                    messagebox.showwarning(
                        "Nom requis",
                        "Tapez d'abord le NOM de l'option (ex: Sciences) "
                        "pour charger ses frais par defaut."
                    )
                    return

        defauts = charger_defauts(niveau, sous_type, option_nom)

        if not defauts:
            messagebox.showinfo("Aucun defaut",
                                "Aucun frais par defaut enregistre pour ce niveau.")
            return

        nb = 0
        for fid, ligne in self.lignes_frais.items():
            if fid in defauts:
                self.etat_frais[fid] = True
                ligne["btn_toggle"].configure(
                    text="[X]", fg_color="#27ae60",
                    text_color="white", hover_color="#229954",
                )
                ligne["entree"].delete(0, "end")
                ligne["entree"].insert(0, str(int(defauts[fid])))
                nb += 1
            else:
                self.etat_frais[fid] = False
                ligne["btn_toggle"].configure(
                    text="[ ]", fg_color="#e0e0e0",
                    text_color="#666666", hover_color="#c0c0c0",
                )
                ligne["entree"].delete(0, "end")

        self._maj_total()
        messagebox.showinfo("Defauts charges",
                            f"{nb} frais charges depuis le defaut du niveau.")

    def _pre_remplir(self):
        c = self.classe_existante
        self.combo_niveau.set(c.get("niveau", "Primaire"))

        if c.get("sous_type") == "base":
            self.combo_sous_type.set("Education de base")
        elif c.get("sous_type") == "option":
            self.combo_sous_type.set("Option")

        self.entree_nom.delete(0, "end")
        self.entree_nom.insert(0, c.get("nom", ""))

        self.entree_ordre.delete(0, "end")
        self.entree_ordre.insert(0, str(c.get("ordre", 0)))

        self.entree_desc.delete(0, "end")
        self.entree_desc.insert(0, c.get("description", "") or "")

        self._on_niveau_change(self.combo_niveau.get())

    def _maj_total(self):
        total = 0
        nb = 0
        for fid, l in self.lignes_frais.items():
            if self.etat_frais.get(fid, False):
                try:
                    m = float(l["entree"].get().strip()
                              .replace(" ", "").replace(",", "") or 0)
                except ValueError:
                    m = 0
                total += m
                if m > 0:
                    nb += 1

        if hasattr(self, "label_total"):
            self.label_total.configure(
                text=f"TOTAL a payer pour cette classe : "
                     f"{format_montant(total)}   ({nb} frais)"
            )

    def _enregistrer(self):
        niveau = self.combo_niveau.get()
        nom = self.entree_nom.get().strip()

        if not nom:
            messagebox.showerror("Erreur", "Le nom de la classe est obligatoire.")
            return

        sous_type = None
        if niveau == "Secondaire":
            st = self.combo_sous_type.get()
            sous_type = "base" if st == "Education de base" else "option"

        try:
            ordre = int(self.entree_ordre.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "L'ordre doit etre un nombre entier.")
            return

        desc = self.entree_desc.get().strip()

        frais_a_enregistrer = []
        for fid, l in self.lignes_frais.items():
            if self.etat_frais.get(fid, False):
                try:
                    m = float(l["entree"].get().strip()
                              .replace(" ", "").replace(",", "") or 0)
                except ValueError:
                    messagebox.showerror(
                        "Erreur",
                        f"Montant invalide pour '{l['frais']['nom']}'."
                    )
                    return
                if m <= 0:
                    messagebox.showerror(
                        "Erreur",
                        f"Montant > 0 obligatoire pour '{l['frais']['nom']}'."
                    )
                    return
                frais_a_enregistrer.append((fid, m))

        if self.mode_edition:
            ok, msg = modifier_classe(
                self.classe_existante["id"],
                nom=nom, ordre=ordre, description=desc,
                sous_type=sous_type,
            )
            classe_id = self.classe_existante["id"] if ok else None
        else:
            ok, msg = ajouter_classe(niveau, nom, sous_type=sous_type,
                                      ordre=ordre, description=desc)
            classe_id = None
            if ok:
                for cc in lister_classes():
                    if cc["nom"] == nom and cc["niveau"] == niveau:
                        classe_id = cc["id"]
                        break

        if not ok or not classe_id:
            messagebox.showerror("Erreur", msg or "Impossible de creer la classe.")
            return

        for fid in self.lignes_frais.keys():
            retirer_frais_classe(fid, classe_id)

        erreurs = []
        for fid, montant in frais_a_enregistrer:
            ok2, msg2 = assigner_frais_classe(fid, classe_id, montant)
            if not ok2:
                erreurs.append(msg2)

        if erreurs:
            messagebox.showwarning(
                "Attention",
                "Classe enregistree, mais certaines affectations ont echoue :\n\n"
                + "\n".join(erreurs)
            )

        if self.etat_sauver_defaut:
            option_nom = None
            if niveau == "Secondaire" and sous_type == "option":
                option_nom = nom

            ok_d, msg_d = sauvegarder_defauts(
                niveau, sous_type, option_nom, frais_a_enregistrer
            )
            if not ok_d:
                messagebox.showwarning(
                    "Defauts",
                    f"Frais enregistres mais defauts non sauvegardes :\n{msg_d}"
                )

        nb = len(frais_a_enregistrer)
        messagebox.showinfo(
            "Succes",
            f"Classe '{nom}' {'modifiee' if self.mode_edition else 'creee'} "
            f"avec {nb} frais affecte(s)."
            + ("\n\nDefauts enregistres pour ce niveau."
               if self.etat_sauver_defaut else "")
        )

        if self.on_save:
            self.on_save()
        self.destroy()