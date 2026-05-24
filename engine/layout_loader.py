import json
from pathlib import Path

import yaml

from engine.resolver import resolve


SUPPORTED_EXTENSIONS = {".yaml", ".yml", ".json"}
SUPPORTED_LAYER_TYPES = {"rect", "text", "image", "line", "circle", "icon", "qrcode"}


def load_layout(layout_path, extra_vars: dict | None = None):
    path = Path(layout_path)
    if not path.exists():
        raise FileNotFoundError(f"Layout non trovato: {path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Formato non supportato '{path.suffix}'. Usa: {supported}")

    try:
        with path.open("r", encoding="utf-8") as f:
            layout = json.load(f) if path.suffix.lower() == ".json" else yaml.safe_load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON non valido in {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML non valido in {path}: {exc}") from exc

    if layout is None:
        raise ValueError(f"Layout vuoto: {path}")
    if not isinstance(layout, dict):
        raise ValueError("Il layout deve essere un dizionario YAML/JSON.")

    layout = resolve(layout, extra_vars)
    validate_layout(layout)
    return layout


def load_data_file(data_path) -> dict:
    """Carica un file YAML/JSON di variabili da passare come extra_vars."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"File dati non trovato: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) if path.suffix.lower() in {".yaml", ".yml"} else json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Il file dati deve essere un dizionario: {path}")
    return data


def validate_layout(layout):
    canvas = layout.get("canvas")
    if not isinstance(canvas, dict):
        raise ValueError("Il layout deve contenere 'canvas'.")
    for key in ("width", "height"):
        if not canvas.get(key):
            raise ValueError(f"canvas.{key} è obbligatorio.")

    layers = layout.get("layers")
    if not isinstance(layers, list):
        raise ValueError("Il layout deve contenere una lista 'layers'.")

    for index, layer in enumerate(layers, start=1):
        if not isinstance(layer, dict):
            raise ValueError(f"Layer {index}: deve essere un dizionario.")
        layer_type = layer.get("type")
        if layer_type not in SUPPORTED_LAYER_TYPES:
            raise ValueError(
                f"Layer {index}: type '{layer_type}' non supportato. "
                f"Tipi validi: {', '.join(sorted(SUPPORTED_LAYER_TYPES))}"
            )
        _validate_layer(layer, index)


def _require(layer, index, keys):
    missing = [k for k in keys if k not in layer]
    if missing:
        lid = layer.get("id", "senza id")
        raise ValueError(f"Layer {index} ({lid}): campi mancanti: {', '.join(missing)}")


def _validate_layer(layer, index):
    t = layer["type"]
    if t in {"rect", "text", "image", "qrcode"}:
        _require(layer, index, ["x", "y", "w", "h"])
    if t == "circle":
        _require(layer, index, ["x", "y", "w", "h"])
    if t == "text":
        _require(layer, index, ["text"])
    if t == "image":
        _require(layer, index, ["src"])
    if t == "line":
        _require(layer, index, ["x1", "y1", "x2", "y2"])
    if t == "icon":
        _require(layer, index, ["x", "y", "w", "h", "name"])
    if t == "qrcode":
        _require(layer, index, ["data"])
