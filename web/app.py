"""
VolantiniEngine — Web App
Genera volantini PNG da template YAML tramite interfaccia web.
"""
import sys, os, io, base64, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, request, send_file, jsonify
from engine.layout_loader import load_layout, load_data_file
from engine.layout_renderer_png import render_layout_to_png
import tempfile, yaml

app = Flask(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "layouts", "templates")
CAMPAIGNS_DIR = os.path.join(PROJECT_ROOT, "campaigns")
OUTPUT_DIR    = os.path.join(PROJECT_ROOT, "output")

# ── Metadati campi per ogni template ────────────────────────────────────────
TEMPLATE_FIELDS = {
    "overlay_professionale": {
        "label": "Corso Professionale (overlay)",
        "fields": [
            {"key": "titolo_1",      "label": "Titolo riga 1",       "placeholder": "CORSO DI"},
            {"key": "titolo_2",      "label": "Titolo riga 2",       "placeholder": "FORMAZIONE"},
            {"key": "titolo_3",      "label": "Titolo riga 3",       "placeholder": "PER"},
            {"key": "titolo_4",      "label": "Titolo riga 4",       "placeholder": "NUTRIZIONISTI"},
            {"key": "sottotitolo",   "label": "Sottotitolo",         "placeholder": "Formazione pratica..."},
            {"key": "giorni_label",  "label": "Giorni",              "placeholder": "Ogni mercoledì"},
            {"key": "orario_label",  "label": "Orario",              "placeholder": "alle 15:00"},
            {"key": "sede_label",    "label": "Sede",                "placeholder": "Virtus • Via Corfù"},
            {"key": "feature_title", "label": "Benefit principale",  "placeholder": "TIROCINIO GARANTITO"},
            {"key": "feature_body",  "label": "Descrizione benefit", "placeholder": "presso studi qualificati"},
            {"key": "card1",         "label": "Card 1",              "placeholder": "Nutrizione clinica"},
            {"key": "card2",         "label": "Card 2",              "placeholder": "Valutazione antropometrica"},
            {"key": "card3",         "label": "Card 3",              "placeholder": "Educazione alimentare"},
            {"key": "card4",         "label": "Card 4",              "placeholder": "Casi pratici"},
            {"key": "cta_main",      "label": "CTA principale",      "placeholder": "ISCRIVITI ORA"},
            {"key": "cta_sub",       "label": "CTA secondario",      "placeholder": "RICHIEDI INFORMAZIONI IN SEDE"},
            {"key": "template_img",  "label": "Immagine template",   "placeholder": "template_nutrizionisti.jpg"},
            {"key": "output_name",   "label": "Nome file output",    "placeholder": "volantino_output"},
        ]
    },
    "corso_professionale": {
        "label": "Corso Professionale (layout completo)",
        "fields": [
            {"key": "titolo_1",      "label": "Titolo riga 1",       "placeholder": "CORSO DI"},
            {"key": "titolo_2",      "label": "Titolo riga 2",       "placeholder": "FORMAZIONE"},
            {"key": "titolo_3",      "label": "Titolo riga 3",       "placeholder": "PER"},
            {"key": "titolo_4",      "label": "Titolo riga 4",       "placeholder": "NUTRIZIONISTI"},
            {"key": "sottotitolo",   "label": "Sottotitolo",         "placeholder": "Formazione pratica..."},
            {"key": "giorni_label",  "label": "Giorni",              "placeholder": "Ogni mercoledì"},
            {"key": "orario_label",  "label": "Orario",              "placeholder": "alle 15:00"},
            {"key": "sede_label",    "label": "Sede",                "placeholder": "Virtus • Via Corfù"},
            {"key": "feature_title", "label": "Benefit principale",  "placeholder": "TIROCINIO GARANTITO"},
            {"key": "feature_body",  "label": "Descrizione benefit", "placeholder": "presso studi qualificati"},
            {"key": "card1",         "label": "Card 1",              "placeholder": "Nutrizione clinica"},
            {"key": "card2",         "label": "Card 2",              "placeholder": "Valutazione antropometrica"},
            {"key": "card3",         "label": "Card 3",              "placeholder": "Educazione alimentare"},
            {"key": "card4",         "label": "Card 4",              "placeholder": "Casi pratici"},
            {"key": "cta_main",      "label": "CTA principale",      "placeholder": "ISCRIVITI ORA"},
            {"key": "cta_sub",       "label": "CTA secondario",      "placeholder": "RICHIEDI INFORMAZIONI IN SEDE"},
            {"key": "hero_img",      "label": "Immagine hero",       "placeholder": "hero.jpg"},
            {"key": "output_name",   "label": "Nome file output",    "placeholder": "volantino_output"},
        ]
    },
}


def get_available_templates():
    """Restituisce i template disponibili nella cartella layouts/templates."""
    templates = []
    for yaml_path in sorted(glob.glob(os.path.join(TEMPLATES_DIR, "*.yaml"))):
        name = os.path.splitext(os.path.basename(yaml_path))[0]
        meta = TEMPLATE_FIELDS.get(name, {})
        templates.append({
            "name": name,
            "label": meta.get("label", name.replace("_", " ").title()),
            "has_fields": name in TEMPLATE_FIELDS,
        })
    return templates


def generate_png_bytes(template_name, form_data):
    """Genera il PNG e restituisce i bytes."""
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.yaml")
    layout = load_layout(template_path, extra_vars=form_data)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    render_layout_to_png(layout, PROJECT_ROOT, tmp_path)

    with open(tmp_path, "rb") as f:
        data = f.read()
    os.unlink(tmp_path)
    return data


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    templates = get_available_templates()
    default = templates[0]["name"] if templates else None
    default_meta = TEMPLATE_FIELDS.get(default, {})
    return render_template("index.html",
                           templates=templates,
                           active_template=default,
                           fields=default_meta.get("fields", []))


@app.route("/fields/<template_name>")
def get_fields(template_name):
    """Restituisce i campi del template selezionato (AJAX)."""
    meta = TEMPLATE_FIELDS.get(template_name, {})
    return jsonify({"fields": meta.get("fields", [])})


@app.route("/preview", methods=["POST"])
def preview():
    """Genera il PNG e restituisce immagine base64 per l'anteprima."""
    template_name = request.form.get("template_name", "overlay_professionale")
    form_data = {k: v for k, v in request.form.items() if k != "template_name" and v.strip()}
    try:
        png_bytes = generate_png_bytes(template_name, form_data)
        b64 = base64.b64encode(png_bytes).decode("utf-8")
        return jsonify({"ok": True, "image": b64})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/download", methods=["POST"])
def download():
    """Genera il PNG e lo invia come download."""
    template_name = request.form.get("template_name", "overlay_professionale")
    form_data = {k: v for k, v in request.form.items() if k != "template_name" and v.strip()}
    output_name = form_data.get("output_name", "volantino")
    try:
        png_bytes = generate_png_bytes(template_name, form_data)
        return send_file(
            io.BytesIO(png_bytes),
            mimetype="image/png",
            as_attachment=True,
            download_name=f"{output_name}.png"
        )
    except Exception as e:
        return f"Errore: {e}", 500


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("=" * 50)
    print("  VolantiniEngine Web App")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
