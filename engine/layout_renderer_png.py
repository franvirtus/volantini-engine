import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter


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


# ── Gradient helper ───────────────────────────────────────────────────────────

def _draw_gradient(
    composite: Image.Image,
    x: int, y: int, w: int, h: int,
    radius: int,
    gradient: dict,
) -> None:
    direction = gradient.get("direction", "vertical")
    start = _parse_color(gradient["start"])
    end   = _parse_color(gradient["end"])

    band = Image.new("RGBA", (w, h))
    steps = h if direction == "vertical" else w

    for i in range(steps):
        t = i / max(steps - 1, 1)
        pixel = tuple(int(s + t * (e - s)) for s, e in zip(start, end))
        if direction == "vertical":
            band.paste(pixel, (0, i, w, i + 1))   # type: ignore[arg-type]
        else:
            band.paste(pixel, (i, 0, i + 1, h))   # type: ignore[arg-type]

    if radius > 0:
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
        band.putalpha(mask)

    composite.alpha_composite(band, dest=(x, y))


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

    family  = layer.get("font", "Arial")
    bold    = bool(layer.get("bold",   False))
    italic  = bool(layer.get("italic", False))
    size    = max(1, int(float(layer.get("size", 24))))
    color   = _parse_color(layer.get("color", "#000000"), layer.get("opacity"))
    align   = str(layer.get("align", "left")).lower()
    spacing = float(layer.get("letter_spacing", 0))
    lh_mult = float(layer.get("line_height", 1.2))
    shadow  = layer.get("shadow")

    font     = _load_font(family, bold, italic, size, project_font_dir)
    # Fallback automatico CJK: se il testo contiene caratteri cinesi/giapponesi
    # e il font attivo non li supporta, usa SimSun/msgothic automaticamente.
    if _has_cjk(text) and family.lower() not in ("simhei", "simsun", "noto cjk", "msgothic"):
        cjk_font = _load_font("simsun", bold, italic, size, project_font_dir)
        font = cjk_font
    lines    = _wrap(text, font, w)
    line_gap = int(size * lh_mult)

    d   = ImageDraw.Draw(composite)
    ty  = y

    for line in lines:
        bb      = d.textbbox((0, 0), line, font=font)
        text_w  = bb[2] - bb[0]
        text_h  = bb[3] - bb[1]

        if align == "center":
            tx = x + (w - text_w) // 2
        elif align == "right":
            tx = x + w - text_w
        else:
            tx = x

        # Compensate for top descender offset from textbbox
        tx -= bb[0]
        ty_draw = ty - bb[1]

        if shadow:
            sc  = _parse_color(shadow.get("color", "#00000066"))
            sox = int(shadow.get("offset_x", 2))
            soy = int(shadow.get("offset_y", 2))
            sb  = float(shadow.get("blur", 0))
            if sb > 0:
                sl = Image.new("RGBA", composite.size, (0, 0, 0, 0))
                ImageDraw.Draw(sl).text((tx + sox, ty_draw + soy), line, font=font, fill=sc,
                                        spacing=int(spacing))
                sl = sl.filter(ImageFilter.GaussianBlur(sb))
                composite.alpha_composite(sl)
            else:
                d.text((tx + sox, ty_draw + soy), line, font=font, fill=sc, spacing=int(spacing))

        if spacing != 0:
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

    if opacity is not None:
        alpha = img.getchannel("A")
        alpha = alpha.point(lambda p: int(p * float(opacity)))
        img.putalpha(alpha)

    # Clip to canvas bounds
    cw, ch = composite.size
    if x < 0 or y < 0 or x + w > cw or y + h > ch:
        cx1 = max(x, 0); cy1 = max(y, 0)
        cx2 = min(x + w, cw); cy2 = min(y + h, ch)
        crop = img.crop((cx1 - x, cy1 - y, cx2 - x, cy2 - y))
        composite.alpha_composite(crop, dest=(cx1, cy1))
    else:
        composite.alpha_composite(img, dest=(x, y))


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
        except Exception as exc:
            msg = f"Errore nel layer '{layer.get('id', ltype)}': {exc}"
            warnings.append(msg)
            print(f"[WARNING] {msg}")

    composite.convert("RGB").save(str(output_path), "PNG", optimize=False)
    return output_path, warnings
