"""
Generation des recus de paiement (Eleves + Personnel) en PDF
Format compact A5 (petit recu professionnel)
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import A5
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import Image as RLImage

from config import PDF_DIR, format_montant
from core.ecole import get_info_ecole_pour_pdf

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

NAVY = colors.HexColor("#0F2C5C")
GOLD = colors.HexColor("#F2B705")
GREEN = colors.HexColor("#27ae60")
RED = colors.HexColor("#e74c3c")
GREY = colors.HexColor("#666666")
LIGHT_GREY = colors.HexColor("#f0f0f0")

# Largeur utile A5 avec marges 1 cm = 12.8 cm
LARGEUR_UTILE = 12.8 * cm


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TitreRecu", fontName="Helvetica-Bold", fontSize=16,
        textColor=NAVY, alignment=TA_CENTER, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="SousTitreRecu", fontName="Helvetica", fontSize=9,
        textColor=GREY, alignment=TA_CENTER, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="InfoEcole", fontName="Helvetica", fontSize=8,
        textColor=GREY, alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="Label", fontName="Helvetica-Bold", fontSize=8,
        textColor=GREY,
    ))
    styles.add(ParagraphStyle(
        name="Valeur", fontName="Helvetica", fontSize=9,
        textColor=NAVY,
    ))
    styles.add(ParagraphStyle(
        name="MontantGros", fontName="Helvetica-Bold", fontSize=15,
        textColor=GREEN, alignment=TA_RIGHT,
    ))
    styles.add(ParagraphStyle(
        name="Section", fontName="Helvetica-Bold", fontSize=9,
        textColor=NAVY, spaceBefore=4, spaceAfter=3,
    ))
    return styles


def _entete_ecole(story, styles):
    """En-tete compact avec logo + infos ecole"""
    info = get_info_ecole_pour_pdf()

    if info.get("logo_path") and PIL_OK:
        try:
            img = Image.open(info["logo_path"])
            ratio = img.width / img.height if img.height else 1
            hauteur_logo = 1.4 * cm
            largeur_logo = hauteur_logo * ratio

            logo = RLImage(info["logo_path"],
                           width=largeur_logo, height=hauteur_logo)

            texte_html = f"<b><font size=11 color='#0F2C5C'>{info['nom']}</font></b><br/>"
            if info.get("adresse"):
                texte_html += f"<font size=7 color='#666666'>{info['adresse']}</font><br/>"
            contacts = []
            if info.get("telephone"):
                contacts.append(f"Tel : {info['telephone']}")
            if info.get("email"):
                contacts.append(f"{info['email']}")
            if contacts:
                texte_html += f"<font size=7 color='#666666'>{' | '.join(contacts)}</font>"

            txt = Paragraph(texte_html, styles["InfoEcole"])

            tbl = Table(
                [[logo, txt]],
                colWidths=[largeur_logo + 0.3 * cm,
                           LARGEUR_UTILE - largeur_logo - 0.3 * cm],
            )
            tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(tbl)
        except Exception as e:
            print(f"[Erreur logo recu] {e}")
            _entete_sans_logo(story, styles, info)
    else:
        _entete_sans_logo(story, styles, info)


def _entete_sans_logo(story, styles, info):
    story.append(Paragraph(info["nom"], styles["TitreRecu"]))
    if info.get("adresse"):
        story.append(Paragraph(info["adresse"], styles["InfoEcole"]))
    contacts = []
    if info.get("telephone"):
        contacts.append(f"Tel : {info['telephone']}")
    if info.get("email"):
        contacts.append(f"{info['email']}")
    if contacts:
        story.append(Paragraph(" | ".join(contacts), styles["InfoEcole"]))


def _footer(canvas, doc):
    info = get_info_ecole_pour_pdf()
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GREY)
    canvas.drawString(
        1 * cm, 0.6 * cm,
        f"{info['nom']}  |  {datetime.now().strftime('%d/%m/%Y %H:%M')}",
    )
    canvas.drawRightString(13.8 * cm, 0.6 * cm, "Merci")
    canvas.restoreState()


# ============================================================
# RECU POUR ELEVE (format A5 compact)
# ============================================================
def generer_recu_eleve(paiement):
    num = paiement.get("numero_recu", "REC-XXXX")
    nom_fichier = f"recu_{num}_{datetime.now().strftime('%H%M%S')}.pdf"
    chemin = os.path.join(PDF_DIR, nom_fichier)

    doc = SimpleDocTemplate(
        chemin, pagesize=A5,
        leftMargin=1 * cm, rightMargin=1 * cm,
        topMargin=0.8 * cm, bottomMargin=1 * cm,
        title=f"Recu {num}",
        author="B-NDEKE Comptability One",
    )

    styles = _styles()
    story = []

    # En-tete ecole
    _entete_ecole(story, styles)
    story.append(Spacer(1, 0.3 * cm))

    # Ligne bleue
    ligne = Table([[""]], colWidths=[LARGEUR_UTILE], rowHeights=[2])
    ligne.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY)]))
    story.append(ligne)
    story.append(Spacer(1, 0.3 * cm))

    # Titre
    story.append(Paragraph("REÇU DE PAIEMENT", styles["TitreRecu"]))
    story.append(Paragraph("ELEVE", styles["SousTitreRecu"]))

    # Numero + Date
    date_str = paiement.get("date_paiement", "")
    if date_str and len(date_str) >= 10:
        date_str = date_str[:10]

    info_tbl = Table([
        [Paragraph("<b>N° RECU</b>", styles["Label"]),
         Paragraph(f"<b>{num}</b>", styles["Valeur"]),
         Paragraph("<b>DATE</b>", styles["Label"]),
         Paragraph(f"<b>{date_str}</b>", styles["Valeur"])],
    ], colWidths=[1.8 * cm, 4.5 * cm, 1.5 * cm, 5 * cm])

    info_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0F7FF")),
        ("BOX", (0, 0), (-1, -1), 1, NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # Infos eleve
    story.append(Paragraph("INFORMATIONS DE L'ELEVE", styles["Section"]))

    eleve_tbl = Table([
        ["Matricule", paiement.get("matricule", "-")],
        ["Nom complet", f"{paiement.get('nom', '')} {paiement.get('prenom', '')}"],
        ["Classe", paiement.get("classe", "-")],
    ], colWidths=[3 * cm, 9.8 * cm])

    eleve_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), GREY),
        ("TEXTCOLOR", (1, 0), (1, -1), NAVY),
        ("BOX", (0, 0), (-1, -1), 0.5, GREY),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, LIGHT_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(eleve_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # Detail paiement
    story.append(Paragraph("DETAIL DU PAIEMENT", styles["Section"]))

    detail_tbl = Table([
        ["Motif", paiement.get("motif", "-")],
        ["Mode de paiement", paiement.get("mode_paiement", "-")],
    ], colWidths=[3 * cm, 9.8 * cm])

    detail_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), GREY),
        ("TEXTCOLOR", (1, 0), (1, -1), NAVY),
        ("BOX", (0, 0), (-1, -1), 0.5, GREY),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, LIGHT_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(detail_tbl)
    story.append(Spacer(1, 0.5 * cm))

    # Montant
    montant = float(paiement.get("montant", 0) or 0)
    montant_tbl = Table([
        [Paragraph("<b>MONTANT PAYE</b>",
                   ParagraphStyle(name="lab", fontName="Helvetica-Bold",
                                  fontSize=11, textColor=NAVY)),
         Paragraph(f"<b>{format_montant(montant)}</b>",
                   styles["MontantGros"])],
    ], colWidths=[6.8 * cm, 6 * cm])

    montant_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FFF4")),
        ("BOX", (0, 0), (-1, -1), 1.5, GREEN),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(montant_tbl)
    story.append(Spacer(1, 0.8 * cm))

    # Signatures
    sign_data = [
        ["Le Payeur", "Le Caissier"],
        ["\n\n_________________", "\n\n_________________"],
    ]
    sign_tbl = Table(sign_data, colWidths=[6.4 * cm, 6.4 * cm])
    sign_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(sign_tbl)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return chemin


# ============================================================
# RECU POUR PERSONNEL (format A5 compact)
# ============================================================
def generer_recu_personnel(paiement):
    num = paiement.get("numero_paie", "PAIE-XXXX")
    nom_fichier = f"paie_{num}_{datetime.now().strftime('%H%M%S')}.pdf"
    chemin = os.path.join(PDF_DIR, nom_fichier)

    doc = SimpleDocTemplate(
        chemin, pagesize=A5,
        leftMargin=1 * cm, rightMargin=1 * cm,
        topMargin=0.8 * cm, bottomMargin=1 * cm,
        title=f"Paie {num}",
        author="B-NDEKE Comptability One",
    )

    styles = _styles()
    story = []

    _entete_ecole(story, styles)
    story.append(Spacer(1, 0.3 * cm))

    ligne = Table([[""]], colWidths=[LARGEUR_UTILE], rowHeights=[2])
    ligne.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY)]))
    story.append(ligne)
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("BULLETIN DE PAIE", styles["TitreRecu"]))
    story.append(Paragraph("PERSONNEL", styles["SousTitreRecu"]))

    # Numero + date
    date_str = paiement.get("date_paiement", "")
    if date_str and len(date_str) >= 10:
        date_str = date_str[:10]

    info_tbl = Table([
        [Paragraph("<b>N° PAIE</b>", styles["Label"]),
         Paragraph(f"<b>{num}</b>", styles["Valeur"]),
         Paragraph("<b>DATE</b>", styles["Label"]),
         Paragraph(f"<b>{date_str}</b>", styles["Valeur"])],
    ], colWidths=[1.8 * cm, 4.5 * cm, 1.5 * cm, 5 * cm])

    info_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0F7FF")),
        ("BOX", (0, 0), (-1, -1), 1, NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # Infos employe
    story.append(Paragraph("INFORMATIONS DE L'EMPLOYE", styles["Section"]))

    emp_tbl = Table([
        ["Code", paiement.get("code", "-")],
        ["Nom complet", f"{paiement.get('nom', '')} {paiement.get('prenom', '')}"],
        ["Fonction", paiement.get("fonction", "-")],
    ], colWidths=[3 * cm, 9.8 * cm])

    emp_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), GREY),
        ("TEXTCOLOR", (1, 0), (1, -1), NAVY),
        ("BOX", (0, 0), (-1, -1), 0.5, GREY),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, LIGHT_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(emp_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # Detail salaire
    story.append(Paragraph("DETAIL DU PAIEMENT", styles["Section"]))

    montant_total = float(paiement.get("montant", 0) or 0)
    montant_avance = float(paiement.get("montant_avance_deduit", 0) or 0)
    net_a_payer = montant_total - montant_avance

    detail_tbl = Table([
        ["Salaire brut", format_montant(montant_total)],
        ["Avance deduite", f"- {format_montant(montant_avance)}" if montant_avance > 0 else "0"],
        ["Motif", paiement.get("motif", "-")],
        ["Mode de paiement", paiement.get("mode_paiement", "-")],
    ], colWidths=[5 * cm, 7.8 * cm])

    detail_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), GREY),
        ("TEXTCOLOR", (1, 0), (1, -1), NAVY),
        ("ALIGN", (1, 0), (1, 1), "RIGHT"),
        ("BOX", (0, 0), (-1, -1), 0.5, GREY),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, LIGHT_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(detail_tbl)
    story.append(Spacer(1, 0.5 * cm))

    # Net a payer
    montant_tbl = Table([
        [Paragraph("<b>NET A PAYER</b>",
                   ParagraphStyle(name="lab2", fontName="Helvetica-Bold",
                                  fontSize=11, textColor=NAVY)),
         Paragraph(f"<b>{format_montant(net_a_payer)}</b>",
                   styles["MontantGros"])],
    ], colWidths=[6.8 * cm, 6 * cm])

    montant_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FFF4")),
        ("BOX", (0, 0), (-1, -1), 1.5, GREEN),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(montant_tbl)
    story.append(Spacer(1, 0.8 * cm))

    # Signatures
    sign_data = [
        ["L'Employe", "Le Comptable"],
        ["\n\n_________________", "\n\n_________________"],
    ]
    sign_tbl = Table(sign_data, colWidths=[6.4 * cm, 6.4 * cm])
    sign_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(sign_tbl)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return chemin

    

# ============================================================
# FEUILLE DE 6 RECUS PAR PAGE A4
# ============================================================
def _mini_recu_data(paiement, type_="eleve"):
    """Retourne les elements (flowables) d'un mini-recu compact"""
    from reportlab.platypus import Table, TableStyle, Paragraph

    info = get_info_ecole_pour_pdf()

    # Styles compactes
    styles = getSampleStyleSheet()

    titre_style = ParagraphStyle(
        name="mini_titre", fontName="Helvetica-Bold", fontSize=9,
        textColor=NAVY, alignment=TA_CENTER, spaceAfter=2,
    )
    nom_ecole_style = ParagraphStyle(
        name="mini_ecole", fontName="Helvetica-Bold", fontSize=9,
        textColor=NAVY, alignment=TA_CENTER,
    )
    info_style = ParagraphStyle(
        name="mini_info", fontName="Helvetica", fontSize=6.5,
        textColor=GREY, alignment=TA_CENTER,
    )
    label_style = ParagraphStyle(
        name="mini_label", fontName="Helvetica", fontSize=6.5,
        textColor=GREY,
    )
    val_style = ParagraphStyle(
        name="mini_val", fontName="Helvetica-Bold", fontSize=7.5,
        textColor=NAVY,
    )
    montant_style = ParagraphStyle(
        name="mini_montant", fontName="Helvetica-Bold", fontSize=13,
        textColor=GREEN, alignment=TA_CENTER,
    )

    elements = []

    # Ligne 1 : Nom ecole (petit)
    elements.append(Paragraph(info["nom"], nom_ecole_style))
    if info.get("telephone"):
        elements.append(Paragraph(f"Tel : {info['telephone']}", info_style))

    # Ligne 2 : Titre
    if type_ == "eleve":
        elements.append(Paragraph("REÇU DE PAIEMENT - ELEVE", titre_style))
    else:
        elements.append(Paragraph("BULLETIN DE PAIE - PERSONNEL", titre_style))

    # Ligne de separation
    ligne = Table([[""]], colWidths=[8.8 * cm], rowHeights=[1])
    ligne.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY)]))
    elements.append(Spacer(1, 2))
    elements.append(ligne)
    elements.append(Spacer(1, 3))

    # Numero + Date
    date_str = paiement.get("date_paiement", "")
    if date_str and len(date_str) >= 10:
        date_str = date_str[:10]

    if type_ == "eleve":
        num = paiement.get("numero_recu", "-")
        nom_prenom = f"{paiement.get('nom', '')} {paiement.get('prenom', '')}"
        code = paiement.get("matricule", "-")
        extra = paiement.get("classe", "-")
        montant = float(paiement.get("montant", 0) or 0)
    else:
        num = paiement.get("numero_paie", "-")
        nom_prenom = f"{paiement.get('nom', '')} {paiement.get('prenom', '')}"
        code = paiement.get("code", "-")
        extra = paiement.get("fonction", "-")
        m_total = float(paiement.get("montant", 0) or 0)
        m_avance = float(paiement.get("montant_avance_deduit", 0) or 0)
        montant = m_total - m_avance

    infos_tbl = Table([
        [Paragraph(f"<b>N°</b> {num}", label_style),
         Paragraph(f"<b>Date</b> {date_str}", label_style)],
    ], colWidths=[5 * cm, 4 * cm])
    infos_tbl.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(infos_tbl)

    elements.append(Paragraph(f"<b>{nom_prenom}</b>", val_style))
    elements.append(Paragraph(f"{code}  |  {extra}", label_style))

    if type_ == "eleve":
        elements.append(Paragraph(f"Motif : {paiement.get('motif', '-')}", label_style))
    else:
        elements.append(Paragraph(
            f"Salaire : {format_montant(m_total)}  -  Avance : {format_montant(m_avance)}",
            label_style
        ))
        elements.append(Paragraph(f"Motif : {paiement.get('motif', '-')}", label_style))

    elements.append(Spacer(1, 3))

    # Montant en gros
    label_montant = "MONTANT PAYE" if type_ == "eleve" else "NET A PAYER"
    montant_tbl = Table([
        [Paragraph(f"<b>{label_montant}</b>", label_style),
         Paragraph(f"<b>{format_montant(montant)}</b>", montant_style)],
    ], colWidths=[3.5 * cm, 5.5 * cm])
    montant_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FFF4")),
        ("BOX", (0, 0), (-1, -1), 0.8, GREEN),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(montant_tbl)

    elements.append(Spacer(1, 3))
    elements.append(Paragraph("Signature : _______________", label_style))

    return elements


def generer_feuille_recus(liste_paiements, type_="eleve"):
    """
    Genere une feuille A4 avec jusqu'a 6 recus (2 colonnes x 3 lignes).
    - liste_paiements : liste de dict paiement
    - type_ : "eleve" ou "personnel"
    Retourne le chemin du PDF.
    """
    from reportlab.lib.pagesizes import A4

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefixe = "feuille_recus_eleves" if type_ == "eleve" else "feuille_paies_personnel"
    nom_fichier = f"{prefixe}_{timestamp}.pdf"
    chemin = os.path.join(PDF_DIR, nom_fichier)

    doc = SimpleDocTemplate(
        chemin, pagesize=A4,
        leftMargin=0.6 * cm, rightMargin=0.6 * cm,
        topMargin=0.6 * cm, bottomMargin=0.6 * cm,
        title="Feuille de recus",
        author="B-NDEKE Comptability One",
    )

    story = []

    # Nombre de recus a imprimer (max 6 par page)
    paiements = list(liste_paiements)

    # Decouper en pages de 6 recus max
    par_page = 6
    pages = [paiements[i:i + par_page] for i in range(0, len(paiements), par_page)]

    if not pages:
        pages = [[]]

    for page_idx, page_paiements in enumerate(pages):
        # Construire les 6 cellules
        cellules = []

        for i in range(par_page):
            if i < len(page_paiements):
                # Cellule avec recu
                contenu = _mini_recu_data(page_paiements[i], type_)
                cellules.append(contenu)
            else:
                # Cellule vide (espace)
                cellules.append([""])

        # Organiser en 2 colonnes x 3 lignes
        # Ligne 1 : cellules[0] | cellules[1]
        # Ligne 2 : cellules[2] | cellules[3]
        # Ligne 3 : cellules[4] | cellules[5]

        # Chaque cellule est une liste de flowables → on la met dans une Table imbriquee
        def _wrap(cell_flowables):
            if len(cell_flowables) == 1 and cell_flowables[0] == "":
                return Paragraph("", label_style_vide())
            t = Table([[f] for f in cell_flowables], colWidths=[8.8 * cm])
            t.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            return t

        cell_0 = _wrap(cellules[0])
        cell_1 = _wrap(cellules[1])
        cell_2 = _wrap(cellules[2])
        cell_3 = _wrap(cellules[3])
        cell_4 = _wrap(cellules[4])
        cell_5 = _wrap(cellules[5])

        # Grille 2 x 3
        grille = Table([
            [cell_0, cell_1],
            [cell_2, cell_3],
            [cell_4, cell_5],
        ], colWidths=[9.7 * cm, 9.7 * cm], rowHeights=[9.3 * cm, 9.3 * cm, 9.3 * cm])

        # Style de la grille : bordures fines en pointille pour la DECOUPE
        style_grille = [
            # Cadre general en pointille
            ("BOX", (0, 0), (-1, -1), 0.5, GREY),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            # Padding interne dans chaque cellule
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            # Ajouter des ciseaux visuels : coins pointilles
            # Rendre les bordures en pointille
            ("LINEBELOW", (0, 0), (0, 0), 0.4, colors.HexColor("#AAAAAA")),
        ]

        grille.setStyle(TableStyle(style_grille))
        story.append(grille)

        # Saut de page (sauf pour la derniere)
        if page_idx < len(pages) - 1:
            story.append(PageBreak())

    # Pied de page
    def _footer_feuille(canvas, doc):
        info = get_info_ecole_pour_pdf()
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GREY)
        canvas.drawString(
            1 * cm, 0.3 * cm,
            f"{info['nom']} - Planche de recus - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        )
        canvas.drawRightString(20 * cm, 0.3 * cm, f"Page {doc.page}")
        canvas.restoreState()

    from reportlab.platypus import PageBreak

    doc.build(story, onFirstPage=_footer_feuille, onLaterPages=_footer_feuille)
    return chemin


def label_style_vide():
    """Style pour cellule vide"""
    s = getSampleStyleSheet()
    return s["Normal"]