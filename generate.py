import argparse
import sys
from pathlib import Path

from engine.config_loader import load_campaign_config
from engine.exporters import export_with_powerpoint
from engine.pptx_renderer import render_pptx


PROJECT_ROOT = Path(__file__).resolve().parent


def print_debug_report(config_path, output_path, report):
    print("\n[DEBUG] Config usato:")
    print(f"  {config_path}")
    print("[DEBUG] Output creato:")
    print(f"  {output_path}")

    print("[DEBUG] Placeholder testo trovati:")
    if report.text_found:
        for item in report.text_found:
            print(f"  slide {item['slide']} | {item['shape']} | {item['placeholder']}")
    else:
        print("  Nessuno")

    print("[DEBUG] Placeholder testo sostituiti:")
    if report.text_replaced:
        for item in report.text_replaced:
            print(f"  slide {item['slide']} | {item['shape']} | {item['placeholder']}")
    else:
        print("  Nessuno")

    print("[DEBUG] Immagini trovate:")
    if report.images_found:
        for item in report.images_found:
            print(f"  slide {item['slide']} | {item['shape']}")
    else:
        print("  Nessuna")

    print("[DEBUG] Immagini sostituite:")
    if report.images_replaced:
        for item in report.images_replaced:
            print(f"  slide {item['slide']} | {item['shape']} -> {item['path']}")
    else:
        print("  Nessuna")

    print("[DEBUG] Placeholder rimasti:")
    if report.remaining_placeholders:
        for item in report.remaining_placeholders:
            print(f"  {item['type']} | slide {item['slide']} | {item['shape']} | {item['value']}")
    else:
        print("  Nessuno")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generatore generico di volantini PowerPoint modificabili per Virtus."
    )
    parser.add_argument("config", help="Percorso config JSON/YAML, es. campaigns/lotta_pugilato_10_14.yaml")
    parser.add_argument("--out-dir", default="output", help="Cartella output per il PPTX generato.")
    parser.add_argument("--pdf", action="store_true", help="Esporta anche PDF usando PowerPoint su Windows.")
    parser.add_argument("--png", action="store_true", help="Esporta anche PNG usando PowerPoint su Windows.")
    parser.add_argument("--debug", action="store_true", help="Stampa placeholder trovati, sostituiti e rimasti.")
    return parser.parse_args()


def main():
    args = parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = PROJECT_ROOT / out_dir

    try:
        print(f"[VolantiniEngine] Leggo config: {config_path}")
        config = load_campaign_config(config_path)
        output_path, report = render_pptx(config, PROJECT_ROOT, out_dir)

        if args.debug:
            print_debug_report(config_path, output_path, report)

        export_with_powerpoint(output_path, export_pdf=args.pdf, export_png=args.png)
    except Exception as exc:
        print(f"[ERRORE] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
