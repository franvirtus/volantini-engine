import platform
from pathlib import Path


POWERPOINT_FORMAT_PDF = 32
POWERPOINT_FORMAT_PNG = 18


def export_with_powerpoint(pptx_path, export_pdf=False, export_png=False):
    if not export_pdf and not export_png:
        return []

    outputs = []
    if platform.system() != "Windows":
        print("[WARNING] Export PDF/PNG disponibile solo su Windows con PowerPoint installato.")
        return outputs

    try:
        import win32com.client
    except ImportError:
        print(
            "[WARNING] Export PDF/PNG richiesto ma pywin32 non e installato. "
            "Il PPTX e stato comunque generato."
        )
        print("[WARNING] Per abilitare export automatico: python -m pip install pywin32")
        return outputs

    pptx_path = Path(pptx_path)
    powerpoint = None
    presentation = None

    try:
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        powerpoint.Visible = 1
        presentation = powerpoint.Presentations.Open(str(pptx_path), WithWindow=False)

        if export_pdf:
            pdf_path = pptx_path.with_suffix(".pdf")
            presentation.SaveAs(str(pdf_path), POWERPOINT_FORMAT_PDF)
            outputs.append(pdf_path)
            print(f"[VolantiniEngine] PDF generato: {pdf_path}")

        if export_png:
            png_dir = pptx_path.with_suffix("")
            presentation.SaveAs(str(png_dir), POWERPOINT_FORMAT_PNG)
            outputs.append(png_dir)
            print(f"[VolantiniEngine] PNG generati nella cartella: {png_dir}")

    except Exception as exc:
        print(f"[WARNING] Export PDF/PNG non completato: {exc}")
    finally:
        if presentation is not None:
            presentation.Close()
        if powerpoint is not None:
            powerpoint.Quit()

    return outputs

