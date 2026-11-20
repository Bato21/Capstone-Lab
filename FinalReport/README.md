# Final report · NextLap · Group 1

IIT414W capstone. Members: Vicente Rodríguez, Baptiste Vial. Due 22 November 2026, 23:59 (one PDF per team in Canvas).

**Repository:** https://github.com/Bato21/Capstone-Lab · **Exact commit:** the commit tagged `Final`. Its full SHA is printed on page one of the submitted PDF and given in the Canvas submission, because a file cannot contain the hash of the commit it belongs to.

| File | Role |
| --- | --- |
| [FINAL_REPORT.md](FINAL_REPORT.md) | The report, following the final report template. The submitted PDF is exported from it. |
| [DECISION_LOG.md](DECISION_LOG.md) | Part 3 of the decision log: Demo Day, feedback received, the priority revision (trial E, rule written before running), contributions and AI use after Hito 2. Parts 1–2 are in [Hito2/DECISION_LOG.md](../Hito2/DECISION_LOG.md). |
| [run_final.py](run_final.py) | Trial E, the priority revision: short-history rows use the frozen reference A, all other rows keep candidate B. Reads the saved Hito 2 predictions only (no data, no refit) and applies the pre-declared rule. |
| [predict.py](predict.py) | The frozen final model E for the improvement bonus: fits A and B on rounds 1–7, scores prediction requests from an as-of history view and reports fallback counts. `--self-check` reproduces E on rounds 8–9. |
| `build_pdf.py` | Exports the PDF, inserts the commit SHA and pins every relative link to that commit on GitHub. |

The comparison, error tables and SHAP come from the Hito 2 run, unchanged: data instructions, environment, run command and the evidence map are in [Hito2/README.md](../Hito2/README.md).

## Run the revision and the final model

```bash
# from the repository root, in the Hito 2 environment (pip install -r Hito2/requirements.txt)
python FinalReport/run_final.py                 # about 1 s; reads Hito2/outputs and Hito1/outputs only
python FinalReport/predict.py --self-check      # about 30 s; needs the released data in base_NextLap/
python FinalReport/predict.py --requests REQUESTS.csv --history HISTORY.csv --out predictions.csv
```

| Output in `FinalReport/outputs/` | Content |
| --- | --- |
| `trial_E_checks.csv` | The four conditions of the pre-declared rule, observed values and pass/fail; the same-rows check |
| `trial_E_table.csv` | MAE of A, B and E with n, overall, per race, on the short-history rows (overall and per race) and on the full-history rows; A − E and B − E |
| `trial_E_bootstrap.csv` | Supplementary stint bootstrap (112 stints, 2,000 replicates, seed 414) of A − E, B − E and A − B (the last reproduces Hito 2) |
| `validation_predictions_E.csv` | Row-level predictions of A, B and E for the 1,808 validation `pair_id`s, with the source of E (B or the A fallback) and absolute errors |
| `trial_log.csv` | Every configuration tried (A–E) on the same rows: MAE overall, per race and on the short-history rows, the rule each was judged by and its outcome |
| `run_manifest.json` | SHA-256 of the inputs read, the validation `pair_id` hash, the short-history count and the frozen model |
| `predict_self_check.csv`, `.json` | Predictions of `predict.py` on rounds 8–9, fallback counts, and the largest difference from trial E |

## Export the PDF

```bash
# from the repository root, after the final commit is pushed and tagged
python FinalReport/build_pdf.py --sha $(git rev-parse Final) --out NextLap_Final_Report_Group1.pdf
```

Needs the `markdown` package and Microsoft Edge (headless print to PDF).

## Before uploading

- Page one shows both names, the repository URL and the full SHA of the commit tagged `Final`, and the SHA link opens that commit.
- The repository opens without signing in, and every link in the PDF opens a file at that commit: code, environment, data instructions, saved tables and decision logs.
- Every number in the report matches the saved output it cites, including the revision in section 4.
- Another reader can follow the run instructions and see what each partner contributed and how AI was used and checked.
- If entering the bonus, the nominated model is at the same commit.
