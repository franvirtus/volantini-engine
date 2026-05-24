# VolantiniEngine

Motore Python generico per generare volantini PowerPoint modificabili per Virtus.

Il motore prende:

- un template PowerPoint master
- un file JSON con i contenuti
- immagini dalla cartella `assets/images/`

e genera un file `.pptx` modificabile in `output/`.

Il design resta nel template PowerPoint. Il programma sostituisce solo placeholder testuali e immagini nominate.

## Struttura progetto

```text
VolantiniEngine/
  templates/
    combat_dark_vertical.pptx
  assets/
    images/
  data/
    examples/
      boxe_10_14.json
      bjj_6_9.json
  output/
  generate.py
  requirements.txt
  README.md
```

## Installazione Windows

Apri PowerShell nella cartella del progetto:

```powershell
cd "C:\Users\sense\OneDrive\Documents\Virtus\VolantiniEngine"
```

Crea l'ambiente virtuale:

```powershell
py -m venv .venv
```

Attiva l'ambiente virtuale:

```powershell
.\.venv\Scripts\Activate.ps1
```

Installa le dipendenze:

```powershell
python -m pip install -r requirements.txt
```

Metti il template PowerPoint in:

```text
templates/combat_dark_vertical.pptx
```

Metti le immagini in:

```text
assets/images/
```

Genera un volantino:

```powershell
python generate.py data/examples/boxe_10_14.json
```

Il file generato sara in:

```text
output/boxe_10_14.pptx
```

Genera anche PDF, se PowerPoint e installato e `pywin32` e disponibile:

```powershell
python generate.py data/examples/boxe_10_14.json --pdf
```

Genera anche PNG, se PowerPoint e installato e `pywin32` e disponibile:

```powershell
python generate.py data/examples/boxe_10_14.json --png
```

Genera PPTX, PDF e PNG insieme:

```powershell
python generate.py data/examples/boxe_10_14.json --pdf --png
```

## Come preparare il template PowerPoint

1. Crea il design del volantino direttamente in PowerPoint.
2. Inserisci i testi come caselle testo PowerPoint modificabili.
3. Scrivi i placeholder dentro le caselle testo, per esempio `{{TITLE}}`, `{{CTA}}`, `{{PHONE}}`.
4. Non usare testo dentro immagini.
5. Usa solo caselle testo PowerPoint per i contenuti che vuoi modificare.
6. Inserisci immagini o forme segnaposto dove vuoi sostituire immagini.
7. Dai alle immagini o forme segnaposto nomi precisi come `IMAGE_HERO`, `IMAGE_GALLERY_1`, `IMAGE_GALLERY_2`, `IMAGE_GALLERY_3`, `IMAGE_GALLERY_4`, `LOGO`.

Per rinominare una forma o immagine in PowerPoint:

1. Vai su `Home`.
2. Apri `Disponi`.
3. Scegli `Riquadro di selezione`.
4. Clicca sul nome dell'elemento.
5. Rinominalo con uno dei nomi previsti.

## Creare il template light

Per ricostruire il template verticale chiaro ispirato alla reference:

```powershell
python build_template_light.py
```

Il file viene creato in:

```text
templates/combat_light_vertical.pptx
```

## Placeholder testo supportati

```text
{{TITLE}}
{{SUBTITLE}}
{{AGE}}
{{CLAIM}}
{{DESCRIPTION}}
{{CTA}}
{{PHONE}}
{{INSTAGRAM}}
{{ADDRESS}}
{{BENEFIT_1_TITLE}}
{{BENEFIT_1_TEXT}}
{{BENEFIT_2_TITLE}}
{{BENEFIT_2_TEXT}}
{{BENEFIT_3_TITLE}}
{{BENEFIT_3_TEXT}}
{{BENEFIT_4_TITLE}}
{{BENEFIT_4_TEXT}}
{{BENEFIT_5_TITLE}}
{{BENEFIT_5_TEXT}}
{{BENEFIT_6_TITLE}}
{{BENEFIT_6_TEXT}}
```

Puoi aggiungere altri placeholder nel JSON. Il motore sostituisce qualsiasi chiave presente in `texts` usando il formato `{{CHIAVE}}`.

## Placeholder immagini supportati

```text
IMAGE_HERO
IMAGE_GALLERY_1
IMAGE_GALLERY_2
IMAGE_GALLERY_3
IMAGE_GALLERY_4
LOGO
```

Puoi aggiungere altri nomi immagine nel JSON. Il motore cerca forme o immagini con lo stesso nome nel template.

Se un'immagine indicata nel JSON non esiste, il motore lascia il placeholder nel template e stampa un warning.

## Formato JSON

```json
{
  "template": "combat_dark_vertical.pptx",
  "output_name": "boxe_10_14",
  "texts": {
    "TITLE": "BOXE",
    "SUBTITLE": "CORSO DI PUGILATO",
    "CTA": "PRENOTA LA TUA PROVA GRATUITA"
  },
  "images": {
    "IMAGE_HERO": "assets/images/boxe_hero.jpg",
    "LOGO": "assets/images/logo_virtus.png"
  }
}
```

## Output PNG/PDF

Il motore genera sempre il PowerPoint modificabile.

L'export automatico PDF/PNG usa PowerPoint installato su Windows tramite automazione COM.

Se usi `--pdf` o `--png` e vedi un warning su `pywin32`, installalo con:

```powershell
python -m pip install pywin32
```

Senza PowerPoint o senza `pywin32`, il file `.pptx` modificabile viene comunque generato.
