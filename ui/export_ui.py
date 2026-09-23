"""
Interface Export Excel
"""
import os
import sys
import subprocess
import platform
from tkinter import messagebox
import customtkinter as ctk
from config import COLOR_NAVY, COLOR_GOLD
from core.export_excel import (
    exporter_tout_vers_excel, get_dossier_exports, lister_exports,
)


class ExportPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")

        self.utilisateur = utilisateur

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self._construire_interface()

    def _construire_interface(self):
        ctk.CTkLabel(
            self.scroll,
            text="Export Excel",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_NAVY,
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            self.scroll,
            text="Exportez toutes les donnees dans un fichier Excel (.xlsx)",
            font=("Segoe UI", 13),
            text_color="#666666",
        ).pack(anchor="w", pady=(0, 20))

        # ===== CARTE PRINCIPALE =====
        card = ctk.CTkFrame(self.scroll, fg_color="white", corner_radius=15,
                            border_width=2, border_color="#27ae60")
        card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card,
            text="Export complet en un clic",
            font=("Segoe UI", 16, "bold"),
            text_color="#27ae60",
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            card,
            text="Cree un fichier Excel avec 10 onglets :",
            font=("Segoe UI", 12),
            text_color="#333333",
        ).pack(pady=(0, 10))

        onglets_frame = ctk.CTkFrame(card, fg_color="#F0FFF4", corner_radius=8)
        onglets_frame.pack(fill="x", padx=30, pady=(0, 15))

        onglets = [
            "Eleves",
            "Personnel",
            "Paiements Eleves",
            "Paies Personnel",
            "Avances",
            "Depenses",
            "Journal General",
            "Balance",
            "Bilan",
            "Compte Resultat",
        ]

        col1 = ctk.CTkFrame(onglets_frame, fg_color="transparent")
        col1.pack(side="left", fill="both", expand=True, padx=(15, 5), pady=10)
        col2 = ctk.CTkFrame(onglets_frame, fg_color="transparent")
        col2.pack(side="left", fill="both", expand=True, padx=(5, 15), pady=10)

        for i, nom in enumerate(onglets):
            col = col1 if i < 5 else col2
            ctk.CTkLabel(
                col,
                text=f"  {nom}",
                font=("Segoe UI", 11),
                text_color="#2d7a2d",
                anchor="w",
            ).pack(fill="x", pady=2)

        ctk.CTkButton(
            card,
            text="EXPORTER TOUT EN EXCEL",
            font=("Segoe UI", 14, "bold"),
            fg_color="#27ae60",
            hover_color="#229954",
            height=50,
            command=self._exporter,
        ).pack(padx=30, pady=(5, 20), fill="x")

        # ===== SECTION FICHIERS EXPORTES =====
        ctk.CTkLabel(
            self.scroll,
            text="Fichiers exportes",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_NAVY,
        ).pack(anchor="w", pady=(5, 8))

        ligne_btns = ctk.CTkFrame(self.scroll, fg_color="transparent")
        ligne_btns.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            ligne_btns,
            text="Ouvrir le dossier",
            font=("Segoe UI", 11),
            fg_color="#e0e0e0",
            text_color="#333333",
            hover_color="#c0c0c0",
            height=32,
            command=self._ouvrir_dossier,
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            ligne_btns,
            text="Rafraichir",
            font=("Segoe UI", 11),
            fg_color="#e0e0e0",
            text_color="#333333",
            hover_color="#c0c0c0",
            height=32,
            command=self._rafraichir_liste,
        ).pack(side="left", padx=5)

        self.frame_fichiers = ctk.CTkScrollableFrame(
            self.scroll, fg_color="white", corner_radius=10, height=250,
        )
        self.frame_fichiers.pack(fill="both", expand=True)

        self._rafraichir_liste()

    def _exporter(self):
        self.update()
        ok, resultat = exporter_tout_vers_excel()

        if ok:
            messagebox.showinfo(
                "Export reussi",
                f"Fichier Excel cree :\n\n{resultat}\n\n"
                f"10 onglets : Eleves, Personnel, Paiements, Avances,\n"
                f"Depenses, Journal, Balance, Bilan, Compte de resultat"
            )
            self._rafraichir_liste()
            try:
                if platform.system() == "Windows":
                    os.startfile(resultat)
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", resultat])
                else:
                    subprocess.Popen(["xdg-open", resultat])
            except Exception:
                pass
        else:
            messagebox.showerror("Erreur", str(resultat))

    def _ouvrir_dossier(self):
        dossier = get_dossier_exports()
        try:
            if platform.system() == "Windows":
                os.startfile(dossier)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", dossier])
            else:
                subprocess.Popen(["xdg-open", dossier])
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def _rafraichir_liste(self):
        for w in self.frame_fichiers.winfo_children():
            w.destroy()

        fichiers = lister_exports()

        if not fichiers:
            ctk.CTkLabel(
                self.frame_fichiers,
                text="Aucun fichier exporte pour le moment.\n\n"
                     "Cliquez sur 'EXPORTER TOUT EN EXCEL' ci-dessus.",
                font=("Segoe UI", 12),
                text_color="#999999",
                justify="center",
            ).pack(pady=40)
            return

        entete = ctk.CTkFrame(self.frame_fichiers, fg_color="#f0f0f0", corner_radius=6)
        entete.pack(fill="x", pady=(0, 5))

        for nom, larg in [("Date", 180), ("Fichier", 350), ("Taille", 100)]:
            ctk.CTkLabel(entete, text=nom,
                         font=("Segoe UI", 11, "bold"),
                         text_color=COLOR_NAVY, width=larg,
                         anchor="w").pack(side="left", padx=5, pady=10)

        ctk.CTkLabel(entete, text="Actions",
                     font=("Segoe UI", 11, "bold"),
                     text_color=COLOR_NAVY, width=180,
                     anchor="center").pack(side="right", padx=5, pady=10)

        for i, f in enumerate(fichiers):
            fond = "#ffffff" if i % 2 == 0 else "#fafafa"
            ligne = ctk.CTkFrame(self.frame_fichiers, fg_color=fond, corner_radius=4)
            ligne.pack(fill="x", pady=1)

            taille_ko = f["taille"] / 1024
            taille_str = (f"{taille_ko:.1f} Ko" if taille_ko < 1024
                          else f"{taille_ko/1024:.2f} Mo")

            for val, larg, coul in [
                (f["date"].strftime("%d/%m/%Y %H:%M"), 180, "#333333"),
                (f["nom"], 350, "#0066CC"),
                (taille_str, 100, "#666666"),
            ]:
                ctk.CTkLabel(ligne, text=str(val),
                             font=("Segoe UI", 11),
                             text_color=coul, width=larg,
                             anchor="w").pack(side="left", padx=5, pady=8)

            actions = ctk.CTkFrame(ligne, fg_color="transparent", width=180)
            actions.pack(side="right", padx=5)

            ctk.CTkButton(actions, text="Ouvrir",
                          font=("Segoe UI", 10, "bold"),
                          width=80, height=26,
                          fg_color="#3498db", hover_color="#2980b9",
                          command=lambda ff=f: self._ouvrir_fichier(ff)).pack(side="left", padx=2)

            ctk.CTkButton(actions, text="X",
                          font=("Segoe UI", 10, "bold"),
                          width=36, height=26,
                          fg_color="#e74c3c", hover_color="#c0392b",
                          command=lambda ff=f: self._supprimer(ff)).pack(side="left", padx=2)

    def _ouvrir_fichier(self, f):
        try:
            if platform.system() == "Windows":
                os.startfile(f["chemin"])
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", f["chemin"]])
            else:
                subprocess.Popen(["xdg-open", f["chemin"]])
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def _supprimer(self, f):
        rep = messagebox.askyesno(
            "Confirmation",
            f"Supprimer le fichier :\n\n{f['nom']} ?"
        )
        if rep:
            try:
                os.remove(f["chemin"])
                self._rafraichir_liste()
            except Exception as e:
                messagebox.showerror("Erreur", str(e))