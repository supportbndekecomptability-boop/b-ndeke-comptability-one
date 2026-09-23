"""
Interface de gestion des eleves
Avec separation frais scolaires / autres frais
"""
import customtkinter as ctk
from tkinter import messagebox
from config import COLOR_NAVY, COLOR_GOLD, format_montant, CURRENCY_SYMBOL
from core.eleves import (
    ajouter_eleve, lister_eleves, modifier_eleve,
    supprimer_eleve, get_eleve, generer_matricule
)
from ui.scroll_frame import HorizontalScrollFrame


class ElevesPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.eleve_selectionne = None
        self._construire_interface()
        self.rafraichir_tableau()

    # ================== INTERFACE ==================
    def _construire_interface(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            top,
            text="Gestion des eleves",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        ctk.CTkButton(
            top,
            text="+ Nouvel eleve",
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_NAVY,
            hover_color="#1a3d75",
            height=40,
            command=self._ouvrir_formulaire,
        ).pack(side="right")

        # Barre de recherche
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
            placeholder_text="Nom, matricule ou classe...",
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
            text="Astuce : le SOLDE ne compte que les FRAIS SCOLAIRES  |  "
                 "Les autres frais (Uniforme, Transport...) sont separes  |  "
                 "Shift + molette pour defiler",
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
        self.tableau = HorizontalScrollFrame(self, fg_color="white",
                                             corner_radius=10)
        self.tableau.pack(fill="both", expand=True)

        self.tableau_frame = self.tableau.interior
        self._creer_entete()

    def _creer_entete(self):
        entete = ctk.CTkFrame(self.tableau_frame, fg_color="#f0f0f0",
                              corner_radius=6)
        entete.pack(fill="x", pady=(0, 5))

        colonnes = [
            ("Matricule", 115),
            ("Nom", 100),
            ("Prenom", 100),
            ("Classe", 90),
            ("Frais scol.", 95),
            ("Paye scol.", 95),
            ("Solde", 90),
            ("Uniforme", 85),
            ("Transport", 85),
            ("Cantine", 80),
            ("Inscript.", 85),
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
            width=80,
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
        eleves = lister_eleves(recherche)

        self.label_compteur.configure(text=f"{len(eleves)} eleve(s) trouve(s)")

        if not eleves:
            ctk.CTkLabel(
                self.tableau_frame,
                text="Aucun eleve enregistre. Cliquez sur '+ Nouvel eleve'.",
                font=("Segoe UI", 13),
                text_color="#999999",
            ).pack(pady=40)
            return

        for i, eleve in enumerate(eleves):
            couleur_fond = "#ffffff" if i % 2 == 0 else "#fafafa"
            ligne = ctk.CTkFrame(self.tableau_frame, fg_color=couleur_fond,
                                 corner_radius=4)
            ligne.pack(fill="x", pady=1)

            frais = eleve.get("frais_scolarite", 0) or 0
            paye_sc = eleve.get("paye_scolaire", 0) or 0
            solde = eleve.get("solde", 0) or 0
            paye_uni = eleve.get("paye_uniforme", 0) or 0
            paye_tra = eleve.get("paye_transport", 0) or 0
            paye_can = eleve.get("paye_cantine", 0) or 0
            paye_ins = eleve.get("paye_inscription", 0) or 0

            couleur_solde = "#e74c3c" if solde > 0 else "#27ae60"

            # Matricule cliquable
            label_matricule = ctk.CTkLabel(
                ligne,
                text=eleve["matricule"],
                font=("Segoe UI", 11, "bold", "underline"),
                text_color="#0066CC",
                width=115,
                anchor="w",
                cursor="hand2",
            )
            label_matricule.pack(side="left", padx=4, pady=8)
            label_matricule.bind(
                "<Button-1>",
                lambda e, m=eleve["matricule"], lbl=label_matricule:
                    self._copier_matricule(m, lbl)
            )

            # Autres colonnes
            autres = [
                (eleve["nom"], 100, "#333333", "normal"),
                (eleve["prenom"], 100, "#333333", "normal"),
                (eleve["classe"], 90, "#333333", "normal"),
                # ===== FRAIS SCOLAIRES (colore en bleu marine) =====
                (format_montant(frais), 95, "#0F2C5C", "bold"),
                (format_montant(paye_sc), 95, "#27ae60", "bold"),
                (format_montant(solde), 90, couleur_solde, "bold"),
                # ===== AUTRES FRAIS (colore en orange) =====
                (format_montant(paye_uni) if paye_uni > 0 else "-",
                 85, "#e67e22", "normal"),
                (format_montant(paye_tra) if paye_tra > 0 else "-",
                 85, "#e67e22", "normal"),
                (format_montant(paye_can) if paye_can > 0 else "-",
                 80, "#e67e22", "normal"),
                (format_montant(paye_ins) if paye_ins > 0 else "-",
                 85, "#e67e22", "normal"),
            ]

            for valeur, largeur, couleur, poids in autres:
                ctk.CTkLabel(
                    ligne,
                    text=str(valeur),
                    font=("Segoe UI", 11, poids),
                    text_color=couleur,
                    width=largeur,
                    anchor="w",
                ).pack(side="left", padx=4, pady=8)

            # Actions
            actions = ctk.CTkFrame(ligne, fg_color="transparent", width=80)
            actions.pack(side="left", padx=4)

            ctk.CTkButton(
                actions,
                text="M",
                font=("Segoe UI", 11, "bold"),
                width=32,
                height=26,
                fg_color="#3498db",
                hover_color="#2980b9",
                command=lambda e=eleve: self._modifier_eleve(e),
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                actions,
                text="X",
                font=("Segoe UI", 11, "bold"),
                width=32,
                height=26,
                fg_color="#e74c3c",
                hover_color="#c0392b",
                command=lambda e=eleve: self._supprimer_eleve(e),
            ).pack(side="left", padx=2)

    def _copier_matricule(self, matricule, label_widget):
        try:
            self.clipboard_clear()
            self.clipboard_append(matricule)
            self.update()
            label_widget.configure(text="Copie !", text_color="#27ae60")
            self.after(
                800,
                lambda: label_widget.configure(
                    text=matricule, text_color="#0066CC"
                )
            )
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de copier : {e}")

    # ================== ACTIONS ==================
    def _ouvrir_formulaire(self, eleve=None):
        FormulaireEleve(self, eleve=eleve, on_save=self.rafraichir_tableau)

    def _modifier_eleve(self, eleve):
        eleve_complet = get_eleve(eleve["id"])
        self._ouvrir_formulaire(eleve_complet)

    def _supprimer_eleve(self, eleve):
        reponse = messagebox.askyesno(
            "Confirmation",
            f"Voulez-vous vraiment supprimer l'eleve :\n\n"
            f"{eleve['nom']} {eleve['prenom']} ({eleve['matricule']}) ?"
        )
        if reponse:
            ok, msg = supprimer_eleve(eleve["id"])
            if ok:
                self.rafraichir_tableau()
            else:
                messagebox.showerror("Erreur", msg)


# ============================================================
# FORMULAIRE D'AJOUT / MODIFICATION
# ============================================================
class FormulaireEleve(ctk.CTkToplevel):
    def __init__(self, parent, eleve=None, on_save=None):
        super().__init__(parent)

        self.eleve = eleve
        self.on_save = on_save
        self.mode = "modification" if eleve else "ajout"

        titre = "Modifier un eleve" if eleve else "Nouvel eleve"
        self.title(titre)

        largeur = 520
        hauteur = 620
        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        x = (self.winfo_screenwidth() // 2) - (largeur // 2)
        y = 30
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

        titre = "Modifier un eleve" if self.eleve else "Nouvel eleve"
        ctk.CTkLabel(
            ligne_titre,
            text=titre,
            font=("Segoe UI", 18, "bold"),
            text_color=COLOR_NAVY,
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

        zone_scroll = ctk.CTkScrollableFrame(card, fg_color="transparent",
                                             corner_radius=0)
        zone_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        self.champs = {}

        self.champs["matricule"] = self._ajouter_champ(
            zone_scroll, "Matricule *",
            valeur=self.eleve["matricule"] if self.eleve else generer_matricule()
        )

        self.champs["nom"] = self._ajouter_champ(
            zone_scroll, "Nom *",
            valeur=self.eleve["nom"] if self.eleve else ""
        )

        self.champs["prenom"] = self._ajouter_champ(
            zone_scroll, "Prenom *",
            valeur=self.eleve["prenom"] if self.eleve else ""
        )

        # Classe editable
        ctk.CTkLabel(
            zone_scroll, text="Classe * (tapez librement)",
            font=("Segoe UI", 12, "bold"), text_color="#333333", anchor="w"
        ).pack(padx=10, pady=(8, 4), fill="x")

        valeur_classe = self.eleve["classe"] if self.eleve else "1ere Primaire"

        self.champs["classe"] = ctk.CTkEntry(
            zone_scroll,
            font=("Segoe UI", 13),
            height=36,
            placeholder_text="Ex: 1ere Primaire, CE1, Terminale A...",
        )
        self.champs["classe"].insert(0, valeur_classe)
        self.champs["classe"].pack(padx=10, pady=(0, 4), fill="x")

        ctk.CTkLabel(
            zone_scroll, text="Suggestions rapides :",
            font=("Segoe UI", 10), text_color="#888888", anchor="w"
        ).pack(padx=10, pady=(2, 2), fill="x")

        ligne_suggestions = ctk.CTkFrame(zone_scroll, fg_color="transparent")
        ligne_suggestions.pack(padx=10, pady=(0, 6), fill="x")

        for classe_rapide in ["Maternelle 1", "1ere Primaire",
                              "1ere Secondaire", "1ere Universite"]:
            ctk.CTkButton(
                ligne_suggestions,
                text=classe_rapide,
                font=("Segoe UI", 10),
                fg_color="#e0e0e0",
                text_color="#333333",
                hover_color="#c0c0c0",
                height=26,
                command=lambda c=classe_rapide: self._set_classe(c),
            ).pack(side="left", padx=(0, 4))

        # Sexe
        ctk.CTkLabel(
            zone_scroll, text="Sexe",
            font=("Segoe UI", 12, "bold"), text_color="#333333", anchor="w"
        ).pack(padx=10, pady=(8, 4), fill="x")

        self.champs["sexe"] = ctk.CTkComboBox(
            zone_scroll,
            values=["Masculin", "Feminin"],
            font=("Segoe UI", 13),
            height=36,
        )
        self.champs["sexe"].set(self.eleve["sexe"]
                                if self.eleve and self.eleve["sexe"]
                                else "Masculin")
        self.champs["sexe"].pack(padx=10, pady=(0, 6), fill="x")

        self.champs["nom_parent"] = self._ajouter_champ(
            zone_scroll, "Nom du parent / tuteur",
            valeur=self.eleve["nom_parent"]
            if self.eleve and self.eleve["nom_parent"] else ""
        )

        self.champs["telephone_parent"] = self._ajouter_champ(
            zone_scroll, "Telephone du parent",
            valeur=self.eleve["telephone_parent"]
            if self.eleve and self.eleve["telephone_parent"] else ""
        )

        # Frais de scolarite
        valeur_frais = ""
        if self.eleve and self.eleve.get("frais_scolarite"):
            valeur_frais = str(int(self.eleve["frais_scolarite"]))

        self.champs["frais_scolarite"] = self._ajouter_champ(
            zone_scroll, f"Frais de scolarite annuels ({CURRENCY_SYMBOL})",
            valeur=valeur_frais
        )

        # Boutons
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
            fg_color=COLOR_NAVY,
            hover_color="#1a3d75",
            height=42,
            command=self._enregistrer,
        ).pack(side="left", expand=True, fill="x", padx=(5, 0))

    def _set_classe(self, valeur):
        self.champs["classe"].delete(0, "end")
        self.champs["classe"].insert(0, valeur)

    def _ajouter_champ(self, parent, label, valeur=""):
        ctk.CTkLabel(
            parent, text=label,
            font=("Segoe UI", 12, "bold"), text_color="#333333", anchor="w"
        ).pack(padx=10, pady=(8, 4), fill="x")

        entree = ctk.CTkEntry(parent, font=("Segoe UI", 13), height=36)
        entree.insert(0, valeur)
        entree.pack(padx=10, pady=(0, 5), fill="x")
        return entree

    def _enregistrer(self):
        matricule = self.champs["matricule"].get().strip()
        nom = self.champs["nom"].get().strip()
        prenom = self.champs["prenom"].get().strip()
        classe = self.champs["classe"].get().strip()
        sexe = self.champs["sexe"].get().strip()
        nom_parent = self.champs["nom_parent"].get().strip() or None
        telephone_parent = self.champs["telephone_parent"].get().strip() or None

        frais_str = self.champs["frais_scolarite"].get().strip().replace(" ", "").replace(",", "")
        try:
            frais_scolarite = float(frais_str) if frais_str else 0
        except ValueError:
            messagebox.showerror("Erreur", "Le montant des frais doit etre un nombre.")
            return

        if not matricule or not nom or not prenom or not classe:
            messagebox.showerror("Champs obligatoires",
                                 "Veuillez remplir tous les champs marques d'un *.")
            return

        if self.eleve:
            ok, msg = modifier_eleve(
                self.eleve["id"], matricule, nom, prenom, classe,
                sexe, None, nom_parent, telephone_parent, frais_scolarite
            )
        else:
            ok, msg = ajouter_eleve(
                matricule, nom, prenom, classe,
                sexe, None, nom_parent, telephone_parent, frais_scolarite
            )

        if ok:
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Erreur", msg)