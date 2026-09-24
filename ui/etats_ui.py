"""
Interface Etats financiers SYSCOHADA
Permissions : tous les roles (sauf caissier) peuvent generer les etats.
              Bilan initial et Suivi budgetaire : admin/gestionnaire uniquement.
"""
from datetime import datetime
import os
import customtkinter as ctk
from tkinter import messagebox
from config import COLOR_NAVY, COLOR_GOLD, format_montant, DATA_DIR

from ui.permissions_ui import peut
from core.permissions import get_role
from core.etats_financiers import (
    etat_journal, etat_grand_livre, etat_balance,
    etat_compte_resultat, etat_bilan, etat_tresorerie,
)
from services.etats_pdf import (
    pdf_journal, pdf_grand_livre, pdf_balance,
    pdf_compte_resultat, pdf_bilan, pdf_tresorerie,
)
from ui.pdf_viewer import PdfViewerWindow
from ui.suivi_budgetaire_ui import SuiviBudgetaireWindow
from core.bilan_initial import (
    get_bilan_initial, total_actif, total_passif,
    capitaux_propres, get_libelle,
)


class EtatsPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")

        self.utilisateur = utilisateur or {}

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self._construire_interface()

    # ================== PERMISSIONS ==================
    def _peut_gerer_bilan_initial(self):
        """Bilan initial et Suivi budgetaire : admin/gestionnaire uniquement."""
        return (peut(self.utilisateur, "peut_gerer_utilisateurs")
                or peut(self.utilisateur, "peut_gerer_permissions"))

    # ================== INTERFACE ==================
    def _construire_interface(self):
        # ===== EN-TETE =====
        ligne_top = ctk.CTkFrame(self.scroll, fg_color="transparent")
        ligne_top.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(
            ligne_top,
            text="Etats financiers SYSCOHADA",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        # Badge role
        role = get_role(self.utilisateur)
        if role in ("admin", "gestionnaire"):
            info_role = "Vue : acces complet"
            couleur_role = "#27ae60"
        elif role == "comptable":
            info_role = "Vue : acces complet"
            couleur_role = "#e67e22"
        else:
            info_role = "Vue : lecture seule"
            couleur_role = "#3498db"

        ctk.CTkLabel(
            ligne_top,
            text=info_role,
            font=("Segoe UI", 10, "italic"),
            text_color=couleur_role,
        ).pack(side="right", pady=(8, 0))

        ctk.CTkLabel(
            self.scroll,
            text="Generez les etats financiers selon le referentiel OHADA / SYSCOHADA",
            font=("Segoe UI", 13),
            text_color="#666666",
        ).pack(anchor="w", pady=(0, 15))

        # ===== FILTRE DE PERIODE =====
        periode_frame = ctk.CTkFrame(self.scroll, fg_color="white", corner_radius=10)
        periode_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            periode_frame,
            text="Periode de l'exercice",
            font=("Segoe UI", 12, "bold"),
            text_color=COLOR_NAVY,
        ).pack(anchor="w", padx=15, pady=(12, 8))

        ligne_dates = ctk.CTkFrame(periode_frame, fg_color="transparent")
        ligne_dates.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkLabel(
            ligne_dates, text="Du :",
            font=("Segoe UI", 11, "bold"),
            text_color="#333333",
        ).pack(side="left")

        self.entree_debut = ctk.CTkEntry(
            ligne_dates,
            font=("Segoe UI", 11),
            width=120, height=34,
            placeholder_text="AAAA-MM-JJ",
        )
        annee = datetime.now().year
        self.entree_debut.insert(0, f"{annee}-01-01")
        self.entree_debut.pack(side="left", padx=(5, 20))

        ctk.CTkLabel(
            ligne_dates, text="Au :",
            font=("Segoe UI", 11, "bold"),
            text_color="#333333",
        ).pack(side="left")

        self.entree_fin = ctk.CTkEntry(
            ligne_dates,
            font=("Segoe UI", 11),
            width=120, height=34,
            placeholder_text="AAAA-MM-JJ",
        )
        self.entree_fin.insert(0, f"{annee}-12-31")
        self.entree_fin.pack(side="left", padx=5)

        ctk.CTkButton(
            ligne_dates,
            text="Ce mois",
            font=("Segoe UI", 10),
            fg_color="#e0e0e0",
            text_color="#333333",
            hover_color="#c0c0c0",
            width=80, height=30,
            command=self._periode_mois_actuel,
        ).pack(side="left", padx=(20, 5))

        ctk.CTkButton(
            ligne_dates,
            text="Cette annee",
            font=("Segoe UI", 10),
            fg_color="#e0e0e0",
            text_color="#333333",
            hover_color="#c0c0c0",
            width=100, height=30,
            command=self._periode_annee_actuelle,
        ).pack(side="left", padx=5)

        # ===== GRILLE D'ETATS =====
        ctk.CTkLabel(
            self.scroll,
            text="Choisissez un etat financier",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_NAVY,
        ).pack(anchor="w", pady=(5, 10))

        grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        grid.pack(fill="x", expand=False)

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(2, weight=1)

        self._creer_carte(
            grid, 0, 0,
            titre="Journal General",
            description="Toutes les ecritures comptables en ordre chronologique (debit / credit par piece).",
            couleur="#3498db",
            on_generer=self._generer_journal,
        )

        self._creer_carte(
            grid, 0, 1,
            titre="Grand Livre",
            description="Detail de tous les mouvements, classe par compte comptable SYSCOHADA.",
            couleur="#9b59b6",
            on_generer=self._generer_grand_livre,
        )

        self._creer_carte(
            grid, 0, 2,
            titre="Balance Generale",
            description="Balance a 6 colonnes : mouvements et soldes debiteurs / crediteurs.",
            couleur="#e67e22",
            on_generer=self._generer_balance,
        )

        self._creer_carte(
            grid, 1, 0,
            titre="Compte de Resultat",
            description="Produits - Charges = Resultat net de l'exercice. Vue synthetique de la performance.",
            couleur="#27ae60",
            on_generer=self._generer_compte_resultat,
        )

        self._creer_carte(
            grid, 1, 1,
            titre="Bilan",
            description="Situation patrimoniale a la date de cloture : Actif et Passif (SYSCOHADA).",
            couleur="#e74c3c",
            on_generer=self._generer_bilan,
        )

        self._creer_carte(
            grid, 1, 2,
            titre="Etat de Tresorerie",
            description="Flux d'encaissements et de decaissements de la periode, solde de tresorerie.",
            couleur="#16a085",
            on_generer=self._generer_tresorerie,
        )

        # ===== BILAN INITIAL + SUIVI BUDGETAIRE (admin/gestionnaire uniquement) =====
        if self._peut_gerer_bilan_initial():
            self._creer_carte(
                grid, 2, 0,
                titre="Bilan initial",
                description="Situation de depart de l'ecole. Affiche les comptes saisis dans Parametres > Bilan initial.",
                couleur="#8e44ad",
                on_generer=self._afficher_bilan_initial,
            )

            self._creer_carte(
                grid, 2, 1,
                titre="Suivi budgetaire",
                description="Comparaison Prevu / Reel / Ecart pour chaque budget et chaque sous-categorie.",
                couleur="#16a085",
                on_generer=self._afficher_suivi_budgetaire,
            )

    def _creer_carte(self, parent, row, col, titre, description, couleur, on_generer):
        carte = ctk.CTkFrame(parent, fg_color="white", corner_radius=12,
                             border_width=2, border_color=couleur)
        carte.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        ctk.CTkLabel(
            carte, text=titre,
            font=("Segoe UI", 13, "bold"),
            text_color=couleur,
            wraplength=250,
        ).pack(pady=(15, 6), padx=10)

        ctk.CTkLabel(
            carte, text=description,
            font=("Segoe UI", 10),
            text_color="#666666",
            wraplength=250,
            justify="left",
        ).pack(padx=10, pady=(0, 10), fill="both", expand=True)

        ctk.CTkButton(
            carte,
            text="Generer",
            font=("Segoe UI", 12, "bold"),
            fg_color=couleur,
            hover_color=couleur,
            height=38,
            command=on_generer,
        ).pack(padx=10, pady=(0, 15), fill="x")

    # ================== PERIODES RAPIDES ==================
    def _periode_mois_actuel(self):
        now = datetime.now()
        debut = now.replace(day=1).strftime("%Y-%m-%d")
        fin = now.strftime("%Y-%m-%d")

        self.entree_debut.delete(0, "end")
        self.entree_debut.insert(0, debut)
        self.entree_fin.delete(0, "end")
        self.entree_fin.insert(0, fin)

    def _periode_annee_actuelle(self):
        annee = datetime.now().year
        self.entree_debut.delete(0, "end")
        self.entree_debut.insert(0, f"{annee}-01-01")
        self.entree_fin.delete(0, "end")
        self.entree_fin.insert(0, f"{annee}-12-31")

    def _get_periode(self):
        debut = self.entree_debut.get().strip()
        fin = self.entree_fin.get().strip()

        if not debut or not fin:
            messagebox.showerror("Erreur", "Veuillez saisir les 2 dates (debut et fin).")
            return None, None

        try:
            datetime.strptime(debut, "%Y-%m-%d")
            datetime.strptime(fin, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror(
                "Format invalide",
                "Format attendu : AAAA-MM-JJ\n\n"
                "Exemple : 2025-01-01"
            )
            return None, None

        return debut, fin

    # ================== GENERATION ==================
    def _generer_journal(self):
        debut, fin = self._get_periode()
        if not debut:
            return
        try:
            donnees = etat_journal(debut, fin)
            chemin = pdf_journal(donnees)
            PdfViewerWindow(self, chemin, titre="Journal General")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def _generer_grand_livre(self):
        debut, fin = self._get_periode()
        if not debut:
            return
        try:
            donnees = etat_grand_livre(debut, fin)
            chemin = pdf_grand_livre(donnees)
            PdfViewerWindow(self, chemin, titre="Grand Livre")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def _generer_balance(self):
        debut, fin = self._get_periode()
        if not debut:
            return
        try:
            donnees = etat_balance(debut, fin)
            chemin = pdf_balance(donnees)
            PdfViewerWindow(self, chemin, titre="Balance Generale")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def _generer_compte_resultat(self):
        debut, fin = self._get_periode()
        if not debut:
            return
        try:
            donnees = etat_compte_resultat(debut, fin)
            chemin = pdf_compte_resultat(donnees)
            PdfViewerWindow(self, chemin, titre="Compte de Resultat")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def _generer_bilan(self):
        debut, fin = self._get_periode()
        if not debut:
            return
        try:
            donnees = etat_bilan(debut, fin)
            chemin = pdf_bilan(donnees)
            PdfViewerWindow(self, chemin, titre="Bilan")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def _generer_tresorerie(self):
        debut, fin = self._get_periode()
        if not debut:
            return
        try:
            donnees = etat_tresorerie(debut, fin)
            chemin = pdf_tresorerie(donnees)
            PdfViewerWindow(self, chemin, titre="Etat de Tresorerie")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")

    # ================== BILAN INITIAL ==================
    def _afficher_bilan_initial(self):
        if not self._peut_gerer_bilan_initial():
            messagebox.showerror("Acces refuse",
                                 "Seul un administrateur peut voir le bilan initial.")
            return
        try:
            data = get_bilan_initial()

            if not data.get("actif") and not data.get("passif"):
                messagebox.showinfo(
                    "Bilan initial vide",
                    "Aucun compte n'a ete saisi dans le bilan initial.\n\n"
                    "Allez dans Parametres > Bilan initial pour saisir vos comptes."
                )
                return

            BilanInitialViewer(self, data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")

    # ================== SUIVI BUDGETAIRE ==================
    def _afficher_suivi_budgetaire(self):
        if not self._peut_gerer_bilan_initial():
            messagebox.showerror("Acces refuse",
                                 "Seul un administrateur peut voir le suivi budgetaire.")
            return
        try:
            SuiviBudgetaireWindow(self)
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")


# ============================================================
# FENETRE D'AFFICHAGE DU BILAN INITIAL (inchangee)
# ============================================================
class BilanInitialViewer(ctk.CTkToplevel):
    def __init__(self, parent, data):
        super().__init__(parent)

        self.data = data

        self.title("Bilan initial")
        largeur = 900
        hauteur = 720
        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#F5F7FB")

        x = (self.winfo_screenwidth() // 2) - (largeur // 2)
        y = max(20, (self.winfo_screenheight() // 2) - (hauteur // 2))
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")

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
        header = ctk.CTkFrame(self, fg_color=COLOR_NAVY, corner_radius=0, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="BILAN INITIAL",
            font=("Segoe UI", 20, "bold"),
            text_color="white",
        ).pack(pady=20)

        corps = ctk.CTkScrollableFrame(self, fg_color="transparent")
        corps.pack(fill="both", expand=True, padx=15, pady=15)

        colonnes = ctk.CTkFrame(corps, fg_color="transparent")
        colonnes.pack(fill="both", expand=True)
        colonnes.columnconfigure(0, weight=1, uniform="col")
        colonnes.columnconfigure(1, weight=1, uniform="col")

        cadre_actif = ctk.CTkFrame(colonnes, fg_color="white", corner_radius=10)
        cadre_actif.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            cadre_actif, text="ACTIF",
            font=("Segoe UI", 15, "bold"),
            text_color="#1e7e34",
        ).pack(pady=(15, 10))

        actif = self.data.get("actif", {})
        if actif:
            for code in sorted(actif.keys()):
                self._ligne(cadre_actif, code, get_libelle(code), actif[code])
        else:
            ctk.CTkLabel(
                cadre_actif, text="Aucun compte d'actif",
                font=("Segoe UI", 10),
                text_color="#999999",
            ).pack(pady=20)

        ctk.CTkFrame(cadre_actif, fg_color="#e0e0e0", height=2).pack(
            fill="x", padx=15, pady=10
        )

        ctk.CTkLabel(
            cadre_actif,
            text=f"TOTAL ACTIF : {format_montant(total_actif())}",
            font=("Segoe UI", 13, "bold"),
            text_color="#1e7e34",
        ).pack(pady=(5, 15))

        cadre_passif = ctk.CTkFrame(colonnes, fg_color="white", corner_radius=10)
        cadre_passif.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(
            cadre_passif, text="PASSIF",
            font=("Segoe UI", 15, "bold"),
            text_color="#c0392b",
        ).pack(pady=(15, 10))

        passif = self.data.get("passif", {})
        if passif:
            for code in sorted(passif.keys()):
                self._ligne(cadre_passif, code, get_libelle(code), passif[code])
        else:
            ctk.CTkLabel(
                cadre_passif, text="Aucun compte de passif",
                font=("Segoe UI", 10),
                text_color="#999999",
            ).pack(pady=20)

        ctk.CTkFrame(cadre_passif, fg_color="#e0e0e0", height=2).pack(
            fill="x", padx=15, pady=10
        )

        ctk.CTkLabel(
            cadre_passif,
            text=f"TOTAL PASSIF : {format_montant(total_passif())}",
            font=("Segoe UI", 13, "bold"),
            text_color="#c0392b",
        ).pack(pady=(5, 15))

        cadre_cp = ctk.CTkFrame(corps, fg_color="#F0F7FF", corner_radius=10)
        cadre_cp.pack(fill="x", pady=(15, 0))

        cp = capitaux_propres()
        couleur_cp = "#27ae60" if cp >= 0 else "#e74c3c"

        ctk.CTkLabel(
            cadre_cp, text="CAPITAUX PROPRES",
            font=("Segoe UI", 13, "bold"),
            text_color=COLOR_NAVY,
        ).pack(pady=(15, 3))

        ctk.CTkLabel(
            cadre_cp, text="(Total Actif - Total Passif)",
            font=("Segoe UI", 9),
            text_color="#666666",
        ).pack()

        ctk.CTkLabel(
            cadre_cp, text=format_montant(cp),
            font=("Segoe UI", 22, "bold"),
            text_color=couleur_cp,
        ).pack(pady=(5, 15))

        boutons = ctk.CTkFrame(self, fg_color="transparent")
        boutons.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            boutons, text="Exporter en PDF",
            font=("Segoe UI", 12, "bold"),
            fg_color="#3498db", hover_color="#2980b9",
            height=42,
            command=self._export_pdf,
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(
            boutons, text="Fermer",
            font=("Segoe UI", 12),
            fg_color="#e0e0e0", text_color="#333333",
            hover_color="#c0c0c0",
            height=42,
            command=self.destroy,
        ).pack(side="left", expand=True, fill="x", padx=(5, 0))

    def _ligne(self, parent, code, libelle, montant):
        ligne = ctk.CTkFrame(parent, fg_color="transparent")
        ligne.pack(fill="x", padx=15, pady=3)

        ctk.CTkLabel(
            ligne, text=code,
            font=("Consolas", 11, "bold"),
            text_color=COLOR_NAVY,
            width=40, anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            ligne, text=libelle,
            font=("Segoe UI", 10),
            text_color="#333333",
            anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))

        ctk.CTkLabel(
            ligne, text=format_montant(montant),
            font=("Segoe UI", 11, "bold"),
            text_color="#333333",
            width=130, anchor="e",
        ).pack(side="right")

    def _export_pdf(self):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
            )
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER

            dossier = os.path.join(DATA_DIR, "rapports")
            os.makedirs(dossier, exist_ok=True)

            nom = f"Bilan_initial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            chemin = os.path.join(dossier, nom)

            doc = SimpleDocTemplate(
                chemin, pagesize=A4,
                leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                topMargin=1.5 * cm, bottomMargin=1.5 * cm,
            )

            styles = getSampleStyleSheet()
            titre_style = ParagraphStyle(
                'Titre', parent=styles['Heading1'],
                alignment=TA_CENTER, fontSize=16, spaceAfter=20,
                textColor=colors.HexColor("#0F2C5C"),
            )

            elements = []
            elements.append(Paragraph("BILAN INITIAL", titre_style))
            elements.append(Spacer(1, 0.3 * cm))

            actif = self.data.get("actif", {})
            passif = self.data.get("passif", {})
            actif_items = sorted(actif.items())
            passif_items = sorted(passif.items())

            data_tab = [["ACTIF", "Montant", "PASSIF", "Montant"]]

            max_len = max(len(actif_items), len(passif_items))
            for i in range(max_len):
                if i < len(actif_items):
                    c, m = actif_items[i]
                    a_txt = f"{c} {get_libelle(c)}"
                    a_m = format_montant(m)
                else:
                    a_txt, a_m = "", ""

                if i < len(passif_items):
                    c, m = passif_items[i]
                    p_txt = f"{c} {get_libelle(c)}"
                    p_m = format_montant(m)
                else:
                    p_txt, p_m = "", ""

                data_tab.append([a_txt, a_m, p_txt, p_m])

            data_tab.append([
                "TOTAL ACTIF", format_montant(total_actif()),
                "TOTAL PASSIF", format_montant(total_passif()),
            ])

            cp = capitaux_propres()
            data_tab.append([
                "CAPITAUX PROPRES", format_montant(cp), "", "",
            ])

            t = Table(data_tab, colWidths=[6.5 * cm, 3 * cm, 6.5 * cm, 3 * cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F2C5C")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('FONTNAME', (0, -2), (-1, -2), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -2), (-1, -2), colors.HexColor("#E8F4EA")),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#F0F7FF")),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(t)

            doc.build(elements)

            PdfViewerWindow(self, chemin, titre="Bilan initial")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur PDF", f"Erreur : {e}")