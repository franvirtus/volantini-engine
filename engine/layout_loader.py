from pathlib import Path

import yaml


SUPPORTED_EXTENSIONS = {".yaml", ".yml", ".json"}
SUPPORTED_LAYER_TYPES = {"rect", "text", "image", "line"}


def load_layout(layout_path):
    path = Path(layout_path)
    if not path.exists():
        raise FileNotFoundError(f"Layout non trovato: {path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Formato layout non supportato '{path.suffix}'. Usa: {supported}")

    try:
        with path.open("r", encoding="utf-8") as file:
            layout = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise ValueError(f"Layout YAML non valido in {path}: {exc}") from exc

    if layout is None:
        raise ValueError(f"Layout vuoto: {path}")
    if not isinstance(layout, dict):
        raise ValueError("Il layout deve essere un dizionario YAML/JSON.")

    validate_layout(layout)
    return layout


def validate_layout(layout):
    canvas = layout.get("canvas")
    if not isinstance(canvas, dict):
        raise ValueError("Il layout deve contenere 'canvas'.")

    for key in ("width", "height"):
        if not canvas.get(key):
            raise ValueError(f"canvas.{key} e obbligatorio.")

    layers = layout.get("layers")
    if not isinstance(layers, list):
        raise ValueError("Il layout deve contenere una lista 'layers'.")

    for index, layer in enumerate(layers, start=1):
        if not isinstance(layer, dict):
            raise ValueError(f"Layer {index}: deve essere un dizionario.")
        layer_type = layer.get("type")
        if layer_type not in SUPPORTED_LAYER_TYPES:
            raise ValueError(f"Layer {index}: type non supportato '{layer_type}'.")
        validate_layer(layer, index)


def require_keys(layer, index, keys):
    missing = [key for key in keys if key not in layer]
    if missing:
        raise ValueError(f"Layer {index} ({layer.get('id', 'senza id')}): campi mancanti: {', '.join(missing)}")


def validate_layer(layer, index):
    layer_type = layer["type"]
    if layer_type in {"rect", "text", "image"}:
        require_keys(layer, index, ["x", "y", "w", "h"])
    if layer_type == "text":
        require_keys(layer, index, ["text"])
    elif layer_type == "image":
        require_keys(layer, index, ["src"])
    elif layer_type == "line":
        require_keys(layer, index, ["x1", "y1", "x2", "y2"])

