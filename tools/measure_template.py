"""
Analizza template_nutrizionisti.jpg e trova le bounding box
degli elementi chiave per posizionare i testi.
Scala tutto alle coordinate del canvas 1080x1530.
"""
from PIL import Image
import numpy as np

IMG_PATH = "assets/images/template_nutrizionisti.jpg"
CANVAS_W, CANVAS_H = 1080, 1530

img = Image.open(IMG_PATH).convert("RGB")
orig_w, orig_h = img.size
sx = CANVAS_W / orig_w   # scale x
sy = CANVAS_H / orig_h   # scale y

arr = np.array(img)

def to_canvas(x, y):
    return int(x * sx), int(y * sy)

def scan_color_row(arr, target_rgb, tolerance=30, min_width=50):
    """Trova la prima riga che contiene una banda del colore target."""
    results = []
    for y in range(arr.shape[0]):
        row = arr[y]
        match = np.all(np.abs(row.astype(int) - target_rgb) < tolerance, axis=1)
        run = 0
        for v in match:
            if v:
                run += 1
            else:
                if run >= min_width:
                    break
                run = 0
        if run >= min_width:
            results.append(y)
    return results

def find_box_extents(arr, target_rgb, tolerance=30):
    """Trova top/bottom/left/right di una zona colorata."""
    mask = np.all(np.abs(arr.astype(int) - target_rgb) < tolerance, axis=2)
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if len(rows) == 0 or len(cols) == 0:
        return None
    return {"top": rows[0], "bottom": rows[-1],
            "left": cols[0],  "right": cols[-1]}

print(f"Template originale: {orig_w}x{orig_h}")
print(f"Scale: sx={sx:.4f}  sy={sy:.4f}")
print()

# ── Verde scuro dei pill/box (#254A18) ─────────────────────────────────────
green = [37, 74, 24]
g = find_box_extents(arr, green, tolerance=25)
if g:
    print("ZONA VERDE SCURO (pill + feature box):")
    print(f"  orig:   y={g['top']}-{g['bottom']}  x={g['left']}-{g['right']}")
    print(f"  canvas: y={int(g['top']*sy)}-{int(g['bottom']*sy)}  x={int(g['left']*sx)}-{int(g['right']*sx)}")
    print()

# ── Oro del badge/divisore (#C5A635) ──────────────────────────────────────
gold = [197, 166, 53]
go = find_box_extents(arr, gold, tolerance=30)
if go:
    print("ZONA ORO (badge + divisori):")
    print(f"  orig:   y={go['top']}-{go['bottom']}  x={go['left']}-{go['right']}")
    print(f"  canvas: y={int(go['top']*sy)}-{int(go['bottom']*sy)}  x={int(go['left']*sx)}-{int(go['right']*sx)}")
    print()

# Cerca le singole bande verdi (pill) scansionando per sottosezioni
print("BANDE ORIZZONTALI VERDI (ogni pill/box):")
in_band = False
bands = []
for y in range(arr.shape[0]):
    row_green = np.all(np.abs(arr[y].astype(int) - green) < 25, axis=1)
    green_count = row_green.sum()
    if green_count > 100 and not in_band:
        in_band = True
        band_start = y
        band_max_green = 0
    if in_band:
        if green_count > band_max_green:
            band_max_green = green_count
        if green_count < 30:
            in_band = False
            bands.append((band_start, y - 1, band_max_green))

for i, (ys, ye, gc) in enumerate(bands):
    ys_c, ye_c = int(ys * sy), int(ye * sy)
    h = ye_c - ys_c
    print(f"  Banda {i+1}: orig y={ys}-{ye}  ->  canvas y={ys_c}-{ye_c}  h={h}px  ({gc}px green/row)")

# Divider line (gold thin horizontal line)
print()
print("LINEA GOLD ORIZZONTALE (divisore):")
thin_gold_rows = []
for y in range(arr.shape[0]):
    row = arr[y]
    gold_px = np.all(np.abs(row.astype(int) - gold) < 35, axis=1).sum()
    if 20 < gold_px < 250:
        thin_gold_rows.append(y)

if thin_gold_rows:
    # Raggruppa
    groups = []
    start = thin_gold_rows[0]
    prev = thin_gold_rows[0]
    for y in thin_gold_rows[1:]:
        if y - prev > 5:
            groups.append((start, prev))
            start = y
        prev = y
    groups.append((start, prev))
    for gs, ge in groups:
        print(f"  orig y={gs}-{ge}  ->  canvas y={int(gs*sy)}-{int(ge*sy)}")
