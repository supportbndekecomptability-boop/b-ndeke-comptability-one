"""
Interface Paiements (Eleves + Personnel) avec scroll horizontal
+ Impression par feuille de 6 recus
+ Affectation aux dettes eleves (OUI/NON au choix du caissier)
+ Modification des dates (passe / futur) - saisie manuelle
+ Fenetre adaptative aux petits ecrans
+ Permissions par role (caissier / comptable / admin / gestionnaire)
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
from config import COLOR_NAVY, COLOR_GOLD, format_montant, CURRENCY_SYMBOL
from core.paiements import (
    ajouter_paiement_eleve, ajouter_paiement_personnel,
    modifier_paiement_eleve, modifier_paiement_personnel,
    lister_paiements_eleves, lister_paiements_personnel,
    supprimer_paiement_eleve, supprimer_paiement_personnel,
    rechercher_eleve_par_matricule, rechercher_personnel_par_code,
    dettes_en_cours_eleve,
)
from core.avances import total_avance_en_cours, deduire_avances_personnel
from core.permissions import a_permission, get_role
from services.recus_pdf import (
    generer_recu_eleve, generer_recu_personnel, generer_feuille_recus,
)
from ui.pdf_viewer import PdfViewerWindow
from ui.scroll_frame import HorizontalScrollFrame


# ===== HELPER : IDs des caissiers (pour le comptable) =====
def _ids_caissiers():
    """Retourne l'ensemble des IDs utilisateurs ayant le role caissier."""
    try:
        from database import get_connection
        c = get_connection()
        cur = c.cursor()
        cur.execute("SELECT id FROM utilisateurs WHERE LOWER(role) = 'caissier'")
        ids = {row["id"] for row in cur.fetchall()}
        c.close()
        return ids
    except Exception as e:
        print(f"[PERMISSIONS] Impossible de charger les caissiers : {e}")
        return set()


class PaiementsPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")

        self.utilisateur = utilisateur
        self.type_actuel = "eleve"
        self.caissier_ids = _ids_caissiers()

        self._construire_interface()
        self.rafraichir_tableau()

    # ================== PERMISSIONS ==================
    def _peut_creer(self):
        """Creer un paiement : caissier, admin, gestionnaire."""
        return a_permission(self.utilisateur, "peut_gerer_paiements")

    def _peut_modifier_op(self):
        """Modifier une operation : comptable, admin, gestionnaire."""
        return (a_permission(self.utilisateur, "peut_modifier_operations_caissier")
                or a_permission(self.utilisateur, "peut_tout_modifier"))

    def _peut_supprimer_op(self):
        """Supprimer une operation : comptable, admin, gestionnaire."""
        return (a_permission(self.utilisateur, "peut_supprimer_operations_caissier")
                or a_permission(self.utilisateur, "peut_supprimer"))

    def _peut_imprimer(self):
        return a_permission(self.utilisateur, "peut_imprimer")

    def _nb_actions(self):
        n = 0
        if self._peut_imprimer():
            n += 1
        if self._peut_modifier_op():
            n += 1
        if self._peut_supprimer_op():
            n += 1
        return n

    def _largeur_actions(self):
        largeur = 0
        if self._peut_imprimer():
            largeur += 79
        if self._peut_modifier_op():
            largeur += 79
        if self._peut_supprimer_op():
            largeur += 40
        return largeur if largeur > 0 else 40

    # ================== FILTRE PAR ROLE ==================
    def _filtrer_paiements(self, paiements):
        """
        - admin / gestionnaire : tout
        - caissier : uniquement SES operations
        - comptable : uniquement les operations des CAISSIERS
        - directeur / prefet : rien (page normalement inaccessible)
        """
        role = get_role(self.utilisateur)

        if role in ("admin", "gestionnaire"):
            return paiements

        if role == "caissier":
            uid = self.utilisateur.get("id")
            return [p for p in paiements if p.get("utilisateur_id") == uid]

        if role == "comptable":
            return [p for p in paiements
                    if p.get("utilisateur_id") in self.caissier_ids]

        if role in ("directeur", "prefet"):
            return []

        return paiements

    # ================== INTERFACE ==================
    def _construire_interface(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            top,
            text="Paiements",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        # ===== Bouton "+ Nouveau paiement" =====
        if self._peut_creer():
            ctk.CTkButton(
                top,
                text="+ Nouveau paiement",
                font=("Segoe UI", 13, "bold"),
                fg_color=COLOR_NAVY,
                hover_color="#1a3d75",
                height=40,
                command=self._ouvrir_formulaire,
            ).pack(side="right")

        # ===== Bouton "Feuille 6 recus" =====
        if self._peut_imprimer():
            ctk.CTkButton(
                top,
                text="Feuille 6 recus",
                font=("Segoe UI", 12, "bold"),
                fg_color="#27ae60",
                hover_color="#229954",
                height=40,
                command=self._imprimer_feuille_6,
            ).pack(side="right", padx=(0, 10))

        # ===== Badge info role =====
        role = get_role(self.utilisateur)
        if role == "caissier":
            info_role = "Vue : vos propres operations uniquement"
            couleur_role = "#3498db"
        elif role == "comptable":
            info_role = "Vue : operations des caissiers (lecture + modification)"
            couleur_role = "#e67e22"
        else:
            info_role = "Vue : toutes les operations"
            couleur_role = "#27ae60"

        ctk.CTkLabel(
            top,
            text=info_role,
            font=("Segoe UI", 10, "italic"),
            text_color=couleur_role,
        ).pack(side="right", padx=(0, 15))

        # ===== Onglets =====
        onglets = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        onglets.pack(fill="x", pady=(0, 10))

        self.btn_eleve = ctk.CTkButton(
            onglets,
            text="Paiements Eleves (Recettes)",
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_NAVY,
            hover_color="#1a3d75",
            text_color="white",
            height=45,
            corner_radius=8,
            command=lambda: self._changer_type("eleve"),
        )
        self.btn_eleve.pack(side="left", expand=True, fill="x", padx=(10, 5), pady=10)

        self.btn_personnel = ctk.CTkButton(
            onglets,
            text="Paiements Personnel (Depenses)",
            font=("Segoe UI", 13, "bold"),
            fg_color="#e0e0e0",
            hover_color="#c0c0c0",
            text_color="#333333",
            height=45,
            corner_radius=8,
            command=lambda: self._changer_type("personnel"),
        )
        self.btn_personnel.pack(side="left", expand=True, fill="x", padx=(5, 10), pady=10)

        # ===== Recherche =====
        recherche_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        recherche_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            recherche_frame,
            text="Recherche :",
            font=("Segoe UI", 12, "bold"),
            text_color="#666666",
        ).pack(side="left", padx=(15, 5), pady=12)

        self.entree_recherche = ctk.CTkEntry(
            recherche_frame,
            placeholder_text="Numero, matricule/code, nom, motif...",
            font=("Segoe UI", 13),
            border_width=0,
            fg_color="white",
            height=35,
        )
        self.entree_recherche.pack(side="left", fill="x", expand=True, padx=5, pady=12)
        self.entree_recherche.bind("<KeyRelease>", lambda e: self.rafraichir_tableau())

        ctk.CTkButton(
            recherche_frame,
            text="Effacer",
            font=("Segoe UI", 11),
            fg_color="#e0e0e0",
            text_color="#333333",
            hover_color="#c0c0c0",
            width=80,
            height=32,
            command=self._effacer_recherche,
        ).pack(side="right", padx=15, pady=12)

        self.label_compteur = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 12),
            text_color="#666666",
        )
        self.label_compteur.pack(anchor="w", pady=(0, 10))

        self.tableau = HorizontalScrollFrame(self, fg_color="white",
                                             corner_radius=10)
        self.tableau.pack(fill="both", expand=True)

        self.tableau_frame = self.tableau.interior
        self.entete_frame = None

    def _changer_type(self, type_):
        self.type_actuel = type_
        if type_ == "eleve":
            self.btn_eleve.configure(fg_color=COLOR_NAVY, text_color="white")
            self.btn_personnel.configure(fg_color="#e0e0e0", text_color="#333333")
        else:
            self.btn_eleve.configure(fg_color="#e0e0e0", text_color="#333333")
            self.btn_personnel.configure(fg_color=COLOR_NAVY, text_color="white")
        self.entree_recherche.delete(0, "end")
        self.rafraichir_tableau()

    def _effacer_recherche(self):
        self.entree_recherche.delete(0, "end")
        self.rafraichir_tableau()

    # ================== TABLEAU ==================
    def _truncate(self, texte, longueur_max):
        texte = str(texte) if texte is not None else ""
        if len(texte) <= longueur_max:
            return texte
        return texte[:longueur_max - 3] + "..."

    def _creer_entete(self):
        if self.entete_frame:
            self.entete_frame.destroy()

        self.entete_frame = ctk.CTkFrame(self.tableau_frame,
                                         fg_color="#f0f0f0", corner_radius=6)
        self.entete_frame.pack(fill="x", pady=(0, 5))

        if self.type_actuel == "eleve":
            colonnes = [
                ("N Recu", 115),
                ("Date", 130),
                ("Matricule", 100),
                ("Eleve", 150),
                ("Classe", 95),
                ("Motif", 200),
                ("Mode", 90),
                ("Montant", 100),
            ]
        else:
            colonnes = [
                ("N Paie", 105),
                ("Date", 130),
                ("Code", 95),
                ("Personnel", 150),
                ("Motif", 180),
                ("Mode", 90),
                ("Salaire", 90),
                ("Avance", 90),
                ("Net", 90),
            ]

        for nom, largeur in colonnes:
            ctk.CTkLabel(
                self.entete_frame,
                text=nom,
                font=("Segoe UI", 11, "bold"),
                text_color=COLOR_NAVY,
                width=largeur,
                anchor="w",
            ).pack(side="left", padx=4, pady=10)

        if self._nb_actions() > 0:
            ctk.CTkLabel(
                self.entete_frame,
                text="Actions",
                font=("Segoe UI", 11, "bold"),
                text_color=COLOR_NAVY,
                width=self._largeur_actions(),
                anchor="center",
            ).pack(side="left", padx=4, pady=10)

    def rafraichir_tableau(self):
        self.tableau.clear()
        self._creer_entete()

        recherche = self.entree_recherche.get()

        if self.type_actuel == "eleve":
            paiements = lister_paiements_eleves(recherche)
        else:
            paiements = lister_paiements_personnel(recherche)

        self.label_compteur.configure(text=f"{len(paiements)} enregistrement(s)")

        if not paiements:
            ctk.CTkLabel(
                self.tableau_frame,
                text="Aucun paiement. Cliquez sur '+ Nouveau paiement'.",
                font=("Segoe UI", 13),
                text_color="#999999",
            ).pack(pady=40)
            return

        for i, p in enumerate(paiements):
            fond = "#ffffff" if i % 2 == 0 else "#fafafa"
            ligne = ctk.CTkFrame(self.tableau_frame, fg_color=fond, corner_radius=4)
            ligne.pack(fill="x", pady=1)

            try:
                date_p = p["date_paiement"][:16].replace("T", " ")
            except Exception:
                date_p = str(p.get("date_paiement", ""))[:16]

            if self.type_actuel == "eleve":
                num = self._truncate(p["numero_recu"], 16)
                code = self._truncate(p["matricule"], 14)
                nom_p = self._truncate(f"{p['nom']} {p['prenom']}", 22)
                extra = self._truncate(p["classe"], 14)
                motif = self._truncate(p["motif"], 30)
                mode = self._truncate(p["mode_paiement"], 14)
                couleur_num = "#0066CC"

                valeurs = [
                    (num, 115, couleur_num, "bold"),
                    (date_p, 130, "#333333", "normal"),
                    (code, 100, "#333333", "normal"),
                    (nom_p, 150, "#333333", "normal"),
                    (extra, 95, "#333333", "normal"),
                    (motif, 200, "#333333", "normal"),
                    (mode, 90, "#333333", "normal"),
                    (format_montant(p["montant"]), 100, "#27ae60", "bold"),
                ]
            else:
                num = self._truncate(p["numero_paie"], 16)
                code = self._truncate(p["code"], 14)
                nom_p = self._truncate(f"{p['nom']} {p['prenom']}", 22)
                motif = self._truncate(p["motif"], 26)
                mode = self._truncate(p["mode_paiement"], 14)
                montant_total = p["montant"] or 0
                avance = p.get("montant_avance_deduit", 0) or 0
                net = montant_total - avance
                couleur_num = "#e67e22"

                valeurs = [
                    (num, 105, couleur_num, "bold"),
                    (date_p, 130, "#333333", "normal"),
                    (code, 95, "#333333", "normal"),
                    (nom_p, 150, "#333333", "normal"),
                    (motif, 180, "#333333", "normal"),
                    (mode, 90, "#333333", "normal"),
                    (format_montant(montant_total), 90, "#e67e22", "normal"),
                    (format_montant(avance) if avance > 0 else "-",
                     90, "#8e44ad", "normal"),
                    (format_montant(net), 90, "#e74c3c", "bold"),
                ]

            for valeur, largeur, couleur, poids in valeurs:
                ctk.CTkLabel(
                    ligne,
                    text=str(valeur),
                    font=("Segoe UI", 11, poids),
                    text_color=couleur,
                    width=largeur,
                    anchor="w",
                ).pack(side="left", padx=4, pady=8)

            # ===== Actions conditionnelles =====
            if self._nb_actions() == 0:
                continue

            actions = ctk.CTkFrame(
                ligne, fg_color="transparent",
                width=self._largeur_actions()
            )
            actions.pack(side="left", padx=4)

            # Imprimer : tout le monde
            if self._peut_imprimer():
                ctk.CTkButton(
                    actions,
                    text="Imprimer",
                    font=("Segoe UI", 10, "bold"),
                    width=75,
                    height=28,
                    fg_color="#3498db",
                    hover_color="#2980b9",
                    command=lambda pay=p: self._imprimer_recu(pay),
                ).pack(side="left", padx=2)

            # Modifier : comptable + admin/gestionnaire
            if self._peut_modifier_op():
                ctk.CTkButton(
                    actions,
                    text="Modifier",
                    font=("Segoe UI", 10, "bold"),
                    width=75,
                    height=28,
                    fg_color="#e67e22",
                    hover_color="#d35400",
                    command=lambda pay=p: self._modifier(pay),
                ).pack(side="left", padx=2)

            # Supprimer : comptable + admin/gestionnaire
            if self._peut_supprimer_op():
                ctk.CTkButton(
                    actions,
                    text="X",
                    font=("Segoe UI", 11, "bold"),
                    width=36,
                    height=28,
                    fg_color="#e74c3c",
                    hover_color="#c0392b",
                    command=lambda pay=p: self._supprimer(pay),
                ).pack(side="left", padx=2)

    # ================== ACTIONS ==================
    def _ouvrir_formulaire(self):
        if not self._peut_creer():
            messagebox.showerror("Acces refuse",
                                 "Vous n'avez pas la permission de creer un paiement.")
            return
        FormulairePaiement(
            self,
            type_=self.type_actuel,
            utilisateur=self.utilisateur,
            on_save=self.rafraichir_tableau,
        )

    def _modifier(self, p):
        if not self._peut_modifier_op():
            messagebox.showerror("Acces refuse",
                                 "Vous n'avez pas la permission de modifier.")
            return

        FormulairePaiement(
            self,
            type_=self.type_actuel,
            utilisateur=self.utilisateur,
            on_save=self.rafraichir_tableau,
            paiement_existant=p,
        )

    def _imprimer_feuille_6(self):
        if not self._peut_imprimer():
            return

        recherche = self.entree_recherche.get()

        if self.type_actuel == "eleve":
            paiements = lister_paiements_eleves(recherche)
        else:
            paiements = lister_paiements_personnel(recherche)

        if not paiements:
            messagebox.showwarning(
                "Aucun paiement",
                "Il n'y a aucun paiement a imprimer."
            )
            return

        a_imprimer = paiements[:6]

        rep = messagebox.askyesno(
            "Confirmation",
            f"Imprimer une feuille avec {len(a_imprimer)} recu(s) ?\n\n"
            f"Les 6 premiers resultats affiches seront imprimes\n"
            f"sur une seule page A4 (2 colonnes x 3 lignes)."
        )

        if not rep:
            return

        try:
            chemin = generer_feuille_recus(a_imprimer, self.type_actuel)
            PdfViewerWindow(self.master, chemin,
                            titre=f"Feuille de {len(a_imprimer)} recus")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur",
                                 f"Impossible de generer la feuille :\n{e}")

    def _imprimer_recu(self, p):
        if not self._peut_imprimer():
            return
        try:
            if self.type_actuel == "eleve":
                paiement_info = {
                    "numero_recu": p.get("numero_recu", ""),
                    "date_paiement": p.get("date_paiement", ""),
                    "montant": p.get("montant", 0),
                    "motif": p.get("motif", ""),
                    "mode_paiement": p.get("mode_paiement", ""),
                    "matricule": p.get("matricule", ""),
                    "nom": p.get("nom", ""),
                    "prenom": p.get("prenom", ""),
                    "classe": p.get("classe", ""),
                }
                chemin = generer_recu_eleve(paiement_info)
                PdfViewerWindow(self.master, chemin,
                                titre=f"Recu {p.get('numero_recu', '')}")
            else:
                paiement_info = {
                    "numero_paie": p.get("numero_paie", ""),
                    "date_paiement": p.get("date_paiement", ""),
                    "montant": p.get("montant", 0),
                    "montant_avance_deduit": p.get("montant_avance_deduit", 0),
                    "motif": p.get("motif", ""),
                    "mode_paiement": p.get("mode_paiement", ""),
                    "code": p.get("code", ""),
                    "nom": p.get("nom", ""),
                    "prenom": p.get("prenom", ""),
                    "fonction": p.get("fonction", ""),
                }
                chemin = generer_recu_personnel(paiement_info)
                PdfViewerWindow(self.master, chemin,
                                titre=f"Bulletin paie {p.get('numero_paie', '')}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Impossible de generer le recu :\n{e}")

    def _supprimer(self, p):
        if not self._peut_supprimer_op():
            messagebox.showerror("Acces refuse",
                                 "Vous n'avez pas la permission de supprimer.")
            return

        if self.type_actuel == "eleve":
            titre = "paiement eleve"
            numero = p.get("numero_recu", "")
            suppr = supprimer_paiement_eleve
        else:
            titre = "paie personnel"
            numero = p.get("numero_paie", "")
            suppr = supprimer_paiement_personnel

        rep = messagebox.askyesno(
            "Confirmation",
            f"Voulez-vous vraiment supprimer ce {titre} ?\n\n"
            f"N {numero}\n{format_montant(p['montant'])}\n\n"
            f"Le solde de la personne sera recalcule."
        )
        if rep:
            ok, msg = suppr(p["id"])
            if ok:
                self.rafraichir_tableau()
            else:
                messagebox.showerror("Erreur", msg)


# ============================================================
# FORMULAIRE DE PAIEMENT (inchange)
# ============================================================
class FormulairePaiement(ctk.CTkToplevel):
    def __init__(self, parent, type_="eleve", utilisateur=None, on_save=None,
                 paiement_existant=None):
        super().__init__(parent)

        self.type_ = type_
        self.utilisateur = utilisateur
        self.on_save = on_save
        self.personne = None
        self.avance_disponible = 0
        self.dettes_eleve = []
        self.paiement_existant = paiement_existant
        self.mode_edition = paiement_existant is not None

        if self.mode_edition:
            titre = "Modifier paiement" if type_ == "eleve" else "Modifier paie"
        else:
            titre = "Paiement eleve" if type_ == "eleve" else "Paie personnel"
        self.title(titre)

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        largeur = min(540, screen_w - 60)
        hauteur = min(720, screen_h - 100)

        x = max(0, (screen_w // 2) - (largeur // 2))
        y = max(10, (screen_h - hauteur) // 2 - 20)

        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        self.bind("<Escape>", lambda e: self.destroy())

        self.transient(parent)
        self.after(100, self._activer_grab)

        self._construire_interface()

        if self.mode_edition:
            self.after(200, self._pre_remplir_edition)

    def _activer_grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _construire_interface(self):
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=15, pady=(5, 12), side="bottom")

        ctk.CTkButton(
            boutons,
            text="Annuler (Echap)",
            font=("Segoe UI", 13, "bold"),
            fg_color="#e74c3c",
            text_color="white",
            hover_color="#c0392b",
            height=42,
            command=self.destroy,
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        texte_btn = "Enregistrer les modifications" if self.mode_edition else "Enregistrer"
        ctk.CTkButton(
            boutons,
            text=texte_btn,
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_NAVY if self.type_ == "eleve" else "#e67e22",
            hover_color="#1a3d75" if self.type_ == "eleve" else "#d35400",
            height=42,
            command=self._enregistrer,
        ).pack(side="left", expand=True, fill="x", padx=(5, 0))

        ligne_titre = ctk.CTkFrame(card, fg_color="transparent")
        ligne_titre.pack(fill="x", padx=15, pady=(12, 5), side="top")

        if self.mode_edition:
            titre = "MODIFIER PAIEMENT" if self.type_ == "eleve" else "MODIFIER PAIE"
        else:
            titre = "Nouveau paiement Eleve" if self.type_ == "eleve" else "Nouvelle paie Personnel"
        couleur_titre = COLOR_NAVY if self.type_ == "eleve" else "#e67e22"

        ctk.CTkLabel(
            ligne_titre,
            text=titre,
            font=("Segoe UI", 17, "bold"),
            text_color=couleur_titre,
        ).pack(side="left")

        ctk.CTkButton(
            ligne_titre,
            text="X",
            font=("Segoe UI", 14, "bold"),
            width=32,
            height=32,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.destroy,
        ).pack(side="right")

        zone = ctk.CTkScrollableFrame(card, fg_color="transparent", corner_radius=0)
        zone.pack(fill="both", expand=True, padx=5, pady=5)

        label_recherche = "Matricule de l'eleve *" if self.type_ == "eleve" else "Code du personnel *"
        placeholder = "Ex: BN20250001" if self.type_ == "eleve" else "Ex: PERS-0001"

        ctk.CTkLabel(
            zone, text=label_recherche,
            font=("Segoe UI", 12, "bold"), text_color="#333333", anchor="w"
        ).pack(padx=10, pady=(8, 4), fill="x")

        ligne_recherche = ctk.CTkFrame(zone, fg_color="transparent")
        ligne_recherche.pack(padx=10, pady=(0, 6), fill="x")

        self.entree_code = ctk.CTkEntry(
            ligne_recherche,
            font=("Segoe UI", 13),
            height=38,
            placeholder_text=placeholder,
        )
        self.entree_code.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entree_code.bind("<Return>", lambda e: self._rechercher())

        if self.mode_edition:
            self.entree_code.configure(state="disabled")
            btn_recherche_state = "disabled"
        else:
            btn_recherche_state = "normal"

        ctk.CTkButton(
            ligne_recherche,
            text="Rechercher",
            font=("Segoe UI", 12, "bold"),
            fg_color=COLOR_NAVY,
            hover_color="#1a3d75",
            width=110,
            height=38,
            state=btn_recherche_state,
            command=self._rechercher,
        ).pack(side="left")

        self.frame_fiche = ctk.CTkFrame(zone, fg_color="#F0F7FF", corner_radius=8)

        self.label_fiche = ctk.CTkLabel(
            self.frame_fiche,
            text="",
            font=("Segoe UI", 12),
            text_color=COLOR_NAVY,
            justify="left",
        )
        self.label_fiche.pack(padx=15, pady=12, anchor="w")

        self.frame_dettes = ctk.CTkFrame(zone, fg_color="#FFF3CD", corner_radius=8)

        self.label_message = ctk.CTkLabel(
            zone,
            text="Saisissez le code puis cliquez sur Rechercher",
            font=("Segoe UI", 11),
            text_color="#999999",
        )
        self.label_message.pack(padx=10, pady=(4, 8))

        if self.type_ == "personnel":
            self.frame_avance = ctk.CTkFrame(zone, fg_color="#FFF4E6", corner_radius=8)

            self.var_deduire_avance = ctk.BooleanVar(value=False)

            ctk.CTkCheckBox(
                self.frame_avance,
                text="Deduire l'avance sur salaire",
                variable=self.var_deduire_avance,
                font=("Segoe UI", 11, "bold"),
                text_color="#8B6914",
                fg_color="#e67e22",
                hover_color="#d35400",
                command=self._on_check_avance,
            ).pack(padx=15, pady=(10, 5), anchor="w")

            self.label_avance_info = ctk.CTkLabel(
                self.frame_avance,
                text="",
                font=("Segoe UI", 10),
                text_color="#8B6914",
                justify="left",
                wraplength=420,
            )
            self.label_avance_info.pack(padx=15, pady=(0, 10), anchor="w")

        ctk.CTkLabel(
            zone, text="Date de l'operation (AAAA-MM-JJ) *",
            font=("Segoe UI", 12, "bold"), text_color="#333333", anchor="w"
        ).pack(padx=10, pady=(12, 4), fill="x")

        self.entree_date = ctk.CTkEntry(
            zone,
            font=("Segoe UI", 13, "bold"),
            height=40,
            placeholder_text="Tapez la date : AAAA-MM-JJ",
        )
        self.entree_date.pack(padx=10, pady=(0, 4), fill="x")

        ligne_dates = ctk.CTkFrame(zone, fg_color="transparent")
        ligne_dates.pack(padx=10, pady=(0, 6), fill="x")

        for label, delta, color, hover in [
            ("Aujourd'hui", 0, "#3498db", "#2980b9"),
            ("Hier", -1, "#9b59b6", "#8e44ad"),
            ("Demain", 1, "#16a085", "#13876f"),
            ("-7j", -7, "#7f8c8d", "#5d6d6e"),
        ]:
            ctk.CTkButton(
                ligne_dates,
                text=label,
                font=("Segoe UI", 10, "bold"),
                fg_color=color,
                hover_color=hover,
                height=28,
                width=90,
                command=lambda d=delta: self._set_date_rapide(d),
            ).pack(side="left", padx=2)

        ctk.CTkLabel(
            zone, text=f"Montant total ({CURRENCY_SYMBOL}) *",
            font=("Segoe UI", 12, "bold"), text_color="#333333", anchor="w"
        ).pack(padx=10, pady=(12, 4), fill="x")

        self.entree_montant = ctk.CTkEntry(
            zone,
            font=("Segoe UI", 14, "bold"),
            height=42,
            placeholder_text="0",
        )
        self.entree_montant.pack(padx=10, pady=(0, 6), fill="x")

        rapides = ctk.CTkFrame(zone, fg_color="transparent")
        rapides.pack(padx=10, pady=(0, 8), fill="x")

        ctk.CTkButton(
            rapides,
            text="Payer le solde total",
            font=("Segoe UI", 10, "bold"),
            fg_color=COLOR_GOLD,
            text_color="#333333",
            hover_color="#d9a500",
            height=28,
            command=self._payer_solde_total,
        ).pack(side="left", padx=(0, 4))

        for montant in [10, 20, 50, 100]:
            ctk.CTkButton(
                rapides,
                text=f"+{montant}",
                font=("Segoe UI", 10),
                fg_color="#e0e0e0",
                text_color="#333333",
                hover_color="#c0c0c0",
                width=45,
                height=28,
                command=lambda m=montant: self._ajouter_montant(m),
            ).pack(side="left", padx=2)

        ctk.CTkLabel(
            zone, text="Motif *",
            font=("Segoe UI", 12, "bold"), text_color="#333333", anchor="w"
        ).pack(padx=10, pady=(8, 4), fill="x")

        if self.type_ == "eleve":
            motifs = [
                "Frais scolaires",
                "Frais d'inscription",
                "Frais de reinscription",
                "Uniforme",
                "Fournitures scolaires",
                "Transport",
                "Cantine",
                "Autre",
            ]
        else:
            motifs = [
                "Salaire mensuel",
                "Prime",
                "Heures supplementaires",
                "Indemnite",
                "Autre",
            ]

        self.combo_motif = ctk.CTkComboBox(
            zone, values=motifs, font=("Segoe UI", 12), height=38,
        )
        self.combo_motif.set(motifs[0])
        self.combo_motif.pack(padx=10, pady=(0, 8), fill="x")

        ctk.CTkLabel(
            zone, text="Mode de paiement *",
            font=("Segoe UI", 12, "bold"), text_color="#333333", anchor="w"
        ).pack(padx=10, pady=(8, 4), fill="x")

        self.combo_mode = ctk.CTkComboBox(
            zone,
            values=["Especes", "Mobile Money", "Virement bancaire", "Cheque", "Carte"],
            font=("Segoe UI", 12),
            height=38,
        )
        self.combo_mode.set("Especes")
        self.combo_mode.pack(padx=10, pady=(0, 8), fill="x")

        if not self.mode_edition:
            self.after(200, lambda: self.entree_code.focus_set())

    def _set_date_rapide(self, delta_jours):
        nouvelle = (datetime.now() + timedelta(days=delta_jours)).strftime("%Y-%m-%d")
        self.entree_date.delete(0, "end")
        self.entree_date.insert(0, nouvelle)

    def _pre_remplir_edition(self):
        p = self.paiement_existant

        if self.type_ == "eleve":
            code = p.get("matricule", "")
            self.personne = rechercher_eleve_par_matricule(code)
        else:
            code = p.get("code", "")
            self.personne = rechercher_personnel_par_code(code)

        if not self.personne:
            messagebox.showerror("Erreur", "Personne introuvable.")
            self.destroy()
            return

        self.entree_code.configure(state="normal")
        self.entree_code.delete(0, "end")
        self.entree_code.insert(0, code)
        self.entree_code.configure(state="disabled")

        self.label_message.configure(text="", text_color="#999999")
        self.frame_fiche.pack(padx=10, pady=(6, 8), fill="x")

        if self.type_ == "eleve":
            frais = self.personne.get("frais_scolarite", 0) or 0
            solde = self.personne.get("solde", 0) or 0
            paye = frais - solde
            info = (
                f"{self.personne['nom']} {self.personne['prenom']}\n"
                f"Classe : {self.personne['classe']}\n"
                f"Frais totaux : {format_montant(frais)}\n"
                f"Deja paye : {format_montant(paye)}\n"
                f"Solde restant : {format_montant(solde)}"
            )
            self.frame_dettes.pack_forget()
        else:
            salaire = self.personne.get("salaire_mensuel", 0) or 0
            duree = self.personne.get("duree_contrat_mois", 12) or 12
            engagement = self.personne.get("engagement_total", salaire * duree) or 0
            paye = self.personne.get("total_paye", 0) or 0
            solde = self.personne.get("solde_a_payer", 0) or 0
            info = (
                f"{self.personne['nom']} {self.personne['prenom']}\n"
                f"Fonction : {self.personne['fonction']}\n"
                f"Salaire mensuel : {format_montant(salaire)}  x  {duree} mois\n"
                f"Engagement total : {format_montant(engagement)}\n"
                f"Deja paye : {format_montant(paye)}\n"
                f"Reste a payer : {format_montant(solde)}"
            )

        self.label_fiche.configure(text=info)

        self.entree_montant.delete(0, "end")
        self.entree_montant.insert(0, str(int(p.get("montant", 0))))

        date_p = p.get("date_paiement", "")[:10]
        self.entree_date.delete(0, "end")
        self.entree_date.insert(0, date_p)

        motif = p.get("motif", "")
        if "(Dettes:" in motif:
            motif = motif.split("(Dettes:")[0].strip()
        values = list(self.combo_motif.cget("values"))
        if motif and motif not in values:
            values.append(motif)
            self.combo_motif.configure(values=values)
        self.combo_motif.set(motif if motif else (values[0] if values else ""))

        mode = p.get("mode_paiement", "")
        mode_values = list(self.combo_mode.cget("values"))
        if mode and mode not in mode_values:
            mode_values.append(mode)
            self.combo_mode.configure(values=mode_values)
        self.combo_mode.set(mode if mode else "Especes")

    def _rechercher(self):
        code = self.entree_code.get().strip()

        if not code:
            self.label_message.configure(
                text="Veuillez saisir un matricule/code.",
                text_color="#e74c3c",
            )
            return

        if self.type_ == "eleve":
            self.personne = rechercher_eleve_par_matricule(code)
        else:
            self.personne = rechercher_personnel_par_code(code)

        if not self.personne:
            self.frame_fiche.pack_forget()
            if hasattr(self, "frame_dettes"):
                self.frame_dettes.pack_forget()
            type_label = "eleve" if self.type_ == "eleve" else "personnel"
            self.label_message.configure(
                text=f"Aucun {type_label} trouve avec le code : {code}",
                text_color="#e74c3c",
            )
            return

        self.label_message.configure(text="", text_color="#999999")
        self.frame_fiche.pack(padx=10, pady=(6, 8), fill="x")

        if self.type_ == "eleve":
            frais = self.personne.get("frais_scolarite", 0) or 0
            solde = self.personne.get("solde", 0) or 0
            paye = frais - solde

            info = (
                f"{self.personne['nom']} {self.personne['prenom']}\n"
                f"Classe : {self.personne['classe']}\n"
                f"Frais totaux : {format_montant(frais)}\n"
                f"Deja paye : {format_montant(paye)}\n"
                f"Solde restant : {format_montant(solde)}"
            )

            self._charger_dettes_eleve()

        else:
            salaire = self.personne.get("salaire_mensuel", 0) or 0
            duree = self.personne.get("duree_contrat_mois", 12) or 12
            engagement = self.personne.get("engagement_total", salaire * duree) or 0
            paye = self.personne.get("total_paye", 0) or 0
            solde = self.personne.get("solde_a_payer", 0) or 0

            info = (
                f"{self.personne['nom']} {self.personne['prenom']}\n"
                f"Fonction : {self.personne['fonction']}\n"
                f"Salaire mensuel : {format_montant(salaire)}  x  {duree} mois\n"
                f"Engagement total : {format_montant(engagement)}\n"
                f"Deja paye : {format_montant(paye)}\n"
                f"Reste a payer : {format_montant(solde)}"
            )

            self._maj_avance_disponible()

        self.label_fiche.configure(text=info)

    def _charger_dettes_eleve(self):
        try:
            self.dettes_eleve = dettes_en_cours_eleve(self.personne["id"])
        except Exception:
            self.dettes_eleve = []

        for w in self.frame_dettes.winfo_children():
            w.destroy()

        if not self.dettes_eleve:
            self.frame_dettes.pack_forget()
            return

        total = sum(d.get("solde", 0) for d in self.dettes_eleve)
        lignes = "\n".join(
            f"  - {d['categorie']} ({d['annee_libelle']}) : "
            f"{format_montant(d['solde'])}"
            for d in self.dettes_eleve
        )
        texte = (
            f"ATTENTION - DETTES EN COURS\n\n"
            f"Total dettes : {format_montant(total)}\n\n"
            f"{lignes}"
        )

        ctk.CTkLabel(
            self.frame_dettes,
            text=texte,
            font=("Segoe UI", 11, "bold"),
            text_color="#8B6914",
            justify="left",
            wraplength=460,
        ).pack(padx=15, pady=(12, 6), anchor="w")

        ctk.CTkLabel(
            self.frame_dettes,
            text="Affecter ce paiement aux dettes ?",
            font=("Segoe UI", 11, "bold"),
            text_color="#333333",
            anchor="w",
        ).pack(padx=15, pady=(6, 4), anchor="w")

        self.var_affecter_dettes = ctk.StringVar(value="oui")

        ligne_radio = ctk.CTkFrame(self.frame_dettes, fg_color="transparent")
        ligne_radio.pack(padx=15, pady=(0, 12), anchor="w")

        ctk.CTkRadioButton(
            ligne_radio,
            text="OUI - Affecter aux dettes d'abord",
            variable=self.var_affecter_dettes,
            value="oui",
            font=("Segoe UI", 11, "bold"),
            text_color="#27ae60",
            fg_color="#27ae60",
            hover_color="#229954",
        ).pack(side="left", padx=(0, 20))

        ctk.CTkRadioButton(
            ligne_radio,
            text="NON - Paiement normal (scolarite)",
            variable=self.var_affecter_dettes,
            value="non",
            font=("Segoe UI", 11, "bold"),
            text_color="#e74c3c",
            fg_color="#e74c3c",
            hover_color="#c0392b",
        ).pack(side="left")

        self.frame_dettes.pack(padx=10, pady=(6, 8), fill="x")

    def _maj_avance_disponible(self):
        if self.type_ != "personnel" or not hasattr(self, "frame_avance"):
            return

        try:
            self.avance_disponible = total_avance_en_cours(self.personne["id"])
        except Exception:
            self.avance_disponible = 0

        if self.avance_disponible > 0.01 and not self.mode_edition:
            self.frame_avance.pack(padx=10, pady=(5, 5), fill="x")
            self.label_avance_info.configure(
                text=f"Avance en cours : {format_montant(self.avance_disponible)}\n\n"
                     f"Si coche : le salaire sera paye en entier dans la comptabilite, "
                     f"mais l'avance sera deduite du net verse a l'employe."
            )
            self.var_deduire_avance.set(True)
        else:
            self.frame_avance.pack_forget()
            self.var_deduire_avance.set(False)

    def _on_check_avance(self):
        pass

    def _ajouter_montant(self, montant):
        actuel = self.entree_montant.get().strip()
        try:
            valeur = float(actuel) if actuel else 0
        except ValueError:
            valeur = 0
        self.entree_montant.delete(0, "end")
        self.entree_montant.insert(0, str(int(valeur + montant)))

    def _payer_solde_total(self):
        if not self.personne:
            messagebox.showinfo("Info", "Recherchez d'abord une personne.")
            return

        if self.type_ == "eleve":
            solde = self.personne.get("solde", 0) or 0
            if self.dettes_eleve:
                total_dettes = sum(d.get("solde", 0) for d in self.dettes_eleve)
                solde = solde + total_dettes
        else:
            solde = self.personne.get("salaire_mensuel", 0) or 0

        if solde <= 0:
            messagebox.showinfo("Info", "Aucun solde a payer.")
            return

        self.entree_montant.delete(0, "end")
        self.entree_montant.insert(0, str(int(solde)))

    def _enregistrer(self):
        if not self.personne:
            messagebox.showerror("Erreur",
                                 "Veuillez d'abord rechercher la personne par matricule/code.")
            return

        montant_str = self.entree_montant.get().strip().replace(" ", "").replace(",", "")
        try:
            montant = float(montant_str) if montant_str else 0
        except ValueError:
            messagebox.showerror("Erreur", "Montant invalide.")
            return

        if montant <= 0:
            messagebox.showerror("Erreur", "Le montant doit etre superieur a 0.")
            return

        date_op = self.entree_date.get().strip()
        if not date_op:
            messagebox.showerror(
                "Erreur",
                "Vous devez TAPER la date de l'operation.\n\n"
                "Format : AAAA-MM-JJ (ex: 2025-09-24)\n\n"
                "Ou utilisez les boutons rapides : Aujourd'hui / Hier / Demain."
            )
            return
        try:
            datetime.strptime(date_op, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror(
                "Erreur",
                f"Date invalide : '{date_op}'\n\n"
                "Format attendu : AAAA-MM-JJ (ex: 2025-09-24)"
            )
            return

        motif = self.combo_motif.get().strip()
        mode = self.combo_mode.get().strip()
        user_id = self.utilisateur["id"] if self.utilisateur else None

        if self.mode_edition:
            pid = self.paiement_existant["id"]
            if self.type_ == "eleve":
                ok, msg = modifier_paiement_eleve(
                    pid, montant=montant, motif=motif,
                    mode_paiement=mode, date_operation=date_op,
                )
            else:
                ok, msg = modifier_paiement_personnel(
                    pid, montant=montant, motif=motif,
                    mode_paiement=mode, date_operation=date_op,
                )

            if not ok:
                messagebox.showerror("Erreur", msg)
                return

            messagebox.showinfo("Modification", msg)
            if self.on_save:
                self.on_save()
            self.destroy()
            return

        if self.type_ == "eleve":
            affecter = True
            if self.dettes_eleve and hasattr(self, "var_affecter_dettes"):
                affecter = (self.var_affecter_dettes.get() == "oui")

            resultat = ajouter_paiement_eleve(
                self.personne["id"], montant, motif, mode, user_id,
                affecter_dettes=affecter,
                date_operation=date_op,
            )
            if len(resultat) == 4:
                ok, msg, numero, details = resultat
            else:
                ok, msg, numero = resultat
                details = []

            if not ok:
                messagebox.showerror("Erreur", msg)
                return

            paiement_info = {
                "numero_recu": numero,
                "date_paiement": date_op + " " + datetime.now().strftime("%H:%M"),
                "montant": montant,
                "motif": motif,
                "mode_paiement": mode,
                "matricule": self.personne["matricule"],
                "nom": self.personne["nom"],
                "prenom": self.personne["prenom"],
                "classe": self.personne["classe"],
            }

            message = (
                f"Numero : {numero}\n\n"
                f"Eleve : {self.personne['nom']} {self.personne['prenom']}\n"
                f"Montant : {format_montant(montant)}\n"
                f"Date : {date_op}\n"
                f"Motif : {motif}\n"
            )

            if details:
                message += "\n\nAFFECTATION AUTOMATIQUE AUX DETTES :\n"
                for d in details:
                    message += (
                        f"  - {d['categorie']} : {format_montant(d['montant'])} "
                        f"(reste {format_montant(d['nouveau_solde'])})\n"
                    )
            elif affecter is False and self.dettes_eleve:
                message += "\n\n(NON affecte aux dettes - paiement normal)"

            message += "\nVoulez-vous IMPRIMER le recu ?"

            rep = messagebox.askyesno("Paiement enregistre", message)

            if rep:
                try:
                    chemin = generer_recu_eleve(paiement_info)
                    PdfViewerWindow(self.master, chemin,
                                    titre=f"Recu {numero}")
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    messagebox.showerror("Erreur",
                                         f"Impossible de generer le recu :\n{e}")

            if self.on_save:
                self.on_save()
            self.destroy()
            return

        montant_avance_a_deduire = 0

        if hasattr(self, "var_deduire_avance") and self.var_deduire_avance.get():
            montant_avance_a_deduire = min(self.avance_disponible, montant)

        ok, msg, numero = ajouter_paiement_personnel(
            self.personne["id"], montant, motif, mode, user_id,
            montant_avance_deduit=montant_avance_a_deduire,
            date_operation=date_op,
        )

        if not ok:
            messagebox.showerror("Erreur", msg)
            return

        if montant_avance_a_deduire > 0:
            try:
                deduire_avances_personnel(
                    self.personne["id"], montant_avance_a_deduire
                )
            except Exception as e:
                print(f"[Erreur deduction avance] {e}")

        net_a_remettre = montant - montant_avance_a_deduire

        if montant_avance_a_deduire > 0:
            details = (
                f"Numero : {numero}\n\n"
                f"Personne : {self.personne['nom']} {self.personne['prenom']}\n"
                f"Salaire total : {format_montant(montant)}\n"
                f"Avance deduite : {format_montant(montant_avance_a_deduire)}\n"
                f"A REMETTRE EN ESPECES : {format_montant(net_a_remettre)}\n"
                f"Date : {date_op}\n\n"
                f"Motif : {motif}"
            )
        else:
            details = (
                f"Numero : {numero}\n\n"
                f"Personne : {self.personne['nom']} {self.personne['prenom']}\n"
                f"Montant : {format_montant(montant)}\n"
                f"Date : {date_op}\n"
                f"Motif : {motif}"
            )

        rep = messagebox.askyesno(
            "Paiement enregistre",
            details + "\n\nVoulez-vous IMPRIMER le bulletin de paie ?"
        )

        if rep:
            paiement_info = {
                "numero_paie": numero,
                "date_paiement": date_op + " " + datetime.now().strftime("%H:%M"),
                "montant": montant,
                "montant_avance_deduit": montant_avance_a_deduire,
                "motif": motif,
                "mode_paiement": mode,
                "code": self.personne["code"],
                "nom": self.personne["nom"],
                "prenom": self.personne["prenom"],
                "fonction": self.personne["fonction"],
            }
            try:
                chemin = generer_recu_personnel(paiement_info)
                PdfViewerWindow(self.master, chemin,
                                titre=f"Bulletin paie {numero}")
            except Exception as e:
                import traceback
                traceback.print_exc()
                messagebox.showerror("Erreur",
                                     f"Impossible de generer le bulletin :\n{e}")

        if self.on_save:
            self.on_save()
        self.destroy()