from PIL import Image, ImageDraw, ImageFont

img = Image.new("RGB", (1, 1))
d = ImageDraw.Draw(img)

words = ["CORSO DI", "FORMAZIONE", "PER", "NUTRIZIONISTI"]

for size in [88, 80, 72, 68, 64, 60]:
    font = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", size)
    print(f"\n=== {size}pt ===")
    for w in words:
        bb = d.textbbox((0, 0), w, font=font)
        print(f"  {w:<20} w={bb[2]-bb[0]:4d}px  h={bb[3]-bb[1]:3d}px")
