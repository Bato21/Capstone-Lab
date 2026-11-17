# Hito 2 · NextLap · Team 1

IIT414W capstone. Members: Vicente Rodríguez, Baptiste Vial.

**Repository:** https://github.com/Bato21/Capstone-Lab · **Exact commit:** the commit tagged `Hito2` (GitHub release `Hito2`). The full hash is also in the Canvas submission text and in `SUBMISSION_COMMIT.txt` inside `Hito2_Team1.zip`. A file cannot contain the hash of the commit it belongs to, so the hash is recorded outside this README.

| File | Role |
| --- | --- |
| [HITO2.md](HITO2.md) | Interpretation: comparison, ablation, errors by context, SHAP, decision, individual explanations. |
| [DECISION_LOG.md](DECISION_LOG.md) | Hito 1 entries (kept unchanged) + Hito 2 trials, checks, decisions, feedback, contributions, AI record. |
| `run_hito2.py` | The single script that produces every Hito 2 result. |
| `features.py` | Builds `recent_std_s` from the raw snapshots, plus the independent as-of recomputation and the alternative "last 3 clean laps" reading used only for the convention check. |
| `requirements.txt` | Exact package versions of the reported run. |
| `outputs/` | Saved results (map below). |

## Data

The released data are not redistributed (public repository). Download `IIT414W_Capstone_NextLap_StudentData_v1.zip` (Canvas, course data release of 30 Oct 2026; SHA-256 of our copy `e5b4603897b849d2e7ad741214f17b7a1cfbff584f8d097b7bc31ef94988e50a`). The zip has no top folder, so extract it into `base_NextLap/` at the repository root, next to `Hito1/` and `Hito2/` (git-ignored):

```bash
unzip IIT414W_Capstone_NextLap_StudentData_v1.zip -d base_NextLap
```

The script stops if any of these hashes differs. `run_manifest.json` stores them, together with the SHA-256 of the nine snapshots in `data/`, which `load_snapshots` checks against `source_manifest_v2.json`.

| File | SHA-256 |
| --- | --- |
| `train_clean_v1.csv` (5,772 rows, rounds 1–7) | `43544f38cc9ef32b44886e6751e03522601265160086fe3a4956f04b87bd5c13` |
| `validation_clean_v1.csv` (1,808 rows, rounds 8–9) | `b19efb6a908af12a5d2c6bdde29aa40984295e62ce0f187a201b579278db7ee8` |
| `nextlap_reference_v1.py` | `f6c58925cd4a477bf3e1a5a2b3968e67df3a1cffabecee9e89701c3ac2d5f994` |
| `data/race_2026_r01…r09_laps_v2.csv` | listed in `outputs/run_manifest.json` → `sha256.snapshots` |

No external source and no reserved final-evaluation data are used. The script also reads `../Hito1/outputs/` to confirm that the re-executed OLS reference equals the Hito 1 result.

## Run

```bash
# from the repository root, Python 3.11
python -m venv .venv
source .venv/Scripts/activate     # Git Bash on Windows; PowerShell: .venv\Scripts\Activate.ps1; macOS/Linux: source .venv/bin/activate
pip install -r Hito2/requirements.txt
cd Hito2
python run_hito2.py                               # uses ../base_NextLap
python run_hito2.py --base PATH/TO/base_NextLap   # if the data are elsewhere
```

The run takes about 10 s and overwrites `outputs/`. It prints every check as PASS/FAIL. **One check is expected to print FAIL:** the pre-declared rule of follow-up trial D, which failed (HITO2.md §4.5). Every other check, and every assertion, must pass, or the script stops.

Reported environment: Windows 11, Python 3.11.9, numpy 2.4.6, pandas 3.1.1, scikit-learn 1.9.1, scipy 1.17.1, shap 0.51.0, matplotlib 3.11.2 (also recorded in `outputs/run_manifest.json`). `RANDOM_SEED = 414` seeds numpy, the stint bootstrap and the beeswarm jitter. OLS itself has no randomness. Verification: two consecutive runs gave byte-identical CSV and JSON outputs, and a fresh virtual environment built from `requirements.txt` reproduced every CSV, PNG and the manifest byte for byte. The Hito 1 OLS reference was verified on Python 3.10.4 with older packages, and our re-execution matches it to 2.8e-14 s.

## Evidence map (HITO2.md section → code → saved output)

Row identities: every row-level file carries `pair_id`.

| HITO2.md | What | Code (`run_hito2.py` section) | Output |
| --- | --- | --- | --- |
| §2, C1 | Race split, counts, disjoint IDs | §1 | `checks.csv` (race split), `run_manifest.json` |
| §2, C1 | Feature construction, last lap used per row | `features.py` `history_features`; §2 | `features_recent_std.csv` |
| §2, C1 | Availability at t (all rows + as-of recomputation) | `features.py` `as_of_recompute`; §2 | `checks.csv` (check 1), `features_recent_std.csv` (`recent_std_as_of`) |
| §2, C1 | Window convention (Hito 1 feedback): count of rows where "last 3 clean laps" would differ, worked history | `features.py` `last_clean_laps_std`; §2 | `history_convention.csv`, `history_convention_example.csv`, `checks.csv` (history convention) |
| §2, C1 | Coverage and train-fitted fill value | §3 | `coverage.csv` |
| §2, C1 | Same validation IDs, hash = Hito 1 | §3 | `checks.csv` (check 2) |
| §3, C2–C3 | A / B / C (and D) fits, metrics, n | §3–§4 | `comparison_metrics.csv`, `validation_predictions.csv`, `coefficients.csv` |
| §3 | Prior-signal check (training rows) | §3 | `checks.csv` (check 3) |
| §3 | Support rule | §4 | `checks.csv` (check 4) |
| §3 | Stint bootstrap, gain concentration | §5 | `bootstrap.csv`, `gain_concentration.csv` |
| §4.1, C4 | R8/R9 table, n-weighted pooling | §4 | `race_table.csv` |
| §4.2, C4 | Inspected cases and their raw laps | §6 | `inspected_cases.csv`, `inspected_cases_raw_laps.csv` |
| §4.3, C4 | Slices (history, std quartile, compound, race × history) | §5 | `slices.csv` |
| §4.5 | Trial D, next check | §5 | `followup_D_table.csv`, `checks.csv` (D) |
| §5, C5 | Local SHAP for `2026-R9-23-L7`, reconstruction | §7 | `shap_local.csv`, `shap_encoded_mapping.csv`, `checks.csv` (SHAP reconstruction) |
| §6, C6 | Global SHAP over 1,808 validation rows | §7 | `shap_global.csv`, `shap_global_bar.png`, `shap_beeswarm_numeric.png`, `shap_values_validation.csv` |
| §7, C7 | Versions, hashes, settings, results | §8 | `run_manifest.json` |

Column guide for `validation_predictions.csv`: `y_true_next_lap_s` (observed target), `pred_A_OLS_reference`, `pred_B_candidate`, `pred_C_matched_control`, `pred_D_followup_no_indicator`, the matching `abs_err_*` columns, `persistence` (= `current_lap_s`) and `pred_B_minus_C_s`.
