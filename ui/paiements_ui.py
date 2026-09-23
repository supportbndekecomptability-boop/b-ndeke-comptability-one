"""
Interface Paiements (Eleves + Personnel) avec scroll horizontal
+ Impression par feuille de 6 recus
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from config import COLOR_NAVY, COLOR_GOLD, format_montant, CURRENCY_SYMBOL
from core.paiements import (
    ajouter_paiement_eleve, ajouter_paiement_personnel,
    lister_paiements_eleves, lister_paiements_personnel,
    supprimer_paiement_eleve, supprimer_paiement_personnel,
    rechercher_eleve_par_matricule, rechercher_personnel_par_code
)
from core.avances import total_avance_en_cours, deduire_avances_personnel
from services.recus_pdf import (
    generer_recu_eleve, generer_recu_personnel, generer_feuille_recus,
)
from ui.pdf_viewer import PdfViewerWindow
from ui.scroll_frame import HorizontalScrollFrame


class PaiementsPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")

        self.utilisateur = utilisateur
        self.type_actuel = "eleve"

        self._construire_interface()
        self.rafraichir_tableau()

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

        ctk.CTkButton(
            top,
            text="+ Nouveau paiement",
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_NAVY,
            hover_color="#1a3d75",
            height=40,
            command=self._ouvrir_formulaire,
        ).pack(side="right")

        ctk.CTkButton(
            top,
            text="Feuille 6 recus",
            font=("Segoe UI", 12, "bold"),
            fg_color="#27ae60",
            hover_color="#229954",
            height=40,
            command=self._imprimer_feuille_6,
        ).pack(side="right", padx=(0, 10))

        # Onglets
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

        # Recherche
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

        # Tableau avec scroll horizontal
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
    def _creer_entete(self):
        if self.entete_frame:
            self.entete_frame.destroy()

        self.entete_frame = ctk.CTkFrame(self.tableau_frame,
                                         fg_color="#f0f0f0", corner_radius=6)
        self.entete_frame.pack(fill="x", pady=(0, 5))

        if self.type_actuel == "eleve":
            colonnes = [
                ("N Recu", 105),
                ("Date", 130),
                ("Matricule", 95),
                ("Eleve", 145),
                ("Classe", 90),
                ("Motif", 120),
                ("Mode", 90),
                ("Montant", 100),
            ]
        else:
            colonnes = [
                ("N Paie", 100),
                ("Date", 130),
                ("Code", 95),
                ("Personnel", 135),
                ("Motif", 110),
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

        ctk.CTkLabel(
            self.entete_frame,
            text="Actions",
            font=("Segoe UI", 11, "bold"),
            text_color=COLOR_NAVY,
            width=130,
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
                num = p["numero_recu"]
                code = p["matricule"]
                nom_p = f"{p['nom']} {p['prenom']}"
                extra = p["classe"]
                couleur_num = "#0066CC"

                valeurs = [
                    (num, 105, couleur_num, "bold"),
                    (date_p, 130, "#333333", "normal"),
                    (code, 95, "#333333", "normal"),
                    (nom_p, 145, "#333333", "normal"),
                    (extra, 90, "#333333", "normal"),
                    (p["motif"], 120, "#333333", "normal"),
                    (p["mode_paiement"], 90, "#333333", "normal"),
                    (format_montant(p["montant"]), 100, "#27ae60", "bold"),
                ]
            else:
                num = p["numero_paie"]
                code = p["code"]
                nom_p = f"{p['nom']} {p['prenom']}"
                montant_total = p["montant"] or 0
                avance = p.get("montant_avance_deduit", 0) or 0
                net = montant_total - avance
                couleur_num = "#e67e22"

                valeurs = [
                    (num, 100, couleur_num, "bold"),
                    (date_p, 130, "#333333", "normal"),
                    (code, 95, "#333333", "normal"),
                    (nom_p, 135, "#333333", "normal"),
                    (p["motif"], 110, "#333333", "normal"),
                    (p["mode_paiement"], 90, "#333333", "normal"),
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

            # Actions
            actions = ctk.CTkFrame(ligne, fg_color="transparent", width=130)
            actions.pack(side="left", padx=4)

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
        FormulairePaiement(
            self,
            type_=self.type_actuel,
            utilisateur=self.utilisateur,
            on_save=self.rafraichir_tableau,
        )

    def _imprimer_feuille_6(self):
        """Imprime une feuille A4 avec jusqu'a 6 recus"""
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
        """Imprime le recu d'un paiement existant"""
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
# FORMULAIRE DE PAIEMENT (Eleve OU Personnel)
# ============================================================
class FormulairePaiement(ctk.CTkToplevel):
    def __init__(self, parent, type_="eleve", utilisateur=None, on_save=None):
        super().__init__(parent)

        self.type_ = type_
        self.utilisateur = utilisateur
        self.on_save = on_save
        self.personne = None
        self.avance_disponible = 0

        titre = "Paiement eleve" if type_ == "eleve" else "Paie personnel"
        self.title(f"Nouveau - {titre}")

        largeur = 540
        hauteur = 600
        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        x = (self.winfo_screenwidth() // 2) - (largeur // 2)
        y = max(10, (self.winfo_screenheight() // 2) - (hauteur // 2) - 30)
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

        # RECHERCHE
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

        ctk.CTkButton(
            ligne_recherche,
            text="Rechercher",
            font=("Segoe UI", 12, "bold"),
            fg_color=COLOR_NAVY,
            hover_color="#1a3d75",
            width=110,
            height=38,
            command=self._rechercher,
        ).pack(side="left")

        # FICHE
        self.frame_fiche = ctk.CTkFrame(zone, fg_color="#F0F7FF", corner_radius=8)

        self.label_fiche = ctk.CTkLabel(
            self.frame_fiche,
            text="",
            font=("Segoe UI", 12),
            text_color=COLOR_NAVY,
            justify="left",
        )
        self.label_fiche.pack(padx=15, pady=12, anchor="w")

        self.label_message = ctk.CTkLabel(
            zone,
            text="Saisissez le code puis cliquez sur Rechercher",
            font=("Segoe UI", 11),
            text_color="#999999",
        )
        self.label_message.pack(padx=10, pady=(4, 8))

        # FRAME AVANCE
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

        # MONTANT
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

        # MOTIF
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

        # MODE
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

        # BOUTONS
        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=15, pady=(5, 12))

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

        ctk.CTkButton(
            boutons,
            text="Enregistrer",
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_NAVY if self.type_ == "eleve" else "#e67e22",
            hover_color="#1a3d75" if self.type_ == "eleve" else "#d35400",
            height=42,
            command=self._enregistrer,
        ).pack(side="left", expand=True, fill="x", padx=(5, 0))

        self.after(200, lambda: self.entree_code.focus_set())

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

    def _maj_avance_disponible(self):
        if self.type_ != "personnel" or not hasattr(self, "frame_avance"):
            return

        try:
            self.avance_disponible = total_avance_en_cours(self.personne["id"])
        except Exception:
            self.avance_disponible = 0

        if self.avance_disponible > 0.01:
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
        else:
            solde = self.personne.get("salaire_mensuel", 0) or 0

        if solde <= 0:
            messagebox.showinfo("Info", "Aucun solde a payer.")
            return

        self.entree_montant.delete(0, "end")
        self.entree_montant.insert(0, str(int(solde)))

    # ================== ENREGISTREMENT ==================
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

        motif = self.combo_motif.get().strip()
        mode = self.combo_mode.get().strip()
        user_id = self.utilisateur["id"] if self.utilisateur else None

        # ===== CAS ELEVE =====
        if self.type_ == "eleve":
            ok, msg, numero = ajouter_paiement_eleve(
                self.personne["id"], montant, motif, mode, user_id
            )

            if not ok:
                messagebox.showerror("Erreur", msg)
                return

            paiement_info = {
                "numero_recu": numero,
                "date_paiement": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "montant": montant,
                "motif": motif,
                "mode_paiement": mode,
                "matricule": self.personne["matricule"],
                "nom": self.personne["nom"],
                "prenom": self.personne["prenom"],
                "classe": self.personne["classe"],
            }

            rep = messagebox.askyesno(
                "Paiement enregistre",
                f"Numero : {numero}\n\n"
                f"Eleve : {self.personne['nom']} {self.personne['prenom']}\n"
                f"Montant : {format_montant(montant)}\n"
                f"Motif : {motif}\n\n"
                f"Voulez-vous IMPRIMER le recu ?"
            )

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

        # ===== CAS PERSONNEL =====
        montant_avance_a_deduire = 0

        if hasattr(self, "var_deduire_avance") and self.var_deduire_avance.get():
            montant_avance_a_deduire = min(self.avance_disponible, montant)

        ok, msg, numero = ajouter_paiement_personnel(
            self.personne["id"], montant, motif, mode, user_id,
            montant_avance_deduit=montant_avance_a_deduire,
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
                f"A REMETTRE EN ESPECES : {format_montant(net_a_remettre)}\n\n"
                f"Motif : {motif}"
            )
        else:
            details = (
                f"Numero : {numero}\n\n"
                f"Personne : {self.personne['nom']} {self.personne['prenom']}\n"
                f"Montant : {format_montant(montant)}\n"
                f"Motif : {motif}"
            )

        rep = messagebox.askyesno(
            "Paiement enregistre",
            details + "\n\nVoulez-vous IMPRIMER le bulletin de paie ?"
        )

        if rep:
            paiement_info = {
                "numero_paie": numero,
                "date_paiement": datetime.now().strftime("%Y-%m-%d %H:%M"),
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