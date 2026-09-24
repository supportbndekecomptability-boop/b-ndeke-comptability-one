"""
Interface de gestion du personnel
Fenetre adaptative a tout ecran + fonctions predefinies + multi-niveaux.
"""
import customtkinter as ctk
from tkinter import messagebox
from config import COLOR_NAVY, COLOR_GOLD, format_montant, CURRENCY_SYMBOL
from ui.scroll_frame import HorizontalScrollFrame
from core.personnel import (
    ajouter_personnel, lister_personnel, modifier_personnel,
    supprimer_personnel, get_personnel, generer_code
)
from core.avances import total_avance_en_cours
from ui.avances_ui import AvancesWindow
from ui.editer_avances_ui import EditerAvancesWindow
from ui.permissions_ui import peut
from core.permissions import niveaux_autorises


FONCTIONS_PERSONNEL = [
    "Enseignant", "Directeur", "Directeur adjoint", "Prefet",
    "Surveillant", "Conseiller pedagogique", "Ingenieur informaticien",
    "Comptable", "Agent financier", "Gardien", "Chauffeur", "Menager",
    "Secretaire", "Autre",
]

FONCTIONS_MULTI_NIVEAUX = [
    "Conseiller pedagogique",
    "Ingenieur informaticien",
]


class PersonnelPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")
        self.utilisateur = utilisateur or {}
        self._construire_interface()
        self.rafraichir_tableau()

    def _peut_gerer(self):
        return peut(self.utilisateur, "peut_gerer_personnel")

    def _peut_supprimer(self):
        return peut(self.utilisateur, "peut_supprimer")

    def _nb_actions(self):
        n = 0
        if self._peut_gerer():
            n += 5
        if self._peut_supprimer():
            n += 1
        return n

    def _largeur_actions(self):
        n = self._nb_actions()
        return 40 if n == 0 else n * 42 + 10

    def _filtrer_personnel(self, membres):
        niveaux = niveaux_autorises(self.utilisateur)
        if niveaux is None:
            return membres
        resultat = []
        for p in membres:
            val = (p.get("niveau") or "").strip()
            if not val:
                continue
            niveaux_item = [v.strip() for v in val.split(",")]
            if any(n in niveaux for n in niveaux_item):
                resultat.append(p)
        return resultat

    def _construire_interface(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(top, text="Gestion du personnel",
                     font=("Segoe UI", 22, "bold"),
                     text_color=COLOR_NAVY).pack(side="left")

        niveaux = niveaux_autorises(self.utilisateur)
        if niveaux:
            ctk.CTkLabel(top, text=" | ".join(niveaux),
                         font=("Segoe UI", 10, "bold"),
                         text_color="#8e44ad").pack(side="left", padx=(15, 0), pady=(8, 0))

        if self._peut_gerer():
            ctk.CTkButton(top, text="+ Nouveau personnel",
                          font=("Segoe UI", 13, "bold"),
                          fg_color=COLOR_NAVY, hover_color="#1a3d75",
                          height=40,
                          command=self._ouvrir_formulaire).pack(side="right")

        recherche_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        recherche_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(recherche_frame, text="Recherche :",
                     font=("Segoe UI", 12, "bold"),
                     text_color="#666666").pack(side="left", padx=(15, 5), pady=12)

        self.entree_recherche = ctk.CTkEntry(
            recherche_frame,
            placeholder_text="Code, nom, prenom ou fonction...",
            font=("Segoe UI", 13), border_width=0, fg_color="white", height=35)
        self.entree_recherche.pack(side="left", fill="x", expand=True, padx=5, pady=12)
        self.entree_recherche.bind("<KeyRelease>", lambda e: self.rafraichir_tableau())

        ctk.CTkButton(recherche_frame, text="Effacer",
                      font=("Segoe UI", 11), fg_color="#e0e0e0",
                      text_color="#333333", hover_color="#c0c0c0",
                      width=80, height=32,
                      command=self._effacer_recherche).pack(side="right", padx=15, pady=12)

        astuces = ["cliquez sur un code (souligne) pour le copier"]
        if self._peut_gerer():
            astuces += ["P = Payer", "A = Avances", "E = Editer avances",
                        "R = Releve de paie", "M = Modifier"]
        if self._peut_supprimer():
            astuces.append("X = Supprimer")

        if astuces:
            info_frame = ctk.CTkFrame(self, fg_color="#FFF7E0", corner_radius=6)
            info_frame.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(info_frame, text="Astuce : " + "  |  ".join(astuces),
                         font=("Segoe UI", 11),
                         text_color="#8B6914").pack(padx=15, pady=6, anchor="w")

        self.label_compteur = ctk.CTkLabel(self, text="",
                                            font=("Segoe UI", 12),
                                            text_color="#666666")
        self.label_compteur.pack(anchor="w", pady=(0, 10))

        self.tableau = HorizontalScrollFrame(self, fg_color="white", corner_radius=10)
        self.tableau.pack(fill="both", expand=True)
        self._creer_entete()

    def _creer_entete(self):
        entete = ctk.CTkFrame(self.tableau.interior, fg_color="#f0f0f0", corner_radius=6)
        entete.pack(fill="x", pady=(0, 5))

        colonnes = [
            ("Code", 85), ("Nom", 100), ("Prenom", 90), ("Fonction", 100),
            ("Niveau", 85), ("Telephone", 110), ("Salaire/mois", 90),
            ("Mois", 45), ("Engagement", 90), ("Paye", 80),
            ("Reste a payer", 90), ("Avance", 80),
        ]
        for nom, largeur in colonnes:
            ctk.CTkLabel(entete, text=nom, font=("Segoe UI", 11, "bold"),
                         text_color=COLOR_NAVY, width=largeur,
                         anchor="w").pack(side="left", padx=4, pady=10)

        if self._nb_actions() > 0:
            ctk.CTkLabel(entete, text="Actions", font=("Segoe UI", 11, "bold"),
                         text_color=COLOR_NAVY, width=self._largeur_actions(),
                         anchor="center").pack(side="left", padx=4, pady=10)

    def _effacer_recherche(self):
        self.entree_recherche.delete(0, "end")
        self.rafraichir_tableau()

    def rafraichir_tableau(self):
        self.tableau.clear()
        self._creer_entete()
        recherche = self.entree_recherche.get()
        membres = lister_personnel(recherche)
        membres = self._filtrer_personnel(membres)

        self.label_compteur.configure(text=f"{len(membres)} membre(s) du personnel")

        if not membres:
            ctk.CTkLabel(self.tableau.interior,
                         text="Aucun personnel enregistre.",
                         font=("Segoe UI", 13),
                         text_color="#999999").pack(pady=40)
            return

        for i, p in enumerate(membres):
            fond = "#ffffff" if i % 2 == 0 else "#fafafa"
            ligne = ctk.CTkFrame(self.tableau.interior, fg_color=fond, corner_radius=4)
            ligne.pack(fill="x", pady=1)

            salaire = p.get("salaire_mensuel", 0) or 0
            duree = p.get("duree_contrat_mois", 12) or 12
            engagement = p.get("engagement_total", 0) or 0
            paye = p.get("total_paye", 0) or 0
            reste = p.get("solde_a_payer", 0) or 0

            try:
                avance = total_avance_en_cours(p["id"])
            except Exception:
                avance = 0

            label_code = ctk.CTkLabel(ligne, text=p["code"],
                                      font=("Segoe UI", 11, "bold", "underline"),
                                      text_color="#0066CC", width=85,
                                      anchor="w", cursor="hand2")
            label_code.pack(side="left", padx=4, pady=10)
            label_code.bind("<Button-1>",
                            lambda e, c=p["code"], lbl=label_code: self._copier_code(c, lbl))

            couleur_reste = "#e74c3c" if reste > 0 else "#27ae60"
            couleur_avance = "#e67e22" if avance > 0.01 else "#999999"

            niveau = p.get("niveau") or "-"
            if "," in str(niveau):
                couleur_niveau = "#8e44ad"
            else:
                couleur_niveau = {
                    "Maternelle": "#e67e22",
                    "Primaire": "#27ae60",
                    "Secondaire": "#3498db",
                }.get(niveau, "#999999")

            valeurs = [
                (p["nom"], 100, "#333333", "normal"),
                (p["prenom"], 90, "#333333", "normal"),
                (p["fonction"], 100, "#333333", "normal"),
                (niveau, 85, couleur_niveau, "bold"),
                (p["telephone"] or "-", 110, "#333333", "normal"),
                (format_montant(salaire), 90, "#333333", "normal"),
                (str(duree), 45, "#333333", "normal"),
                (format_montant(engagement), 90, "#8e44ad", "normal"),
                (format_montant(paye), 80, "#27ae60", "normal"),
                (format_montant(reste), 90, couleur_reste, "bold"),
                (format_montant(avance), 80, couleur_avance, "bold"),
            ]
            for v, larg, coul, poids in valeurs:
                ctk.CTkLabel(ligne, text=str(v), font=("Segoe UI", 11, poids),
                             text_color=coul, width=larg,
                             anchor="w").pack(side="left", padx=4, pady=10)

            if self._nb_actions() == 0:
                continue

            actions = ctk.CTkFrame(ligne, fg_color="transparent",
                                    width=self._largeur_actions())
            actions.pack(side="left", padx=4)

            if self._peut_gerer():
                ctk.CTkButton(actions, text="P", font=("Segoe UI", 11, "bold"),
                              width=36, height=28, fg_color="#27ae60",
                              hover_color="#229954",
                              command=lambda pp=p: self._ouvrir_paiement(pp)).pack(side="left", padx=2)
                ctk.CTkButton(actions, text="A", font=("Segoe UI", 11, "bold"),
                              width=36, height=28, fg_color="#e67e22",
                              hover_color="#d35400",
                              command=lambda pp=p: self._ouvrir_avances(pp)).pack(side="left", padx=2)
                ctk.CTkButton(actions, text="E", font=("Segoe UI", 11, "bold"),
                              width=36, height=28, fg_color="#9b59b6",
                              hover_color="#8e44ad",
                              command=lambda pp=p: self._editer_avances(pp)).pack(side="left", padx=2)
                ctk.CTkButton(actions, text="R", font=("Segoe UI", 11, "bold"),
                              width=36, height=28, fg_color="#e91e63",
                              hover_color="#c2185b",
                              command=lambda pp=p: self._releve_paie(pp)).pack(side="left", padx=2)
                ctk.CTkButton(actions, text="M", font=("Segoe UI", 11, "bold"),
                              width=36, height=28, fg_color="#3498db",
                              hover_color="#2980b9",
                              command=lambda pp=p: self._modifier(pp)).pack(side="left", padx=2)

            if self._peut_supprimer():
                ctk.CTkButton(actions, text="X", font=("Segoe UI", 11, "bold"),
                              width=36, height=28, fg_color="#e74c3c",
                              hover_color="#c0392b",
                              command=lambda pp=p: self._supprimer(pp)).pack(side="left", padx=2)

    def _copier_code(self, code, label_widget):
        try:
            self.clipboard_clear()
            self.clipboard_append(code)
            self.update()
            label_widget.configure(text="Copie !", text_color="#27ae60")
            self.after(800, lambda: label_widget.configure(text=code, text_color="#0066CC"))
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de copier : {e}")

    def _ouvrir_formulaire(self, personne=None):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        FormulairePersonnel(self, personne=personne, on_save=self.rafraichir_tableau)

    def _modifier(self, p):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        complet = get_personnel(p["id"])
        self._ouvrir_formulaire(complet)

    def _ouvrir_avances(self, p):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        AvancesWindow(self, p["id"], f"{p['nom']} {p['prenom']}",
                      on_save=self.rafraichir_tableau)

    def _editer_avances(self, p):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        EditerAvancesWindow(self, p["id"], f"{p['nom']} {p['prenom']}",
                            on_save=self.rafraichir_tableau)

    def _releve_paie(self, p):
        try:
            from ui.releve_paie_ui import RelevePaieWindow
            complet = get_personnel(p["id"])
            RelevePaieWindow(self, complet)
        except ImportError:
            messagebox.showerror("Indisponible", "Module non installe.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def _ouvrir_paiement(self, p):
        if not self._peut_gerer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        try:
            from ui.paiement_personnel_ui import PaiementPersonnelWindow
            complet = get_personnel(p["id"])
            PaiementPersonnelWindow(self, complet, on_save=self.rafraichir_tableau)
        except ImportError:
            messagebox.showerror("Indisponible", "Module non installe.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def _supprimer(self, p):
        if not self._peut_supprimer():
            messagebox.showerror("Acces refuse", "Permission requise.")
            return
        rep = messagebox.askyesno(
            "Confirmation",
            f"Supprimer :\n\n{p['nom']} {p['prenom']}\n"
            f"Fonction : {p['fonction']}\nCode : {p['code']} ?"
        )
        if rep:
            ok, msg = supprimer_personnel(p["id"])
            if ok:
                self.rafraichir_tableau()
            else:
                messagebox.showerror("Erreur", msg)


class FormulairePersonnel(ctk.CTkToplevel):
    def __init__(self, parent, personne=None, on_save=None):
        super().__init__(parent)

        self.personne = personne
        self.on_save = on_save

        titre = "Modifier un personnel" if personne else "Nouveau personnel"
        self.title(titre)

        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        largeur = min(540, int(sw * 0.85))
        hauteur = min(680, int(sh * 0.88))
        largeur = max(420, largeur)
        hauteur = max(450, hauteur)

        x = max(10, (sw - largeur) // 2)
        y = 15

        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")
        self.minsize(420, 450)
        self.configure(fg_color="#F5F7FB")

        self.after(80, lambda: self.geometry(f"{largeur}x{hauteur}+{x}+{y}"))

        try:
            self.attributes("-topmost", True)
            self.after(400, lambda: self.attributes("-topmost", False))
        except Exception:
            pass

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
        barre_bas = ctk.CTkFrame(self, fg_color="white", corner_radius=0, height=60)
        barre_bas.pack(fill="x", side="bottom")
        barre_bas.pack_propagate(False)

        ctk.CTkButton(barre_bas, text="Annuler (Echap)",
                      font=("Segoe UI", 12, "bold"),
                      fg_color="#e74c3c", text_color="white",
                      hover_color="#c0392b", height=40,
                      command=self.destroy).pack(side="left", expand=True, fill="x",
                                                  padx=(10, 5), pady=10)

        ctk.CTkButton(barre_bas, text="Enregistrer",
                      font=("Segoe UI", 12, "bold"),
                      fg_color=COLOR_NAVY, hover_color="#1a3d75",
                      height=40,
                      command=self._enregistrer).pack(side="left", expand=True, fill="x",
                                                       padx=(5, 10), pady=10)

        barre_haut = ctk.CTkFrame(self, fg_color="white", corner_radius=0, height=50)
        barre_haut.pack(fill="x", side="top")
        barre_haut.pack_propagate(False)

        titre = "Modifier un personnel" if self.personne else "Nouveau personnel"
        ctk.CTkLabel(barre_haut, text=titre,
                     font=("Segoe UI", 15, "bold"),
                     text_color=COLOR_NAVY).pack(side="left", padx=15, pady=12)

        ctk.CTkButton(barre_haut, text="X",
                      font=("Segoe UI", 13, "bold"),
                      width=30, height=30,
                      fg_color="#e74c3c", hover_color="#c0392b",
                      command=self.destroy).pack(side="right", padx=10)

        zone = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=0)
        zone.pack(fill="both", expand=True)

        self.champs = {}

        self.champs["code"] = self._champ(zone, "Code *",
            self.personne["code"] if self.personne else generer_code())

        ligne_np = ctk.CTkFrame(zone, fg_color="transparent")
        ligne_np.pack(fill="x", padx=10, pady=(2, 2))
        ligne_np.columnconfigure(0, weight=1)
        ligne_np.columnconfigure(1, weight=1)

        col1 = ctk.CTkFrame(ligne_np, fg_color="transparent")
        col1.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        self.champs["nom"] = self._champ(col1, "Nom *",
            self.personne["nom"] if self.personne else "")

        col2 = ctk.CTkFrame(ligne_np, fg_color="transparent")
        col2.grid(row=0, column=1, sticky="ew", padx=(3, 0))
        self.champs["prenom"] = self._champ(col2, "Prenom *",
            self.personne["prenom"] if self.personne else "")

        ctk.CTkLabel(zone, text="Fonction *",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w").pack(padx=10, pady=(3, 2), fill="x")

        vf = "Enseignant"
        if self.personne and self.personne.get("fonction"):
            vf = self.personne["fonction"]
            if vf not in FONCTIONS_PERSONNEL:
                FONCTIONS_PERSONNEL.append(vf)

        self.champs["fonction"] = ctk.CTkComboBox(
            zone, values=FONCTIONS_PERSONNEL,
            font=("Segoe UI", 12), height=34,
            command=self._on_fonction_change)
        self.champs["fonction"].set(vf)
        self.champs["fonction"].pack(padx=10, pady=(0, 3), fill="x")

        ctk.CTkLabel(zone, text="Niveau d'affectation *",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w").pack(padx=10, pady=(3, 2), fill="x")

        self.frame_simple = ctk.CTkFrame(zone, fg_color="transparent")
        self.frame_simple.pack(fill="x", padx=10, pady=(0, 3))

        self.champs["niveau_simple"] = ctk.CTkComboBox(
            self.frame_simple,
            values=["Aucun", "Maternelle", "Primaire", "Secondaire"],
            font=("Segoe UI", 12), height=34)
        self.champs["niveau_simple"].pack(fill="x")

        self.frame_multi = ctk.CTkFrame(zone, fg_color="#F0F7FF", corner_radius=6)

        ctk.CTkLabel(self.frame_multi,
                     text="Ce role peut couvrir PLUSIEURS niveaux :",
                     font=("Segoe UI", 10, "bold"),
                     text_color="#1565C0", anchor="w").pack(padx=12, pady=(6, 3), fill="x")

        self.var_mat = ctk.BooleanVar()
        self.var_prim = ctk.BooleanVar()
        self.var_sec = ctk.BooleanVar()

        for var, label, couleur in [
            (self.var_mat, "Maternelle", "#e67e22"),
            (self.var_prim, "Primaire", "#27ae60"),
            (self.var_sec, "Secondaire", "#3498db"),
        ]:
            ctk.CTkCheckBox(self.frame_multi, text=label, variable=var,
                            font=("Segoe UI", 11, "bold"),
                            text_color=couleur, fg_color=couleur,
                            hover_color=couleur,
                            checkbox_width=18, checkbox_height=18
                            ).pack(padx=15, pady=1, anchor="w")

        ctk.CTkFrame(self.frame_multi, fg_color="transparent", height=3).pack()

        if self.personne:
            niveau_actuel = (self.personne.get("niveau") or "").strip()
            fonction = self.personne.get("fonction", "")
            if fonction in FONCTIONS_MULTI_NIVEAUX:
                nl = [v.strip() for v in niveau_actuel.split(",")]
                self.var_mat.set("Maternelle" in nl)
                self.var_prim.set("Primaire" in nl)
                self.var_sec.set("Secondaire" in nl)
            else:
                if niveau_actuel and "," not in niveau_actuel:
                    self.champs["niveau_simple"].set(niveau_actuel)
                else:
                    self.champs["niveau_simple"].set("Aucun")
        else:
            self.champs["niveau_simple"].set("Aucun")

        self._on_fonction_change(vf)

        sep = ctk.CTkFrame(zone, fg_color="#e0e0e0", height=1)
        sep.pack(fill="x", padx=10, pady=(6, 4))

        ctk.CTkLabel(zone, text="SALAIRE ET ENGAGEMENT",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#8e44ad", anchor="w").pack(padx=10, pady=(3, 4), fill="x")

        ligne_sd = ctk.CTkFrame(zone, fg_color="transparent")
        ligne_sd.pack(fill="x", padx=10, pady=(2, 2))
        ligne_sd.columnconfigure(0, weight=2)
        ligne_sd.columnconfigure(1, weight=1)

        col_s = ctk.CTkFrame(ligne_sd, fg_color="transparent")
        col_s.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        vs = ""
        if self.personne and self.personne.get("salaire_mensuel"):
            vs = str(int(self.personne["salaire_mensuel"]))
        self.champs["salaire_mensuel"] = self._champ(
            col_s, f"Salaire ({CURRENCY_SYMBOL}) *", vs)
        self.champs["salaire_mensuel"].bind("<KeyRelease>", lambda e: self._maj_apercu())

        col_d = ctk.CTkFrame(ligne_sd, fg_color="transparent")
        col_d.grid(row=0, column=1, sticky="ew", padx=(3, 0))
        vd = "12"
        if self.personne and self.personne.get("duree_contrat_mois"):
            vd = str(int(self.personne["duree_contrat_mois"]))
        self.champs["duree_contrat_mois"] = self._champ(
            col_d, "Duree (mois) *", vd)
        self.champs["duree_contrat_mois"].bind("<KeyRelease>", lambda e: self._maj_apercu())

        self.label_apercu = ctk.CTkLabel(
            zone, text="Engagement total : --",
            font=("Segoe UI", 11, "bold"),
            text_color="#8e44ad", anchor="w")
        self.label_apercu.pack(padx=10, pady=(2, 5), fill="x")
        self._maj_apercu()

        sep2 = ctk.CTkFrame(zone, fg_color="#e0e0e0", height=1)
        sep2.pack(fill="x", padx=10, pady=(3, 3))

        ctk.CTkLabel(zone, text="INFORMATIONS COMPLEMENTAIRES",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#666666", anchor="w").pack(padx=10, pady=(3, 4), fill="x")

        ctk.CTkLabel(zone, text="Sexe",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w").pack(padx=10, pady=(3, 2), fill="x")

        self.champs["sexe"] = ctk.CTkComboBox(
            zone, values=["Masculin", "Feminin"],
            font=("Segoe UI", 12), height=34)
        self.champs["sexe"].set(self.personne["sexe"]
                                if self.personne and self.personne.get("sexe")
                                else "Masculin")
        self.champs["sexe"].pack(padx=10, pady=(0, 3), fill="x")

        self.champs["telephone"] = self._champ(
            zone, "Telephone",
            self.personne["telephone"] if self.personne and self.personne.get("telephone") else "")

        self.champs["email"] = self._champ(
            zone, "Email",
            self.personne["email"] if self.personne and self.personne.get("email") else "")

    def _champ(self, parent, label, valeur=""):
        ctk.CTkLabel(parent, text=label,
                     font=("Segoe UI", 11, "bold"),
                     text_color="#333333", anchor="w").pack(padx=0, pady=(2, 1), fill="x")
        entree = ctk.CTkEntry(parent, font=("Segoe UI", 12), height=32)
        entree.insert(0, valeur)
        entree.pack(padx=0, pady=(0, 2), fill="x")
        return entree

    def _on_fonction_change(self, valeur):
        if valeur in FONCTIONS_MULTI_NIVEAUX:
            self.frame_simple.pack_forget()
            self.frame_multi.pack(fill="x", padx=10, pady=(0, 3))
        else:
            self.frame_multi.pack_forget()
            self.frame_simple.pack(fill="x", padx=10, pady=(0, 3))

    def _maj_apercu(self):
        try:
            s = self.champs["salaire_mensuel"].get().strip().replace(" ", "").replace(",", "")
            d = self.champs["duree_contrat_mois"].get().strip()
            salaire = float(s) if s else 0
            duree = int(d) if d else 0
            total = salaire * duree
            self.label_apercu.configure(
                text=f"Engagement total : {format_montant(total)}  ({duree} mois x {format_montant(salaire)})")
        except Exception:
            self.label_apercu.configure(text="Engagement total : --")

    def _enregistrer(self):
        code = self.champs["code"].get().strip()
        nom = self.champs["nom"].get().strip()
        prenom = self.champs["prenom"].get().strip()
        fonction = self.champs["fonction"].get().strip()
        sexe = self.champs["sexe"].get().strip()
        telephone = self.champs["telephone"].get().strip() or None
        email = self.champs["email"].get().strip() or None

        if fonction in FONCTIONS_MULTI_NIVEAUX:
            ns = []
            if self.var_mat.get(): ns.append("Maternelle")
            if self.var_prim.get(): ns.append("Primaire")
            if self.var_sec.get(): ns.append("Secondaire")
            if not ns:
                messagebox.showerror(
                    "Erreur",
                    f"Pour la fonction '{fonction}', cochez au moins un niveau.")
                return
            niveau = ",".join(ns)
        else:
            nc = self.champs["niveau_simple"].get().strip()
            niveau = None if nc == "Aucun" else nc

        s = self.champs["salaire_mensuel"].get().strip().replace(" ", "").replace(",", "")
        try:
            salaire = float(s) if s else 0
        except ValueError:
            messagebox.showerror("Erreur", "Le salaire doit etre un nombre.")
            return

        d = self.champs["duree_contrat_mois"].get().strip()
        try:
            duree = int(d) if d else 12
            if duree <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Erreur", "La duree doit etre un nombre entier superieur a 0.")
            return

        if not code or not nom or not prenom or not fonction:
            messagebox.showerror("Champs obligatoires",
                                 "Veuillez remplir tous les champs marques d'un *.")
            return

        if self.personne:
            ok, msg = modifier_personnel(
                self.personne["id"], code, nom, prenom, fonction,
                sexe, telephone, email, salaire, duree, None,
                niveau=niveau,
            )
        else:
            ok, msg = ajouter_personnel(
                code, nom, prenom, fonction,
                sexe, telephone, email, salaire, duree, None,
                niveau=niveau,
            )

        if ok:
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Erreur", msg)