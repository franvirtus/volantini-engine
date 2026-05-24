# VolantiniEngine 🌿

Motore di generazione volantini PNG per palestre e studi fitness.  
Crea volantini professionali da template YAML — senza grafico, senza Canva.

## Come funziona

```
Template immagine (AI) + Layout YAML + Dati campagna  →  PNG pronto
```

1. L'AI genera un'immagine base senza testi
2. Il layout YAML definisce dove posizionare i testi
3. Il file campagna contiene i contenuti (titolo, orario, sede...)
4. Il motore sovrappone i testi e produce il PNG finale

## Struttura

```
VolantiniEngine/
├── engine/
│   ├── layout_loader.py        # Carica e valida il YAML
│   ├── layout_renderer_png.py  # Genera PNG con Pillow
│   └── resolver.py             # Variabili, temi, preset canvas
├── layouts/
│   └── templates/              # Template YAML riutilizzabili
├── campaigns/                  # Contenuti per ogni campagna
├── assets/images/              # Immagini template e hero
├── web/                        # Web app Flask
│   ├── app.py
│   └── templates/index.html
├── tools/                      # Script di misurazione/debug
├── generate_layout.py          # CLI principale
└── requirements.txt
```

## Installazione

```bash
pip install -r requirements.txt
```

## Avvio rapido

**Da CLI:**
```bash
python generate_layout.py layouts/templates/overlay_professionale.yaml \
       --data campaigns/nutrizionisti.yaml --format png
```

**Web app:**
```bash
python web/app.py
# Apri http://localhost:5000
```

## Template disponibili

| Template | Descrizione |
|---|---|
| `overlay_professionale` | Testi sovrapposti su immagine AI (consigliato) |
| `corso_professionale` | Layout completo generato da codice |

## Aggiungere un nuovo corso

1. Crea `campaigns/nuovo_corso.yaml` con i contenuti
2. Metti l'immagine template in `assets/images/`
3. Esegui il comando CLI oppure usa la web app

## Roadmap

- [ ] Upload immagini dal browser
- [ ] Galleria template con anteprima
- [ ] Editor posizioni drag & drop
- [ ] Multi-cliente / autenticazione
- [ ] Deploy online
