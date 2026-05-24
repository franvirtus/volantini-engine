import argparse
import sys
from pathlib import Path

from engine.layout_loader import load_layout, load_data_file
from engine.layout_renderer_pptx import render_layout_to_pptx
from engine.layout_renderer_png import render_layout_to_png


PROJECT_ROOT = Path(__file__).resolve().parent


def parse_args():
    parser = argparse.ArgumentParser(
        description="Genera un volantino da un layout YAML.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python generate_layout.py layouts/approved/pilates.yaml --format png
  python generate_layout.py layouts/templates/corso.yaml --data campaigns/yoga.yaml --format png
  python generate_layout.py layouts/templates/corso.yaml --var corso_nome=YOGA --var orario="18:00-19:00" --format png
""",
    )
    parser.add_argument("layout", help="Percorso layout YAML.")
    parser.add_argument(
        "--format",
        choices=["pptx", "png"],
        default="png",
        help="Formato output: png (default) oppure pptx.",
    )
    parser.add_argument("--out-dir", default="output", help="Cartella output.")
    parser.add_argument(
        "--data",
        metavar="FILE",
        help="File YAML con valori per le variabili {{...}} del template.",
    )
    parser.add_argument(
        "--var",
        metavar="CHIAVE=VALORE",
        action="append",
        default=[],
        help="Variabile singola (ripetibile). Sovrascrive --data.",
    )
    return parser.parse_args()


def _parse_vars(var_list: list[str]) -> dict:
    result = {}
    for item in var_list:
        if "=" not in item:
            print(f"[WARNING] --var ignorata (formato atteso CHIAVE=VALORE): '{item}'")
            continue
        k, _, v = item.partition("=")
        result[k.strip()] = v
    return result


def main():
    args = parse_args()

    layout_path = Path(args.layout)
    if not layout_path.is_absolute():
        layout_path = PROJECT_ROOT / layout_path

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = PROJECT_ROOT / out_dir

    try:
        extra_vars: dict = {}
        if args.data:
            data_path = Path(args.data)
            if not data_path.is_absolute():
                data_path = PROJECT_ROOT / data_path
            extra_vars.update(load_data_file(data_path))

        extra_vars.update(_parse_vars(args.var))

        print(f"[VolantiniEngine] Leggo layout: {layout_path}")
        if extra_vars:
            print(f"[VolantiniEngine] Variabili: {list(extra_vars.keys())}")

        layout = load_layout(layout_path, extra_vars=extra_vars or None)
        output_name = layout.get("output_name") or layout_path.stem

        if args.format == "png":
            output_path = out_dir / f"{output_name}.png"
            output_path, warnings = render_layout_to_png(layout, PROJECT_ROOT, output_path)
            print(f"[VolantiniEngine] PNG generato: {output_path}")
        else:
            output_path = out_dir / f"{output_name}.pptx"
            output_path, warnings = render_layout_to_pptx(layout, PROJECT_ROOT, output_path)
            print(f"[VolantiniEngine] PowerPoint generato: {output_path}")

        if warnings:
            print(f"[VolantiniEngine] {len(warnings)} warning(s):")
            for w in warnings:
                print(f"  - {w}")

    except Exception as exc:
        print(f"[ERRORE] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
