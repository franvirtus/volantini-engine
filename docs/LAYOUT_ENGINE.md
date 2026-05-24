# Generic Layout Engine

Il layout engine generico esiste per trasformare una bozza approvata in un PowerPoint modificabile senza dover creare ogni volta un template rigido.

Il flusso previsto è:

1. L'utente chiede un volantino tramite prompt.
2. ChatGPT genera una bozza immagine.
3. L'utente approva la bozza.
4. La bozza viene descritta come layout YAML/JSON strutturato.
5. Il motore legge il layout e genera un `.pptx` modificabile.

## Legacy vs Layout Engine

Il sistema legacy usa:

```text
template.pptx + campaign.yaml -> output.pptx
```

È utile quando esiste già un template PowerPoint con placeholder `{{...}}` e shape nominate.

Il nuovo layout engine usa:

```text
layout.yaml -> output.pptx
```

È utile quando il design nasce da una bozza approvata e deve essere ricostruito come elementi PowerPoint modificabili: testi, immagini, rettangoli e linee.

I due sistemi convivono. `generate.py` resta il comando legacy. `generate_layout.py` è il comando del layout engine.

## Struttura Layout

Un layout contiene:

- `canvas`: dimensioni virtuali e colore di sfondo
- `assets_base`: cartella base delle immagini
- `layers`: lista ordinata degli elementi grafici, dal basso verso l'alto

Esempio:

```yaml
canvas:
  width: 1080
  height: 1530
  background: "#F7F4F0"

assets_base: "assets/images"

layers:
  - id: hero
    type: image
    src: "hero.jpg"
    x: 80
    y: 180
    w: 920
    h: 520
    fit: cover
```

Le coordinate sono pixel virtuali. Il renderer le converte internamente in pollici PowerPoint mantenendo il rapporto del canvas.

## Layer Supportati

### Rect

```yaml
- id: cta_box
  type: rect
  x: 80
  y: 1280
  w: 920
  h: 110
  fill: "#8B1A2B"
  radius: 24
  opacity: 1
```

Genera una forma PowerPoint modificabile.

Nota: il campo `radius` oggi abilita gli angoli arrotondati, ma non controlla ancora con precisione il raggio in pixel.

### Text

```yaml
- id: cta_text
  type: text
  text: "PROVA GRATUITA"
  x: 80
  y: 1305
  w: 920
  h: 60
  font: "Montserrat"
  bold: true
  size: 42
  color: "#FFFFFF"
  align: center
```

Genera una casella testo PowerPoint modificabile.

### Image

```yaml
- id: hero
  type: image
  src: "hero.jpg"
  x: 80
  y: 180
  w: 920
  h: 520
  fit: cover
```

Genera un'immagine PowerPoint. `fit: cover` riempie il box con crop, `fit: contain` mantiene tutta l'immagine visibile.

Se l'immagine manca, il comando stampa un warning e continua.

### Line

```yaml
- id: divider
  type: line
  x1: 80
  y1: 920
  x2: 1000
  y2: 920
  color: "#8B1A2B"
  width: 3
```

Genera una linea PowerPoint modificabile.

## Comando

```powershell
python generate_layout.py layouts/examples/virtus_difesa_personale_layout.yaml
```

Output:

```text
output/virtus_difesa_personale_layout.pptx
```

## Modifiche Future

Per cambiare telefono, indirizzo, logo, testi o immagini senza perdere lo stile:

1. Apri il file layout YAML.
2. Modifica il campo `text` del layer interessato, oppure il campo `src` di un layer immagine.
3. Mantieni invariati `x`, `y`, `w`, `h`, colori e font se vuoi conservare lo stile.
4. Rigenera il PPTX con `generate_layout.py`.

Il PowerPoint generato resta modificabile anche manualmente dopo la generazione.
