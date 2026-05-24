"""
Probing preciso: salva profili orizzontali del template
per identificare le bande verdi e le zone di testo.
"""
from PIL import Image, ImageDraw

img = Image.open("assets/images/template_nutrizionisti.jpg").convert("RGB")
w, h = img.size
sx = 1080 / w
sy = 1530 / h

# Analizza ogni riga: media R,G,B nella colonna sinistra (x=20..550)
# e nella zona destra (x=550..1000)
rows_left = []
for y in range(h):
    pixels = [img.getpixel((x, y)) for x in range(20, 550, 5)]
    avg_r = sum(p[0] for p in pixels) / len(pixels)
    avg_g = sum(p[1] for p in pixels) / len(pixels)
    avg_b = sum(p[2] for p in pixels) / len(pixels)
    # Verifica se la riga e dominata da verde scuro (G alto rispetto a R/B)
    is_green = avg_g > 60 and avg_r < 100 and avg_b < 80 and avg_g > avg_r * 1.5
    # Verifica sfondo chiaro (crema)
    is_cream = avg_r > 200 and avg_g > 190 and avg_b > 160
    rows_left.append((y, avg_r, avg_g, avg_b, is_green, is_cream))

# Trova bande verdi consecutive
print("BANDE VERDI SCURE (sinistra, x=20-550):")
in_band = False
bands = []
for y, r, g, b, is_green, _ in rows_left:
    if is_green and not in_band:
        in_band = True
        band_y = y
    elif not is_green and in_band:
        in_band = False
        if y - band_y > 8:  # almeno 8px di altezza
            bands.append((band_y, y - 1))
if in_band:
    bands.append((band_y, h - 1))

for ys, ye in bands:
    print(f"  orig y={ys:4d}-{ye:4d}  h={ye-ys:3d}px  -> canvas y={int(ys*sy):4d}-{int(ye*sy):4d}  h={int((ye-ys)*sy):3d}px")

# Zona destra: cerchio dorato del badge
print()
print("ZONA DESTRA (x=600-1000) - bande non-crema:")
in_band = False
right_bands = []
for y in range(h):
    pixels = [img.getpixel((x, y)) for x in range(600, min(1000, w), 5)]
    avg_r = sum(p[0] for p in pixels) / len(pixels)
    avg_g = sum(p[1] for p in pixels) / len(pixels)
    avg_b = sum(p[2] for p in pixels) / len(pixels)
    is_gold = avg_r > 160 and avg_g > 130 and avg_b < 80 and avg_r > avg_b * 2
    is_green_r = avg_g > 60 and avg_r < 100 and avg_b < 80
    notable = is_gold or is_green_r
    if notable and not in_band:
        in_band = True
        band_y = y
        band_type = "GOLD" if is_gold else "GREEN"
    elif not notable and in_band:
        in_band = False
        if y - band_y > 6:
            right_bands.append((band_y, y - 1, band_type))

for ys, ye, t in right_bands:
    print(f"  [{t}] orig y={ys:4d}-{ye:4d}  h={ye-ys:3d}px  -> canvas y={int(ys*sy):4d}-{int(ye*sy):4d}")

# Profilo verticale sulla colonna x=30 (testo titolo):
# trova dove inizia e finisce la zona chiara (sfondo crema) per il titolo
print()
print("COLONNA x=30: transizioni sfondo chiaro/scuro (zona titolo):")
prev_cream = None
for y, r, g, b, is_green, is_cream in rows_left:
    if prev_cream is None:
        prev_cream = is_cream
    if is_cream != prev_cream:
        cy = int(y * sy)
        print(f"  y={y:4d} (canvas {cy}) : {'CREAM->DARK' if prev_cream else 'DARK->CREAM'}")
        prev_cream = is_cream

# Genera immagine annotata per verifica visiva
print()
print("Generando annotated_template.png per verifica visiva...")
annotated = img.copy().convert("RGB")
draw = ImageDraw.Draw(annotated)
for ys, ye in bands:
    draw.rectangle([0, ys, 10, ye], fill=(255, 0, 0))
annotated.save("output/annotated_template.png")
print("Salvato in output/annotated_template.png")
print(f"\nCanvas scale: {sx:.4f} x {sy:.4f}")
print(f"Usa moltiplicatore x*{sx:.4f} y*{sy:.4f} per convertire coord template->canvas")
