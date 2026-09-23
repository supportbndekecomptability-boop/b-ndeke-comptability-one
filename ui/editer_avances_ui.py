"""
Fenetre d'edition directe des avances d'un employe
Chaque ligne est editable (montant, motif, date)
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from config import COLOR_NAVY, format_montant, CURRENCY_SYMBOL
from core.avances import lister_avances
from database import get_connection


class EditerAvancesWindow(ctk.CTkToplevel):
    def __init__(self, parent, personnel_id, personnel_nom, on_save=None):
        super().__init__(parent)

        self.personnel_id = personnel_id
        self.personnel_nom = personnel_nom
        self.on_save = on_save
        self.lignes = {}

        self.title(f"Modifier les avances - {personnel_nom}")

        # Adapter a la taille de l'ecran
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        largeur = min(950, sw - 40)
        hauteur = min(600, sh - 100)

        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        x = (sw // 2) - (largeur // 2)
        y = max(10, (sh // 2) - (hauteur // 2) - 20)
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")

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

        # ===== TITRE =====
        ligne_titre = ctk.CTkFrame(card, fg_color="transparent")
        ligne_titre.pack(fill="x", padx=15, pady=(12, 5))

        ctk.CTkLabel(
            ligne_titre,
            text=f"Modifier les avances - {self.personnel_nom}",
            font=("Segoe UI", 15, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        ctk.CTkButton(
            ligne_titre, text="X",
            font=("Segoe UI", 13, "bold"),
            width=30, height=30,
            fg_color="#e74c3c", hover_color="#c0392b",
            command=self.destroy,
        ).pack(side="right")

        # ===== AVERTISSEMENT (compact) =====
        avis = ctk.CTkFrame(card, fg_color="#FFF7E0", corner_radius=6)
        avis.pack(fill="x", padx=15, pady=(2, 8))
        ctk.CTkLabel(
            avis,
            text=(
                "Modifiez directement les avances ci-dessous. "
                "Le montant ne peut pas etre inferieur a la somme deja deduite."
            ),
            font=("Segoe UI", 9),
            text_color="#8B6914",
            justify="left",
            wraplength=850,
        ).pack(padx=10, pady=6, anchor="w")

        # ===== ENTETE =====
        entete = ctk.CTkFrame(card, fg_color="#f0f0f0", corner_radius=6)
        entete.pack(fill="x", padx=15, pady=(0, 4))

        for nom, larg in [
            ("Numero", 115),
            ("Date (AAAA-MM-JJ)", 145),
            ("Motif", 240),
            (f"Montant ({CURRENCY_SYMBOL})", 130),
            ("Deja deduit", 115),
        ]:
            ctk.CTkLabel(
                entete, text=nom,
                font=("Segoe UI", 10, "bold"),
                text_color=COLOR_NAVY,
                width=larg, anchor="w",
            ).pack(side="left", padx=3, pady=8)

        # ===== TABLEAU =====
        self.tableau = ctk.CTkScrollableFrame(card, fg_color="white", corner_radius=10)
        self.tableau.pack(fill="both", expand=True, padx=15, pady=(0, 8))

        avances = lister_avances(self.personnel_id)

        if not avances:
            ctk.CTkLabel(
                self.tableau,
                text="Aucune avance pour cet employe.",
                font=("Segoe UI", 12),
                text_color="#999999",
            ).pack(pady=40)
        else:
            for a in avances:
                self._ajouter_ligne(a)

        # ===== BOUTONS =====
        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=15, pady=(5, 12))

        ctk.CTkButton(
            boutons, text="Annuler",
            font=("Segoe UI", 12),
            fg_color="#e74c3c", hover_color="#c0392b",
            height=38,
            command=self.destroy,
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(
            boutons, text="Sauvegarder les modifications",
            font=("Segoe UI", 12, "bold"),
            fg_color="#27ae60", hover_color="#229954",
            height=38,
            command=self._sauvegarder,
        ).pack(side="left", expand=True, fill="x", padx=(5, 0))

    def _ajouter_ligne(self, a):
        fond = "#fafafa" if a["en_cours"] else "#ffffff"
        ligne = ctk.CTkFrame(self.tableau, fg_color=fond, corner_radius=4)
        ligne.pack(fill="x", pady=2)

        ctk.CTkLabel(
            ligne, text=a["numero_avance"],
            font=("Segoe UI", 10, "bold"),
            text_color="#0066CC",
            width=115, anchor="w",
        ).pack(side="left", padx=3, pady=6)

        try:
            date_str = str(a["date_avance"])[:10]
        except Exception:
            date_str = ""

        e_date = ctk.CTkEntry(
            ligne,
            font=("Segoe UI", 10),
            height=30,
            width=145,
        )
        e_date.insert(0, date_str)
        e_date.pack(side="left", padx=3)

        e_motif = ctk.CTkEntry(
            ligne,
            font=("Segoe UI", 10),
            height=30,
            width=240,
        )
        e_motif.insert(0, a["motif"] or "")
        e_motif.pack(side="left", padx=3)

        e_montant = ctk.CTkEntry(
            ligne,
            font=("Segoe UI", 10, "bold"),
            height=30,
            width=130,
        )
        e_montant.insert(0, str(int(a["montant"])))
        e_montant.pack(side="left", padx=3)

        deja = a["montant_deduit"] or 0
        couleur_deja = "#27ae60" if deja > 0.01 else "#999999"

        ctk.CTkLabel(
            ligne, text=format_montant(deja),
            font=("Segoe UI", 10, "bold"),
            text_color=couleur_deja,
            width=115, anchor="w",
        ).pack(side="left", padx=3, pady=6)

        self.lignes[a["id"]] = {
            "montant": e_montant,
            "motif": e_motif,
            "date": e_date,
            "deja_deduit": deja,
            "numero": a["numero_avance"],
        }

    def _sauvegarder(self):
        modifications = []

        for avance_id, champs in self.lignes.items():
            try:
                montant_str = champs["montant"].get().strip().replace(" ", "").replace(",", "")
                montant = float(montant_str) if montant_str else 0
            except ValueError:
                messagebox.showerror(
                    "Erreur",
                    f"Montant invalide pour l'avance {champs['numero']}."
                )
                return

            if montant <= 0:
                messagebox.showerror(
                    "Erreur",
                    f"Le montant de l'avance {champs['numero']} doit etre > 0."
                )
                return

            deja_deduit = champs["deja_deduit"] or 0
            if montant < deja_deduit - 0.01:
                messagebox.showerror(
                    "Erreur",
                    f"Pour l'avance {champs['numero']}, le montant "
                    f"({format_montant(montant)}) ne peut pas etre inferieur "
                    f"a ce qui a deja ete deduit ({format_montant(deja_deduit)})."
                )
                return

            date_str = champs["date"].get().strip()
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror(
                    "Erreur",
                    f"Date invalide pour l'avance {champs['numero']}.\n"
                    f"Format attendu : AAAA-MM-JJ"
                )
                return

            motif = champs["motif"].get().strip() or "Avance sur salaire"

            modifications.append({
                "id": avance_id,
                "montant": montant,
                "motif": motif,
                "date": date_str,
                "numero": champs["numero"],
            })

        rep = messagebox.askyesno(
            "Confirmation",
            f"Sauvegarder les modifications de {len(modifications)} avance(s) ?"
        )
        if not rep:
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()

            for m in modifications:
                cursor.execute("""
                    UPDATE avances_personnel
                    SET montant = ?, motif = ?, date_avance = ?
                    WHERE id = ?
                """, (m["montant"], m["motif"], m["date"], m["id"]))

            conn.commit()
            conn.close()

            messagebox.showinfo("Succes", "Modifications enregistrees.")
            if self.on_save:
                self.on_save()
            self.destroy()

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")