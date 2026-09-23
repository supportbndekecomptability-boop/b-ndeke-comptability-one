"""
Gestion des avances sur salaire - Fenetre modale
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from config import COLOR_NAVY, COLOR_GOLD, format_montant, CURRENCY_SYMBOL
from database import get_connection
from core.avances import (
    ajouter_avance, lister_avances, total_avance_en_cours,
    supprimer_avance, get_avance,
)


def modifier_avance(avance_id, montant, motif, date_avance):
    """Modifie une avance existante."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE avances_personnel
            SET montant = ?, motif = ?, date_avance = ?
            WHERE id = ?
        """, (float(montant), motif.strip(), date_avance, avance_id))
        conn.commit()
        return True, "Avance modifiee"
    except Exception as e:
        return False, f"Erreur : {str(e)}"
    finally:
        conn.close()


class AvancesWindow(ctk.CTkToplevel):
    """Fenetre de gestion des avances d'un employe"""

    def __init__(self, parent, personnel_id, personnel_nom, on_save=None):
        super().__init__(parent)

        self.personnel_id = personnel_id
        self.personnel_nom = personnel_nom
        self.on_save = on_save

        self.title(f"Avances - {personnel_nom}")
        largeur = 850
        hauteur = 620
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
        self.rafraichir()

    def _activer_grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _construire_interface(self):
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        # Titre
        ligne_titre = ctk.CTkFrame(card, fg_color="transparent")
        ligne_titre.pack(fill="x", padx=15, pady=(12, 5))

        ctk.CTkLabel(
            ligne_titre,
            text=f"Avances - {self.personnel_nom}",
            font=("Segoe UI", 16, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        ctk.CTkButton(
            ligne_titre, text="X",
            font=("Segoe UI", 14, "bold"),
            width=32, height=32,
            fg_color="#e74c3c", hover_color="#c0392b",
            command=self.destroy,
        ).pack(side="right")

        # Resume
        self.frame_resume = ctk.CTkFrame(card, fg_color="#FFF7E0", corner_radius=8)
        self.frame_resume.pack(fill="x", padx=15, pady=(5, 10))

        self.label_resume = ctk.CTkLabel(
            self.frame_resume,
            text="",
            font=("Segoe UI", 12, "bold"),
            text_color="#8B6914",
        )
        self.label_resume.pack(padx=15, pady=10, anchor="w")

        # Bouton nouvelle avance
        ligne_btn = ctk.CTkFrame(card, fg_color="transparent")
        ligne_btn.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkButton(
            ligne_btn,
            text="+ Nouvelle avance",
            font=("Segoe UI", 12, "bold"),
            fg_color=COLOR_NAVY,
            hover_color="#1a3d75",
            height=38,
            command=self._nouvelle_avance,
        ).pack(side="left")

        # Tableau
        self.tableau = ctk.CTkScrollableFrame(card, fg_color="white", corner_radius=10)
        self.tableau.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def rafraichir(self):
        for w in self.tableau.winfo_children():
            w.destroy()

        total = total_avance_en_cours(self.personnel_id)
        self.label_resume.configure(
            text=f"Total des avances en cours : {format_montant(total)}"
        )

        # Entete
        entete = ctk.CTkFrame(self.tableau, fg_color="#f0f0f0", corner_radius=6)
        entete.pack(fill="x", pady=(0, 5))

        for nom, larg in [
            ("Numero", 120),
            ("Date", 130),
            ("Motif", 180),
            ("Montant", 100),
            ("Deduit", 100),
            ("Reste", 100),
            ("Statut", 90),
        ]:
            ctk.CTkLabel(
                entete, text=nom,
                font=("Segoe UI", 11, "bold"),
                text_color=COLOR_NAVY,
                width=larg, anchor="w",
            ).pack(side="left", padx=3, pady=10)

        ctk.CTkLabel(
            entete, text="Action",
            font=("Segoe UI", 11, "bold"),
            text_color=COLOR_NAVY,
            width=110, anchor="center",
        ).pack(side="right", padx=3, pady=10)

        avances = lister_avances(self.personnel_id)

        if not avances:
            ctk.CTkLabel(
                self.tableau,
                text="Aucune avance pour cet employe.",
                font=("Segoe UI", 12),
                text_color="#999999",
            ).pack(pady=30)
            return

        for a in avances:
            fond = "#ffffff" if not a["en_cours"] else "#fafafa"
            ligne = ctk.CTkFrame(self.tableau, fg_color=fond, corner_radius=4)
            ligne.pack(fill="x", pady=1)

            try:
                date_str = a["date_avance"][:10]
            except Exception:
                date_str = ""

            if a["en_cours"]:
                statut = "En cours"
                coul_statut = "#e74c3c"
            else:
                statut = "Soldee"
                coul_statut = "#27ae60"

            valeurs = [
                (a["numero_avance"], 120, "#0066CC", "bold"),
                (date_str, 130, "#333333", "normal"),
                (a["motif"][:25] if a["motif"] else "-", 180, "#333333", "normal"),
                (format_montant(a["montant"]), 100, "#333333", "normal"),
                (format_montant(a["montant_deduit"]), 100, "#27ae60", "normal"),
                (format_montant(a["reste"]), 100, "#e74c3c", "bold"),
                (statut, 90, coul_statut, "bold"),
            ]

            for val, larg, coul, poids in valeurs:
                ctk.CTkLabel(
                    ligne, text=str(val),
                    font=("Segoe UI", 11, poids),
                    text_color=coul,
                    width=larg, anchor="w",
                ).pack(side="left", padx=3, pady=8)

            # Boutons M (Modifier) + X (Supprimer)
            act = ctk.CTkFrame(ligne, fg_color="transparent", width=110)
            act.pack(side="right", padx=3)

            ctk.CTkButton(
                act, text="M",
                font=("Segoe UI", 11, "bold"),
                width=36, height=26,
                fg_color="#3498db", hover_color="#2980b9",
                command=lambda av=a: self._modifier(av),
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                act, text="X",
                font=("Segoe UI", 11, "bold"),
                width=36, height=26,
                fg_color="#e74c3c", hover_color="#c0392b",
                command=lambda av=a: self._supprimer(av),
            ).pack(side="left", padx=2)

    def _nouvelle_avance(self):
        FormulaireAvance(self, self.personnel_id, self.personnel_nom,
                        on_save=self._on_avance_change)

    def _modifier(self, a):
        FormulaireAvance(
            self,
            self.personnel_id,
            self.personnel_nom,
            avance=a,
            on_save=self._on_avance_change,
        )

    def _on_avance_change(self):
        self.rafraichir()
        if self.on_save:
            self.on_save()

    def _supprimer(self, a):
        rep = messagebox.askyesno(
            "Confirmation",
            f"Supprimer l'avance {a['numero_avance']} ?\n\n"
            f"Montant : {format_montant(a['montant'])}\n"
            f"Deja deduit : {format_montant(a['montant_deduit'])}\n\n"
            f"Attention : cette action est irreversible."
        )
        if rep:
            ok, msg = supprimer_avance(a["id"])
            if ok:
                self._on_avance_change()
            else:
                messagebox.showerror("Erreur", msg)


# ============================================================
# FORMULAIRE AVANCE (nouvelle ou modification)
# ============================================================
class FormulaireAvance(ctk.CTkToplevel):
    def __init__(self, parent, personnel_id, personnel_nom,
                 avance=None, on_save=None):
        super().__init__(parent)

        self.personnel_id = personnel_id
        self.personnel_nom = personnel_nom
        self.avance = avance
        self.on_save = on_save
        self.mode_edition = avance is not None

        titre = "Modifier une avance" if self.mode_edition else "Nouvelle avance"
        self.title(titre)
        largeur = 500
        hauteur = 560 if self.mode_edition else 520
        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        x = (self.winfo_screenwidth() // 2) - (largeur // 2)
        y = max(30, (self.winfo_screenheight() // 2) - (hauteur // 2))
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

        titre = "Modifier l'avance" if self.mode_edition else "Nouvelle avance sur salaire"
        ctk.CTkLabel(
            ligne_titre,
            text=titre,
            font=("Segoe UI", 16, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        ctk.CTkButton(
            ligne_titre, text="X",
            font=("Segoe UI", 14, "bold"),
            width=32, height=32,
            fg_color="#e74c3c", hover_color="#c0392b",
            command=self.destroy,
        ).pack(side="right")

        # Info employe
        info = ctk.CTkFrame(card, fg_color="#F0F7FF", corner_radius=8)
        info.pack(fill="x", padx=15, pady=(5, 15))

        ctk.CTkLabel(
            info,
            text=f"Employe : {self.personnel_nom}",
            font=("Segoe UI", 12, "bold"),
            text_color=COLOR_NAVY,
        ).pack(padx=15, pady=10, anchor="w")

        # Avertissement si en cours et deja partiellement deduit
        if self.mode_edition and self.avance.get("montant_deduit", 0) > 0.01:
            avis = ctk.CTkFrame(card, fg_color="#FFF7E0", corner_radius=6)
            avis.pack(fill="x", padx=30, pady=(0, 10))
            ctk.CTkLabel(
                avis,
                text=(
                    f"ATTENTION : {format_montant(self.avance['montant_deduit'])} "
                    f"deja deduit sur cette avance.\n"
                    f"Le montant final ne peut pas etre inferieur a cette somme."
                ),
                font=("Segoe UI", 10, "bold"),
                text_color="#8B6914",
                justify="left",
            ).pack(padx=12, pady=8, anchor="w")

        # Montant
        ctk.CTkLabel(
            card, text=f"Montant de l'avance ({CURRENCY_SYMBOL}) *",
            font=("Segoe UI", 12, "bold"),
            text_color="#333333", anchor="w",
        ).pack(padx=30, pady=(5, 4), fill="x")

        self.entree_montant = ctk.CTkEntry(
            card,
            font=("Segoe UI", 14, "bold"),
            height=42,
            placeholder_text="0",
        )
        if self.mode_edition:
            self.entree_montant.insert(0, str(int(self.avance["montant"])))
        self.entree_montant.pack(padx=30, pady=(0, 6), fill="x")
        self.entree_montant.bind("<Return>", lambda e: self._enregistrer())

        # Boutons rapides (uniquement en creation)
        if not self.mode_edition:
            rapides = ctk.CTkFrame(card, fg_color="transparent")
            rapides.pack(padx=30, pady=(0, 10), fill="x")

            ctk.CTkLabel(rapides, text="Rapide :",
                         font=("Segoe UI", 10), text_color="#888888").pack(side="left", padx=(0, 4))

            for m in [20, 50, 100, 200]:
                ctk.CTkButton(
                    rapides, text=f"+{m}",
                    font=("Segoe UI", 10),
                    fg_color="#e0e0e0", text_color="#333333",
                    hover_color="#c0c0c0",
                    width=55, height=28,
                    command=lambda mm=m: self._ajouter_montant(mm),
                ).pack(side="left", padx=2)

        # Motif
        ctk.CTkLabel(
            card, text="Motif (optionnel)",
            font=("Segoe UI", 12, "bold"),
            text_color="#333333", anchor="w",
        ).pack(padx=30, pady=(8, 4), fill="x")

        self.entree_motif = ctk.CTkEntry(
            card,
            font=("Segoe UI", 12),
            height=38,
            placeholder_text="Ex: Avance sur salaire de septembre",
        )
        if self.mode_edition and self.avance.get("motif"):
            self.entree_motif.insert(0, self.avance["motif"])
        self.entree_motif.pack(padx=30, pady=(0, 10), fill="x")

        # Date (uniquement en modification)
        self.entree_date = None
        if self.mode_edition:
            ctk.CTkLabel(
                card, text="Date de l'avance (AAAA-MM-JJ)",
                font=("Segoe UI", 12, "bold"),
                text_color="#333333", anchor="w",
            ).pack(padx=30, pady=(5, 4), fill="x")

            self.entree_date = ctk.CTkEntry(
                card,
                font=("Segoe UI", 12),
                height=36,
                placeholder_text="AAAA-MM-JJ",
            )
            date_av = str(self.avance.get("date_avance", ""))[:10]
            self.entree_date.insert(0, date_av)
            self.entree_date.pack(padx=30, pady=(0, 15), fill="x")
        else:
            ctk.CTkLabel(card, text="").pack(pady=5)

        # Boutons
        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=30, pady=(5, 20))

        ctk.CTkButton(
            boutons, text="Annuler",
            font=("Segoe UI", 13),
            fg_color="#e74c3c", text_color="white",
            hover_color="#c0392b", height=42,
            command=self.destroy,
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        txt_enreg = "Enregistrer" if not self.mode_edition else "Modifier"
        ctk.CTkButton(
            boutons, text=txt_enreg,
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_NAVY, hover_color="#1a3d75",
            height=42, command=self._enregistrer,
        ).pack(side="left", expand=True, fill="x", padx=(5, 0))

        self.after(200, lambda: self.entree_montant.focus_set())

    def _ajouter_montant(self, m):
        actuel = self.entree_montant.get().strip()
        try:
            v = float(actuel) if actuel else 0
        except ValueError:
            v = 0
        self.entree_montant.delete(0, "end")
        self.entree_montant.insert(0, str(int(v + m)))

    def _enregistrer(self):
        montant_str = self.entree_montant.get().strip().replace(" ", "").replace(",", "")

        try:
            montant = float(montant_str) if montant_str else 0
        except ValueError:
            messagebox.showerror("Erreur", "Le montant doit etre un nombre.")
            return

        if montant <= 0:
            messagebox.showerror("Erreur", "Le montant doit etre superieur a 0.")
            return

        motif = self.entree_motif.get().strip() or "Avance sur salaire"

        # === MODE CREATION ===
        if not self.mode_edition:
            ok, msg, numero = ajouter_avance(self.personnel_id, montant, motif)
            if ok:
                messagebox.showinfo(
                    "Avance enregistree",
                    f"Numero : {numero}\n\n"
                    f"Montant : {format_montant(montant)}\n"
                    f"Employe : {self.personnel_nom}"
                )
                if self.on_save:
                    self.on_save()
                self.destroy()
            else:
                messagebox.showerror("Erreur", msg)
            return

        # === MODE EDITION ===
        # Verifier que le nouveau montant >= deja deduit
        deja_deduit = self.avance.get("montant_deduit", 0) or 0
        if montant < deja_deduit - 0.01:
            messagebox.showerror(
                "Erreur",
                f"Le montant ne peut pas etre inferieur a ce qui a deja "
                f"ete deduit ({format_montant(deja_deduit)})."
            )
            return

        # Date
        date_av = self.entree_date.get().strip()
        try:
            datetime.strptime(date_av, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror(
                "Erreur",
                "Date invalide. Format attendu : AAAA-MM-JJ\n"
                "Exemple : 2026-09-23"
            )
            return

        ok, msg = modifier_avance(self.avance["id"], montant, motif, date_av)
        if ok:
            messagebox.showinfo("Succes", "Avance modifiee.")
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Erreur", msg)