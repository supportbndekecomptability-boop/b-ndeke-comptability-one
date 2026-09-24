"""
Generation PDF des bulletins scolaires
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

from config import DATA_DIR
from core.ecole import get_info_ecole
from core.bulletins import lister_matieres, notes_eleve, moyenne_eleve, rang_eleve


def generer_bulletin_pdf(eleve, trimestre, annee, chemin=None):
    if chemin is None:
        dossier = os.path.join(DATA_DIR, 'bulletins')
        os.makedirs(dossier, exist_ok=True)
        nom_fichier = f"Bulletin_{eleve['matricule']}_T{trimestre}_{annee}.pdf"
        chemin = os.path.join(dossier, nom_fichier)

    info_ecole = get_info_ecole()

    doc = SimpleDocTemplate(
        chemin, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    titre_style = ParagraphStyle('Titre', parent=styles['Heading1'],
        alignment=TA_CENTER, fontSize=16, spaceAfter=5,
        textColor=colors.HexColor('#0F2C5C'))
    sous_titre = ParagraphStyle('SousTitre', parent=styles['Normal'],
        alignment=TA_CENTER, fontSize=10, spaceAfter=10,
        textColor=colors.HexColor('#666666'))
    label_style = ParagraphStyle('Label', parent=styles['Normal'],
        fontSize=10, leading=14, textColor=colors.HexColor('#333333'))

    elements = []
    elements.append(Paragraph(info_ecole.get('nom', 'B-NDEKE'), titre_style))
    elements.append(Paragraph(
        f"{info_ecole.get('adresse', '')} - Tel : {info_ecole.get('telephone', '')}",
        sous_titre))
    elements.append(Spacer(1, 0.3 * cm))

    bulletin_style = ParagraphStyle('Bulletin', parent=styles['Heading2'],
        alignment=TA_CENTER, fontSize=14, spaceAfter=10,
        textColor=colors.HexColor('#27ae60'))
    elements.append(Paragraph(
        f"BULLETIN DE NOTES - TRIMESTRE {trimestre} - ANNEE {annee}",
        bulletin_style))

    infos = [
        ['Nom complet :', f"{eleve['nom']} {eleve['prenom']}"],
        ['Matricule :', eleve.get('matricule', '-')],
        ['Classe :', eleve.get('classe', '-')],
        ['Sexe :', eleve.get('sexe', '-')],
        ['Parent/Tuteur :', eleve.get('nom_parent', '-')],
    ]
    t_infos = Table(infos, colWidths=[4 * cm, 13 * cm])
    t_infos.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0F2C5C')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_infos)
    elements.append(Spacer(1, 0.5 * cm))

    niveau = None
    if eleve.get('classe'):
        try:
            from core.classes import lister_classes
            for c in lister_classes():
                if c['nom'] == eleve['classe']:
                    niveau = c.get('niveau')
                    break
        except Exception:
            pass

    matieres = lister_matieres(niveau=niveau, actif=True)
    notes = notes_eleve(eleve['id'], trimestre, annee)

    data = [['Matiere', 'Coef.', 'Note/20', 'Note pond.']]
    total_pond = 0
    total_coef = 0

    for m in matieres:
        note_val = notes.get(m['id'], 0)
        coef = m['coefficient'] or 1
        pond = note_val * coef
        total_pond += pond
        total_coef += coef
        data.append([
            m['nom'], str(coef),
            f"{note_val:.2f}" if note_val else '-',
            f"{pond:.2f}" if note_val else '-',
        ])

    moyenne = round(total_pond / total_coef, 2) if total_coef > 0 else 0
    data.append(['TOTAL', str(total_coef), '', f"{total_pond:.2f}"])
    data.append(['MOYENNE', '', '', f"{moyenne:.2f} / 20"])

    t_notes = Table(data, colWidths=[9 * cm, 2 * cm, 3 * cm, 3 * cm])
    t_notes.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F2C5C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -3), 0.5, colors.grey),
        ('BACKGROUND', (0, -2), (-1, -2), colors.HexColor('#E8F4EA')),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F0F7FF')),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#27ae60')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_notes)
    elements.append(Spacer(1, 0.5 * cm))

    rang, effectif = rang_eleve(eleve['id'], eleve.get('classe', ''), trimestre, annee)
    rang_txt = f"{rang} / {effectif}" if rang else f"- / {effectif}"

    infos2 = [['Moyenne generale :', f"{moyenne:.2f} / 20"], ['Rang :', rang_txt]]
    t_infos2 = Table(infos2, colWidths=[5 * cm, 12 * cm])
    t_infos2.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0F2C5C')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_infos2)
    elements.append(Spacer(1, 1 * cm))

    if moyenne >= 16:
        app = 'Excellent travail, felicitations !'
    elif moyenne >= 14:
        app = 'Tres bon travail, continue ainsi.'
    elif moyenne >= 12:
        app = 'Bon travail, peut mieux faire.'
    elif moyenne >= 10:
        app = 'Travail passable, des efforts a fournir.'
    else:
        app = 'Travail insuffisant, doit redoubler d efforts.'

    elements.append(Paragraph(f'<b>Appreciation :</b> {app}', label_style))
    elements.append(Spacer(1, 1.5 * cm))

    sign = [['Le Titulaire', 'Le Directeur', 'Le Parent']]
    t_sign = Table(sign, colWidths=[5.6 * cm, 5.7 * cm, 5.7 * cm])
    t_sign.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0F2C5C')),
        ('TOPPADDING', (0, 0), (-1, -1), 30),
    ]))
    elements.append(t_sign)

    doc.build(elements)
    return chemin
