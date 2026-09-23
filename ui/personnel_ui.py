"""
Interface de gestion du personnel
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


class PersonnelPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self._construire_interface()
        self.rafraichir_tableau()

    # ================== INTERFACE ==================
    def _construire_interface(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            top,
            text="Gestion du personnel",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        ctk.CTkButton(
            top,
            text="+ Nouveau personnel",
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_NAVY,
            hover_color="#1a3d75",
            height=40,
            command=self._ouvrir_formulaire,
        ).pack(side="right")

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
            placeholder_text="Code, nom, prenom ou fonction...",
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

        # Astuce
        info_frame = ctk.CTkFrame(self, fg_color="#FFF7E0", corner_radius=6)
        info_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            info_frame,
            text="Astuce : cliquez sur un code (souligne) pour le copier  |  "
                 "Bouton A = Avances sur salaire  |  Shift + molette pour defiler",
            font=("Segoe UI", 11),
            text_color="#8B6914",
        ).pack(padx=15, pady=6, anchor="w")

        # Compteur
        self.label_compteur = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 12),
            text_color="#666666",
        )
        self.label_compteur.pack(anchor="w", pady=(0, 10))

        # Tableau avec scroll horizontal
        self.tableau = HorizontalScrollFrame(self, fg_color="white", corner_radius=10)
        self.tableau.pack(fill="both", expand=True)

        self._creer_entete()

    def _creer_entete(self):
        entete = ctk.CTkFrame(self.tableau.interior, fg_color="#f0f0f0", corner_radius=6)
        entete.pack(fill="x", pady=(0, 5))

        colonnes = [
            ("Code", 100),
            ("Nom", 110),
            ("Prenom", 110),
            ("Fonction", 130),
            ("Telephone", 130),
            ("Salaire/mois", 110),
            ("Mois", 55),
            ("Engagement", 110),
            ("Paye", 100),
            ("Reste a payer", 110),
            ("Avance", 100),
        ]

        for nom, largeur in colonnes:
            ctk.CTkLabel(
                entete,
                text=nom,
                font=("Segoe UI", 11, "bold"),
                text_color=COLOR_NAVY,
                width=largeur,
                anchor="w",
            ).pack(side="left", padx=4, pady=10)

        ctk.CTkLabel(
            entete,
            text="Actions",
            font=("Segoe UI", 11, "bold"),
            text_color=COLOR_NAVY,
            width=130,
            anchor="center",
        ).pack(side="left", padx=4, pady=10)

    def _effacer_recherche(self):
        self.entree_recherche.delete(0, "end")
        self.rafraichir_tableau()

    # ================== TABLEAU ==================
    def rafraichir_tableau(self):
        self.tableau.clear()
        self._creer_entete()

        recherche = self.entree_recherche.get()
        membres = lister_personnel(recherche)

        self.label_compteur.configure(text=f"{len(membres)} membre(s) du personnel")

        if not membres:
            ctk.CTkLabel(
                self.tableau.interior,
                text="Aucun personnel enregistre. Cliquez sur '+ Nouveau personnel'.",
                font=("Segoe UI", 13),
                text_color="#999999",
            ).pack(pady=40)
            return

        for i, p in enumerate(membres):
            couleur_fond = "#ffffff" if i % 2 == 0 else "#fafafa"
            ligne = ctk.CTkFrame(self.tableau.interior, fg_color=couleur_fond, corner_radius=4)
            ligne.pack(fill="x", pady=1)

            salaire = p.get("salaire_mensuel", 0) or 0
            duree = p.get("duree_contrat_mois", 12) or 12
            engagement = p.get("engagement_total", 0) or 0
            paye = p.get("total_paye", 0) or 0
            reste = p.get("solde_a_payer", 0) or 0

            # Avance en cours
            try:
                avance = total_avance_en_cours(p["id"])
            except Exception:
                avance = 0

            # Code cliquable
            label_code = ctk.CTkLabel(
                ligne,
                text=p["code"],
                font=("Segoe UI", 11, "bold", "underline"),
                text_color="#0066CC",
                width=100,
                anchor="w",
                cursor="hand2",
            )
            label_code.pack(side="left", padx=4, pady=10)
            label_code.bind(
                "<Button-1>",
                lambda e, c=p["code"], lbl=label_code: self._copier_code(c, lbl)
            )

            couleur_reste = "#e74c3c" if reste > 0 else "#27ae60"
            couleur_avance = "#e67e22" if avance > 0.01 else "#999999"

            valeurs = [
                (p["nom"], 110, "#333333", "normal"),
                (p["prenom"], 110, "#333333", "normal"),
                (p["fonction"], 130, "#333333", "normal"),
                (p["telephone"] or "-", 130, "#333333", "normal"),
                (format_montant(salaire), 110, "#333333", "normal"),
                (str(duree), 55, "#333333", "normal"),
                (format_montant(engagement), 110, "#8e44ad", "normal"),
                (format_montant(paye), 100, "#27ae60", "normal"),
                (format_montant(reste), 110, couleur_reste, "bold"),
                (format_montant(avance), 100, couleur_avance, "bold"),
            ]

            for valeur, largeur, couleur, poids in valeurs:
                ctk.CTkLabel(
                    ligne,
                    text=str(valeur),
                    font=("Segoe UI", 11, poids),
                    text_color=couleur,
                    width=largeur,
                    anchor="w",
                ).pack(side="left", padx=4, pady=10)

            # Actions (A = Avances, M = Modifier, X = Supprimer)
            actions = ctk.CTkFrame(ligne, fg_color="transparent", width=130)
            actions.pack(side="left", padx=4)

            ctk.CTkButton(
                actions, text="A",
                font=("Segoe UI", 11, "bold"),
                width=36, height=28,
                fg_color="#e67e22", hover_color="#d35400",
                command=lambda pp=p: self._ouvrir_avances(pp),
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                actions, text="M",
                font=("Segoe UI", 11, "bold"),
                width=36, height=28,
                fg_color="#3498db", hover_color="#2980b9",
                command=lambda pp=p: self._modifier(pp),
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                actions, text="X",
                font=("Segoe UI", 11, "bold"),
                width=36, height=28,
                fg_color="#e74c3c", hover_color="#c0392b",
                command=lambda pp=p: self._supprimer(pp),
            ).pack(side="left", padx=2)

    def _copier_code(self, code, label_widget):
        try:
            self.clipboard_clear()
            self.clipboard_append(code)
            self.update()
            label_widget.configure(text="Copie !", text_color="#27ae60")
            self.after(800, lambda: label_widget.configure(
                text=code, text_color="#0066CC"
            ))
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de copier : {e}")

    # ================== ACTIONS ==================
    def _ouvrir_formulaire(self, personne=None):
        FormulairePersonnel(self, personne=personne, on_save=self.rafraichir_tableau)

    def _modifier(self, p):
        complet = get_personnel(p["id"])
        self._ouvrir_formulaire(complet)

    def _ouvrir_avances(self, p):
        """Ouvre la fenetre de gestion des avances de cet employe"""
        AvancesWindow(
            self,
            p["id"],
            f"{p['nom']} {p['prenom']}",
            on_save=self.rafraichir_tableau,
        )

    def _supprimer(self, p):
        rep = messagebox.askyesno(
            "Confirmation",
            f"Voulez-vous vraiment supprimer :\n\n"
            f"{p['nom']} {p['prenom']}\n"
            f"Fonction : {p['fonction']}\n"
            f"Code : {p['code']} ?"
        )
        if rep:
            ok, msg = supprimer_personnel(p["id"])
            if ok:
                self.rafraichir_tableau()
            else:
                messagebox.showerror("Erreur", msg)


# ============================================================
# FORMULAIRE - Champs importants en HAUT
# ============================================================
class FormulairePersonnel(ctk.CTkToplevel):
    def __init__(self, parent, personne=None, on_save=None):
        super().__init__(parent)

        self.personne = personne
        self.on_save = on_save

        titre = "Modifier un personnel" if personne else "Nouveau personnel"
        self.title(titre)

        largeur = 540
        hauteur = 640
        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        x = (self.winfo_screenwidth() // 2) - (largeur // 2)
        y = 20
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
        ligne_titre.pack(fill="x", padx=15, pady=(10, 5))

        titre = "Modifier un personnel" if self.personne else "Nouveau personnel"
        ctk.CTkLabel(
            ligne_titre, text=titre,
            font=("Segoe UI", 17, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        ctk.CTkButton(
            ligne_titre, text="X",
            font=("Segoe UI", 14, "bold"),
            width=32, height=32,
            fg_color="#e74c3c", hover_color="#c0392b",
            command=self.destroy,
        ).pack(side="right")

        zone = ctk.CTkScrollableFrame(card, fg_color="transparent", corner_radius=0)
        zone.pack(fill="both", expand=True, padx=5, pady=5)

        self.champs = {}

        # ===== IDENTITE =====
        self.champs["code"] = self._ajouter_champ(
            zone, "Code *",
            valeur=self.personne["code"] if self.personne else generer_code()
        )

        self.champs["nom"] = self._ajouter_champ(
            zone, "Nom *",
            valeur=self.personne["nom"] if self.personne else ""
        )

        self.champs["prenom"] = self._ajouter_champ(
            zone, "Prenom *",
            valeur=self.personne["prenom"] if self.personne else ""
        )

        # Fonction
        ctk.CTkLabel(
            zone, text="Fonction * (tapez librement)",
            font=("Segoe UI", 12, "bold"), text_color="#333333", anchor="w"
        ).pack(padx=10, pady=(6, 4), fill="x")

        valeur_fonction = self.personne["fonction"] if self.personne else "Enseignant"

        self.champs["fonction"] = ctk.CTkEntry(
            zone, font=("Segoe UI", 13), height=36,
            placeholder_text="Ex: Enseignant, Directeur, Secretaire...",
        )
        self.champs["fonction"].insert(0, valeur_fonction)
        self.champs["fonction"].pack(padx=10, pady=(0, 4), fill="x")

        ligne_sugg = ctk.CTkFrame(zone, fg_color="transparent")
        ligne_sugg.pack(padx=10, pady=(0, 6), fill="x")

        for fonction_rapide in ["Enseignant", "Directeur", "Secretaire", "Comptable"]:
            ctk.CTkButton(
                ligne_sugg, text=fonction_rapide,
                font=("Segoe UI", 10),
                fg_color="#e0e0e0", text_color="#333333",
                hover_color="#c0c0c0", height=26,
                command=lambda f=fonction_rapide: self._set_fonction(f),
            ).pack(side="left", padx=(0, 4))

        # ===== SALAIRE ET DUREE =====
        separateur = ctk.CTkFrame(zone, fg_color="#e0e0e0", height=1)
        separateur.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            zone, text="SALAIRE ET ENGAGEMENT",
            font=("Segoe UI", 11, "bold"),
            text_color="#8e44ad",
            anchor="w"
        ).pack(padx=10, pady=(5, 8), fill="x")

        valeur_salaire = ""
        if self.personne and self.personne.get("salaire_mensuel"):
            valeur_salaire = str(int(self.personne["salaire_mensuel"]))

        self.champs["salaire_mensuel"] = self._ajouter_champ(
            zone, f"Salaire mensuel ({CURRENCY_SYMBOL}) *",
            valeur=valeur_salaire
        )

        # Duree
        valeur_duree = "12"
        if self.personne and self.personne.get("duree_contrat_mois"):
            valeur_duree = str(int(self.personne["duree_contrat_mois"]))

        ctk.CTkLabel(
            zone, text="Duree du contrat (nombre de mois) *",
            font=("Segoe UI", 12, "bold"), text_color="#333333", anchor="w"
        ).pack(padx=10, pady=(8, 4), fill="x")

        ligne_duree_input = ctk.CTkFrame(zone, fg_color="transparent")
        ligne_duree_input.pack(padx=10, pady=(0, 4), fill="x")

        self.champs["duree_contrat_mois"] = ctk.CTkEntry(
            ligne_duree_input,
            font=("Segoe UI", 13),
            height=36,
            width=100,
        )
        self.champs["duree_contrat_mois"].insert(0, valeur_duree)
        self.champs["duree_contrat_mois"].pack(side="left")
        self.champs["duree_contrat_mois"].bind("<KeyRelease>", lambda e: self._maj_apercu())

        ctk.CTkLabel(
            ligne_duree_input,
            text="mois",
            font=("Segoe UI", 13, "bold"),
            text_color="#666666",
        ).pack(side="left", padx=(8, 0))

        ligne_duree_sugg = ctk.CTkFrame(zone, fg_color="transparent")
        ligne_duree_sugg.pack(padx=10, pady=(4, 6), fill="x")

        ctk.CTkLabel(
            ligne_duree_sugg,
            text="Rapide :",
            font=("Segoe UI", 10),
            text_color="#888888",
        ).pack(side="left", padx=(0, 4))

        for duree_rapide in [3, 6, 9, 10, 12]:
            ctk.CTkButton(
                ligne_duree_sugg,
                text=f"{duree_rapide}",
                font=("Segoe UI", 10, "bold"),
                fg_color="#e0e0e0", text_color="#333333",
                hover_color="#c0c0c0", width=38, height=26,
                command=lambda d=duree_rapide: self._set_duree(d),
            ).pack(side="left", padx=(0, 4))

        self.label_apercu = ctk.CTkLabel(
            zone,
            text="Engagement total : --",
            font=("Segoe UI", 12, "bold"),
            text_color="#8e44ad",
            anchor="w",
        )
        self.label_apercu.pack(padx=10, pady=(6, 8), fill="x")

        self.champs["salaire_mensuel"].bind("<KeyRelease>", lambda e: self._maj_apercu())
        self._maj_apercu()

        # ===== AUTRES =====
        separateur2 = ctk.CTkFrame(zone, fg_color="#e0e0e0", height=1)
        separateur2.pack(fill="x", padx=10, pady=(5, 5))

        ctk.CTkLabel(
            zone, text="INFORMATIONS COMPLEMENTAIRES",
            font=("Segoe UI", 11, "bold"),
            text_color="#666666",
            anchor="w"
        ).pack(padx=10, pady=(5, 8), fill="x")

        ctk.CTkLabel(
            zone, text="Sexe",
            font=("Segoe UI", 12, "bold"), text_color="#333333", anchor="w"
        ).pack(padx=10, pady=(6, 4), fill="x")

        self.champs["sexe"] = ctk.CTkComboBox(
            zone, values=["Masculin", "Feminin"],
            font=("Segoe UI", 13), height=36,
        )
        self.champs["sexe"].set(self.personne["sexe"] if self.personne and self.personne["sexe"] else "Masculin")
        self.champs["sexe"].pack(padx=10, pady=(0, 6), fill="x")

        self.champs["telephone"] = self._ajouter_champ(
            zone, "Telephone",
            valeur=self.personne["telephone"] if self.personne and self.personne["telephone"] else ""
        )

        self.champs["email"] = self._ajouter_champ(
            zone, "Email",
            valeur=self.personne["email"] if self.personne and self.personne["email"] else ""
        )

        # ===== BOUTONS =====
        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=15, pady=(5, 12))

        ctk.CTkButton(
            boutons, text="Annuler (Echap)",
            font=("Segoe UI", 13, "bold"),
            fg_color="#e74c3c", text_color="white",
            hover_color="#c0392b", height=42,
            command=self.destroy,
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(
            boutons, text="Enregistrer",
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_NAVY, hover_color="#1a3d75",
            height=42, command=self._enregistrer,
        ).pack(side="left", expand=True, fill="x", padx=(5, 0))

    def _set_fonction(self, valeur):
        self.champs["fonction"].delete(0, "end")
        self.champs["fonction"].insert(0, valeur)

    def _set_duree(self, duree):
        self.champs["duree_contrat_mois"].delete(0, "end")
        self.champs["duree_contrat_mois"].insert(0, str(duree))
        self._maj_apercu()

    def _maj_apercu(self):
        try:
            salaire_str = self.champs["salaire_mensuel"].get().strip().replace(" ", "").replace(",", "")
            duree_str = self.champs["duree_contrat_mois"].get().strip()
            salaire = float(salaire_str) if salaire_str else 0
            duree = int(duree_str) if duree_str else 0
            total = salaire * duree
            self.label_apercu.configure(
                text=f"Engagement total : {format_montant(total)}   ({duree} mois x {format_montant(salaire)})"
            )
        except Exception:
            self.label_apercu.configure(text="Engagement total : --")

    def _ajouter_champ(self, parent, label, valeur=""):
        ctk.CTkLabel(
            parent, text=label,
            font=("Segoe UI", 12, "bold"), text_color="#333333", anchor="w"
        ).pack(padx=10, pady=(6, 4), fill="x")

        entree = ctk.CTkEntry(parent, font=("Segoe UI", 13), height=36)
        entree.insert(0, valeur)
        entree.pack(padx=10, pady=(0, 5), fill="x")
        return entree

    def _enregistrer(self):
        code = self.champs["code"].get().strip()
        nom = self.champs["nom"].get().strip()
        prenom = self.champs["prenom"].get().strip()
        fonction = self.champs["fonction"].get().strip()
        sexe = self.champs["sexe"].get().strip()
        telephone = self.champs["telephone"].get().strip() or None
        email = self.champs["email"].get().strip() or None

        salaire_str = self.champs["salaire_mensuel"].get().strip().replace(" ", "").replace(",", "")
        try:
            salaire = float(salaire_str) if salaire_str else 0
        except ValueError:
            messagebox.showerror("Erreur", "Le salaire doit etre un nombre.")
            return

        duree_str = self.champs["duree_contrat_mois"].get().strip()
        try:
            duree = int(duree_str) if duree_str else 12
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
                sexe, telephone, email, salaire, duree, None
            )
        else:
            ok, msg = ajouter_personnel(
                code, nom, prenom, fonction,
                sexe, telephone, email, salaire, duree, None
            )

        if ok:
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Erreur", msg)