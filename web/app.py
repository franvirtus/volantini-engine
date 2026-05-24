"""
VolantiniEngine — Web App
Genera volantini PNG da YAML incollato o template salvato.
"""
import sys, os, io, base64, glob, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from engine.layout_loader import load_layout
from engine.layout_renderer_png import render_layout_to_png
from engine.resolver import resolve
import yaml

app = Flask(__name__)
app.secret_key = "volantini-engine-secret"

PROJECT_ROOT  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "layouts", "templates")
IMAGES_DIR    = os.path.join(PROJECT_ROOT, "assets", "images")
OUTPUT_DIR    = os.path.join(PROJECT_ROOT, "output")
ALLOWED_EXT   = {"jpg", "jpeg", "png", "webp"}


# ── Helpers ──────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def get_available_templates():
    templates = []
    for path in sorted(glob.glob(os.path.join(TEMPLATES_DIR, "*.yaml"))):
        name = os.path.splitext(os.path.basename(path))[0]
        templates.append({"name": name, "label": name.replace("_", " ").title()})
    return templates


def get_available_images():
    images = []
    for ext in ALLOWED_EXT:
        images += glob.glob(os.path.join(IMAGES_DIR, f"*.{ext}"))
        images += glob.glob(os.path.join(IMAGES_DIR, f"*.{ext.upper()}"))
    return sorted([os.path.basename(p) for p in images])


def png_from_layout(layout, extra_vars):
    """Risolve variabili e genera PNG, restituisce bytes."""
    layout = resolve(layout, extra_vars=extra_vars)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        render_layout_to_png(layout, PROJECT_ROOT, tmp_path)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def png_from_yaml_text(yaml_text, extra_vars):
    """Parsa YAML incollato e genera PNG."""
    layout = yaml.safe_load(yaml_text)
    return png_from_layout(layout, extra_vars)


def png_from_template(template_name, extra_vars):
    """Carica template salvato e genera PNG."""
    path = os.path.join(TEMPLATES_DIR, f"{template_name}.yaml")
    layout = load_layout(path, extra_vars=extra_vars)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        render_layout_to_png(layout, PROJECT_ROOT, tmp_path)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def extract_vars_from_extra(form):
    """Estrae le variabili custom dal form (esclude i campi di controllo)."""
    skip = {"yaml_text", "template_name", "mode", "output_name"}
    return {k: v for k, v in form.items() if k not in skip and v.strip()}


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html",
                           templates=get_available_templates(),
                           images=get_available_images())


@app.route("/parse-yaml", methods=["POST"])
def parse_yaml_endpoint():
    """Parsa il YAML e restituisce i campi per il form dinamico."""
    yaml_text = request.form.get("yaml_text", "").strip()
    if not yaml_text:
        return jsonify({"ok": False, "error": "YAML vuoto"})
    try:
        data = yaml.safe_load(yaml_text)
        variables = data.get("variables", {})
        fields = []
        for k, v in variables.items():
            fields.append({
                "key":         k,
                "label":       k.replace("_", " ").title(),
                "placeholder": str(v) if v is not None else "",
                "value":       str(v) if v is not None else "",
            })
        return jsonify({"ok": True, "fields": fields})
    except Exception as e:
        return jsonify({"ok": False, "error": f"YAML non valido: {e}"})


@app.route("/upload-image", methods=["POST"])
def upload_image():
    """Carica un'immagine in assets/images/."""
    f = request.files.get("image")
    if not f or f.filename == "":
        return jsonify({"ok": False, "error": "Nessun file selezionato"})
    if not allowed_file(f.filename):
        return jsonify({"ok": False, "error": "Formato non supportato (usa jpg, png, webp)"})
    filename = secure_filename(f.filename)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    f.save(os.path.join(IMAGES_DIR, filename))
    return jsonify({"ok": True, "filename": filename})


@app.route("/preview", methods=["POST"])
def preview():
    """Genera PNG e restituisce immagine base64."""
    mode        = request.form.get("mode", "yaml")
    yaml_text   = request.form.get("yaml_text", "").strip()
    tmpl_name   = request.form.get("template_name", "")
    extra_vars  = extract_vars_from_extra(request.form)

    try:
        if mode == "yaml" and yaml_text:
            png_bytes = png_from_yaml_text(yaml_text, extra_vars)
        elif mode == "template" and tmpl_name:
            png_bytes = png_from_template(tmpl_name, extra_vars)
        else:
            return jsonify({"ok": False, "error": "Nessun YAML o template selezionato"})

        b64 = base64.b64encode(png_bytes).decode("utf-8")
        return jsonify({"ok": True, "image": b64})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/download", methods=["POST"])
def download():
    """Genera PNG e lo invia come download."""
    mode       = request.form.get("mode", "yaml")
    yaml_text  = request.form.get("yaml_text", "").strip()
    tmpl_name  = request.form.get("template_name", "")
    extra_vars = extract_vars_from_extra(request.form)
    out_name   = request.form.get("output_name", "volantino").strip() or "volantino"

    try:
        if mode == "yaml" and yaml_text:
            png_bytes = png_from_yaml_text(yaml_text, extra_vars)
        elif mode == "template" and tmpl_name:
            png_bytes = png_from_template(tmpl_name, extra_vars)
        else:
            return "Nessun YAML o template", 400

        return send_file(
            io.BytesIO(png_bytes),
            mimetype="image/png",
            as_attachment=True,
            download_name=f"{out_name}.png"
        )
    except Exception as e:
        return f"Errore: {e}", 500


@app.route("/parse-yaml-from-template")
def parse_yaml_from_template():
    """Legge un template salvato e restituisce i campi variabili."""
    name = request.args.get("name", "")
    path = os.path.join(TEMPLATES_DIR, f"{name}.yaml")
    if not os.path.exists(path):
        return jsonify({"ok": False, "error": f"Template '{name}' non trovato"})
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        variables = data.get("variables", {})
        fields = [{"key": k, "label": k.replace("_", " ").title(),
                   "placeholder": str(v) if v is not None else "",
                   "value":       str(v) if v is not None else ""}
                  for k, v in variables.items()]
        return jsonify({"ok": True, "fields": fields})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/images")
def list_images():
    """Lista immagini disponibili in assets/images/."""
    return jsonify({"images": get_available_images()})


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    print("=" * 50)
    print("  VolantiniEngine Web App")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
