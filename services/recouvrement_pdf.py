"""
Generation de la liste de recouvrement en PDF
Mode : Eleves qui n'ont pas encore paye X
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import Image as RLImage

from config import RAPPORTS_DIR, format_montant
from core.ecole import get_info_ecole_pour_pdf

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

NAVY = colors.HexColor("#0F2C5C")
GOLD = colors.HexColor("#F2B705")
RED = colors.HexColor("#e74c3c")
GREEN = colors.HexColor("#27ae60")
GREY = colors.HexColor("#666666")
LIGHT_GREY = colors.HexColor("#f0f0f0")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TitreRec", fontName="Helvetica-Bold", fontSize=16,
        textColor=NAVY, alignment=TA_CENTER, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="SousTitreRec", fontName="Helvetica", fontSize=10,
        textColor=GREY, alignment=TA_CENTER, spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="InfoEcole", fontName="Helvetica", fontSize=8,
        textColor=GREY, alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="Section", fontName="Helvetica-Bold", fontSize=11,
        textColor=NAVY, spaceBefore=8, spaceAfter=4,
    ))
    return styles


def _entete(story, styles, titre, sous_titre=""):
    info = get_info_ecole_pour_pdf()

    if info.get("logo_path") and PIL_OK:
        try:
            img = Image.open(info["logo_path"])
            ratio = img.width / img.height if img.height else 1
            h = 1.6 * cm
            l = h * ratio
            logo = RLImage(info["logo_path"], width=l, height=h)

            txt_html = f"<b><font size=12 color='#0F2C5C'>{info['nom']}</font></b><br/>"
            if info.get("adresse"):
                txt_html += f"<font size=8 color='#666666'>{info['adresse']}</font><br/>"
            contacts = []
            if info.get("telephone"):
                contacts.append(f"Tel : {info['telephone']}")
            if info.get("email"):
                contacts.append(f"{info['email']}")
            if contacts:
                txt_html += f"<font size=8 color='#666666'>{' | '.join(contacts)}</font>"

            txt = Paragraph(txt_html, styles["InfoEcole"])

            t = Table([[logo, txt]],
                      colWidths=[l + 0.4 * cm, 18 * cm - l - 0.4 * cm])
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(t)
        except Exception as e:
            print(f"[Erreur logo] {e}")
            story.append(Paragraph(info["nom"], styles["TitreRec"]))
    else:
        story.append(Paragraph(info["nom"], styles["TitreRec"]))
        if info.get("adresse"):
            story.append(Paragraph(info["adresse"], styles["InfoEcole"]))
        contacts = []
        if info.get("telephone"):
            contacts.append(f"Tel : {info['telephone']}")
        if info.get("email"):
            contacts.append(f"{info['email']}")
        if contacts:
            story.append(Paragraph(" | ".join(contacts), styles["InfoEcole"]))

    story.append(Spacer(1, 0.3 * cm))

    ligne = Table([[""]], colWidths=[18 * cm], rowHeights=[2])
    ligne.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY)]))
    story.append(ligne)
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(titre, styles["TitreRec"]))
    if sous_titre:
        story.append(Paragraph(sous_titre, styles["SousTitreRec"]))


def _footer(canvas, doc):
    info = get_info_ecole_pour_pdf()
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GREY)
    canvas.drawString(
        1.5 * cm, 0.8 * cm,
        f"{info['nom']} - Liste de recouvrement - "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M')}",
    )
    canvas.drawRightString(19.5 * cm, 0.8 * cm, f"Page {doc.page}")
    canvas.restoreState()


def generer_liste_recouvrement(eleves, montant_min_paye=0, classe=None):
    """Genere le PDF de la liste de recouvrement"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom_fichier = f"recouvrement_{timestamp}.pdf"
    chemin = os.path.join(RAPPORTS_DIR, nom_fichier)

    doc = SimpleDocTemplate(
        chemin, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.2 * cm, bottomMargin=1.5 * cm,
        title="Liste de recouvrement",
        author="B-NDEKE Comptability One",
    )

    styles = _styles()
    story = []

    # Sous-titre
    sous_titre = f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}"
    if montant_min_paye > 0:
        sous_titre += f"  |  Critere : n'ont pas paye {format_montant(montant_min_paye)}"
    if classe:
        sous_titre += f"  |  Classe : {classe}"

    _entete(story, styles, "LISTE DE RECOUVREMENT", sous_titre)

    # ===== STATS =====
    if eleves:
        total_du = sum(e["solde"] for e in eleves)
        total_paye = sum(e["total_paye"] for e in eleves)
        total_manquant = sum(e["manquant"] for e in eleves)

        stats_data = [
            ["Nombre d'eleves concernes", str(len(eleves))],
            ["Total DEJA PAYE par ces eleves", format_montant(total_paye)],
            ["Ce qu'ils doivent encore atteindre", format_montant(total_manquant)],
            ["Total des soldes restants", format_montant(total_du)],
        ]
        stats_tbl = Table(stats_data, colWidths=[8 * cm, 10 * cm])
        stats_tbl.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TEXTCOLOR", (0, 0), (0, -1), GREY),
            ("TEXTCOLOR", (1, 0), (1, 0), NAVY),
            ("TEXTCOLOR", (1, 1), (1, 1), GREEN),
            ("TEXTCOLOR", (1, 2), (1, 2), "#e67e22"),
            ("TEXTCOLOR", (1, 3), (1, 3), RED),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF4F4")),
            ("BOX", (0, 0), (-1, -1), 0.5, RED),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, LIGHT_GREY),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(stats_tbl)
        story.append(Spacer(1, 0.5 * cm))
    else:
        story.append(Paragraph(
            "Aucun eleve ne correspond aux criteres.",
            styles["Section"],
        ))

    # ===== TABLEAU =====
    if eleves:
        entetes = [
            "N°", "Matricule", "Nom & Prenom", "Classe",
            "Parent", "Telephone", "Frais", "Paye", "Reste",
        ]
        lignes = []

        for i, e in enumerate(eleves, 1):
            nom_complet = f"{e['nom']} {e['prenom']}"
            lignes.append([
                str(i),
                e["matricule"],
                nom_complet[:25],
                e["classe"][:12],
                (e.get("nom_parent") or "-")[:20],
                (e.get("telephone_parent") or "-")[:15],
                format_montant(e["frais_totaux"]),
                format_montant(e["total_paye"]),
                format_montant(e["solde"]),
            ])

        # Ligne de total
        total_du = sum(e["solde"] for e in eleves)
        total_paye = sum(e["total_paye"] for e in eleves)
        footer = [
            "", "", "", "", "", "TOTAUX",
            "", format_montant(total_paye), format_montant(total_du),
        ]

        data = [entetes] + lignes + [footer]

        largeurs = [
            0.9 * cm, 2.4 * cm, 4 * cm, 2.2 * cm,
            3.4 * cm, 2.6 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm,
        ]

        tbl = Table(data, colWidths=largeurs, repeatRows=1)
        style = [
            # En-tete
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            # Corps
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -2), 8),
            ("GRID", (0, 0), (-1, -1), 0.25, GREY),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            # Colonne Paye en vert
            ("TEXTCOLOR", (7, 1), (7, -2), GREEN),
            # Colonne Reste en rouge
            ("TEXTCOLOR", (8, 1), (8, -2), RED),
            ("FONTNAME", (8, 1), (8, -2), "Helvetica-Bold"),
            # Ligne de total
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#FFF4F4")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, -1), (-1, -1), 10),
            ("TEXTCOLOR", (7, -1), (7, -1), GREEN),
            ("TEXTCOLOR", (8, -1), (8, -1), RED),
        ]

        for i in range(1, len(lignes) + 1):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i),
                              colors.HexColor("#fafafa")))

        tbl.setStyle(TableStyle(style))
        story.append(tbl)
        story.append(Spacer(1, 1 * cm))

        # ===== ZONE AGENT =====
        agent_data = [
            ["Agent de recouvrement :", "___________________________________"],
            ["Signature :", "___________________________________"],
            ["Date :", "___ / ___ / _______"],
        ]
        agent_tbl = Table(agent_data, colWidths=[4.5 * cm, 8 * cm])
        agent_tbl.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(agent_tbl)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return chemin