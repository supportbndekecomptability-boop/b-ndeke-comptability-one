"""
Page Bilan initial - Comptes Syscohada
Le comptable ajoute uniquement les comptes qu'il utilise.
"""
import customtkinter as ctk
from tkinter import messagebox
from config import COLOR_NAVY, format_montant
from core.bilan_initial import (
    get_bilan_initial, ajouter_compte, supprimer_compte,
    total_actif, total_passif, capitaux_propres,
    liste_comptes_actif, liste_comptes_passif,
    get_libelle, vider_bilan_initial,
)


class BilanInitialPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")

        self.utilisateur = utilisateur or {}

        self._construire()

    def _construire(self):
        zone = ctk.CTkScrollableFrame(self, fg_color="transparent")
        zone.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            zone, text="Bilan initial",
            font=("Segoe UI", 20, "bold"),
            text_color=COLOR_NAVY,
        ).pack(anchor="w", pady=(5, 3))

        ctk.CTkLabel(
            zone,
            text=(
                "Saisissez la situation de depart de l'ecole (au premier jour "
                "d'utilisation). Ajoutez uniquement les comptes que vous utilisez. "
                "Les comptes non ajoutes n'apparaitront pas sur le bilan."
            ),
            font=("Segoe UI", 10),
            text_color="#666666",
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(0, 15))

        # ===================== ACTIF =====================
        cadre_actif = ctk.CTkFrame(zone, fg_color="white", corner_radius=10)
        cadre_actif.pack(fill="x", pady=(0, 15))

        entete_actif = ctk.CTkFrame(cadre_actif, fg_color="#E8F4EA", corner_radius=8)
        entete_actif.pack(fill="x", padx=8, pady=(8, 5))

        ctk.CTkLabel(
            entete_actif, text="ACTIF",
            font=("Segoe UI", 14, "bold"),
            text_color="#1e7e34",
        ).pack(side="left", padx=12, pady=10)

        ctk.CTkButton(
            entete_actif, text="+ Ajouter un compte d'actif",
            font=("Segoe UI", 11, "bold"),
            fg_color="#27ae60", hover_color="#229954",
            height=32,
            command=lambda: self._ouvrir_formulaire("actif"),
        ).pack(side="right", padx=12, pady=8)

        self.frame_actif = ctk.CTkFrame(cadre_actif, fg_color="transparent")
        self.frame_actif.pack(fill="x", padx=8, pady=(0, 5))

        self.label_total_actif = ctk.CTkLabel(
            cadre_actif, text="",
            font=("Segoe UI", 13, "bold"),
            text_color="#1e7e34",
        )
        self.label_total_actif.pack(anchor="e", padx=15, pady=(5, 12))

        # ===================== PASSIF =====================
        cadre_passif = ctk.CTkFrame(zone, fg_color="white", corner_radius=10)
        cadre_passif.pack(fill="x", pady=(0, 15))

        entete_passif = ctk.CTkFrame(cadre_passif, fg_color="#FDEAEA", corner_radius=8)
        entete_passif.pack(fill="x", padx=8, pady=(8, 5))

        ctk.CTkLabel(
            entete_passif, text="PASSIF",
            font=("Segoe UI", 14, "bold"),
            text_color="#c0392b",
        ).pack(side="left", padx=12, pady=10)

        ctk.CTkButton(
            entete_passif, text="+ Ajouter un compte de passif",
            font=("Segoe UI", 11, "bold"),
            fg_color="#e74c3c", hover_color="#c0392b",
            height=32,
            command=lambda: self._ouvrir_formulaire("passif"),
        ).pack(side="right", padx=12, pady=8)

        self.frame_passif = ctk.CTkFrame(cadre_passif, fg_color="transparent")
        self.frame_passif.pack(fill="x", padx=8, pady=(0, 5))

        self.label_total_passif = ctk.CTkLabel(
            cadre_passif, text="",
            font=("Segoe UI", 13, "bold"),
            text_color="#c0392b",
        )
        self.label_total_passif.pack(anchor="e", padx=15, pady=(5, 12))

        # ===================== CAPITAUX PROPRES =====================
        cadre_cp = ctk.CTkFrame(zone, fg_color="#F0F7FF", corner_radius=10)
        cadre_cp.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            cadre_cp, text="CAPITAUX PROPRES",
            font=("Segoe UI", 13, "bold"),
            text_color=COLOR_NAVY,
        ).pack(anchor="w", padx=15, pady=(12, 3))

        ctk.CTkLabel(
            cadre_cp,
            text="(Total Actif - Total Passif)",
            font=("Segoe UI", 9),
            text_color="#666666",
        ).pack(anchor="w", padx=15, pady=(0, 3))

        self.label_cp = ctk.CTkLabel(
            cadre_cp, text="",
            font=("Segoe UI", 18, "bold"),
            text_color=COLOR_NAVY,
        )
        self.label_cp.pack(anchor="e", padx=15, pady=(0, 12))

        # ===================== ACTIONS =====================
        ligne_actions = ctk.CTkFrame(zone, fg_color="transparent")
        ligne_actions.pack(fill="x", pady=(5, 20))

        ctk.CTkButton(
            ligne_actions, text="Vider tout le bilan initial",
            font=("Segoe UI", 11),
            fg_color="#e74c3c", hover_color="#c0392b",
            height=38,
            command=self._vider_tout,
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            ligne_actions, text="Rafraichir",
            font=("Segoe UI", 11),
            fg_color="#3498db", hover_color="#2980b9",
            height=38,
            command=self._rafraichir,
        ).pack(side="left", padx=5)

        self._rafraichir()

    # =========================================================
    def _rafraichir(self):
        # --- ACTIF ---
        for w in self.frame_actif.winfo_children():
            w.destroy()

        data = get_bilan_initial()
        actif = data.get("actif", {})

        if not actif:
            ctk.CTkLabel(
                self.frame_actif,
                text="Aucun compte d'actif ajoute.",
                font=("Segoe UI", 11),
                text_color="#999999",
            ).pack(pady=20)
        else:
            for code in sorted(actif.keys()):
                self._ajouter_ligne(self.frame_actif, "actif", code, actif[code])

        self.label_total_actif.configure(
            text=f"TOTAL ACTIF : {format_montant(total_actif())}"
        )

        # --- PASSIF ---
        for w in self.frame_passif.winfo_children():
            w.destroy()

        passif = data.get("passif", {})

        if not passif:
            ctk.CTkLabel(
                self.frame_passif,
                text="Aucun compte de passif ajoute.",
                font=("Segoe UI", 11),
                text_color="#999999",
            ).pack(pady=20)
        else:
            for code in sorted(passif.keys()):
                self._ajouter_ligne(self.frame_passif, "passif", code, passif[code])

        self.label_total_passif.configure(
            text=f"TOTAL PASSIF : {format_montant(total_passif())}"
        )

        # --- CAPITAUX PROPRES ---
        cp = capitaux_propres()
        couleur = "#27ae60" if cp >= 0 else "#e74c3c"
        self.label_cp.configure(text=format_montant(cp), text_color=couleur)

    def _ajouter_ligne(self, parent, cote, code, montant):
        ligne = ctk.CTkFrame(parent, fg_color="#fafafa", corner_radius=6)
        ligne.pack(fill="x", pady=2)

        ctk.CTkLabel(
            ligne, text=code,
            font=("Consolas", 12, "bold"),
            text_color=COLOR_NAVY,
            width=50, anchor="w",
        ).pack(side="left", padx=(10, 5), pady=8)

        ctk.CTkLabel(
            ligne, text=get_libelle(code),
            font=("Segoe UI", 11),
            text_color="#333333",
            anchor="w",
        ).pack(side="left", padx=5, pady=8, fill="x", expand=True)

        ctk.CTkLabel(
            ligne, text=format_montant(montant),
            font=("Segoe UI", 11, "bold"),
            text_color=COLOR_NAVY,
            width=150, anchor="e",
        ).pack(side="left", padx=5, pady=8)

        ctk.CTkButton(
            ligne, text="M",
            font=("Segoe UI", 10, "bold"),
            width=32, height=26,
            fg_color="#3498db", hover_color="#2980b9",
            command=lambda c=code, m=montant, ct=cote: self._modifier(ct, c, m),
        ).pack(side="right", padx=2, pady=6)

        ctk.CTkButton(
            ligne, text="X",
            font=("Segoe UI", 10, "bold"),
            width=32, height=26,
            fg_color="#e74c3c", hover_color="#c0392b",
            command=lambda c=code, ct=cote: self._supprimer(ct, c),
        ).pack(side="right", padx=2, pady=6)

    # =========================================================
    def _ouvrir_formulaire(self, cote, code_pre=None, montant_pre=None):
        FormulaireCompteBilan(
            self, cote=cote, code_pre=code_pre, montant_pre=montant_pre,
            on_save=self._rafraichir,
        )

    def _modifier(self, cote, code, montant):
        self._ouvrir_formulaire(cote, code_pre=code, montant_pre=montant)

    def _supprimer(self, cote, code):
        rep = messagebox.askyesno(
            "Confirmation",
            f"Supprimer le compte {code} - {get_libelle(code)} du bilan initial ?"
        )
        if rep:
            supprimer_compte(cote, code)
            self._rafraichir()

    def _vider_tout(self):
        rep = messagebox.askyesno(
            "Confirmation",
            "Vider TOUT le bilan initial ?\n\nCette action est irreversible."
        )
        if rep:
            vider_bilan_initial()
            self._rafraichir()


# ============================================================
# FORMULAIRE D'AJOUT / MODIFICATION
# ============================================================
class FormulaireCompteBilan(ctk.CTkToplevel):
    def __init__(self, parent, cote, code_pre=None, montant_pre=None, on_save=None):
        super().__init__(parent)

        self.cote = cote
        self.on_save = on_save
        self.mode_edition = (code_pre is not None)

        titre = "Modifier un compte" if self.mode_edition else (
            "Ajouter un compte d'actif" if cote == "actif"
            else "Ajouter un compte de passif"
        )
        self.title(titre)

        largeur = 500
        hauteur = 320
        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        x = (self.winfo_screenwidth() // 2) - (largeur // 2)
        y = max(20, (self.winfo_screenheight() // 2) - (hauteur // 2))
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")

        self.bind("<Escape>", lambda e: self.destroy())
        self.transient(parent)
        self.after(100, self._activer_grab)

        self._construire(code_pre, montant_pre)

    def _activer_grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _construire(self, code_pre, montant_pre):
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        couleur = "#27ae60" if self.cote == "actif" else "#e74c3c"
        titre = "Compte d'ACTIF" if self.cote == "actif" else "Compte de PASSIF"

        ctk.CTkLabel(
            card, text=titre,
            font=("Segoe UI", 15, "bold"),
            text_color=couleur,
        ).pack(pady=(18, 10), padx=20, anchor="w")

        # --- Compte ---
        ctk.CTkLabel(
            card, text="Compte",
            font=("Segoe UI", 11, "bold"),
            text_color="#333333",
            anchor="w",
        ).pack(padx=20, pady=(5, 3), fill="x")

        comptes = liste_comptes_actif() if self.cote == "actif" else liste_comptes_passif()
        libelles = [f"{c} - {lib}" for c, lib in comptes]

        self.combo = ctk.CTkComboBox(
            card,
            values=libelles,
            font=("Segoe UI", 12),
            height=38,
            state="readonly" if self.mode_edition else "normal",
        )
        self.combo.pack(padx=20, pady=(0, 10), fill="x")

        if code_pre:
            for c, lib in comptes:
                if c == str(code_pre):
                    self.combo.set(f"{c} - {lib}")
                    break
        elif libelles:
            self.combo.set(libelles[0])

        if self.mode_edition:
            self.combo.configure(state="disabled")

        # --- Montant ---
        ctk.CTkLabel(
            card, text="Montant",
            font=("Segoe UI", 11, "bold"),
            text_color="#333333",
            anchor="w",
        ).pack(padx=20, pady=(5, 3), fill="x")

        self.entree_montant = ctk.CTkEntry(
            card,
            font=("Segoe UI", 14, "bold"),
            height=42,
            placeholder_text="Ex: 500000",
        )
        if montant_pre is not None:
            self.entree_montant.insert(0, str(int(float(montant_pre))))
        self.entree_montant.pack(padx=20, pady=(0, 15), fill="x")

        # --- Boutons ---
        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=20, pady=(5, 15))

        ctk.CTkButton(
            boutons, text="Annuler",
            font=("Segoe UI", 12),
            fg_color="#e74c3c", hover_color="#c0392b",
            height=40,
            command=self.destroy,
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(
            boutons, text="Enregistrer",
            font=("Segoe UI", 12, "bold"),
            fg_color=COLOR_NAVY, hover_color="#1a3d75",
            height=40,
            command=self._enregistrer,
        ).pack(side="left", expand=True, fill="x", padx=(5, 0))

        self.after(300, lambda: self.entree_montant.focus_set())

    def _enregistrer(self):
        # Recuperer le code depuis le combo
        valeur = self.combo.get()
        if " - " not in valeur:
            messagebox.showerror("Erreur", "Choisissez un compte.")
            return
        code = valeur.split(" - ")[0].strip()

        montant_str = self.entree_montant.get().strip()
        if not montant_str:
            messagebox.showerror("Erreur", "Saisissez un montant.")
            return

        montant_str = montant_str.replace(" ", "").replace(",", ".")
        try:
            m = float(montant_str)
        except ValueError:
            messagebox.showerror("Erreur", "Montant invalide.")
            return

        if m < 0:
            messagebox.showerror("Erreur", "Le montant doit etre positif.")
            return

        ok, msg = ajouter_compte(self.cote, code, m)
        if ok:
            if self.on_save:
                self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Erreur", msg)