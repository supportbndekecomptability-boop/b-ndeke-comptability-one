"""
Generation des rapports PDF avec ReportLab
Lit les infos de l'ecole depuis la base de donnees (Parametres)
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
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
ORANGE = colors.HexColor("#e67e22")
GREY = colors.HexColor("#666666")
LIGHT_GREY = colors.HexColor("#f0f0f0")


def _get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="TitreRapport",
        fontName="Helvetica-Bold", fontSize=20,
        textColor=NAVY, alignment=TA_CENTER, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="SousTitre",
        fontName="Helvetica", fontSize=11,
        textColor=GREY, alignment=TA_CENTER, spaceAfter=20,
    ))
    styles.add(ParagraphStyle(
        name="SectionTitre",
        fontName="Helvetica-Bold", fontSize=13,
        textColor=NAVY, spaceBefore=15, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="InfoEcole",
        fontName="Helvetica", fontSize=9,
        textColor=GREY, alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="NomEcole",
        fontName="Helvetica-Bold", fontSize=14,
        textColor=NAVY, alignment=TA_LEFT,
    ))
    return styles


# ============================================================
# EN-TETE AVEC LOGO + INFOS ECOLE (depuis la base)
# ============================================================
def _entete_pdf(story, styles, titre, sous_titre=""):
    info = get_info_ecole_pour_pdf()

    # ===== Bloc logo + infos =====
    if info.get("logo_path") and PIL_OK:
        try:
            img = Image.open(info["logo_path"])
            ratio = img.width / img.height if img.height else 1

            hauteur_logo = 2.2 * cm
            largeur_logo = hauteur_logo * ratio

            logo = RLImage(info["logo_path"],
                           width=largeur_logo, height=hauteur_logo)

            # Texte a droite du logo
            texte_html = f"<b><font size=14 color='#0F2C5C'>{info['nom']}</font></b><br/>"
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

    # ===== Ligne bleue horizontale =====
    ligne = Table([[""]], colWidths=[18 * cm], rowHeights=[2])
    ligne.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY)]))
    story.append(ligne)
    story.append(Spacer(1, 0.5 * cm))

    # ===== Titre de l'etat =====
    story.append(Paragraph(titre, styles["TitreRapport"]))
    if sous_titre:
        story.append(Paragraph(sous_titre, styles["SousTitre"]))


def _entete_sans_logo(story, styles, info):
    """En-tete quand il n'y a pas de logo"""
    story.append(Paragraph(info["nom"], styles["TitreRapport"]))
    if info.get("adresse"):
        story.append(Paragraph(info["adresse"], styles["InfoEcole"]))
    contacts = []
    if info.get("telephone"):
        contacts.append(f"Tel : {info['telephone']}")
    if info.get("email"):
        contacts.append(f"Email : {info['email']}")
    if contacts:
        story.append(Paragraph("  |  ".join(contacts), styles["InfoEcole"]))


# ============================================================
# UTILITAIRES TABLEAUX
# ============================================================
def _tableau_2_colonnes(donnees, largeur=18 * cm, col1=12 * cm):
    t = Table(donnees, colWidths=[col1, largeur - col1])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.5, GREY),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, LIGHT_GREY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _tableau_generique(entetes, lignes, largeurs=None):
    data = [entetes] + lignes
    if largeurs is None:
        largeurs = [18 * cm / len(entetes)] * len(entetes)

    t = Table(data, colWidths=largeurs, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.25, GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(data)):
        if i % 2 == 1:
            style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fafafa")))
    t.setStyle(TableStyle(style))
    return t


def _pied_page(canvas, doc):
    info = get_info_ecole_pour_pdf()
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(
        2 * cm, 1.2 * cm,
        f"{info['nom']} | Genere le {datetime.now().strftime('%d/%m/%Y %H:%M')}",
    )
    canvas.drawRightString(19 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


# ============================================================
# RAPPORT MENSUEL
# ============================================================
def generer_pdf_rapport_mensuel(donnees):
    annee = donnees["annee"]
    mois = donnees["mois"]
    nom_fichier = f"rapport_mensuel_{annee}-{mois:02d}_{datetime.now().strftime('%H%M%S')}.pdf"
    chemin = os.path.join(RAPPORTS_DIR, nom_fichier)

    doc = SimpleDocTemplate(
        chemin, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.5 * cm, bottomMargin=2 * cm,
        title=f"Rapport mensuel {mois:02d}/{annee}",
        author="B-NDEKE Comptability One",
    )

    styles = _get_styles()
    story = []

    mois_noms = ["", "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
                 "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre"]
    _entete_pdf(story, styles, "RAPPORT MENSUEL",
                f"{mois_noms[mois]} {annee}  |  Genere le {donnees['date_generation']}")

    story.append(Paragraph("1. SYNTHESE", styles["SectionTitre"]))

    synthese_data = [
        ["Recettes eleves", format_montant(donnees["recettes_totales"])],
        ["Depenses personnel", f"- {format_montant(donnees['depenses_personnel']['total'])}"],
        ["Depenses generales", f"- {format_montant(donnees['depenses_generales']['total'])}"],
        ["TOTAL DEPENSES", f"- {format_montant(donnees['depenses_totales'])}"],
        ["BENEFICE", format_montant(donnees["benefice"])],
    ]

    t = Table(synthese_data, colWidths=[12 * cm, 6 * cm])
    couleur_benefice = GREEN if donnees["benefice"] >= 0 else RED

    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BOX", (0, 0), (-1, -1), 0.5, GREY),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, LIGHT_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#f0f0f0")),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("FONTNAME", (0, 4), (-1, 4), "Helvetica-Bold"),
        ("FONTSIZE", (0, 4), (-1, 4), 13),
        ("TEXTCOLOR", (1, 4), (1, 4), couleur_benefice),
    ]))
    story.append(t)

    story.append(Paragraph("2. IMPAYES ACTUELS", styles["SectionTitre"]))
    impayes_data = [
        ["Nombre d'eleves avec impayes", str(donnees["impayes"]["nombre"])],
        ["Total a recouvrer", format_montant(donnees["impayes"]["total"])],
    ]
    story.append(_tableau_2_colonnes(impayes_data))

    if donnees["depenses_par_categorie"]:
        story.append(Paragraph("3. DEPENSES PAR CATEGORIE", styles["SectionTitre"]))
        lignes = []
        for d in donnees["depenses_par_categorie"]:
            lignes.append([d["categorie"], str(d["nombre"]), format_montant(d["total"])])
        story.append(_tableau_generique(
            ["Categorie", "Nb", "Montant"], lignes,
            largeurs=[10 * cm, 2 * cm, 6 * cm],
        ))

    if donnees["paies_personnel"]:
        story.append(PageBreak())
        story.append(Paragraph("4. PAIEMENTS AU PERSONNEL", styles["SectionTitre"]))
        lignes = []
        for p in donnees["paies_personnel"]:
            lignes.append([p["code"], f"{p['nom']} {p['prenom']}",
                           p["fonction"], format_montant(p["total"])])
        story.append(_tableau_generique(
            ["Code", "Nom", "Fonction", "Montant paye"], lignes,
            largeurs=[2.5 * cm, 5 * cm, 4 * cm, 4.5 * cm],
        ))

    story.append(Spacer(1, 1.5 * cm))
    sign_data = [
        ["Le Comptable", "La Direction"],
        ["\n\n\n_________________", "\n\n\n_________________"],
    ]
    sign_t = Table(sign_data, colWidths=[9 * cm, 9 * cm])
    sign_t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(sign_t)

    doc.build(story, onFirstPage=_pied_page, onLaterPages=_pied_page)
    return chemin


# ============================================================
# RAPPORT IMPAYES
# ============================================================
def generer_pdf_rapport_impayes(donnees):
    nom_fichier = f"rapport_impayes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    chemin = os.path.join(RAPPORTS_DIR, nom_fichier)

    doc = SimpleDocTemplate(chemin, pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.5 * cm, bottomMargin=2 * cm)

    styles = _get_styles()
    story = []

    _entete_pdf(story, styles, "ETAT DES IMPAYES",
                f"Genere le {donnees['date_generation']}")

    synthese = [
        ["Nombre d'eleves avec impayes", str(donnees["nombre_impayes"])],
        ["Total a recouvrer", format_montant(donnees["total_impaye"])],
    ]
    story.append(_tableau_2_colonnes(synthese))
    story.append(Spacer(1, 0.5 * cm))

    if donnees["eleves"]:
        lignes = []
        for e in donnees["eleves"]:
            lignes.append([
                e["matricule"], f"{e['nom']} {e['prenom']}", e["classe"],
                format_montant(e["frais"]), format_montant(e["paye"]),
                format_montant(e["solde"]),
            ])
        story.append(_tableau_generique(
            ["Matricule", "Eleve", "Classe", "Frais", "Paye", "Solde"],
            lignes,
            largeurs=[2.3 * cm, 4.5 * cm, 2.5 * cm, 2.9 * cm, 2.9 * cm, 2.9 * cm],
        ))
    else:
        story.append(Paragraph("Aucun impaye. Tous les eleves sont a jour.",
                               styles["Normal"]))

    doc.build(story, onFirstPage=_pied_page, onLaterPages=_pied_page)
    return chemin


# ============================================================
# RAPPORT DETTES PERSONNEL
# ============================================================
def generer_pdf_rapport_dettes_personnel(donnees):
    nom_fichier = f"rapport_dettes_personnel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    chemin = os.path.join(RAPPORTS_DIR, nom_fichier)

    doc = SimpleDocTemplate(chemin, pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.5 * cm, bottomMargin=2 * cm)

    styles = _get_styles()
    story = []

    _entete_pdf(story, styles, "ETAT DES DETTES ENVERS LE PERSONNEL",
                f"Genere le {donnees['date_generation']}")

    synthese = [
        ["Nombre de personnes", str(donnees["nombre"])],
        ["Total a payer", format_montant(donnees["total_dette"])],
    ]
    story.append(_tableau_2_colonnes(synthese))
    story.append(Spacer(1, 0.5 * cm))

    if donnees["personnel"]:
        lignes = []
        for p in donnees["personnel"]:
            lignes.append([
                p["code"], f"{p['nom']} {p['prenom']}", p["fonction"],
                format_montant(p["engagement"]), format_montant(p["paye"]),
                format_montant(p["reste"]),
            ])
        story.append(_tableau_generique(
            ["Code", "Personnel", "Fonction", "Engagement", "Paye", "Reste"],
            lignes,
            largeurs=[2.2 * cm, 4.3 * cm, 3 * cm, 2.9 * cm, 2.9 * cm, 2.9 * cm],
        ))
    else:
        story.append(Paragraph("Aucune dette envers le personnel. Tout est regle.",
                               styles["Normal"]))

    doc.build(story, onFirstPage=_pied_page, onLaterPages=_pied_page)
    return chemin


# ============================================================
# RAPPORT JOURNALIER
# ============================================================
def generer_pdf_rapport_journalier(donnees):
    nom_fichier = f"rapport_journalier_{donnees['date']}_{datetime.now().strftime('%H%M%S')}.pdf"
    chemin = os.path.join(RAPPORTS_DIR, nom_fichier)

    doc = SimpleDocTemplate(chemin, pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.5 * cm, bottomMargin=2 * cm)

    styles = _get_styles()
    story = []

    _entete_pdf(story, styles, "RAPPORT JOURNALIER",
                f"Journee du {donnees['date']}  |  Genere le {donnees['date_generation']}")

    synthese = [
        ["Recettes eleves", format_montant(donnees["total_recettes"])],
        ["Paiements personnel", f"- {format_montant(donnees['total_personnel'])}"],
        ["Depenses generales", f"- {format_montant(donnees['total_depenses'])}"],
        ["SOLDE DU JOUR", format_montant(donnees["solde_jour"])],
    ]
    story.append(_tableau_2_colonnes(synthese))

    if donnees["paiements_eleves"]:
        story.append(Paragraph("Paiements eleves", styles["SectionTitre"]))
        lignes = []
        for p in donnees["paiements_eleves"]:
            lignes.append([
                p["numero_recu"], f"{p['nom']} {p['prenom']}", p["classe"],
                p["motif"], format_montant(p["montant"]),
            ])
        story.append(_tableau_generique(
            ["Recu", "Eleve", "Classe", "Motif", "Montant"], lignes,
            largeurs=[2.5 * cm, 5 * cm, 2.5 * cm, 4 * cm, 4 * cm],
        ))

    if donnees["paiements_personnel"]:
        story.append(Paragraph("Paiements personnel", styles["SectionTitre"]))
        lignes = []
        for p in donnees["paiements_personnel"]:
            lignes.append([
                p["numero_paie"], f"{p['nom']} {p['prenom']}", p["fonction"],
                p["motif"], format_montant(p["montant"]),
            ])
        story.append(_tableau_generique(
            ["Paie", "Personnel", "Fonction", "Motif", "Montant"], lignes,
            largeurs=[2.5 * cm, 5 * cm, 2.5 * cm, 4 * cm, 4 * cm],
        ))

    if donnees["depenses"]:
        story.append(Paragraph("Depenses", styles["SectionTitre"]))
        lignes = []
        for d in donnees["depenses"]:
            lignes.append([d["categorie"], d["libelle"], format_montant(d["montant"])])
        story.append(_tableau_generique(
            ["Categorie", "Libelle", "Montant"], lignes,
            largeurs=[5 * cm, 9 * cm, 4 * cm],
        ))

    doc.build(story, onFirstPage=_pied_page, onLaterPages=_pied_page)
    return chemin