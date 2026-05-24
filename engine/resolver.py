"""
Risolve variabili, temi e preset canvas in un layout dict prima del rendering.

Sostituzione: {{chiave}} nel valore YAML viene rimpiazzata con il valore
corrispondente in `variables` o `theme` (come `theme.chiave`).
"""

import re


CANVAS_PRESETS: dict[str, dict] = {
    "instagram_story":  {"width": 1080, "height": 1920},
    "instagram_reel":   {"width": 1080, "height": 1920},
    "instagram_square": {"width": 1080, "height": 1080},
    "facebook_post":    {"width": 1200, "height": 630},
    "facebook_cover":   {"width": 1640, "height": 624},
    "a4_portrait":      {"width": 2480, "height": 3508},
    "a4_landscape":     {"width": 3508, "height": 2480},
    "a5_portrait":      {"width": 1748, "height": 2480},
    "a5_landscape":     {"width": 2480, "height": 1748},
    "volantino":        {"width": 1080, "height": 1530},
}


def resolve(layout: dict, extra_vars: dict | None = None) -> dict:
    """
    1. Espande preset canvas se presente.
    2. Costruisce la mappa di sostituzione da `theme` e `variables`.
    3. Applica la sostituzione ricorsiva su tutti i valori stringa del layout.
    """
    # ── 1. Canvas preset ──────────────────────────────────────────────────────
    canvas = dict(layout.get("canvas") or {})
    preset_name = canvas.pop("preset", None)
    if preset_name:
        preset = CANVAS_PRESETS.get(str(preset_name))
        if preset is None:
            available = ", ".join(CANVAS_PRESETS)
            raise ValueError(
                f"Canvas preset sconosciuto: '{preset_name}'.\n"
                f"Disponibili: {available}"
            )
        for k, v in preset.items():
            canvas.setdefault(k, v)
    layout = {**layout, "canvas": canvas}

    # ── 2. Mappa sostituzioni ─────────────────────────────────────────────────
    subs: dict[str, str] = {}

    for k, v in (layout.get("theme") or {}).items():
        subs[f"theme.{k}"] = str(v)

    merged_vars = dict(layout.get("variables") or {})
    if extra_vars:
        merged_vars.update(extra_vars)
    for k, v in merged_vars.items():
        subs[str(k)] = str(v)

    if not subs:
        return layout

    # ── 3. Sostituzione ricorsiva ──────────────────────────────────────────────
    return _sub(layout, subs)


def _sub(obj: object, subs: dict[str, str]) -> object:
    if isinstance(obj, str):
        def _replace(m: re.Match) -> str:
            key = m.group(1).strip()
            return subs.get(key, m.group(0))
        return re.sub(r"\{\{([^}]+)\}\}", _replace, obj)
    if isinstance(obj, dict):
        return {k: _sub(v, subs) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sub(item, subs) for item in obj]
    return obj
