"""
Genere une icone B-NDEKE professionnelle en .ico
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Couleurs de l'app
NAVY = (15, 44, 92)       # #0F2C5C
GOLD = (242, 183, 5)      # #F2B705
WHITE = (255, 255, 255)

TAILLE = 512
img = Image.new("RGBA", (TAILLE, TAILLE), NAVY)
draw = ImageDraw.Draw(img)

# ===== Fond bleu marine avec bord arrondi =====
# Cercle interieur dore
marge = 40
draw.ellipse(
    [marge, marge, TAILLE - marge, TAILLE - marge],
    outline=GOLD,
    width=20,
)

# ===== Texte "B" au centre =====
try:
    # Essayer avec une police systeme
    police = ImageFont.truetype("segoeuib.ttf", 260)
except Exception:
    try:
        police = ImageFont.truetype("arialbd.ttf", 260)
    except Exception:
        police = ImageFont.load_default()

texte = "B"
bbox = draw.textbbox((0, 0), texte, font=police)
largeur = bbox[2] - bbox[0]
hauteur = bbox[3] - bbox[1]
x = (TAILLE - largeur) // 2 - bbox[0]
y = (TAILLE - hauteur) // 2 - bbox[1] - 20

draw.text((x, y), texte, fill=WHITE, font=police)

# ===== Petite etoile doree en haut a droite =====
def etoile(centre_x, centre_y, taille, couleur):
    """Dessine une etoile a 5 branches"""
    import math
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = taille if i % 2 == 0 else taille * 0.4
        points.append((
            centre_x + r * math.cos(angle),
            centre_y + r * math.sin(angle),
        ))
    draw.polygon(points, fill=couleur)

etoile(400, 120, 40, GOLD)

# ===== Enregistrer en .ico =====
os.makedirs("data", exist_ok=True)
chemin_ico = "data/bndeke.ico"

img.save(
    chemin_ico,
    format="ICO",
    sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
)

print(f"[OK] Icone creee : {chemin_ico}")
print(f"     Taille : {os.path.getsize(chemin_ico)} octets")