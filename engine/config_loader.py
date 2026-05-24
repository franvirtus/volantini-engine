import json
from pathlib import Path

import yaml


SUPPORTED_EXTENSIONS = {".json", ".yaml", ".yml"}


def load_campaign_config(config_path):
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config non trovato: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Formato config non supportato '{suffix}'. Usa: {supported}")

    try:
        with path.open("r", encoding="utf-8") as file:
            if suffix == ".json":
                config = json.load(file)
            else:
                config = yaml.safe_load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON non valido in {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML non valido in {path}: {exc}") from exc

    if config is None:
        raise ValueError(f"Config vuoto: {path}")
    if not isinstance(config, dict):
        raise ValueError(f"Il config deve contenere un oggetto/dizionario: {path}")

    validate_campaign_config(config)
    return config


def validate_campaign_config(config):
    required_fields = ["template", "output_name"]
    missing = [field for field in required_fields if not config.get(field)]
    if missing:
        raise ValueError("Campi obbligatori mancanti nel config: " + ", ".join(missing))

    texts = config.get("texts", {})
    images = config.get("images", {})

    if texts is None:
        config["texts"] = {}
    elif not isinstance(texts, dict):
        raise ValueError("Il campo 'texts' deve essere un dizionario.")

    if images is None:
        config["images"] = {}
    elif not isinstance(images, dict):
        raise ValueError("Il campo 'images' deve essere un dizionario.")

