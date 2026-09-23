"""
Fenetre de paiement du salaire d'un membre du personnel
Avec deduction d'avance MANUELLE (le comptable decide)
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from config import COLOR_NAVY, format_montant, CURRENCY_SYMBOL
from core.personnel import get_personnel
from core.avances import (
    total_avance_en_cours,
    deduire_avances_personnel,
)
from database import get_connection


class PaiementPersonnelWindow(ctk.CTkToplevel):
    def __init__(self, parent, personnel, on_save=None):
        super().__init__(parent)

        self.personnel = personnel
        self.on_save = on_save
        self.avance_en_cours = 0

        self.title(f"Paiement - {personnel['nom']} {personnel['prenom']}")

        # Adapter a l'ecran
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        largeur = min(580, sw - 40)
        hauteur = min(680, sh - 80)

        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        x = (sw // 2) - (largeur // 2)
        y = max(5, (sh // 2) - (hauteur // 2) - 20)
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
        # ===== CARD SCROLLABLE (pour petits ecrans) =====
        card = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=10, pady=10)

        # ===== EN-TETE =====
        ctk.CTkLabel(
            card,
            text="Paiement de salaire",
            font=("Segoe UI", 16, "bold"),
            text_color=COLOR_NAVY,
        ).pack(pady=(10, 2))

        ctk.CTkLabel(
            card,
            text=f"{self.personnel['nom']} {self.personnel['prenom']}  ({self.personnel['code']})",
            font=("Segoe UI", 11),
            text_color="#666666",
        ).pack(pady=(0, 10))

        # ===== RESUME DU CONTRAT =====
        cadre_resume = ctk.CTkFrame(card, fg_color="#F0F7FF", corner_radius=10)
        cadre_resume.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            cadre_resume,
            text="RESUME DU CONTRAT",
            font=("Segoe UI", 10, "bold"),
            text_color=COLOR_NAVY,
        ).pack(anchor="w", padx=12, pady=(8, 4))

        salaire = self.personnel.get("salaire_mensuel", 0) or 0
        duree = self.personnel.get("duree_contrat_mois", 12) or 12
        engagement = salaire * duree

        deja_paye = self._get_total_paye()
        reste = engagement - deja_paye

        self.avance_en_cours = total_avance_en_cours(self.personnel["id"])

        for label, valeur, couleur in [
            ("Salaire mensuel", format_montant(salaire), "#333333"),
            ("Duree du contrat", f"{duree} mois", "#333333"),
            ("Engagement total", format_montant(engagement), "#8e44ad"),
            ("Deja paye", format_montant(deja_paye), "#27ae60"),
            ("Reste a payer", format_montant(reste),
             "#e74c3c" if reste > 0 else "#27ae60"),
            ("Avance en cours", format_montant(self.avance_en_cours),
             "#e67e22" if self.avance_en_cours > 0.01 else "#999999"),
        ]:
            ligne = ctk.CTkFrame(cadre_resume, fg_color="transparent")
            ligne.pack(fill="x", padx=12, pady=1)
            ctk.CTkLabel(
                ligne, text=label,
                font=("Segoe UI", 10), text_color="#666666",
                anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                ligne, text=valeur,
                font=("Segoe UI", 10, "bold"), text_color=couleur,
                anchor="e",
            ).pack(side="right")

        ctk.CTkLabel(cadre_resume, text="").pack(pady=1)

        # ===== MONTANT A PAYER =====
        ctk.CTkLabel(
            card, text=f"Montant a payer ({CURRENCY_SYMBOL})",
            font=("Segoe UI", 11, "bold"),
            text_color="#333333", anchor="w",
        ).pack(padx=15, pady=(6, 3), fill="x")

        self.entree_montant = ctk.CTkEntry(
            card,
            font=("Segoe UI", 13, "bold"),
            height=38,
            placeholder_text="0",
        )
        if salaire > 0:
            self.entree_montant.insert(0, str(int(salaire)))
        self.entree_montant.pack(padx=15, pady=(0, 4), fill="x")
        self.entree_montant.bind("<KeyRelease>", lambda e: self._maj_resume())

        # Boutons rapides
        ligne_rapide = ctk.CTkFrame(card, fg_color="transparent")
        ligne_rapide.pack(fill="x", padx=15, pady=(0, 8))

        ctk.CTkLabel(
            ligne_rapide, text="Rapide :",
            font=("Segoe UI", 9), text_color="#888888",
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            ligne_rapide, text="Salaire",
            font=("Segoe UI", 9),
            fg_color="#e0e0e0", text_color="#333333",
            hover_color="#c0c0c0", height=26, width=70,
            command=lambda: self._set_montant(salaire),
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            ligne_rapide, text="Reste",
            font=("Segoe UI", 9),
            fg_color="#e0e0e0", text_color="#333333",
            hover_color="#c0c0c0", height=26, width=60,
            command=lambda: self._set_montant(max(0, reste)),
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            ligne_rapide, text="Effacer",
            font=("Segoe UI", 9),
            fg_color="#e0e0e0", text_color="#333333",
            hover_color="#c0c0c0", height=26, width=65,
            command=lambda: self._set_montant(0),
        ).pack(side="left", padx=2)

        # ===== MOTIF =====
        ctk.CTkLabel(
            card, text="Motif",
            font=("Segoe UI", 11, "bold"),
            text_color="#333333", anchor="w",
        ).pack(padx=15, pady=(4, 3), fill="x")

        self.combo_motif = ctk.CTkComboBox(
            card,
            values=["Salaire mensuel", "Prime", "Heures supplementaires",
                    "Indemnite", "Autre"],
            font=("Segoe UI", 11),
            height=34,
        )
        self.combo_motif.set("Salaire mensuel")
        self.combo_motif.pack(padx=15, pady=(0, 8), fill="x")

        # ===== MODE =====
        ctk.CTkLabel(
            card, text="Mode de paiement",
            font=("Segoe UI", 11, "bold"),
            text_color="#333333", anchor="w",
        ).pack(padx=15, pady=(4, 3), fill="x")

        self.combo_mode = ctk.CTkComboBox(
            card,
            values=["Especes", "Banque", "Cheque", "Mobile Money"],
            font=("Segoe UI", 11),
            height=34,
        )
        self.combo_mode.set("Especes")
        self.combo_mode.pack(padx=15, pady=(0, 8), fill="x")

        # ===== DEDUCTION AVANCE =====
        self.var_deduire = ctk.StringVar(value="0")

        cadre_avance = ctk.CTkFrame(card, fg_color="#FFF7E0", corner_radius=8)
        cadre_avance.pack(fill="x", padx=15, pady=(2, 8))

        if self.avance_en_cours > 0.01:
            ctk.CTkCheckBox(
                cadre_avance,
                text=f"Deduire une avance (solde : {format_montant(self.avance_en_cours)})",
                variable=self.var_deduire,
                onvalue="1", offvalue="0",
                font=("Segoe UI", 10, "bold"),
                text_color="#8B6914",
                command=self._on_toggle_avance,
            ).pack(padx=12, pady=(8, 4), anchor="w")

            ligne_ded = ctk.CTkFrame(cadre_avance, fg_color="transparent")
            ligne_ded.pack(padx=12, pady=(0, 4), fill="x")

            ctk.CTkLabel(
                ligne_ded,
                text="Montant :",
                font=("Segoe UI", 10),
                text_color="#666666",
            ).pack(side="left")

            self.entree_deduction = ctk.CTkEntry(
                ligne_ded,
                font=("Segoe UI", 11, "bold"),
                height=30,
                width=120,
                placeholder_text="0",
            )
            self.entree_deduction.pack(side="left", padx=(6, 4))
            self.entree_deduction.bind("<KeyRelease>", lambda e: self._maj_resume())
            self.entree_deduction.configure(state="disabled")

            ctk.CTkButton(
                ligne_ded,
                text="Max",
                font=("Segoe UI", 9, "bold"),
                fg_color="#e0e0e0", text_color="#333333",
                hover_color="#c0c0c0", width=45, height=26,
                command=lambda: self._set_deduction(self.avance_en_cours),
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                ligne_ded,
                text="0",
                font=("Segoe UI", 9, "bold"),
                fg_color="#e0e0e0", text_color="#333333",
                hover_color="#c0c0c0", width=35, height=26,
                command=lambda: self._set_deduction(0),
            ).pack(side="left", padx=2)

            ctk.CTkLabel(
                cadre_avance,
                text="Le comptable decide du montant a deduire.",
                font=("Segoe UI", 8),
                text_color="#999999",
            ).pack(padx=12, pady=(0, 8), anchor="w")
        else:
            ctk.CTkLabel(
                cadre_avance,
                text="Aucune avance en cours pour cet employe.",
                font=("Segoe UI", 10),
                text_color="#999999",
            ).pack(padx=12, pady=8, anchor="w")
            self.entree_deduction = None

        # ===== RESUME FINAL =====
        cadre_final = ctk.CTkFrame(card, fg_color="#E8F4EA", corner_radius=8)
        cadre_final.pack(fill="x", padx=15, pady=(2, 10))

        self.label_resume_final = ctk.CTkLabel(
            cadre_final,
            text="",
            font=("Consolas", 10, "bold"),
            text_color="#1e7e34",
            justify="left",
            anchor="w",
        )
        self.label_resume_final.pack(padx=12, pady=8, fill="x")

        # ===== BOUTONS =====
        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=15, pady=(2, 15))

        ctk.CTkButton(
            boutons, text="Annuler",
            font=("Segoe UI", 11),
            fg_color="#e74c3c", hover_color="#c0392b",
            height=40,
            command=self.destroy,
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        ctk.CTkButton(
            boutons, text="PAYER",
            font=("Segoe UI", 12, "bold"),
            fg_color="#27ae60", hover_color="#229954",
            height=40,
            command=self._payer,
        ).pack(side="left", expand=True, fill="x", padx=(4, 0))

        self.after(300, lambda: self.entree_montant.focus_set())
        self._maj_resume()

    # =========================================================
    def _on_toggle_avance(self):
        try:
            if self.var_deduire.get() == "1":
                self.entree_deduction.configure(state="normal")
                self.entree_deduction.focus_set()
            else:
                self.entree_deduction.delete(0, "end")
                self.entree_deduction.configure(state="disabled")
        except Exception:
            pass
        self._maj_resume()

    def _set_deduction(self, valeur):
        if not self.entree_deduction:
            return
        try:
            self.entree_deduction.configure(state="normal")
            self.entree_deduction.delete(0, "end")
            if valeur > 0:
                self.entree_deduction.insert(0, str(int(valeur)))
        except Exception:
            pass
        self._maj_resume()

    def _get_total_paye(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COALESCE(SUM(montant), 0) as total "
                "FROM paiements_personnel WHERE personnel_id = ?",
                (self.personnel["id"],)
            )
            total = cursor.fetchone()["total"] or 0
            conn.close()
            return total
        except Exception:
            return 0

    def _set_montant(self, valeur):
        self.entree_montant.delete(0, "end")
        if valeur > 0:
            self.entree_montant.insert(0, str(int(valeur)))
        self._maj_resume()

    def _get_montant_deduit(self, montant):
        if self.var_deduire.get() != "1" or self.avance_en_cours <= 0.01:
            return 0
        if not self.entree_deduction:
            return 0
        try:
            s = self.entree_deduction.get().strip().replace(" ", "").replace(",", "")
            ded = float(s) if s else 0
        except Exception:
            ded = 0
        return min(ded, self.avance_en_cours)

    def _maj_resume(self):
        try:
            montant_str = self.entree_montant.get().strip().replace(" ", "").replace(",", "")
            montant = float(montant_str) if montant_str else 0
        except Exception:
            montant = 0

        montant_deduit = self._get_montant_deduit(montant)
        net = montant - montant_deduit

        if net < 0:
            texte = (
                f"Salaire brut     : {format_montant(montant)}\n"
                f"- Avance deduite : - {format_montant(montant_deduit)}\n"
                f"= NET A VERSER   : {format_montant(0)}\n"
                f"\n"
                f"ATTENTION : deduction > salaire.\n"
                f"Employe debiteur de {format_montant(-net)}."
            )
            self.label_resume_final.configure(text=texte, text_color="#e74c3c")
        else:
            texte = (
                f"Salaire brut     : {format_montant(montant)}\n"
                f"- Avance deduite : - {format_montant(montant_deduit)}\n"
                f"= NET A VERSER   : {format_montant(net)}"
            )
            self.label_resume_final.configure(text=texte, text_color="#1e7e34")

    def _payer(self):
        montant_str = self.entree_montant.get().strip().replace(" ", "").replace(",", "")
        try:
            montant = float(montant_str) if montant_str else 0
        except ValueError:
            messagebox.showerror("Erreur", "Montant invalide.")
            return

        if montant <= 0:
            messagebox.showerror("Erreur", "Le montant doit etre superieur a 0.")
            return

        montant_deduit = self._get_montant_deduit(montant)
        net = max(0, montant - montant_deduit)

        if montant_deduit > montant:
            rep = messagebox.askyesno(
                "Confirmation",
                f"Le montant a deduire ({format_montant(montant_deduit)}) depasse "
                f"le salaire ({format_montant(montant)}).\n\n"
                f"Le net a verser sera de 0.\n"
                f"Confirmer ?"
            )
            if not rep:
                return

        motif = self.combo_motif.get()
        mode = self.combo_mode.get()

        try:
            conn = get_connection()
            cursor = conn.cursor()

            numero_paie = self._generer_numero_paie(cursor)
            date_paiement = datetime.now().strftime("%Y-%m-%d")

            cursor.execute("""
                INSERT INTO paiements_personnel
                    (numero_paie, personnel_id, date_paiement, montant, motif,
                     mode_paiement, montant_avance_deduit)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (numero_paie, self.personnel["id"], date_paiement,
                  montant, motif, mode, montant_deduit))

            conn.commit()
            conn.close()

            if montant_deduit > 0.01:
                ok, effectif, msg = deduire_avances_personnel(
                    self.personnel["id"], montant_deduit
                )
                if not ok:
                    print(f"[PAIEMENT] Attention : {msg}")

            messagebox.showinfo(
                "Succes",
                f"Paiement enregistre !\n\n"
                f"Numero : {numero_paie}\n"
                f"Salaire brut : {format_montant(montant)}\n"
                f"Avance deduite : {format_montant(montant_deduit)}\n"
                f"Net verse : {format_montant(net)}"
            )

            if self.on_save:
                self.on_save()
            self.destroy()

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def _generer_numero_paie(self, cursor):
        cursor.execute("SELECT COUNT(*) as total FROM paiements_personnel")
        total = cursor.fetchone()["total"]
        return f"PAIE-{total + 1:05d}"