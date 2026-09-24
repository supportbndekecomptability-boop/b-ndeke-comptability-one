"""
Interface Parametres
- Ecole + Bilan initial + Frais du budget + Budgets + Utilisateurs + Sauvegarde
Permissions :
- Admin : lecture seule sur les utilisateurs
- Gestionnaire : peut tout faire (creer, modifier, supprimer, bloquer)
- Compte gestionnaire : protege (jamais modifiable/supprimable)
"""
import os
import sys
import subprocess
import platform
from tkinter import messagebox, filedialog
import customtkinter as ctk

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

from config import COLOR_NAVY, COLOR_GOLD, format_montant
from ui.permissions_ui import peut
from core.permissions import get_role, a_permission
from core.ecole import (
    get_info_ecole, set_info_ecole, set_logo, get_logo_path,
    supprimer_logo,
    sauvegarder_base, lister_sauvegardes, restaurer_sauvegarde,
    supprimer_sauvegarde, get_sauvegarde_auto, set_sauvegarde_auto,
    get_derniere_sauvegarde, nettoyer_vieilles_sauvegardes,
    get_dossier_backups,
)
from core.utilisateurs import (
    lister_utilisateurs, creer_utilisateur, modifier_utilisateur,
    supprimer_utilisateur, email_existe, compter_admins,
    FONCTIONNALITES_BLOQUABLES,
    get_fonctionnalites_bloquees,
    set_fonctionnalites_bloquees,
)
from core.frais import lister_frais, modifier_frais, total_frais_dans_budget
from ui.bilan_initial_ui import BilanInitialPage
from ui.budgets_ui import BudgetsPage


class ParametresPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")

        self.utilisateur_connecte = utilisateur or {}

        # ===== VERIFICATION ACCES GLOBAL =====
        if not self._peut_acceder_parametres():
            cadre = ctk.CTkFrame(self, fg_color="#FFF3CD", corner_radius=10)
            cadre.pack(fill="x", padx=40, pady=60)

            ctk.CTkLabel(
                cadre,
                text="ACCES REFUSE",
                font=("Segoe UI", 18, "bold"),
                text_color="#e74c3c",
            ).pack(pady=(25, 5))

            ctk.CTkLabel(
                cadre,
                text=("Les parametres sont reserves a l'administrateur "
                      "et au gestionnaire.\n\n"
                      "Votre role ne vous permet pas d'acceder a cette page."),
                font=("Segoe UI", 12),
                text_color="#8B6914",
                justify="center",
            ).pack(pady=(0, 25))
            return

        # ===== BADGE ROLE =====
        ligne_top = ctk.CTkFrame(self, fg_color="transparent")
        ligne_top.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            ligne_top,
            text="Parametres",
            font=("Segoe UI", 20, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        role = get_role(self.utilisateur_connecte)
        ctk.CTkLabel(
            ligne_top,
            text=f"Role : {role.upper()}",
            font=("Segoe UI", 10, "bold"),
            text_color="#27ae60",
        ).pack(side="right", pady=(8, 0))

        # ===== TABVIEW =====
        self.tabview = ctk.CTkTabview(
            self,
            fg_color="white",
            segmented_button_selected_color=COLOR_NAVY,
            segmented_button_selected_hover_color="#1a3d75",
            segmented_button_unselected_color="#e0e0e0",
        )
        self.tabview.pack(fill="both", expand=True)

        self.tabview.add("Informations Ecole")
        self.tabview.add("Bilan initial")
        self.tabview.add("Frais du budget")
        self.tabview.add("Budgets")

        # Onglet Utilisateurs : seulement si peut_gerer_utilisateurs
        if self._peut_gerer_utilisateurs():
            self.tabview.add("Utilisateurs")

        self.tabview.add("Sauvegarde")

        self._construire_onglet_ecole(self.tabview.tab("Informations Ecole"))
        self._construire_onglet_bilan_initial(self.tabview.tab("Bilan initial"))
        self._construire_onglet_frais_budget(self.tabview.tab("Frais du budget"))
        self._construire_onglet_budgets(self.tabview.tab("Budgets"))

        if self._peut_gerer_utilisateurs():
            self._construire_onglet_utilisateurs(self.tabview.tab("Utilisateurs"))

        self._construire_onglet_sauvegarde(self.tabview.tab("Sauvegarde"))

    # ================== PERMISSIONS ==================
    def _peut_acceder_parametres(self):
        return (peut(self.utilisateur_connecte, "peut_gerer_utilisateurs")
                or peut(self.utilisateur_connecte, "peut_gerer_permissions"))

    def _peut_gerer_utilisateurs(self):
        return peut(self.utilisateur_connecte, "peut_gerer_utilisateurs")

    def _est_gestionnaire_acteur(self):
        """True si l'utilisateur connecte est le gestionnaire."""
        return (self.utilisateur_connecte.get("role") or "").lower() == "gestionnaire"

    def _est_admin_acteur(self):
        """True si l'utilisateur connecte est admin."""
        return (self.utilisateur_connecte.get("role") or "").lower() == "admin"

    # ============================================================
    # ONGLET 1 : INFO ECOLE
    # ============================================================
    def _construire_onglet_ecole(self, parent):
        zone = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        zone.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            zone, text="Informations de l'etablissement",
            font=("Segoe UI", 18, "bold"),
            text_color=COLOR_NAVY,
        ).pack(anchor="w", pady=(5, 5))

        ctk.CTkLabel(
            zone,
            text="Ces informations apparaissent en en-tete des rapports PDF",
            font=("Segoe UI", 11),
            text_color="#666666",
        ).pack(anchor="w", pady=(0, 15))

        info = get_info_ecole()
        self.champs_ecole = {}

        ctk.CTkLabel(zone, text="Nom de l'ecole *",
                     font=("Segoe UI", 12, "bold"),
                     text_color="#333333", anchor="w").pack(padx=5, pady=(8, 4), fill="x")
        self.champs_ecole["nom"] = ctk.CTkEntry(zone, font=("Segoe UI", 13), height=38)
        self.champs_ecole["nom"].insert(0, info["nom"])
        self.champs_ecole["nom"].pack(padx=5, pady=(0, 10), fill="x")

        ctk.CTkLabel(zone, text="Adresse",
                     font=("Segoe UI", 12, "bold"),
                     text_color="#333333", anchor="w").pack(padx=5, pady=(8, 4), fill="x")
        self.champs_ecole["adresse"] = ctk.CTkEntry(zone, font=("Segoe UI", 13), height=38)
        self.champs_ecole["adresse"].insert(0, info["adresse"])
        self.champs_ecole["adresse"].pack(padx=5, pady=(0, 10), fill="x")

        ctk.CTkLabel(zone, text="Telephone",
                     font=("Segoe UI", 12, "bold"),
                     text_color="#333333", anchor="w").pack(padx=5, pady=(8, 4), fill="x")
        self.champs_ecole["telephone"] = ctk.CTkEntry(zone, font=("Segoe UI", 13), height=38)
        self.champs_ecole["telephone"].insert(0, info["telephone"])
        self.champs_ecole["telephone"].pack(padx=5, pady=(0, 10), fill="x")

        ctk.CTkLabel(zone, text="Email",
                     font=("Segoe UI", 12, "bold"),
                     text_color="#333333", anchor="w").pack(padx=5, pady=(8, 4), fill="x")
        self.champs_ecole["email"] = ctk.CTkEntry(zone, font=("Segoe UI", 13), height=38)
        self.champs_ecole["email"].insert(0, info["email"])
        self.champs_ecole["email"].pack(padx=5, pady=(0, 15), fill="x")
        # ===== PAYS =====
        ctk.CTkLabel(zone, text="Pays de l'etablissement *",
                     font=("Segoe UI", 12, "bold"),
                     text_color="#333333", anchor="w").pack(padx=5, pady=(8, 4), fill="x")

        from core.pays import lister_pays
        from core.ecole import get_pays_ecole

        liste_pays = ["-- Choisir un pays --"] + lister_pays()

        self.combo_pays = ctk.CTkComboBox(
            zone, values=liste_pays,
            font=("Segoe UI", 13), height=38,
        )
        pays_actuel = get_pays_ecole() or ""
        if pays_actuel and pays_actuel in liste_pays:
            self.combo_pays.set(pays_actuel)
        else:
            self.combo_pays.set("-- Choisir un pays --")
        self.combo_pays.pack(padx=5, pady=(0, 8), fill="x")

        ctk.CTkLabel(
            zone,
            text="Ce pays determine le systeme educatif des bulletins.",
            font=("Segoe UI", 10),
            text_color="#888888",
            anchor="w",
        ).pack(padx=5, pady=(0, 15), fill="x")


        ctk.CTkLabel(zone, text="Logo de l'ecole",
                     font=("Segoe UI", 12, "bold"),
                     text_color="#333333", anchor="w").pack(padx=5, pady=(8, 4), fill="x")

        ligne_logo = ctk.CTkFrame(zone, fg_color="transparent")
        ligne_logo.pack(fill="x", padx=5, pady=(0, 15))

        self.frame_logo = ctk.CTkFrame(ligne_logo, fg_color="#F0F7FF",
                                        corner_radius=8, width=180, height=180)
        self.frame_logo.pack(side="left")
        self.frame_logo.pack_propagate(False)

        self.label_logo = ctk.CTkLabel(self.frame_logo, text="Aucun logo",
                                        font=("Segoe UI", 11), text_color="#999999")
        self.label_logo.pack(expand=True)

        ligne_btns = ctk.CTkFrame(ligne_logo, fg_color="transparent")
        ligne_btns.pack(side="left", padx=(15, 0), fill="both", expand=True)

        ctk.CTkButton(
            ligne_btns, text="Choisir une image...",
            font=("Segoe UI", 12, "bold"),
            fg_color=COLOR_NAVY, hover_color="#1a3d75",
            height=38, command=self._choisir_logo,
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkButton(
            ligne_btns, text="Supprimer le logo",
            font=("Segoe UI", 11),
            fg_color="#e0e0e0", text_color="#333333",
            hover_color="#c0c0c0", height=32, command=self._supprimer_logo,
        ).pack(anchor="w")

        ctk.CTkButton(
            zone, text="Enregistrer les informations",
            font=("Segoe UI", 13, "bold"),
            fg_color="#27ae60", hover_color="#229954",
            height=45, command=self._enregistrer_ecole,
        ).pack(fill="x", padx=5, pady=(15, 10))

        self._afficher_logo()

    def _afficher_logo(self):
        chemin = get_logo_path()

        for w in self.frame_logo.winfo_children():
            w.destroy()

        if not chemin or not PIL_OK:
            self.label_logo = ctk.CTkLabel(self.frame_logo, text="Aucun logo",
                                            font=("Segoe UI", 11), text_color="#999999")
            self.label_logo.pack(expand=True)
            return

        try:
            img = Image.open(chemin)
            img.thumbnail((170, 170), Image.LANCZOS)
            photo = ctk.CTkImage(light_image=img, size=img.size)
            label = ctk.CTkLabel(self.frame_logo, text="", image=photo)
            label.image = photo
            label.pack(expand=True)
        except Exception as e:
            print(f"[Erreur affichage logo] {e}")

    def _choisir_logo(self):
        chemin = filedialog.askopenfilename(
            title="Choisir un logo",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Tous les fichiers", "*.*"),
            ]
        )
        if not chemin:
            return

        ok, msg = set_logo(chemin)
        if ok:
            self._afficher_logo()
            messagebox.showinfo("Logo", "Logo enregistre avec succes !")
        else:
            messagebox.showerror("Erreur", msg)

    def _supprimer_logo(self):
        if not get_logo_path():
            return
        rep = messagebox.askyesno("Confirmation", "Supprimer le logo actuel ?")
        if rep:
            supprimer_logo()
            self._afficher_logo()

    def _enregistrer_ecole(self):
        nom = self.champs_ecole["nom"].get().strip()
        if not nom:
            messagebox.showerror("Erreur", "Le nom de l'ecole est obligatoire.")
            return

        set_info_ecole(
            nom,
            self.champs_ecole["adresse"].get(),
            self.champs_ecole["telephone"].get(),
            self.champs_ecole["email"].get(),
        )
        messagebox.showinfo("Succes",
                            "Informations enregistrees !\n\n"
                            "Elles apparaitront sur les prochains rapports PDF.")

    # ============================================================
    # ONGLET : BILAN INITIAL
    # ============================================================
    def _construire_onglet_bilan_initial(self, parent):
        page = BilanInitialPage(parent, utilisateur=self.utilisateur_connecte)
        page.pack(fill="both", expand=True)

    # ============================================================
    # ONGLET : FRAIS DU BUDGET
    # ============================================================
    def _construire_onglet_frais_budget(self, parent):
        if not a_permission(self.utilisateur_connecte, "peut_gerer_frais"):
            cadre = ctk.CTkFrame(parent, fg_color="#FFF3CD", corner_radius=10)
            cadre.pack(fill="x", padx=20, pady=30)
            ctk.CTkLabel(
                cadre,
                text=("Acces reserve a l'administrateur et au gestionnaire.\n\n"
                      "Seuls ces roles peuvent definir quels frais "
                      "constituent le budget annuel."),
                font=("Segoe UI", 12, "bold"),
                text_color="#8B6914",
                justify="center",
            ).pack(pady=30)
            return

        zone = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        zone.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(zone, text="Frais qui constituent le budget annuel",
                     font=("Segoe UI", 18, "bold"),
                     text_color=COLOR_NAVY).pack(anchor="w", pady=(5, 5))

        ctk.CTkLabel(
            zone,
            text=("Cochez les frais qui entrent dans le budget annuel de l'ecole.\n"
                  "Ces frais seront utilises pour les calculs de repartition "
                  "budgetaire (Scolarite, Salaires, Investissement, etc.)."),
            font=("Segoe UI", 11),
            text_color="#666666",
            justify="left",
        ).pack(anchor="w", pady=(0, 15))

        cadre_total = ctk.CTkFrame(zone, fg_color="#E3F2FD", corner_radius=10)
        cadre_total.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(cadre_total, text="Somme des frais dans le budget",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#1565C0").pack(side="left", padx=20, pady=15)

        self.label_total_budget = ctk.CTkLabel(
            cadre_total,
            text=format_montant(total_frais_dans_budget()),
            font=("Segoe UI", 18, "bold"),
            text_color="#1565C0",
        )
        self.label_total_budget.pack(side="right", padx=20, pady=15)

        frais_liste = lister_frais(actif=True)

        if not frais_liste:
            ctk.CTkLabel(zone,
                         text="Aucun frais dans le catalogue.\n\n"
                              "Ajoutez d'abord des frais dans le module 'Frais'.",
                         font=("Segoe UI", 12),
                         text_color="#999999").pack(pady=40)
            return

        self.etat_budget_frais = {}

        entete = ctk.CTkFrame(zone, fg_color="#f0f0f0", corner_radius=6)
        entete.pack(fill="x", pady=(0, 3))

        for nom, larg in [
            ("Inclus", 80),
            ("Nom du frais", 300),
            ("Montant defaut", 150),
        ]:
            ctk.CTkLabel(entete, text=nom,
                         font=("Segoe UI", 10, "bold"),
                         text_color=COLOR_NAVY, width=larg,
                         anchor="w").pack(side="left", padx=4, pady=8)

        for i, f in enumerate(frais_liste):
            fond = "#ffffff" if i % 2 == 0 else "#fafafa"
            ligne = ctk.CTkFrame(zone, fg_color=fond, corner_radius=4)
            ligne.pack(fill="x", pady=1)

            dans = bool(f.get("dans_budget"))

            btn = ctk.CTkButton(
                ligne,
                text="[X]" if dans else "[ ]",
                font=("Segoe UI", 12, "bold"),
                width=50, height=28,
                fg_color="#27ae60" if dans else "#e0e0e0",
                text_color="white" if dans else "#666666",
                hover_color="#229954" if dans else "#c0c0c0",
            )
            btn.pack(side="left", padx=(10, 5), pady=8)

            self.etat_budget_frais[f["id"]] = dans

            btn.configure(command=lambda fid=f["id"]: self._toggle_frais_budget(fid))

            ctk.CTkLabel(ligne, text=f["nom"],
                         font=("Segoe UI", 11, "bold"),
                         text_color="#333333",
                         width=300, anchor="w").pack(side="left", padx=4, pady=8)

            montant = f.get("montant_defaut", 0) or 0
            ctk.CTkLabel(ligne, text=format_montant(montant),
                         font=("Segoe UI", 11),
                         text_color="#333333",
                         width=150, anchor="w").pack(side="left", padx=4, pady=8)

            self.etat_budget_frais.setdefault("_btn_refs", {})[f["id"]] = btn

        ctk.CTkButton(
            zone,
            text="Enregistrer les choix",
            font=("Segoe UI", 13, "bold"),
            fg_color="#27ae60", hover_color="#229954",
            height=45,
            command=self._enregistrer_frais_budget,
        ).pack(fill="x", pady=(20, 10))

    def _toggle_frais_budget(self, frais_id):
        nouvel = not self.etat_budget_frais.get(frais_id, False)
        self.etat_budget_frais[frais_id] = nouvel

        btn = self.etat_budget_frais.get("_btn_refs", {}).get(frais_id)
        if btn:
            if nouvel:
                btn.configure(text="[X]", fg_color="#27ae60",
                              text_color="white", hover_color="#229954")
            else:
                btn.configure(text="[ ]", fg_color="#e0e0e0",
                              text_color="#666666", hover_color="#c0c0c0")

        self._maj_total_budget()

    def _maj_total_budget(self):
        total = 0
        frais_liste = lister_frais(actif=True)
        for f in frais_liste:
            if self.etat_budget_frais.get(f["id"], False):
                total += (f.get("montant_defaut") or 0)

        if hasattr(self, "label_total_budget"):
            self.label_total_budget.configure(text=format_montant(total))

    def _enregistrer_frais_budget(self):
        erreurs = []
        nb_ok = 0

        for frais_id, dans in self.etat_budget_frais.items():
            if frais_id == "_btn_refs":
                continue
            try:
                ok, msg = modifier_frais(frais_id, dans_budget=dans)
                if ok:
                    nb_ok += 1
                else:
                    erreurs.append(msg)
            except Exception as e:
                erreurs.append(str(e))

        if erreurs:
            messagebox.showwarning(
                "Attention",
                f"{nb_ok} frais mis a jour.\n\n"
                f"Erreurs :\n" + "\n".join(erreurs[:5])
            )
        else:
            messagebox.showinfo(
                "Succes",
                f"{nb_ok} frais mis a jour.\n\n"
                f"Somme des frais dans le budget : "
                f"{format_montant(total_frais_dans_budget())}"
            )

    # ============================================================
    # ONGLET : BUDGETS
    # ============================================================
    def _construire_onglet_budgets(self, parent):
        page = BudgetsPage(parent, utilisateur=self.utilisateur_connecte)
        page.pack(fill="both", expand=True)

    # ============================================================
    # ONGLET : UTILISATEURS
    # ============================================================
    def _construire_onglet_utilisateurs(self, parent):
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            top, text="Gestion des utilisateurs",
            font=("Segoe UI", 18, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        # Bouton "+ Nouvel utilisateur" : seulement gestionnaire
        if self._est_gestionnaire_acteur():
            ctk.CTkButton(
                top, text="+ Nouvel utilisateur",
                font=("Segoe UI", 12, "bold"),
                fg_color=COLOR_NAVY, hover_color="#1a3d75",
                height=36, command=self._nouvel_utilisateur,
            ).pack(side="right")

        # Info role actuel
        if self._est_admin_acteur():
            texte_info = ("Lecture seule : vous voyez les utilisateurs mais "
                          "seul le gestionnaire peut les modifier.")
            couleur_info = "#e67e22"
        else:
            texte_info = ("Vous pouvez creer, modifier, supprimer et bloquer "
                          "les fonctionnalites des utilisateurs "
                          "(sauf le compte gestionnaire, protege).")
            couleur_info = "#27ae60"

        ctk.CTkLabel(
            parent,
            text=texte_info,
            font=("Segoe UI", 10, "italic"),
            text_color=couleur_info,
            justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 10))

        self.frame_users = ctk.CTkScrollableFrame(parent, fg_color="white", corner_radius=10)
        self.frame_users.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._rafraichir_users()

    def _rafraichir_users(self):
        for w in self.frame_users.winfo_children():
            w.destroy()

        # Largeur des colonnes selon le role acteur
        if self._est_gestionnaire_acteur():
            largeur_actions = 160  # M + X + B
        else:
            largeur_actions = 60   # aucune action (juste place vide)

        entete = ctk.CTkFrame(self.frame_users, fg_color="#f0f0f0", corner_radius=6)
        entete.pack(fill="x", pady=(0, 5))

        for nom, largeur in [
            ("Nom complet", 180),
            ("Email", 230),
            ("Role", 100),
            ("Modules bloques", 120),
            ("Date creation", 130),
        ]:
            ctk.CTkLabel(entete, text=nom,
                         font=("Segoe UI", 11, "bold"),
                         text_color=COLOR_NAVY, width=largeur,
                         anchor="w").pack(side="left", padx=5, pady=10)

        ctk.CTkLabel(entete, text="Actions",
                     font=("Segoe UI", 11, "bold"),
                     text_color=COLOR_NAVY, width=largeur_actions,
                     anchor="center").pack(side="right", padx=5, pady=10)

        users = lister_utilisateurs()

        for i, u in enumerate(users):
            fond = "#ffffff" if i % 2 == 0 else "#fafafa"
            ligne = ctk.CTkFrame(self.frame_users, fg_color=fond, corner_radius=4)
            ligne.pack(fill="x", pady=1)

            try:
                date_str = u["date_creation"][:10]
            except Exception:
                date_str = str(u.get("date_creation", ""))[:10]

            role_lower = (u["role"] or "").lower()
            if role_lower == "gestionnaire":
                couleur_role = "#8e44ad"
            elif role_lower == "admin":
                couleur_role = "#e74c3c"
            else:
                couleur_role = "#3498db"

            # Compter les modules bloques
            bloques = u.get("bloques") or []
            if role_lower == "gestionnaire":
                nb_bloques = 0
                txt_bloques = "Protege"
                coul_bloques = "#8e44ad"
            elif bloques:
                nb_bloques = len(bloques)
                txt_bloques = f"{nb_bloques} bloque(s)"
                coul_bloques = "#e74c3c"
            else:
                nb_bloques = 0
                txt_bloques = "Aucun"
                coul_bloques = "#27ae60"

            for val, larg, coul, poids in [
                (u["nom_complet"], 180, "#333333", "normal"),
                (u["email"], 230, "#0066CC", "normal"),
                (u["role"].upper(), 100, couleur_role, "bold"),
                (txt_bloques, 120, coul_bloques, "bold"),
                (date_str, 130, "#666666", "normal"),
            ]:
                ctk.CTkLabel(ligne, text=str(val),
                             font=("Segoe UI", 11, poids),
                             text_color=coul, width=larg,
                             anchor="w").pack(side="left", padx=5, pady=8)

            # ===== ACTIONS =====
            actions = ctk.CTkFrame(ligne, fg_color="transparent",
                                    width=largeur_actions)
            actions.pack(side="right", padx=5)

            # Regles :
            # - Cible gestionnaire -> aucun bouton
            # - Acteur admin -> aucun bouton (lecture seule)
            # - Acteur gestionnaire -> M + X + B
            #   - Sauf X sur son propre compte (pas d'auto-suppression)
            cible_est_gestionnaire = (role_lower == "gestionnaire")
            self_id = self.utilisateur_connecte.get("id")

            if cible_est_gestionnaire:
                # Protege : rien
                pass
            elif self._est_admin_acteur():
                # Admin : lecture seule
                pass
            elif self._est_gestionnaire_acteur():
                # M : Modifier
                ctk.CTkButton(actions, text="M",
                              font=("Segoe UI", 11, "bold"),
                              width=36, height=28,
                              fg_color="#3498db", hover_color="#2980b9",
                              command=lambda uu=u: self._modifier_user(uu)
                              ).pack(side="left", padx=2)

                # X : Supprimer (sauf sur soi-meme)
                if u["id"] != self_id:
                    ctk.CTkButton(actions, text="X",
                                  font=("Segoe UI", 11, "bold"),
                                  width=36, height=28,
                                  fg_color="#e74c3c", hover_color="#c0392b",
                                  command=lambda uu=u: self._supprimer_user(uu)
                                  ).pack(side="left", padx=2)

                # B : Bloquer / Debloquer
                ctk.CTkButton(actions, text="B",
                              font=("Segoe UI", 11, "bold"),
                              width=36, height=28,
                              fg_color="#e67e22", hover_color="#d35400",
                              command=lambda uu=u: self._bloquer_user(uu)
                              ).pack(side="left", padx=2)

    def _nouvel_utilisateur(self):
        if not self._est_gestionnaire_acteur():
            messagebox.showerror("Acces refuse",
                                 "Seul le gestionnaire peut creer des utilisateurs.")
            return
        FormulaireUtilisateur(self, on_save=self._rafraichir_users)

    def _modifier_user(self, u):
        if not self._est_gestionnaire_acteur():
            messagebox.showerror("Acces refuse",
                                 "Seul le gestionnaire peut modifier les utilisateurs.")
            return
        if (u.get("role") or "").lower() == "gestionnaire":
            messagebox.showerror("Protege",
                                 "Le compte gestionnaire est protege.")
            return
        FormulaireUtilisateur(self, user=u, on_save=self._rafraichir_users)

    def _supprimer_user(self, u):
        if not self._est_gestionnaire_acteur():
            messagebox.showerror("Acces refuse",
                                 "Seul le gestionnaire peut supprimer des utilisateurs.")
            return

        if (u.get("role") or "").lower() == "gestionnaire":
            messagebox.showerror("Protege",
                                 "Le compte gestionnaire est protege.")
            return

        if u["role"] == "admin" and compter_admins() <= 1:
            messagebox.showerror("Erreur",
                                 "Impossible de supprimer le dernier administrateur.")
            return

        rep = messagebox.askyesno(
            "Confirmation",
            f"Supprimer l'utilisateur ?\n\n"
            f"{u['nom_complet']} ({u['email']})\n"
            f"Role : {u['role']}"
        )
        if rep:
            ok, msg = supprimer_utilisateur(u["id"])
            if ok:
                self._rafraichir_users()
            else:
                messagebox.showerror("Erreur", msg)

    def _bloquer_user(self, u):
        if not self._est_gestionnaire_acteur():
            messagebox.showerror("Acces refuse",
                                 "Seul le gestionnaire peut bloquer les fonctionnalites.")
            return
        if (u.get("role") or "").lower() == "gestionnaire":
            messagebox.showerror("Protege",
                                 "Le compte gestionnaire ne peut pas etre bloque.")
            return
        FenetreBlocage(self, u, on_save=self._rafraichir_users)

    # ============================================================
    # ONGLET : SAUVEGARDE
    # ============================================================
    def _construire_onglet_sauvegarde(self, parent):
        zone = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        zone.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(zone, text="Sauvegarde des donnees",
                     font=("Segoe UI", 18, "bold"),
                     text_color=COLOR_NAVY).pack(anchor="w", pady=(5, 5))

        ctk.CTkLabel(zone,
                     text="La sauvegarde cree une copie de la base dans data/backups/",
                     font=("Segoe UI", 11),
                     text_color="#666666").pack(anchor="w", pady=(0, 15))

        cadre_auto = ctk.CTkFrame(zone, fg_color="#F0F7FF", corner_radius=8)
        cadre_auto.pack(fill="x", pady=(0, 15))

        self.var_auto = ctk.BooleanVar(value=get_sauvegarde_auto())
        ctk.CTkCheckBox(
            cadre_auto,
            text="Activer la sauvegarde automatique au demarrage",
            variable=self.var_auto,
            font=("Segoe UI", 12, "bold"),
            text_color=COLOR_NAVY,
            command=self._toggle_auto,
        ).pack(padx=15, pady=(12, 5), anchor="w")

        self.label_derniere_sauvegarde = ctk.CTkLabel(
            cadre_auto,
            text=f"Derniere sauvegarde : {get_derniere_sauvegarde()}",
            font=("Segoe UI", 10),
            text_color="#666666",
        )
        self.label_derniere_sauvegarde.pack(padx=15, pady=(0, 12), anchor="w")

        ligne_btns = ctk.CTkFrame(zone, fg_color="transparent")
        ligne_btns.pack(fill="x", pady=(0, 15))

        ctk.CTkButton(ligne_btns, text="Sauvegarder maintenant",
                      font=("Segoe UI", 12, "bold"),
                      fg_color="#27ae60", hover_color="#229954",
                      height=40, command=self._sauvegarder_maintenant,
                      ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(ligne_btns, text="Ouvrir le dossier",
                      font=("Segoe UI", 11),
                      fg_color="#e0e0e0", text_color="#333333",
                      hover_color="#c0c0c0", height=40,
                      command=self._ouvrir_dossier).pack(side="left", padx=5)

        ctk.CTkButton(ligne_btns, text="Nettoyer (garder 20)",
                      font=("Segoe UI", 11),
                      fg_color="#e67e22", text_color="white",
                      hover_color="#d35400", height=40,
                      command=self._nettoyer).pack(side="left", padx=5)

        ctk.CTkLabel(zone, text="Sauvegardes disponibles",
                     font=("Segoe UI", 13, "bold"),
                     text_color=COLOR_NAVY).pack(anchor="w", pady=(10, 5))

        self.frame_backups = ctk.CTkScrollableFrame(zone, fg_color="white",
                                                    corner_radius=10, height=250)
        self.frame_backups.pack(fill="both", expand=True)

        self._rafraichir_backups()

    def _toggle_auto(self):
        set_sauvegarde_auto(self.var_auto.get())

    def _sauvegarder_maintenant(self):
        ok, msg = sauvegarder_base()
        if ok:
            messagebox.showinfo("Sauvegarde",
                                f"Sauvegarde creee :\n\n{msg}")
            self._rafraichir_backups()
            try:
                self.label_derniere_sauvegarde.configure(
                    text=f"Derniere sauvegarde : {get_derniere_sauvegarde()}"
                )
            except Exception:
                pass
        else:
            messagebox.showerror("Erreur", msg)

    def _ouvrir_dossier(self):
        dossier = get_dossier_backups()
        try:
            if platform.system() == "Windows":
                os.startfile(dossier)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", dossier])
            else:
                subprocess.Popen(["xdg-open", dossier])
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def _nettoyer(self):
        rep = messagebox.askyesno(
            "Nettoyage",
            "Garder uniquement les 20 sauvegardes les plus recentes ?"
        )
        if rep:
            nettoyer_vieilles_sauvegardes(20)
            self._rafraichir_backups()
            messagebox.showinfo("Nettoyage", "Nettoyage effectue.")

    def _rafraichir_backups(self):
        for w in self.frame_backups.winfo_children():
            w.destroy()

        sauvegardes = lister_sauvegardes()

        if not sauvegardes:
            ctk.CTkLabel(self.frame_backups,
                         text="Aucune sauvegarde pour le moment.",
                         font=("Segoe UI", 12),
                         text_color="#999999").pack(pady=30)
            return

        entete = ctk.CTkFrame(self.frame_backups, fg_color="#f0f0f0", corner_radius=6)
        entete.pack(fill="x", pady=(0, 5))

        for nom, larg in [("Date", 160), ("Fichier", 280), ("Taille", 100)]:
            ctk.CTkLabel(entete, text=nom,
                         font=("Segoe UI", 11, "bold"),
                         text_color=COLOR_NAVY, width=larg,
                         anchor="w").pack(side="left", padx=5, pady=8)

        ctk.CTkLabel(entete, text="Actions",
                     font=("Segoe UI", 11, "bold"),
                     text_color=COLOR_NAVY, width=180,
                     anchor="center").pack(side="right", padx=5, pady=8)

        for i, s in enumerate(sauvegardes):
            fond = "#ffffff" if i % 2 == 0 else "#fafafa"
            ligne = ctk.CTkFrame(self.frame_backups, fg_color=fond, corner_radius=4)
            ligne.pack(fill="x", pady=1)

            taille_ko = s["taille"] / 1024
            taille_str = f"{taille_ko:.1f} Ko" if taille_ko < 1024 else f"{taille_ko/1024:.2f} Mo"

            for val, larg, coul, poids in [
                (s["date"].strftime("%d/%m/%Y %H:%M"), 160, "#333333", "normal"),
                (s["nom"], 280, "#0066CC", "normal"),
                (taille_str, 100, "#666666", "normal"),
            ]:
                ctk.CTkLabel(ligne, text=str(val),
                             font=("Segoe UI", 11, poids),
                             text_color=coul, width=larg,
                             anchor="w").pack(side="left", padx=5, pady=6)

            actions = ctk.CTkFrame(ligne, fg_color="transparent", width=180)
            actions.pack(side="right", padx=5)

            ctk.CTkButton(actions, text="Restaurer",
                          font=("Segoe UI", 10, "bold"),
                          width=90, height=26,
                          fg_color="#e67e22", hover_color="#d35400",
                          command=lambda ss=s: self._restaurer(ss)).pack(side="left", padx=2)

            ctk.CTkButton(actions, text="X",
                          font=("Segoe UI", 10, "bold"),
                          width=36, height=26,
                          fg_color="#e74c3c", hover_color="#c0392b",
                          command=lambda ss=s: self._supprimer_backup(ss)).pack(side="left", padx=2)

    def _restaurer(self, sauvegarde):
        rep = messagebox.askyesno(
            "Attention",
            f"RESTAURER la sauvegarde ?\n\n"
            f"Fichier : {sauvegarde['nom']}\n"
            f"Date : {sauvegarde['date'].strftime('%d/%m/%Y %H:%M')}\n\n"
            f"ATTENTION : la base actuelle sera ECRASEE.\n\n"
            f"Continuer ?"
        )
        if rep:
            ok, msg = restaurer_sauvegarde(sauvegarde["chemin"])
            if ok:
                messagebox.showinfo("Restauration", msg)
            else:
                messagebox.showerror("Erreur", msg)

    def _supprimer_backup(self, sauvegarde):
        rep = messagebox.askyesno(
            "Confirmation",
            f"Supprimer la sauvegarde :\n\n{sauvegarde['nom']} ?"
        )
        if rep:
            supprimer_sauvegarde(sauvegarde["chemin"])
            self._rafraichir_backups()


# ============================================================
# FENETRE DE BLOCAGE DES FONCTIONNALITES
# ============================================================
class FenetreBlocage(ctk.CTkToplevel):
    def __init__(self, parent, user, on_save=None):
        super().__init__(parent)

        self.user = user
        self.on_save = on_save

        self.title(f"Bloquer les fonctionnalites - {user['nom_complet']}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        largeur = 560
        hauteur = 700
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        if hauteur > screen_h - 60:
            hauteur = screen_h - 60

        x = (screen_w // 2) - (largeur // 2)
        y = max(20, (screen_h // 2) - (hauteur // 2))
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")

        self.bind("<Escape>", lambda e: self.destroy())
        self.transient(parent)
        self.after(100, self._activer_grab)

        # Charger les fonctionnalites deja bloquees
        self.bloques_actuels = set(get_fonctionnalites_bloquees(user["id"]))

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

        # ===== BOUTONS BAS =====
        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=20, pady=(5, 15), side="bottom")

        ctk.CTkButton(boutons, text="Annuler",
                      font=("Segoe UI", 12),
                      fg_color="#e74c3c", text_color="white",
                      hover_color="#c0392b", height=40, width=120,
                      command=self.destroy).pack(side="right", padx=(5, 0))

        ctk.CTkButton(boutons, text="Enregistrer",
                      font=("Segoe UI", 12, "bold"),
                      fg_color=COLOR_NAVY, hover_color="#1a3d75",
                      height=40,
                      command=self._enregistrer).pack(side="left", expand=True, fill="x")

        # ===== TITRE =====
        ctk.CTkLabel(card,
                     text="BLOQUER LES FONCTIONNALITES",
                     font=("Segoe UI", 15, "bold"),
                     text_color=COLOR_NAVY).pack(pady=(15, 5))

        role_txt = (self.user.get("role") or "").upper()
        ctk.CTkLabel(card,
                     text=f"{self.user['nom_complet']}  ({role_txt})",
                     font=("Segoe UI", 12),
                     text_color="#666666").pack(pady=(0, 10))

        # ===== INFO =====
        info = ctk.CTkFrame(card, fg_color="#FFF3CD", corner_radius=8)
        info.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(
            info,
            text=("Cochez les modules que vous voulez BLOQUER pour cet utilisateur.\n"
                  "Un module coche disparaitra de son menu.\n"
                  "Les modules non coches restent accessibles."),
            font=("Segoe UI", 10),
            text_color="#8B6914",
            justify="left",
            wraplength=480,
        ).pack(padx=15, pady=10, anchor="w")

        # ===== BOUTONS TOUT BLOQUER / TOUT DEBLOQUER =====
        ligne_actions = ctk.CTkFrame(card, fg_color="transparent")
        ligne_actions.pack(fill="x", padx=20, pady=(0, 5))

        ctk.CTkButton(ligne_actions, text="Tout cocher",
                      font=("Segoe UI", 10, "bold"),
                      fg_color="#e74c3c", hover_color="#c0392b",
                      height=28, width=110,
                      command=self._tout_cocher).pack(side="left", padx=(0, 5))

        ctk.CTkButton(ligne_actions, text="Tout decocher",
                      font=("Segoe UI", 10, "bold"),
                      fg_color="#27ae60", hover_color="#229954",
                      height=28, width=130,
                      command=self._tout_decocher).pack(side="left")

        # ===== LISTE DES FONCTIONNALITES =====
        zone = ctk.CTkScrollableFrame(card, fg_color="#FAFAFA", corner_radius=8)
        zone.pack(fill="both", expand=True, padx=20, pady=(5, 5))

        self.checkboxes = {}

        for i, module in enumerate(FONCTIONNALITES_BLOQUABLES):
            fond = "#ffffff" if i % 2 == 0 else "#F5F5F5"
            ligne = ctk.CTkFrame(zone, fg_color=fond, corner_radius=4)
            ligne.pack(fill="x", pady=1, padx=2)

            var = ctk.BooleanVar(value=(module in self.bloques_actuels))

            cb = ctk.CTkCheckBox(
                ligne,
                text=f"  {module}",
                variable=var,
                font=("Segoe UI", 12),
                text_color="#333333",
                fg_color="#e74c3c",
                hover_color="#c0392b",
                checkbox_width=22,
                checkbox_height=22,
            )
            cb.pack(side="left", padx=15, pady=10, anchor="w")

            self.checkboxes[module] = var

        # ===== COMPTEUR =====
        self.label_compteur = ctk.CTkLabel(card, text="",
                                            font=("Segoe UI", 12, "bold"),
                                            text_color="#e74c3c")
        self.label_compteur.pack(pady=(5, 5))

        # Bind pour mettre a jour le compteur
        for module, var in self.checkboxes.items():
            var.trace_add("write", lambda *a: self._maj_compteur())

        self._maj_compteur()

    def _maj_compteur(self):
        nb = sum(1 for v in self.checkboxes.values() if v.get())
        if nb == 0:
            texte = "Aucun module bloque (acces complet)"
            couleur = "#27ae60"
        else:
            texte = f"{nb} module(s) bloque(s)"
            couleur = "#e74c3c"
        self.label_compteur.configure(text=texte, text_color=couleur)

    def _tout_cocher(self):
        for v in self.checkboxes.values():
            v.set(True)

    def _tout_decocher(self):
        for v in self.checkboxes.values():
            v.set(False)

    def _enregistrer(self):
        liste = [m for m, v in self.checkboxes.items() if v.get()]

        ok, msg = set_fonctionnalites_bloquees(self.user["id"], liste)
        if ok:
            if len(liste) == 0:
                messagebox.showinfo("Succes",
                                    f"Aucun blocage : {self.user['nom_complet']} "
                                    f"a retrouve un acces complet.")
            else:
                messagebox.showinfo("Succes",
                                    f"{len(liste)} module(s) bloque(s) pour "
                                    f"{self.user['nom_complet']}.\n\n"
                                    f"L'utilisateur ne verra plus ces modules "
                                    f"dans son menu a sa prochaine connexion.")
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Erreur", msg)


# ============================================================
# FORMULAIRE UTILISATEUR
# ============================================================
class FormulaireUtilisateur(ctk.CTkToplevel):
    def __init__(self, parent, user=None, on_save=None):
        super().__init__(parent)

        self.user = user
        self.on_save = on_save

        titre = "Modifier l'utilisateur" if user else "Nouvel utilisateur"
        self.title(titre)

        largeur = 500
        hauteur = 480
        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        x = (self.winfo_screenwidth() // 2) - (largeur // 2)
        y = max(20, (self.winfo_screenheight() // 2) - (hauteur // 2))
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
        ligne_titre.pack(fill="x", padx=15, pady=(15, 5))

        titre = "Modifier l'utilisateur" if self.user else "Nouvel utilisateur"
        ctk.CTkLabel(ligne_titre, text=titre,
                     font=("Segoe UI", 17, "bold"),
                     text_color=COLOR_NAVY).pack(side="left")

        ctk.CTkButton(ligne_titre, text="X",
                      font=("Segoe UI", 14, "bold"),
                      width=32, height=32,
                      fg_color="#e74c3c", hover_color="#c0392b",
                      command=self.destroy).pack(side="right")

        self.champs = {}

        ctk.CTkLabel(card, text="Nom complet *",
                     font=("Segoe UI", 12, "bold"),
                     text_color="#333333", anchor="w").pack(padx=20, pady=(10, 4), fill="x")
        self.champs["nom"] = ctk.CTkEntry(card, font=("Segoe UI", 13), height=38)
        if self.user:
            self.champs["nom"].insert(0, self.user["nom_complet"])
        self.champs["nom"].pack(padx=20, pady=(0, 10), fill="x")

        ctk.CTkLabel(card, text="Email *",
                     font=("Segoe UI", 12, "bold"),
                     text_color="#333333", anchor="w").pack(padx=20, pady=(10, 4), fill="x")
        self.champs["email"] = ctk.CTkEntry(card, font=("Segoe UI", 13), height=38)
        if self.user:
            self.champs["email"].insert(0, self.user["email"])
            self.champs["email"].configure(state="disabled")
        self.champs["email"].pack(padx=20, pady=(0, 10), fill="x")

        label_mdp = ("Nouveau mot de passe (laisser vide pour ne pas changer)"
                     if self.user else "Mot de passe *")
        ctk.CTkLabel(card, text=label_mdp,
                     font=("Segoe UI", 12, "bold"),
                     text_color="#333333", anchor="w").pack(padx=20, pady=(10, 4), fill="x")
        self.champs["mdp"] = ctk.CTkEntry(card, font=("Segoe UI", 13),
                                          height=38, show="*",
                                          placeholder_text="********")
        self.champs["mdp"].pack(padx=20, pady=(0, 10), fill="x")

        ctk.CTkLabel(card, text="Role *",
                     font=("Segoe UI", 12, "bold"),
                     text_color="#333333", anchor="w").pack(padx=20, pady=(10, 4), fill="x")
        self.combo_role = ctk.CTkComboBox(
            card,
            values=["admin", "gestionnaire", "comptable", "caissier",
                    "directeur", "prefet"],
            font=("Segoe UI", 13), height=38,
        )
        self.combo_role.set(self.user["role"] if self.user else "comptable")
        self.combo_role.pack(padx=20, pady=(0, 15), fill="x")

        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=20, pady=(5, 15))

        ctk.CTkButton(boutons, text="Annuler",
                      font=("Segoe UI", 13),
                      fg_color="#e74c3c", text_color="white",
                      hover_color="#c0392b", height=42,
                      command=self.destroy).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(boutons, text="Enregistrer",
                      font=("Segoe UI", 13, "bold"),
                      fg_color=COLOR_NAVY, hover_color="#1a3d75",
                      height=42, command=self._enregistrer,
                      ).pack(side="left", expand=True, fill="x", padx=(5, 0))

    def _enregistrer(self):
        nom = self.champs["nom"].get().strip()
        email = self.champs["email"].get().strip()
        mdp = self.champs["mdp"].get().strip()
        role = self.combo_role.get().strip()

        if not nom:
            messagebox.showerror("Erreur", "Le nom complet est obligatoire.")
            return

        if not self.user:
            if not email or "@" not in email:
                messagebox.showerror("Erreur", "Email invalide.")
                return
            if not mdp or len(mdp) < 4:
                messagebox.showerror("Erreur",
                                     "Mot de passe trop court (min 4 caracteres).")
                return
            if email_existe(email):
                messagebox.showerror("Erreur", "Cet email est deja utilise.")
                return

            ok, msg = creer_utilisateur(nom, email, mdp, role)
            if ok:
                messagebox.showinfo("Succes", f"Utilisateur cree :\n{email}")
                if self.on_save:
                    self.on_save()
                self.destroy()
            else:
                messagebox.showerror("Erreur", msg)
        else:
            nouveau_mdp = mdp if mdp else None
            ok, msg = modifier_utilisateur(self.user["id"], nom,
                                            role=role, mot_de_passe=nouveau_mdp)
            if ok:
                messagebox.showinfo("Succes", "Utilisateur modifie.")
                if self.on_save:
                    self.on_save()
                self.destroy()
            else:
                messagebox.showerror("Erreur", msg)