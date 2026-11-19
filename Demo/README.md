# Demo Day · NextLap · Group 1 (20 November 2026)

Defence of the Hito 2 decisions, findings and limits: 7 minutes of presentation and 5 minutes of questions (11:25–11:37, Lab 033). Members: Vicente Rodríguez, Baptiste Vial.

| File | Role |
| --- | --- |
| `NextLap_Demo_Team1.pptx` | The deck, built on the official Demo Day slide template (the same six questions and timings): 6 slides for the talk plus 6 backup slides for questions. Speaker notes of slides 1–6 hold the spoken text, the "must say" phrases and the handover to the partner; notes of slides 7–12 say who answers and give the short answer. |
| `NextLap_Demo_Team1.pdf` | Offline copy of the deck, exported from PowerPoint. |
| [SCRIPT.md](SCRIPT.md) | The script: who says what on each slide, timings, "must say" phrases, handover cues, the rehearsal plan and short versions if running late. |
| [PREP_GUIDE.md](PREP_GUIDE.md) | Preparation for the questions: the numbers to know, each idea explained plainly and precisely, how to answer, what we must not claim and what to say instead, a question bank with an owner for each topic, and the checklist for the day. |
| `make_figures.py` | Writes `figures/albon_incident.png`, `figures/shap_waterfall.png` and `figures/deck_data.json` from `Hito2/outputs/` and the released R9 snapshot. |
| `build_deck.js` | Builds the deck from `figures/` and `SCRIPT.md` (tables and bar charts are native PowerPoint objects fed by `deck_data.json`). |

Backup slides: 7 Albon's incident · 8 concentration of the gain and the short-history laps · 9 the checks written in Hito 1 · 10 all runs and the bootstrap · 11 Hito 1 feedback · 12 what this evidence does not show.

Every number in the deck comes from `Hito2/outputs/` at the commit tagged `Hito2`; no result was recomputed or tuned for the demo.

## Rebuild

```bash
# from the repository root, with the Hito 2 environment and the data in base_NextLap/
.venv/Scripts/python Demo/make_figures.py
# pptxgenjs 3.12.0 installed outside the repository (npm install pptxgenjs@3.12.0 in any folder)
NODE_PATH=<that folder>/node_modules APPLY_THEME=<path to apply_theme.js> node Demo/build_deck.js
```

`APPLY_THEME` points to the helper that writes the deck's theme colours after pptxgenjs saves the file. Rebuilding is only needed to change the deck; the `.pptx` in this folder is the version presented.
