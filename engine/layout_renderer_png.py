import os
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops


# ── Font lookup ────────────────────────────────────────────────────────────────

_FONT_CACHE: dict = {}

_SYSTEM_FONT_DIRS = [
    Path("C:/Windows/Fonts"),
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts",
    # Linux/Mac system paths
    Path("/usr/share/fonts/truetype"),
    Path("/usr/share/fonts"),
    Path("/Library/Fonts"),
    Path(os.path.expanduser("~")) / "Library" / "Fonts",
]

# (family_lower) → { (bold, italic) → [filename, ...] }
# I file Lora-*.ttf sono bundled nella cartella fonts/ del progetto
# e fungono da fallback cross-platform per Georgia.
_FONT_FILES: dict = {
    "arial": {
        (False, False): ["arial.ttf", "LiberationSans-Regular.ttf"],
        (True,  False): ["arialbd.ttf", "LiberationSans-Bold.ttf"],
        (False, True):  ["ariali.ttf", "LiberationSans-Italic.ttf"],
        (True,  True):  ["arialbi.ttf", "LiberationSans-BoldItalic.ttf"],
    },
    "georgia": {
        # Prima cerca Georgia di sistema, poi Lora bundled (open-source, SIL OFL)
        (False, False): ["georgia.ttf",  "Lora-Regular.ttf"],
        (True,  False): ["georgiab.ttf", "Lora-Bold.ttf"],
        (False, True):  ["georgiai.ttf", "Lora-Italic.ttf"],
        (True,  True):  ["georgiaz.ttf", "Lora-BoldItalic.ttf"],
    },
    "lora": {
        (False, False): ["Lora-Regular.ttf"],
        (True,  False): ["Lora-Bold.ttf"],
        (False, True):  ["Lora-Italic.ttf"],
        (True,  True):  ["Lora-BoldItalic.ttf"],
    },
    "montserrat": {
        (False, False): ["Montserrat-Regular.ttf",  "Montserrat-VariableFont_wght.ttf"],
        (True,  False): ["Montserrat-Bold.ttf",     "Montserrat-SemiBold.ttf", "Montserrat-VariableFont_wght.ttf"],
        (False, True):  ["Montserrat-Italic.ttf",   "Montserrat-Italic-VariableFont_wght.ttf"],
        (True,  True):  ["Montserrat-BoldItalic.ttf", "Montserrat-Italic-VariableFont_wght.ttf"],
    },
    "times new roman": {
        (False, False): ["times.ttf", "LiberationSerif-Regular.ttf"],
        (True,  False): ["timesbd.ttf", "LiberationSerif-Bold.ttf"],
        (False, True):  ["timesi.ttf", "LiberationSerif-Italic.ttf"],
        (True,  True):  ["timesbi.ttf", "LiberationSerif-BoldItalic.ttf"],
    },
    # ── Font CJK (cinese/giapponese/coreano) ──────────────────────────────────
    # Uso: font: "simhei"  oppure  font: "noto cjk"
    "simhei": {
        (False, False): ["simhei.ttf"],
        (True,  False): ["simhei.ttf"],
        (False, True):  ["simhei.ttf"],
        (True,  True):  ["simhei.ttf"],
    },
    "simsun": {
        (False, False): ["simsun.ttc"],
        (True,  False): ["simsunb.ttf", "simsun.ttc"],
        (False, True):  ["simsun.ttc"],
        (True,  True):  ["simsun.ttc"],
    },
    "noto cjk": {
        (False, False): ["NotoSansCJK-Regular.ttc", "NotoSansSC-Regular.otf", "NotoSerifCJK-Regular.ttc"],
        (True,  False): ["NotoSansCJK-Bold.ttc",    "NotoSansSC-Bold.otf",    "NotoSerifCJK-Bold.ttc"],
        (False, True):  ["NotoSansCJK-Regular.ttc"],
        (True,  True):  ["NotoSansCJK-Bold.ttc"],
    },
}


def _has_cjk(text: str) -> bool:
    """Restituisce True se il testo contiene caratteri CJK (cinese, giapponese, coreano)."""
    for ch in text:
        cp = ord(ch)
        if (0x4E00 <= cp <= 0x9FFF    # CJK Unified Ideographs
                or 0x3400 <= cp <= 0x4DBF   # CJK Extension A
                or 0x3000 <= cp <= 0x303F   # CJK Symbols
                or 0xFF00 <= cp <= 0xFFEF): # Halfwidth/Fullwidth
            return True
    return False


def _find_font_path(family_lower: str, bold: bool, italic: bool, project_font_dir: Path) -> Path | None:
    key = (bold, italic)
    candidates = _FONT_FILES.get(family_lower, {}).get(key, [])

    search_dirs = [project_font_dir] + _SYSTEM_FONT_DIRS

    for filename in candidates:
        for d in search_dirs:
            p = d / filename
            if p.exists():
                return p

    # Fallback: try plain variant
    if bold or italic:
        plain = _FONT_FILES.get(family_lower, {}).get((False, False), [])
        for filename in plain:
            for d in search_dirs:
                p = d / filename
                if p.exists():
                    return p

    return None


def _load_font(family: str, bold: bool, italic: bool, size: int, project_font_dir: Path) -> ImageFont.FreeTypeFont:
    cache_key = (family.lower(), bold, italic, size)
    if cache_key in _FONT_CACHE:
        return _FONT_CACHE[cache_key]

    path = _find_font_path(family.lower(), bold, italic, project_font_dir)
    font: ImageFont.FreeTypeFont
    if path:
        try:
            font = ImageFont.truetype(str(path), size)
            _FONT_CACHE[cache_key] = font
            return font
        except Exception as exc:
            print(f"[WARNING] Impossibile caricare font '{path}': {exc}")

    print(f"[WARNING] Font '{family}' non trovato — uso default")
    font = ImageFont.load_default(size=size)  # type: ignore[arg-type]
    _FONT_CACHE[cache_key] = font
    return font


# ── Color parsing ──────────────────────────────────────────────────────────────

def _parse_color(value: str, opacity: float | None = None) -> tuple[int, int, int, int]:
    """Returns (R, G, B, A). Hex: #RRGGBB or #RRGGBBAA."""
    text = str(value).strip().lstrip("#")
    if len(text) == 8:
        r, g, b, a = (int(text[i:i+2], 16) for i in (0, 2, 4, 6))
    elif len(text) == 6:
        r, g, b = (int(text[i:i+2], 16) for i in (0, 2, 4))
        a = 255
    else:
        raise ValueError(f"Colore non valido: '{value}'")

    if opacity is not None:
        a = int(round(max(0.0, min(1.0, float(opacity))) * a))

    return (r, g, b, a)


# ── Shadow helper ─────────────────────────────────────────────────────────────

def _apply_shape_shadow(
    composite: Image.Image,
    x: int, y: int, w: int, h: int,
    radius: int,
    shadow: dict,
) -> None:
    blur   = float(shadow.get("blur", 8))
    ox     = int(shadow.get("offset_x", 4))
    oy     = int(shadow.get("offset_y", 4))
    color  = _parse_color(shadow.get("color", "#00000066"))

    layer = Image.new("RGBA", composite.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    sx, sy = x + ox, y + oy
    box = [sx, sy, sx + w - 1, sy + h - 1]
    if radius > 0:
        d.rounded_rectangle(box, radius=radius, fill=color)
    else:
        d.rectangle(box, fill=color)

    if blur > 0:
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    composite.alpha_composite(layer)


# ── Gradient helpers ──────────────────────────────────────────────────────────

def _lerp_color(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(a[i] + t * (b[i] - a[i])) for i in range(4))


def _make_gradient_image(w: int, h: int, gradient: dict) -> Image.Image:
    """Crea un'immagine RGBA con gradiente lineare (angolato) o radiale."""
    g_type = gradient.get("type", "linear")
    # supporta sia start/end che from/to
    c_from = _parse_color(gradient.get("from") or gradient.get("start", "#000000"))
    c_to   = _parse_color(gradient.get("to")   or gradient.get("end",   "#FFFFFF"))

    band = Image.new("RGBA", (w, h))
    pixels = band.load()

    if g_type == "radial":
        cx = float(gradient.get("cx", 0.5)) * w
        cy = float(gradient.get("cy", 0.5)) * h
        max_r = math.sqrt((max(cx, w - cx)) ** 2 + (max(cy, h - cy)) ** 2)
        for py in range(h):
            for px in range(w):
                r = math.sqrt((px - cx) ** 2 + (py - cy) ** 2)
                t = min(r / max_r, 1.0)
                pixels[px, py] = _lerp_color(c_from, c_to, t)
    else:
        # Linear — angle in gradi (0=top→bottom, 90=left→right, 45=diagonale)
        angle_deg = float(gradient.get("angle", 0)
                          if "angle" in gradient
                          else (0 if gradient.get("direction", "vertical") == "vertical" else 90))
        angle_rad = math.radians(angle_deg)
        dx = math.sin(angle_rad)
        dy = math.cos(angle_rad)
        # proiezione: t = (px*dx + py*dy) normalizzato in [0,1]
        proj_min = 0 * dx + 0 * dy
        proj_max = (w - 1) * dx + (h - 1) * dy
        span = proj_max - proj_min if proj_max != proj_min else 1
        for py in range(h):
            for px in range(w):
                t = ((px * dx + py * dy) - proj_min) / span
                t = max(0.0, min(1.0, t))
                pixels[px, py] = _lerp_color(c_from, c_to, t)
    return band


def _draw_gradient(
    composite: Image.Image,
    x: int, y: int, w: int, h: int,
    radius: int,
    gradient: dict,
) -> None:
    band = _make_gradient_image(w, h, gradient)

    if radius > 0:
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
        band.putalpha(mask)

    composite.alpha_composite(band, dest=(x, y))


# ── Blend modes ───────────────────────────────────────────────────────────────

def _apply_blend(base: Image.Image, top: Image.Image, mode: str, opacity: float = 1.0) -> None:
    """Applica top su base con blend mode. Modifica base in-place."""
    if opacity < 1.0:
        r, g, b, a = top.split()
        a = a.point(lambda v: int(v * opacity))
        top = Image.merge("RGBA", (r, g, b, a))

    if mode == "normal":
        base.alpha_composite(top)
        return

    # Lavora in RGB, poi riaggiungiamo l'alpha
    base_rgb = base.convert("RGB")
    top_rgb  = top.convert("RGB")
    top_a    = top.split()[3]

    if mode == "multiply":
        blended = ImageChops.multiply(base_rgb, top_rgb)
    elif mode == "screen":
        blended = ImageChops.screen(base_rgb, top_rgb)
    elif mode == "overlay":
        # overlay = 2*a*b/255 se a<128 else 255-2*(255-a)*(255-b)/255
        import numpy as np
        a_arr = np.array(base_rgb, dtype=float)
        b_arr = np.array(top_rgb,  dtype=float)
        mask  = a_arr < 128
        result = np.where(mask, 2 * a_arr * b_arr / 255,
                          255 - 2 * (255 - a_arr) * (255 - b_arr) / 255)
        blended = Image.fromarray(np.clip(result, 0, 255).astype("uint8"), "RGB")
    elif mode == "soft_light":
        import numpy as np
        a_arr = np.array(base_rgb, dtype=float) / 255
        b_arr = np.array(top_rgb,  dtype=float) / 255
        result = (1 - 2 * b_arr) * a_arr ** 2 + 2 * b_arr * a_arr
        blended = Image.fromarray((np.clip(result, 0, 1) * 255).astype("uint8"), "RGB")
    elif mode == "add":
        blended = ImageChops.add(base_rgb, top_rgb)
    elif mode == "difference":
        blended = ImageChops.difference(base_rgb, top_rgb)
    else:
        base.alpha_composite(top)
        return

    # Componi il risultato blend solo dove top è visibile
    blended_rgba = blended.convert("RGBA")
    # Usa l'alpha del layer top come maschera di compositing
    mask_img = Image.new("L", top.size, 0)
    mask_img.paste(top_a, (0, 0))
    base.paste(blended_rgba, (0, 0), mask_img)


# ── Text effects ──────────────────────────────────────────────────────────────

def _draw_text_stroke(
    layer_img: Image.Image,
    line: str, tx: int, ty_draw: int,
    font: ImageFont.FreeTypeFont,
    stroke_color: tuple, stroke_width: int,
) -> None:
    """Disegna il contorno del testo espandendo la maschera del glyph."""
    # Renderizza il testo come maschera
    mask_img = Image.new("L", layer_img.size, 0)
    ImageDraw.Draw(mask_img).text((tx, ty_draw), line, font=font, fill=255)
    # Espandi la maschera (effetto stroke)
    expanded = mask_img.filter(ImageFilter.MaxFilter(stroke_width * 2 + 1))
    stroke_layer = Image.new("RGBA", layer_img.size, (0, 0, 0, 0))
    stroke_layer.paste(Image.new("RGBA", layer_img.size, stroke_color), mask=expanded)
    layer_img.alpha_composite(stroke_layer)


def _draw_text_gradient(
    layer_img: Image.Image,
    line: str, tx: int, ty_draw: int,
    font: ImageFont.FreeTypeFont,
    gradient: dict,
) -> None:
    """Disegna il testo riempito con un gradiente."""
    # 1. Crea maschera testo
    mask_img = Image.new("L", layer_img.size, 0)
    ImageDraw.Draw(mask_img).text((tx, ty_draw), line, font=font, fill=255)
    # 2. Crea gradiente della dimensione del canvas
    grad = _make_gradient_image(layer_img.width, layer_img.height, gradient)
    # 3. Applica maschera al gradiente
    grad.putalpha(mask_img)
    layer_img.alpha_composite(grad)


# ── Text wrapping ─────────────────────────────────────────────────────────────

def _wrap(text: str, font: ImageFont.FreeTypeFont, max_px: int) -> list[str]:
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))

    def measure(t: str) -> int:
        if not t:
            return 0
        bb = dummy.textbbox((0, 0), t, font=font)
        return bb[2] - bb[0]

    def wrap_segment(segment: str) -> list[str]:
        """Word-wrap un singolo segmento (senza \n)."""
        if measure(segment) <= max_px:
            return [segment]
        words = segment.split()
        if not words:
            return [""]
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = (current + " " + word).strip()
            if measure(candidate) <= max_px:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [segment]

    # Rispetta prima i \n espliciti nel testo, poi applica word-wrap a ogni segmento
    result: list[str] = []
    for segment in text.split("\n"):
        result.extend(wrap_segment(segment))

    return result or [text]


# ── Layer renderers ────────────────────────────────────────────────────────────

def _render_rect(composite: Image.Image, layer: dict) -> None:
    x = int(layer["x"])
    y = int(layer["y"])
    w = int(layer["w"])
    h = int(layer["h"])
    radius = int(layer.get("radius", 0) or 0)
    fill = _parse_color(layer.get("fill", "#FFFFFF"), layer.get("opacity"))

    shadow = layer.get("shadow")
    if shadow:
        _apply_shape_shadow(composite, x, y, w, h, radius, shadow)

    gradient = layer.get("gradient")
    if gradient:
        _draw_gradient(composite, x, y, w, h, radius, gradient)
    else:
        d = ImageDraw.Draw(composite)
        box = [x, y, x + w - 1, y + h - 1]
        if radius > 0:
            d.rounded_rectangle(box, radius=radius, fill=fill)
        else:
            d.rectangle(box, fill=fill)


def _render_text(composite: Image.Image, layer: dict, project_font_dir: Path) -> None:
    x     = int(layer["x"])
    y     = int(layer["y"])
    w     = int(layer["w"])
    h     = int(layer["h"])
    text  = str(layer.get("text", ""))
    if layer.get("uppercase"):
        text = text.upper()

    family         = layer.get("font", "Arial")
    bold           = bool(layer.get("bold",   False))
    italic         = bool(layer.get("italic", False))
    size           = max(1, int(float(layer.get("size", 24))))
    color          = _parse_color(layer.get("color", "#000000"), layer.get("opacity"))
    align          = str(layer.get("align", "left")).lower()
    spacing        = float(layer.get("letter_spacing", 0))
    lh_mult        = float(layer.get("line_height", 1.2))
    shadow         = layer.get("shadow")
    stroke_color   = layer.get("stroke_color")
    stroke_width   = int(layer.get("stroke_width", 3))
    gradient_fill  = layer.get("gradient_fill")   # dict con from/to/angle

    font = _load_font(family, bold, italic, size, project_font_dir)
    # Fallback automatico CJK
    if _has_cjk(text) and family.lower() not in ("simhei", "simsun", "noto cjk", "msgothic"):
        font = _load_font("simsun", bold, italic, size, project_font_dir)

    lines    = _wrap(text, font, w)
    line_gap = int(size * lh_mult)

    d  = ImageDraw.Draw(composite)
    ty = y

    for line in lines:
        bb     = d.textbbox((0, 0), line, font=font)
        text_w = bb[2] - bb[0]

        if align == "center":
            tx = x + (w - text_w) // 2
        elif align == "right":
            tx = x + w - text_w
        else:
            tx = x

        tx     -= bb[0]
        ty_draw = ty - bb[1]

        # ── 1. Shadow ────────────────────────────────────────────────────────
        if shadow:
            sc  = _parse_color(shadow.get("color", "#00000066"))
            sox = int(shadow.get("offset_x", 2))
            soy = int(shadow.get("offset_y", 2))
            sb  = float(shadow.get("blur", 0))
            if sb > 0:
                sl = Image.new("RGBA", composite.size, (0, 0, 0, 0))
                ImageDraw.Draw(sl).text((tx + sox, ty_draw + soy), line, font=font, fill=sc)
                sl = sl.filter(ImageFilter.GaussianBlur(sb))
                composite.alpha_composite(sl)
            else:
                d.text((tx + sox, ty_draw + soy), line, font=font, fill=sc)

        # ── 2. Stroke / outline ──────────────────────────────────────────────
        if stroke_color:
            sc_rgba = _parse_color(stroke_color)
            _draw_text_stroke(composite, line, tx, ty_draw, font, sc_rgba, stroke_width)

        # ── 3. Fill: gradiente o colore piatto ───────────────────────────────
        if gradient_fill:
            _draw_text_gradient(composite, line, tx, ty_draw, font, gradient_fill)
        elif spacing != 0:
            _draw_tracked(d, line, tx, ty_draw, font, color, int(spacing))
        else:
            d.text((tx, ty_draw), line, font=font, fill=color)

        ty += line_gap
        if ty > y + h:
            break


def _draw_tracked(
    d: ImageDraw.ImageDraw,
    text: str,
    x: int, y: int,
    font: ImageFont.FreeTypeFont,
    fill: tuple,
    spacing: int,
) -> None:
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        bb = d.textbbox((0, 0), ch, font=font)
        x += (bb[2] - bb[0]) + spacing


def _render_image(
    composite: Image.Image,
    layer: dict,
    assets_base: Path,
    warnings: list[str],
) -> None:
    src  = layer["src"]
    path = assets_base / src
    # Fallback: se non trovata, prova anche assets/images/ relativo alla root
    if not path.exists():
        alt = assets_base.parent.parent / "assets" / "images" / src
        if alt.exists():
            path = alt
    if not path.exists():
        msg = f"Immagine mancante per layer '{layer.get('id', '?')}': {src}"
        warnings.append(msg)
        print(f"[WARNING] {msg}")
        return

    x = int(layer["x"])
    y = int(layer["y"])
    w = int(layer["w"])
    h = int(layer["h"])
    fit     = str(layer.get("fit", "cover")).lower()
    opacity = layer.get("opacity")

    try:
        img = Image.open(path).convert("RGBA")
    except Exception as exc:
        msg = f"Impossibile aprire '{path}': {exc}"
        warnings.append(msg)
        print(f"[WARNING] {msg}")
        return

    iw, ih = img.size

    if fit == "cover":
        img_ar = iw / ih
        box_ar = w / h
        if img_ar > box_ar:
            nw = int(h * img_ar); nh = h
        else:
            nw = w; nh = int(w / img_ar)
        img = img.resize((nw, nh), Image.LANCZOS)
        left = (nw - w) // 2
        top  = (nh - h) // 2
        img  = img.crop((left, top, left + w, top + h))
    elif fit == "contain":
        img_ar = iw / ih
        box_ar = w / h
        if img_ar > box_ar:
            nw = w; nh = int(w / img_ar)
        else:
            nw = int(h * img_ar); nh = h
        img = img.resize((nw, nh), Image.LANCZOS)
        x += (w - nw) // 2
        y += (h - nh) // 2
        w, h = nw, nh
    else:
        img = img.resize((w, h), Image.LANCZOS)

    blend_mode = str(layer.get("blend_mode", "normal")).lower()
    op_val     = float(opacity) if opacity is not None else 1.0

    # Clip to canvas bounds
    cw, ch = composite.size
    if x < 0 or y < 0 or x + w > cw or y + h > ch:
        cx1 = max(x, 0); cy1 = max(y, 0)
        cx2 = min(x + w, cw); cy2 = min(y + h, ch)
        img = img.crop((cx1 - x, cy1 - y, cx2 - x, cy2 - y))
        x, y = cx1, cy1

    if blend_mode == "normal":
        if opacity is not None:
            alpha = img.getchannel("A")
            alpha = alpha.point(lambda p: int(p * op_val))
            img.putalpha(alpha)
        composite.alpha_composite(img, dest=(x, y))
    else:
        # Per blend modes: lavoriamo su un sub-canvas della stessa dimensione
        sub = composite.crop((x, y, x + img.width, y + img.height))
        _apply_blend(sub, img, blend_mode, op_val)
        composite.paste(sub, (x, y))


def _render_line(composite: Image.Image, layer: dict) -> None:
    x1 = int(layer["x1"]); y1 = int(layer["y1"])
    x2 = int(layer["x2"]); y2 = int(layer["y2"])
    color = _parse_color(layer.get("color", "#000000"))
    width = max(1, int(float(layer.get("width", 1))))

    ImageDraw.Draw(composite).line([(x1, y1), (x2, y2)], fill=color, width=width)


def _render_circle(composite: Image.Image, layer: dict) -> None:
    x = int(layer["x"]); y = int(layer["y"])
    w = int(layer["w"]); h = int(layer["h"])
    fill    = _parse_color(layer.get("fill", "#000000"), layer.get("opacity"))
    outline = layer.get("outline")
    outline_w = int(layer.get("outline_width", 2))

    shadow = layer.get("shadow")
    if shadow:
        _apply_shape_shadow(composite, x, y, w, h, min(w, h) // 2, shadow)

    d = ImageDraw.Draw(composite)
    box = [x, y, x + w - 1, y + h - 1]
    kwargs: dict = {"fill": fill}
    if outline:
        kwargs["outline"] = _parse_color(outline)
        kwargs["width"]   = outline_w
    d.ellipse(box, **kwargs)


# ── Icon rendering ─────────────────────────────────────────────────────────────

_ICON_EMOJI: dict[str, str] = {
    "pin":        "📍",
    "location":   "📍",
    "sede":       "📍",
    "phone":      "📞",
    "telefono":   "📞",
    "mail":       "📧",
    "email":      "📧",
    "clock":      "🕐",
    "orario":     "🕐",
    "calendar":   "📅",
    "data":       "📅",
    "star":       "⭐",
    "check":      "✓",
    "arrow":      "➜",
    "info":       "ℹ",
    "whatsapp":   "💬",
    "instagram":  "📷",
    "facebook":   "f",
    "warning":    "⚠",
    "fire":       "🔥",
    "people":     "👥",
    "trophy":     "🏆",
}

_EMOJI_FONT_CACHE: dict = {}


def _get_emoji_font(size: int) -> ImageFont.FreeTypeFont:
    if size in _EMOJI_FONT_CACHE:
        return _EMOJI_FONT_CACHE[size]
    for name in ("seguiemj.ttf", "seguisym.ttf", "NotoColorEmoji.ttf"):
        for d in [Path("C:/Windows/Fonts"), Path.home() / "AppData/Local/Microsoft/Windows/Fonts"]:
            p = d / name
            if p.exists():
                try:
                    f = ImageFont.truetype(str(p), size)
                    _EMOJI_FONT_CACHE[size] = f
                    return f
                except Exception:
                    pass
    f = ImageFont.load_default(size=size)  # type: ignore[arg-type]
    _EMOJI_FONT_CACHE[size] = f
    return f


def _render_icon(composite: Image.Image, layer: dict, project_font_dir: Path) -> None:
    x = int(layer["x"]); y = int(layer["y"])
    w = int(layer["w"]); h = int(layer["h"])
    name  = str(layer.get("name", "")).lower()
    color = _parse_color(layer.get("color", "#000000"), layer.get("opacity"))
    size  = min(w, h)

    glyph = _ICON_EMOJI.get(name, name)

    font = _get_emoji_font(size)
    d    = ImageDraw.Draw(composite)
    bb   = d.textbbox((0, 0), glyph, font=font)
    gw   = bb[2] - bb[0]
    gh   = bb[3] - bb[1]
    tx   = x + (w - gw) // 2 - bb[0]
    ty   = y + (h - gh) // 2 - bb[1]
    d.text((tx, ty), glyph, font=font, fill=color)


# ── QR Code rendering ──────────────────────────────────────────────────────────

def _render_qrcode(composite: Image.Image, layer: dict, warnings: list[str]) -> None:
    try:
        import qrcode  # type: ignore[import]
    except ImportError:
        msg = "qrcode non installato. Esegui: pip install qrcode[pil]"
        warnings.append(msg)
        print(f"[WARNING] {msg}")
        return

    x = int(layer["x"]); y = int(layer["y"])
    w = int(layer["w"]); h = int(layer["h"])
    data = str(layer["data"])

    fg = layer.get("color",      "#000000")
    bg = layer.get("background", "#FFFFFF")

    try:
        fg_rgb = _parse_color(fg)[:3]
        bg_rgb = _parse_color(bg)[:3]
    except Exception:
        fg_rgb = (0, 0, 0)
        bg_rgb = (255, 255, 255)

    qr = qrcode.QRCode(border=1)
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=fg_rgb, back_color=bg_rgb).convert("RGBA")
    qr_img = qr_img.resize((w, h), Image.LANCZOS)
    composite.alpha_composite(qr_img, dest=(x, y))


# ── Vignette & gradient overlay ───────────────────────────────────────────────

def _render_vignette(composite: Image.Image, layer: dict) -> None:
    """Vignetta radiale scura ai bordi — effetto cinematografico."""
    cw, ch = composite.size
    x = int(layer.get("x", 0))
    y = int(layer.get("y", 0))
    w = int(layer.get("w", cw))
    h = int(layer.get("h", ch))
    color     = _parse_color(layer.get("color", "#000000"))
    intensity = float(layer.get("intensity", 0.6))   # 0-1
    feather   = float(layer.get("feather", 0.55))     # raggio relativo del centro trasparente

    vig = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pix = vig.load()
    cx, cy = w / 2, h / 2
    max_r = math.sqrt(cx ** 2 + cy ** 2)

    for py in range(h):
        for px in range(w):
            r = math.sqrt((px - cx) ** 2 + (py - cy) ** 2) / max_r
            t = max(0.0, (r - feather) / (1.0 - feather)) if r > feather else 0.0
            a = int(t * intensity * 255)
            pix[px, py] = (color[0], color[1], color[2], a)

    composite.alpha_composite(vig, dest=(x, y))


def _render_gradient_overlay(composite: Image.Image, layer: dict) -> None:
    """Gradiente sovrapposto all'intera area — utile per scurire/colorare."""
    cw, ch = composite.size
    x = int(layer.get("x", 0))
    y = int(layer.get("y", 0))
    w = int(layer.get("w", cw))
    h = int(layer.get("h", ch))
    opacity    = layer.get("opacity", 1.0)
    blend_mode = str(layer.get("blend_mode", "normal")).lower()
    gradient   = layer.get("gradient", {"from": "#00000000", "to": "#000000AA"})

    band = _make_gradient_image(w, h, gradient)
    if blend_mode == "normal":
        if float(opacity) < 1.0:
            r, g, b, a = band.split()
            a = a.point(lambda v: int(v * float(opacity)))
            band = Image.merge("RGBA", (r, g, b, a))
        composite.alpha_composite(band, dest=(x, y))
    else:
        sub = composite.crop((x, y, x + w, y + h))
        _apply_blend(sub, band, blend_mode, float(opacity))
        composite.paste(sub, (x, y))


# ── Public API ─────────────────────────────────────────────────────────────────

def render_layout_to_png(
    layout: dict,
    project_root: str | Path,
    output_path: str | Path,
) -> tuple[Path, list[str]]:
    project_root = Path(project_root)
    output_path  = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    project_font_dir = project_root / "fonts"

    canvas = layout["canvas"]
    cw = int(canvas["width"])
    ch = int(canvas["height"])
    bg = _parse_color(canvas.get("background", "#FFFFFF"))

    composite = Image.new("RGBA", (cw, ch), bg)

    assets_raw  = layout.get("assets_base", "")
    ab          = Path(assets_raw)
    # Default: assets/images/ — se non specificato usa quella cartella
    assets_base = ab if ab.is_absolute() else project_root / ab if assets_raw else project_root / "assets" / "images"

    warnings: list[str] = []

    for layer in layout.get("layers", []):
        ltype = layer.get("type")
        try:
            if ltype == "rect":
                _render_rect(composite, layer)
            elif ltype == "text":
                _render_text(composite, layer, project_font_dir)
            elif ltype == "image":
                _render_image(composite, layer, assets_base, warnings)
            elif ltype == "line":
                _render_line(composite, layer)
            elif ltype == "circle":
                _render_circle(composite, layer)
            elif ltype == "icon":
                _render_icon(composite, layer, project_font_dir)
            elif ltype == "qrcode":
                _render_qrcode(composite, layer, warnings)
            elif ltype == "vignette":
                _render_vignette(composite, layer)
            elif ltype == "gradient_overlay":
                _render_gradient_overlay(composite, layer)
        except Exception as exc:
            msg = f"Errore nel layer '{layer.get('id', ltype)}': {exc}"
            warnings.append(msg)
            print(f"[WARNING] {msg}")

    composite.convert("RGB").save(str(output_path), "PNG", optimize=False)
    return output_path, warnings
