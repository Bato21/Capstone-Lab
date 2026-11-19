# Demo Day · NextLap · Group 1 (20 November 2026)

Defence of the Hito 2 decisions, findings and limits: 7 minutes of presentation and 5 minutes of questions (11:25–11:37, Lab 033). Members: Vicente Rodríguez, Baptiste Vial.

| File | Role |
| --- | --- |
| `NextLap_Demo_Team1.pptx` | The deck, built on the official Demo Day slide template (the same six questions and timings): 6 slides for the talk plus 5 backup slides for questions. Speaker notes hold the spoken text. |
| `NextLap_Demo_Team1.pdf` | Offline copy of the deck, exported from PowerPoint. |
| [PITCH.md](PITCH.md) | Script: who says what on each slide, timings, "must say" phrases, who answers which question, and the handover cues. |
| `make_figures.py` | Writes `figures/albon_incident.png`, `figures/shap_waterfall.png` and `figures/deck_data.json` from `Hito2/outputs/` and the released R9 snapshot. |
| `build_deck.js` | Builds the deck from `figures/` and `PITCH.md` (tables and bar charts are native PowerPoint objects fed by `deck_data.json`). |

Every number in the deck comes from `Hito2/outputs/` at the commit tagged `Hito2`; no result was recomputed or tuned for the demo.

## Rebuild

```bash
# from the repository root, with the Hito 2 environment and the data in base_NextLap/
.venv/Scripts/python Demo/make_figures.py
# pptxgenjs 3.12.0 installed outside the repository (npm install pptxgenjs@3.12.0 in any folder)
NODE_PATH=<that folder>/node_modules APPLY_THEME=<path to apply_theme.js> node Demo/build_deck.js
```

`APPLY_THEME` points to the helper that writes the deck's theme colours after pptxgenjs saves the file. Rebuilding is only needed to change the deck; the `.pptx` in this folder is the version presented.
