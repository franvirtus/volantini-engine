# VolantiniEngine

Motore Python semplice per generare volantini PowerPoint modificabili per Virtus.

Il progetto prende:

- un template PowerPoint `.pptx`
- un config contenuti in JSON o YAML
- immagini dalla cartella `assets/images/`

e genera sempre un PowerPoint modificabile in `output/`.

Non è una web app e non contiene editor visuale: il design resta nel template PowerPoint, il motore sostituisce solo testi e immagini.

## Struttura

```text
VolantiniEngine/
  engine/
    __init__.py
    config_loader.py
    pptx_renderer.py
    exporters.py
  campaigns/
    lotta_pugilato_10_14.yaml
  templates/
    combat_light_vertical.pptx
  assets/
    images/
  data/
    examples/
  output/
  generate.py
  requirements.txt
  README.md
```

La cartella `output/` contiene file generati e non va tracciata da Git.

## Installazione

Da PowerShell:

```powershell
cd "C:\Users\sense\OneDrive\Documents\Virtus\VolantiniEngine"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Uso YAML

Comando base:

```powershell
python generate.py campaigns/lotta_pugilato_10_14.yaml
```

Con cartella output personalizzata:

```powershell
python generate.py campaigns/lotta_pugilato_10_14.yaml --out-dir output
```

Con export PDF/PNG:

```powershell
python generate.py campaigns/lotta_pugilato_10_14.yaml --pdf --png
```

PDF e PNG richiedono Windows, PowerPoint installato e `pywin32`. Se `pywin32` non è disponibile, il PPTX viene comunque generato e viene stampato un warning.

## Uso JSON Legacy

Gli esempi JSON in `data/examples/` restano supportati:

```powershell
python generate.py data/examples/boxe_10_14.json
```

## Generic Layout Engine

Per creare un PowerPoint modificabile partendo da un layout YAML completo, usa il nuovo comando:

```powershell
python generate_layout.py layouts/examples/virtus_difesa_personale_layout.yaml
```

Flusso operativo quotidiano:

1. Salva il layout approvato in `layouts/approved/nome_volantino.yaml`.
2. Esegui `python generate_layout.py layouts/approved/nome_volantino.yaml`.
3. Trovi il PowerPoint modificabile in `output/`.
4. Cambia testi, telefono, logo o immagini nel file YAML e rigenera.
5. Usa Codex/GitHub solo per modificare il motore, non per produrre ogni volantino.

Documentazione: [docs/LAYOUT_ENGINE.md](docs/LAYOUT_ENGINE.md)

## Formato YAML

```yaml
template: combat_light_vertical.pptx
output_name: lotta_pugilato_10_14

texts:
  TITLE_1: "LOTTA"
  TITLE_2: "PUGILATO"
  AGE: "DAI 10 AI 14 ANNI"
  CTA_MAIN: "PROVA GRATUITA -"
  CTA_SUB: "LA PRIMA LEZIONE TI ASPETTIAMO!"
  PHONE: "3518899843"
  INSTAGRAM: "@virtus_group_"
  ADDRESS: "Via Corfu 71"

images:
  LOGO_TOP: "assets/images/logo.png"
  LOGO_BOTTOM: "assets/images/logo.png"
  IMAGE_HERO: "assets/images/hero.jpg"
  IMAGE_GALLERY_1: "assets/images/gallery_1.jpg"
```

Le chiavi in `texts` devono corrispondere ai placeholder presenti nel template, senza graffe. Per esempio il placeholder PowerPoint `{{TITLE_1}}` viene sostituito dalla chiave YAML `TITLE_1`.

## Placeholder Testo

Nel template PowerPoint inserisci testi modificabili come caselle testo:

```text
{{TITLE_1}}
{{TITLE_2}}
{{AGE}}
{{CTA_MAIN}}
{{PHONE}}
```

Il motore sostituisce anche placeholder spezzati in più run PowerPoint, quando sono nello stesso paragrafo/casella testo.

## Placeholder Immagini

Le immagini vengono sostituite cercando il nome della shape PowerPoint.

Esempi:

```text
IMAGE_HERO
IMAGE_GALLERY_1
IMAGE_GALLERY_2
LOGO_TOP
LOGO_BOTTOM
```

Nel template:

1. Inserisci una forma o immagine segnaposto.
2. Apri `Home > Disponi > Riquadro di selezione`.
3. Rinomina la shape con il nome richiesto, per esempio `IMAGE_HERO`.

Il motore elimina la shape placeholder e inserisce l'immagine nello stesso punto, mantenendo posizione e dimensioni.

Se un file immagine manca, il PPTX viene comunque generato e viene stampato un warning chiaro.

## Template Light

Per rigenerare il template chiaro modificabile:

```powershell
python build_template_light.py
```

Il file viene creato in:

```text
templates/combat_light_vertical.pptx
```

## Git

`.gitignore` deve includere:

```text
.venv/
output/
__pycache__/
*.pyc
.env
```

Non aggiungere file generati in `output/` ai commit.
