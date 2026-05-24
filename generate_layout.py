import argparse
import sys
from pathlib import Path

from engine.layout_loader import load_layout
from engine.layout_renderer_pptx import render_layout_to_pptx


PROJECT_ROOT = Path(__file__).resolve().parent


def parse_args():
    parser = argparse.ArgumentParser(description="Genera un PPTX modificabile da un layout YAML generico.")
    parser.add_argument("layout", help="Percorso layout YAML, es. layouts/examples/virtus_difesa_personale_layout.yaml")
    parser.add_argument("--out-dir", default="output", help="Cartella output per il PPTX generato.")
    return parser.parse_args()


def main():
    args = parse_args()
    layout_path = Path(args.layout)
    if not layout_path.is_absolute():
        layout_path = PROJECT_ROOT / layout_path

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = PROJECT_ROOT / out_dir

    try:
        print(f"[VolantiniEngine] Leggo layout: {layout_path}")
        layout = load_layout(layout_path)
        output_name = layout.get("output_name") or layout_path.stem
        output_path = out_dir / f"{output_name}.pptx"
        output_path, warnings = render_layout_to_pptx(layout, PROJECT_ROOT, output_path)
        print(f"[VolantiniEngine] PowerPoint generato: {output_path}")
        print(f"[VolantiniEngine] Warning: {len(warnings)}")
    except Exception as exc:
        print(f"[ERRORE] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

