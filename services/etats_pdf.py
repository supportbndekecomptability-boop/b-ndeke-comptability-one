"""
Generation des PDF des etats financiers SYSCOHADA
Lit les infos de l'ecole depuis la base de donnees (Parametres)
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
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
GREEN = colors.HexColor("#27ae60")
RED = colors.HexColor("#e74c3c")
GREY = colors.HexColor("#666666")
LIGHT_GREY = colors.HexColor("#f0f0f0")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TitreEcole", fontName="Helvetica-Bold", fontSize=18,
        textColor=NAVY, alignment=TA_CENTER, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="InfoEcole", fontName="Helvetica", fontSize=9,
        textColor=GREY, alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="TitreEtat", fontName="Helvetica-Bold", fontSize=15,
        textColor=NAVY, alignment=TA_CENTER, spaceAfter=4, spaceBefore=10,
    ))
    styles.add(ParagraphStyle(
        name="Periode", fontName="Helvetica", fontSize=10,
        textColor=GREY, alignment=TA_CENTER, spaceAfter=15,
    ))
    styles.add(ParagraphStyle(
        name="Section", fontName="Helvetica-Bold", fontSize=12,
        textColor=NAVY, spaceBefore=12, spaceAfter=6,
    ))
    return styles


# ============================================================
# EN-TETE DYNAMIQUE AVEC LOGO + INFOS ECOLE
# ============================================================
def _entete(story, styles, titre, periode):
    info = get_info_ecole_pour_pdf()

    # ===== Bloc logo + infos =====
    if info.get("logo_path") and PIL_OK:
        try:
            img = Image.open(info["logo_path"])
            ratio = img.width / img.height if img.height else 1

            hauteur_logo = 2 * cm
            largeur_logo = hauteur_logo * ratio

            logo = RLImage(info["logo_path"],
                           width=largeur_logo, height=hauteur_logo)

            # Texte a droite du logo
            texte_html = f"<b><font size=13 color='#0F2C5C'>{info['nom']}</font></b><br/>"
            if info.get("adresse"):
                texte_html += f"<font size=9 color='#666666'>{info['adresse']}</font><br/>"
            contacts = []
            if info.get("telephone"):
                contacts.append(f"Tel : {info['telephone']}")
            if info.get("email"):
                contacts.append(f"Email : {info['email']}")
            if contacts:
                texte_html += f"<font size=9 color='#666666'>{' | '.join(contacts)}</font>"

            txt = Paragraph(texte_html, styles["InfoEcole"])

            entete_tbl = Table(
                [[logo, txt]],
                colWidths=[largeur_logo + 0.4 * cm, 18 * cm - largeur_logo - 0.4 * cm],
            )
            entete_tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(entete_tbl)

        except Exception as e:
            print(f"[Erreur logo PDF] {e}")
            _entete_sans_logo(story, styles, info)
    else:
        _entete_sans_logo(story, styles, info)

    story.append(Spacer(1, 0.4 * cm))

    # Ligne horizontale bleue
    ligne_tbl = Table([[""]], colWidths=[18 * cm], rowHeights=[2])
    ligne_tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY)]))
    story.append(ligne_tbl)
    story.append(Spacer(1, 0.3 * cm))

    # Titre de l'etat
    story.append(Paragraph(titre, styles["TitreEtat"]))
    story.append(Paragraph(f"Periode : {periode}", styles["Periode"]))


def _entete_sans_logo(story, styles, info):
    """En-tete quand il n'y a pas de logo"""
    story.append(Paragraph(info["nom"], styles["TitreEcole"]))
    if info.get("adresse"):
        story.append(Paragraph(info["adresse"], styles["InfoEcole"]))
    contacts = []
    if info.get("telephone"):
        contacts.append(f"Tel : {info['telephone']}")
    if info.get("email"):
        contacts.append(f"Email : {info['email']}")
    if contacts:
        story.append(Paragraph("  |  ".join(contacts), styles["InfoEcole"]))


def _footer(canvas, doc):
    info = get_info_ecole_pour_pdf()
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(2 * cm, 1.2 * cm,
                      f"{info['nom']} | Genere le {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    canvas.drawRightString(19 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def _tableau(entetes, lignes, largeurs, footer=None):
    data = [entetes] + lignes
    if footer:
        data.append(footer)

    t = Table(data, colWidths=largeurs, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for i in range(1, len(data)):
        if i % 2 == 1:
            style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fafafa")))

    if footer:
        style.append(("BACKGROUND", (0, len(data) - 1), (-1, len(data) - 1), colors.HexColor("#e0e0e0")))
        style.append(("FONTNAME", (0, len(data) - 1), (-1, len(data) - 1), "Helvetica-Bold"))

    t.setStyle(TableStyle(style))
    return t


# ============================================================
# 1. JOURNAL
# ============================================================
def pdf_journal(donnees):
    nom = f"journal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    chemin = os.path.join(RAPPORTS_DIR, nom)

    doc = SimpleDocTemplate(chemin, pagesize=landscape(A4),
                            leftMargin=1.2 * cm, rightMargin=1.2 * cm,
                            topMargin=1.2 * cm, bottomMargin=1.8 * cm)
    styles = _styles()
    story = []

    periode = f"Du {donnees['date_debut']} au {donnees['date_fin']}"
    _entete(story, styles, "JOURNAL GENERAL", periode)

    lignes = []
    for l in donnees["lignes"]:
        lignes.append([
            l["date"], l["journal"], l["piece"][:15], l["libelle"][:40],
            l["compte"], l["intitule"][:25],
            format_montant(l["debit"]) if l["debit"] else "",
            format_montant(l["credit"]) if l["credit"] else "",
        ])

    footer = ["", "", "", "", "", "TOTAUX",
              format_montant(donnees["total_debit"]),
              format_montant(donnees["total_credit"])]

    story.append(_tableau(
        ["Date", "Journal", "Piece", "Libelle", "Cpte", "Intitule", "Debit", "Credit"],
        lignes,
        [2 * cm, 1.8 * cm, 2.5 * cm, 6 * cm, 1.3 * cm, 4 * cm, 2.8 * cm, 2.8 * cm],
        footer=footer,
    ))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return chemin


# ============================================================
# 2. GRAND LIVRE
# ============================================================
def pdf_grand_livre(donnees):
    nom = f"grand_livre_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    chemin = os.path.join(RAPPORTS_DIR, nom)

    doc = SimpleDocTemplate(chemin, pagesize=A4,
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.2 * cm, bottomMargin=1.8 * cm)
    styles = _styles()
    story = []

    periode = f"Du {donnees['date_debut']} au {donnees['date_fin']}"
    _entete(story, styles, "GRAND LIVRE", periode)

    for compte in donnees["comptes"]:
        story.append(Paragraph(
            f"Compte {compte['compte']} - {compte['intitule']}",
            styles["Section"],
        ))

        lignes = []
        for mvt in compte["mouvements"]:
            lignes.append([
                mvt["date"], mvt["libelle"][:50],
                format_montant(mvt["debit"]) if mvt["debit"] else "",
                format_montant(mvt["credit"]) if mvt["credit"] else "",
                format_montant(mvt["solde"]),
            ])

        footer = ["", "TOTAUX",
                  format_montant(compte["total_debit"]),
                  format_montant(compte["total_credit"]),
                  format_montant(compte["solde_final"])]

        story.append(_tableau(
            ["Date", "Libelle", "Debit", "Credit", "Solde"],
            lignes,
            [2 * cm, 8 * cm, 2.7 * cm, 2.7 * cm, 2.8 * cm],
            footer=footer,
        ))
        story.append(Spacer(1, 0.6 * cm))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return chemin


# ============================================================
# 3. BALANCE
# ============================================================
def pdf_balance(donnees):
    nom = f"balance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    chemin = os.path.join(RAPPORTS_DIR, nom)

    doc = SimpleDocTemplate(chemin, pagesize=A4,
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.2 * cm, bottomMargin=1.8 * cm)
    styles = _styles()
    story = []

    periode = f"Du {donnees['date_debut']} au {donnees['date_fin']}"
    _entete(story, styles, "BALANCE GENERALE", periode)

    lignes = []
    for l in donnees["lignes"]:
        lignes.append([
            l["compte"],
            l["intitule"][:30],
            format_montant(l["mvt_debit"]) if l["mvt_debit"] else "",
            format_montant(l["mvt_credit"]) if l["mvt_credit"] else "",
            format_montant(l["solde_debit"]) if l["solde_debit"] else "",
            format_montant(l["solde_credit"]) if l["solde_credit"] else "",
        ])

    footer = ["", "TOTAUX",
              format_montant(donnees["total_debit"]),
              format_montant(donnees["total_credit"]),
              format_montant(donnees["total_solde_debit"]),
              format_montant(donnees["total_solde_credit"])]

    story.append(_tableau(
        ["Cpte", "Intitule", "Mvt Debit", "Mvt Credit", "Solde Deb", "Solde Cred"],
        lignes,
        [1.5 * cm, 5 * cm, 2.5 * cm, 2.5 * cm, 2.4 * cm, 2.4 * cm],
        footer=footer,
    ))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return chemin


# ============================================================
# 4. COMPTE DE RESULTAT
# ============================================================
def pdf_compte_resultat(donnees):
    nom = f"compte_resultat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    chemin = os.path.join(RAPPORTS_DIR, nom)

    doc = SimpleDocTemplate(chemin, pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.2 * cm, bottomMargin=1.8 * cm)
    styles = _styles()
    story = []

    periode = f"Du {donnees['date_debut']} au {donnees['date_fin']}"
    _entete(story, styles, "COMPTE DE RESULTAT", periode)

    # PRODUITS
    story.append(Paragraph("PRODUITS (Classe 7)", styles["Section"]))
    lignes_p = []
    for p in donnees["produits"]:
        lignes_p.append([p["compte"], p["intitule"], format_montant(p["montant"])])

    t = _tableau(
        ["Cpte", "Intitule", "Montant"],
        lignes_p,
        [1.5 * cm, 12 * cm, 4 * cm],
        footer=["", "TOTAL PRODUITS", format_montant(donnees["total_produits"])],
    )
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # CHARGES
    story.append(Paragraph("CHARGES (Classe 6)", styles["Section"]))
    lignes_c = []
    for c in donnees["charges"]:
        lignes_c.append([c["compte"], c["intitule"], format_montant(c["montant"])])

    t2 = _tableau(
        ["Cpte", "Intitule", "Montant"],
        lignes_c,
        [1.5 * cm, 12 * cm, 4 * cm],
        footer=["", "TOTAL CHARGES", format_montant(donnees["total_charges"])],
    )
    story.append(t2)
    story.append(Spacer(1, 1 * cm))

    # RESULTAT
    couleur = GREEN if donnees["resultat_net"] >= 0 else RED
    res_data = [[
        Paragraph("<b>RESULTAT NET DE L'EXERCICE</b>",
                  ParagraphStyle(name="res", fontName="Helvetica-Bold", fontSize=13, textColor=couleur)),
        Paragraph(f"<b>{format_montant(donnees['resultat_net'])}</b>",
                  ParagraphStyle(name="res2", fontName="Helvetica-Bold", fontSize=13,
                                 textColor=couleur, alignment=TA_RIGHT)),
    ]]
    t3 = Table(res_data, colWidths=[10 * cm, 7.5 * cm])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f0f0")),
        ("BOX", (0, 0), (-1, -1), 1, NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t3)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return chemin


# ============================================================
# 5. BILAN
# ============================================================
def pdf_bilan(donnees):
    nom = f"bilan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    chemin = os.path.join(RAPPORTS_DIR, nom)

    doc = SimpleDocTemplate(chemin, pagesize=A4,
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.2 * cm, bottomMargin=1.8 * cm)
    styles = _styles()
    story = []

    periode = f"Au {donnees['date_fin']}"
    _entete(story, styles, "BILAN", periode)

    lignes = []
    actif = donnees["actif"]
    passif = donnees["passif"]
    max_rows = max(len(actif), len(passif))

    for i in range(max_rows):
        a = actif[i] if i < len(actif) else None
        p = passif[i] if i < len(passif) else None

        lignes.append([
            a["compte"] if a else "",
            a["intitule"][:25] if a else "",
            format_montant(a["montant"]) if a else "",
            p["compte"] if p else "",
            p["intitule"][:25] if p else "",
            format_montant(p["montant"]) if p else "",
        ])

    footer = ["", "TOTAL ACTIF", format_montant(donnees["total_actif"]),
              "", "TOTAL PASSIF", format_montant(donnees["total_passif"])]

    story.append(_tableau(
        ["Cpte", "ACTIF", "Montant", "Cpte", "PASSIF", "Montant"],
        lignes,
        [1.2 * cm, 4.5 * cm, 2.8 * cm, 1.2 * cm, 4.5 * cm, 2.8 * cm],
        footer=footer,
    ))

    story.append(Spacer(1, 0.5 * cm))
    ecart = donnees["total_actif"] - donnees["total_passif"]
    if abs(ecart) > 0.01:
        story.append(Paragraph(
            f"<b>Attention :</b> Ecart de {format_montant(ecart)} entre l'actif et le passif.",
            ParagraphStyle(name="warn", fontName="Helvetica-Bold", fontSize=10, textColor=RED),
        ))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return chemin


# ============================================================
# 6. TRESORERIE
# ============================================================
def pdf_tresorerie(donnees):
    nom = f"tresorerie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    chemin = os.path.join(RAPPORTS_DIR, nom)

    doc = SimpleDocTemplate(chemin, pagesize=A4,
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.2 * cm, bottomMargin=1.8 * cm)
    styles = _styles()
    story = []

    periode = f"Du {donnees['date_debut']} au {donnees['date_fin']}"
    _entete(story, styles, "ETAT DE TRESORERIE", periode)

    # ENCAISSEMENTS
    story.append(Paragraph("ENCAISSEMENTS", styles["Section"]))
    lignes_e = []
    for e in donnees["encaissements"]:
        lignes_e.append([e["date"], e["libelle"][:55], format_montant(e["montant"])])

    story.append(_tableau(
        ["Date", "Libelle", "Montant"],
        lignes_e,
        [2.5 * cm, 11 * cm, 4 * cm],
        footer=["", "TOTAL ENCAISSEMENTS", format_montant(donnees["total_entrees"])],
    ))
    story.append(Spacer(1, 0.6 * cm))

    # DECAISSEMENTS
    story.append(Paragraph("DECAISSEMENTS", styles["Section"]))
    lignes_d = []
    for d in donnees["decaissements"]:
        lignes_d.append([d["date"], d["libelle"][:55], format_montant(d["montant"])])

    story.append(_tableau(
        ["Date", "Libelle", "Montant"],
        lignes_d,
        [2.5 * cm, 11 * cm, 4 * cm],
        footer=["", "TOTAL DECAISSEMENTS", format_montant(donnees["total_sorties"])],
    ))
    story.append(Spacer(1, 1 * cm))

    # SOLDE
    couleur = GREEN if donnees["solde"] >= 0 else RED
    solde_data = [[
        Paragraph("<b>SOLDE DE TRESORERIE</b>",
                  ParagraphStyle(name="s1", fontName="Helvetica-Bold", fontSize=13, textColor=couleur)),
        Paragraph(f"<b>{format_montant(donnees['solde'])}</b>",
                  ParagraphStyle(name="s2", fontName="Helvetica-Bold", fontSize=13,
                                 textColor=couleur, alignment=TA_RIGHT)),
    ]]
    t = Table(solde_data, colWidths=[10 * cm, 7.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f0f0")),
        ("BOX", (0, 0), (-1, -1), 1, NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return chemin