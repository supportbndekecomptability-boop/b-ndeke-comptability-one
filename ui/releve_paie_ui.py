"""
Releve de paie - Generation PDF imprimable
"""
import os
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from config import COLOR_NAVY, format_montant, DATA_DIR
from core.personnel import get_personnel
from core.avances import total_avance_en_cours
from database import get_connection
from core.ecole import get_info_ecole, get_logo_path


class RelevePaieWindow(ctk.CTkToplevel):
    def __init__(self, parent, personnel):
        super().__init__(parent)

        self.personnel = personnel
        self.info_ecole = get_info_ecole()
        self.logo_path = get_logo_path()

        self.title(f"Releve de paie - {personnel['nom']} {personnel['prenom']}")
        largeur = min(900, self.winfo_screenwidth() - 60)
        hauteur = min(700, self.winfo_screenheight() - 100)

        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        x = (self.winfo_screenwidth() // 2) - (largeur // 2)
        y = max(10, (self.winfo_screenheight() // 2) - (hauteur // 2) - 20)
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
        # ===== HEADER =====
        header = ctk.CTkFrame(self, fg_color=COLOR_NAVY, corner_radius=0, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="RELEVE DE PAIE",
            font=("Segoe UI", 16, "bold"),
            text_color="white",
        ).pack(side="left", padx=20, pady=15)

        ctk.CTkButton(
            header, text="Fermer",
            font=("Segoe UI", 11),
            fg_color="#e74c3c", hover_color="#c0392b",
            width=90, height=32,
            command=self.destroy,
        ).pack(side="right", padx=(5, 20), pady=14)

        ctk.CTkButton(
            header, text="Imprimer (PDF)",
            font=("Segoe UI", 11, "bold"),
            fg_color="#27ae60", hover_color="#229954",
            width=140, height=32,
            command=self._imprimer,
        ).pack(side="right", padx=5, pady=14)

        # ===== CORPS =====
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=15)

        self._afficher_apercu(scroll)

    def _get_paiements(self):
        """Recupere l'historique des paiements de cet employe."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT numero_paie, date_paiement, montant, motif,
                       mode_paiement, COALESCE(montant_avance_deduit, 0) as montant_avance_deduit
                FROM paiements_personnel
                WHERE personnel_id = ?
                ORDER BY date_paiement DESC
            """, (self.personnel["id"],))
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            print(f"[RELEVE] Erreur : {e}")
            return []

    def _afficher_apercu(self, parent):
        p = self.personnel

        # ===== CARTE PRINCIPALE =====
        carte = ctk.CTkFrame(parent, fg_color="white", corner_radius=10)
        carte.pack(fill="x", pady=(0, 15))

        # En-tete ecole
        entete = ctk.CTkFrame(carte, fg_color="transparent")
        entete.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            entete, text=self.info_ecole.get("nom", "Ecole"),
            font=("Segoe UI", 16, "bold"),
            text_color=COLOR_NAVY,
        ).pack()

        adresse = self.info_ecole.get("adresse", "")
        tel = self.info_ecole.get("telephone", "")
        if adresse or tel:
            ctk.CTkLabel(
                entete, text=f"{adresse}  |  {tel}",
                font=("Segoe UI", 10),
                text_color="#666666",
            ).pack(pady=(3, 0))

        ctk.CTkFrame(carte, fg_color="#e0e0e0", height=1).pack(fill="x", padx=20, pady=(10, 15))

        # Info employe
        infos = ctk.CTkFrame(carte, fg_color="transparent")
        infos.pack(fill="x", padx=20, pady=(0, 15))

        ligne1 = ctk.CTkFrame(infos, fg_color="transparent")
        ligne1.pack(fill="x", pady=3)

        ctk.CTkLabel(ligne1, text="Code :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#666666", width=120, anchor="w").pack(side="left")
        ctk.CTkLabel(ligne1, text=p.get("code", ""),
                     font=("Consolas", 11, "bold"),
                     text_color="#0066CC", anchor="w").pack(side="left")

        ligne2 = ctk.CTkFrame(infos, fg_color="transparent")
        ligne2.pack(fill="x", pady=3)

        ctk.CTkLabel(ligne2, text="Nom complet :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#666666", width=120, anchor="w").pack(side="left")
        ctk.CTkLabel(ligne2, text=f"{p.get('nom', '')} {p.get('prenom', '')}",
                     font=("Segoe UI", 11), text_color="#333333", anchor="w").pack(side="left")

        ligne3 = ctk.CTkFrame(infos, fg_color="transparent")
        ligne3.pack(fill="x", pady=3)

        ctk.CTkLabel(ligne3, text="Fonction :",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#666666", width=120, anchor="w").pack(side="left")
        ctk.CTkLabel(ligne3, text=p.get("fonction", ""),
                     font=("Segoe UI", 11), text_color="#333333", anchor="w").pack(side="left")

        # ===== SALAIRE ET ENGAGEMENT =====
        ctk.CTkLabel(carte, text="SALAIRE ET ENGAGEMENT",
                     font=("Segoe UI", 11, "bold"),
                     text_color=COLOR_NAVY, anchor="w").pack(padx=20, pady=(10, 5), fill="x")

        salaire = p.get("salaire_mensuel", 0) or 0
        duree = p.get("duree_contrat_mois", 12) or 12
        engagement = salaire * duree

        paiements = self._get_paiements()
        total_paye = sum(pp["montant"] for pp in paiements)
        total_avance_deduit = sum(pp.get("montant_avance_deduit", 0) or 0 for pp in paiements)
        reste = engagement - total_paye
        avance_en_cours = total_avance_en_cours(p["id"])

        for label, valeur, couleur in [
            ("Salaire mensuel", format_montant(salaire), "#333333"),
            ("Duree du contrat", f"{duree} mois", "#333333"),
            ("Engagement total", format_montant(engagement), "#8e44ad"),
            ("Total paye", format_montant(total_paye), "#27ae60"),
            ("Total avance deduit", format_montant(total_avance_deduit), "#e67e22"),
            ("Reste a payer", format_montant(reste),
             "#e74c3c" if reste > 0 else "#27ae60"),
            ("Avance en cours", format_montant(avance_en_cours),
             "#e67e22" if avance_en_cours > 0.01 else "#999999"),
        ]:
            ligne = ctk.CTkFrame(carte, fg_color="transparent")
            ligne.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(ligne, text=label,
                         font=("Segoe UI", 11), text_color="#666666",
                         anchor="w").pack(side="left")
            ctk.CTkLabel(ligne, text=valeur,
                         font=("Segoe UI", 11, "bold"), text_color=couleur,
                         anchor="e").pack(side="right")

        ctk.CTkFrame(carte, fg_color="#e0e0e0", height=1).pack(fill="x", padx=20, pady=(10, 10))

        # ===== HISTORIQUE DES PAIEMENTS =====
        ctk.CTkLabel(carte, text="HISTORIQUE DES PAIEMENTS",
                     font=("Segoe UI", 11, "bold"),
                     text_color=COLOR_NAVY, anchor="w").pack(padx=20, pady=(5, 5), fill="x")

        if not paiements:
            ctk.CTkLabel(carte, text="Aucun paiement enregistre.",
                         font=("Segoe UI", 10), text_color="#999999",
                         anchor="w").pack(padx=20, pady=(0, 15), fill="x")
        else:
            # Entete tableau
            entete_tab = ctk.CTkFrame(carte, fg_color="#f0f0f0", corner_radius=4)
            entete_tab.pack(fill="x", padx=20, pady=(0, 3))

            for nom, larg in [
                ("Numero", 100),
                ("Date", 100),
                ("Motif", 150),
                ("Brut", 100),
                ("Avance", 100),
                ("Net verse", 100),
            ]:
                ctk.CTkLabel(
                    entete_tab, text=nom,
                    font=("Segoe UI", 10, "bold"),
                    text_color=COLOR_NAVY, width=larg, anchor="w",
                ).pack(side="left", padx=3, pady=6)

            for pp in paiements[:20]:  # max 20 lignes dans l'apercu
                ligne = ctk.CTkFrame(carte, fg_color="#fafafa", corner_radius=4)
                ligne.pack(fill="x", padx=20, pady=1)

                date_str = str(pp["date_paiement"])[:10]
                brut = pp["montant"]
                avance_deduite = pp.get("montant_avance_deduit", 0) or 0
                net = brut - avance_deduite

                for val, larg, coul, poids in [
                    (pp["numero_paie"], 100, "#0066CC", "bold"),
                    (date_str, 100, "#333333", "normal"),
                    (pp["motif"][:20], 150, "#333333", "normal"),
                    (format_montant(brut), 100, "#333333", "normal"),
                    (format_montant(avance_deduite), 100, "#e67e22", "normal"),
                    (format_montant(net), 100, "#27ae60", "bold"),
                ]:
                    ctk.CTkLabel(ligne, text=str(val),
                                 font=("Segoe UI", 10, poids),
                                 text_color=coul,
                                 width=larg, anchor="w").pack(side="left", padx=3, pady=5)

        ctk.CTkLabel(carte, text="").pack(pady=5)

    # =========================================================
    # IMPRIMER (PDF)
    # =========================================================
    def _imprimer(self):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image,
            )
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

            dossier = os.path.join(DATA_DIR, "rapports")
            os.makedirs(dossier, exist_ok=True)

            nom_fichier = (
                f"Releve_paie_{self.personnel['code']}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            chemin = os.path.join(dossier, nom_fichier)

            doc = SimpleDocTemplate(
                chemin, pagesize=A4,
                leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                topMargin=1.5 * cm, bottomMargin=1.5 * cm,
            )

            styles = getSampleStyleSheet()
            titre_style = ParagraphStyle(
                'Titre', parent=styles['Heading1'],
                alignment=TA_CENTER, fontSize=16, spaceAfter=6,
                textColor=colors.HexColor("#0F2C5C"),
            )
            sous_style = ParagraphStyle(
                'Sous', parent=styles['Normal'],
                alignment=TA_CENTER, fontSize=9,
                textColor=colors.grey, spaceAfter=15,
            )
            section_style = ParagraphStyle(
                'Section', parent=styles['Heading2'],
                fontSize=11, spaceBefore=10, spaceAfter=6,
                textColor=colors.HexColor("#0F2C5C"),
            )

            elements = []

            # En-tete avec logo
            if self.logo_path and os.path.exists(self.logo_path):
                try:
                    img = Image(self.logo_path, width=2.5 * cm, height=2.5 * cm)
                    img.hAlign = 'CENTER'
                    elements.append(img)
                    elements.append(Spacer(1, 0.2 * cm))
                except Exception:
                    pass

            elements.append(Paragraph(
                self.info_ecole.get("nom", "Ecole"),
                titre_style
            ))

            adresse = self.info_ecole.get("adresse", "")
            tel = self.info_ecole.get("telephone", "")
            ligne_contact = " | ".join(filter(None, [adresse, tel]))
            if ligne_contact:
                elements.append(Paragraph(ligne_contact, sous_style))

            elements.append(Paragraph(
                "<b>RELEVE DE PAIE</b>",
                ParagraphStyle('TitreR', parent=titre_style, fontSize=14)
            ))
            elements.append(Spacer(1, 0.5 * cm))

            # Info employe
            p = self.personnel
            data_emp = [
                ["Code employe :", p.get("code", "")],
                ["Nom complet :", f"{p.get('nom', '')} {p.get('prenom', '')}"],
                ["Fonction :", p.get("fonction", "")],
                ["Date du releve :", datetime.now().strftime("%d/%m/%Y")],
            ]

            t_emp = Table(data_emp, colWidths=[4 * cm, 12 * cm])
            t_emp.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (0, -1), 10),
                ('FONTSIZE', (1, 0), (1, -1), 10),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor("#666666")),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_emp)
            elements.append(Spacer(1, 0.7 * cm))

            # Salaire et engagement
            elements.append(Paragraph("SALAIRE ET ENGAGEMENT", section_style))

            salaire = p.get("salaire_mensuel", 0) or 0
            duree = p.get("duree_contrat_mois", 12) or 12
            engagement = salaire * duree

            paiements = self._get_paiements()
            total_paye = sum(pp["montant"] for pp in paiements)
            total_avance_deduit = sum(pp.get("montant_avance_deduit", 0) or 0 for pp in paiements)
            reste = engagement - total_paye
            avance_en_cours = total_avance_en_cours(p["id"])

            data_sal = [
                ["Salaire mensuel", format_montant(salaire)],
                ["Duree du contrat", f"{duree} mois"],
                ["Engagement total", format_montant(engagement)],
                ["Total paye", format_montant(total_paye)],
                ["Total avance deduit", format_montant(total_avance_deduit)],
                ["Reste a payer", format_montant(reste)],
                ["Avance en cours", format_montant(avance_en_cours)],
            ]

            t_sal = Table(data_sal, colWidths=[10 * cm, 6 * cm])
            t_sal.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F5F5F5")),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(t_sal)
            elements.append(Spacer(1, 0.7 * cm))

            # Historique des paiements
            elements.append(Paragraph("HISTORIQUE DES PAIEMENTS", section_style))

            if not paiements:
                elements.append(Paragraph(
                    "Aucun paiement enregistre.",
                    ParagraphStyle('norm', parent=styles['Normal'], fontSize=10,
                                   textColor=colors.grey)
                ))
            else:
                data_hist = [["Numero", "Date", "Motif", "Brut",
                              "Avance", "Net verse"]]

                for pp in paiements:
                    date_str = str(pp["date_paiement"])[:10]
                    brut = pp["montant"]
                    avance_deduite = pp.get("montant_avance_deduit", 0) or 0
                    net = brut - avance_deduite

                    data_hist.append([
                        pp["numero_paie"],
                        date_str,
                        pp["motif"][:25],
                        format_montant(brut),
                        format_montant(avance_deduite),
                        format_montant(net),
                    ])

                # Ligne de total
                data_hist.append([
                    "", "", "TOTAL",
                    format_montant(total_paye),
                    format_montant(total_avance_deduit),
                    format_montant(total_paye - total_avance_deduit),
                ])

                t_hist = Table(data_hist, colWidths=[2.5 * cm, 2.5 * cm, 4.5 * cm,
                                                      2.5 * cm, 2 * cm, 2.5 * cm])
                t_hist.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F2C5C")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#E8F4EA")),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(t_hist)

            # Pied de page
            elements.append(Spacer(1, 1.5 * cm))
            elements.append(Paragraph(
                f"<i>Document genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')} "
                f"par B-NDEKE Comptability One</i>",
                ParagraphStyle('pied', parent=styles['Normal'],
                               alignment=TA_CENTER, fontSize=8,
                               textColor=colors.grey)
            ))

            doc.build(elements)

            # Ouvrir le PDF
            from ui.pdf_viewer import PdfViewerWindow
            PdfViewerWindow(self, chemin, titre="Releve de paie")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur : {e}")