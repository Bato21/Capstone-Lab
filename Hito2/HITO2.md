# Capstone NextLap · Hito 2 · Team 1

IIT414W · Team 1 · Members: Vicente Rodríguez, Baptiste Vial · Due 19 November 2026, 23:59

Run instructions and the map from every table below to its file are in [README.md](README.md). Trials, decisions, feedback and AI use are in [DECISION_LOG.md](DECISION_LOG.md). Every number here is read from `outputs/`, produced by one command (`python run_hito2.py`).

## Summary

| Question | Answer |
| --- | --- |
| Hypothesis (Hito 1, unchanged) | Recent pace **variability** adds information beyond the six reference inputs: `recent_std_s`, the standard deviation of the clean lap times among the last 3 laps of the stint (t−2…t), the same window as `recent_mean_s`. |
| Pre-declared rule (Hito 1, check 4) | Supported if control − candidate ≥ 0.01 s overall **and** ≥ 0 in R8 and in R9. |
| Result | Control − candidate = **+0.0179 s** overall (R8 +0.0128 s, R9 +0.0253 s) on the same 1,808 validation rows → **supported**. |
| Decision | **Keep** `recent_std_s`. The candidate (B) is our working model. |
| Main limit | The gain is concentrated: 50 of 1,808 rows (2.8%) give 94.5% of it, almost all after an unusually slow lap. On the 148 short-history rows the candidate is **worse** than the reference. |
| Follow-up check | Trial D (indicator removed) was declared before running and **failed** its rule on short-history rows, so we kept B (section 4.5). |
| Hito 1 feedback | Window convention stated and checked on every row, with a worked history (section 2); mechanism stated as a bounded hypothesis and compared with the fitted model (section 3); below-threshold outcomes described as not meeting the predeclared criterion. `HITO1.md` was revised accordingly. |

## 1. What we carried forward and what changed

| Hito 1 item | Hito 2 | Reason |
| --- | --- | --- |
| Hypothesis and feature: `recent_std_s`, window 3, ≥ 2 clean laps, sample std, race/driver/stint grouping, original timeline | **Unchanged** | It was fixed before seeing validation results. No window or model search was done on validation. |
| Runs A (reference), B (candidate), C (control) | **Unchanged**, all executed | – |
| Check 1: availability "for a sample of rows" | **Extended to all 7,580 rows**, plus an independent as-of recomputation | A sample could miss rare stint-boundary cases; checking every row costs a few seconds. The original wording is kept in `DECISION_LOG.md`. |
| Checks 2–5 and the 0.01 s rule | **Unchanged** | – |
| Not in Hito 1 | Trial D (follow-up), cluster bootstrap, gain concentration | Added after seeing the slice table, labelled as post-hoc. They do not change the decision on B vs C. |
| Wording "last 3 clean laps" (Hito 1 feedback, C3.1) | **Clarified, not changed:** the window is the last 3 laps of the stint, as in `recent_mean_s`. A history-convention check was added (section 2). | The code always used the `recent_mean_s` window; only the description was ambiguous. |
| Expected mechanism (C3.1) | **Stated as a bounded hypothesis** in `HITO1.md` §3 and compared with the fitted coefficients (section 3) | Feedback asked how the variable could correct the point prediction. Written after the results were known, so it explains rather than predicts. |
| Check 4 wording (C4.4) | **Threshold unchanged**; a gain below 0.01 s is described as not meeting the predeclared improvement criterion, not as refuting the idea | Feedback: a small gain does not show variability carries no information. |

## 2. The new input and its availability at t (C1)

| Item | Evidence |
| --- | --- |
| Source | Released snapshots `base_NextLap/data/race_2026_r0{1..9}_laps_v2.csv` (FastF1-parsed official timing; SHA-256 verified against `source_manifest_v2.json` by `load_snapshots`). No external source. |
| Construction | `features.py`, `history_features`: on the full original lap timeline (before the clean-pair filter), laps that are clean **at their own end** (same `current_clean` rule as the reference: lap > 1, accurate, not pit in/out, not deleted, green flag) keep their time; others are missing. `rolling(3, min_periods=2).std(ddof=1)` within season, round, driver and stint. Lap t is included; lap t+1 is never in the window. |
| Same window as the reference | Our code also rebuilds `recent_mean_s` and `recent_count`. They match the released columns exactly on all 7,580 rows (`attach` in `run_hito2.py`). So `recent_std_s` uses the same laps as the reference's own `recent_mean_s`. |
| Window convention (Hito 1 feedback) | The window is the last 3 **laps** of the stint (t−2, t−1, t), not the last 3 **clean** laps. A non-clean lap in the window is left out and is not replaced by an earlier clean lap. The "last 3 clean laps" reading would give a different value on 111 of 1,808 validation rows (6.1%) and 524 of 5,772 training rows; on 41 validation short-history rows it would reach back far enough to produce a value (`outputs/history_convention.csv`). We keep the `recent_mean_s` window so that B and C differ from the reference only in the aggregation. |
| Worked history | `2026-R8-1-L28` (driver 1, McLaren, R8, stint 2), selected by a fixed rule in the code (`outputs/history_convention_example.csv`). Lap 23 = 72.148 s (clean); laps 24–26 non-clean (track status not green, not accurate); lap 27 = 71.773 s and lap 28 = t = 71.568 s (clean). Window = laps 26–28 → two clean times → `recent_std_s` = **0.145 s** (`recent_count` = 2, released `recent_mean_s` = 71.6705 s from the same two laps). The other reading would reach back to lap 23 and give 0.294 s. Lap 29 (t+1) is the target and is never used. |
| Last observation used | Saved per row in `outputs/features_recent_std.csv` (`first_lap_in_window`, `last_lap_used`, `last_end_time_used_s`). On all 7,580 rows the last lap used is lap t itself and its `end_time_s` ≤ the row's `end_time_s`. The window never leaves laps t−2…t of the same stint (there are no lap-number gaps inside a stint, asserted). |
| Independent check | `as_of_recompute` rebuilds the value for every pair from an **as-of view**: only laps of that driver whose `end_time_s` ≤ the pair's `end_time_s`. It agrees with the rolling version on every row, including which rows are missing (`checks.csv`, check 1). |
| Excluded | `next_lap_s`, every `next_*` field and `clean_pair` (asserted not in any model's inputs). `clean_pair` only defines the evaluated population. |
| Missing / short history | Fewer than 2 clean laps in the window → `recent_std_s` is missing (a std of 1 lap is undefined; 0 would wrongly mean "perfectly stable"). The Pipeline's median imputer, fitted on training rows only, fills it with **0.2579 s**, and `short_history = 1`. |
| Coverage (`outputs/coverage.csv`) | Train: 5,316 of 5,772 observed (92.1%), 456 filled. Validation: 1,660 of 1,808 observed (91.8%), 148 filled. No row is dropped. |
| Training-only fitting | Imputer, scaler and one-hot encoder live inside `make_model`'s Pipeline. `.fit` is called on training rows only; validation is only transformed (`run_hito2.py`, section 3). Quartile edges and the SHAP background also come from training rows. |
| Common rows | All runs predict the same 1,808 validation `pair_id`s: unique, 1:1 join coverage, and the SHA-256 of the sorted IDs (`f453a98d…`) equals the Hito 1 value (check 2). |

## 3. Executed comparison and ablation (C2, C3)

All four models are OLS from the supplied `make_model`, with the same categoricals (`current_compound`, `current_team`), the same training rows (rounds 1–7, n = 5,772), the same Pipeline and the same seed (414). Only the numeric inputs change. Predictions with their `pair_id`s: `outputs/validation_predictions.csv`. Metrics: `outputs/comparison_metrics.csv`.

| Version | Model and inputs | Validation n | MAE (s) | Output / run |
| --- | --- | --- | --- | --- |
| OLS reference (A) | OLS, six published inputs | 1,808 | 0.38671 | `pred_A_OLS_reference`; equals the saved Hito 1 predictions (max diff 2.8e-14 s) |
| Candidate (B) | OLS, six inputs + `recent_std_s` + `short_history` | 1,808 | **0.36973** | `pred_B_candidate` |
| Matched control (C) | OLS, six inputs + `short_history` (B with `recent_std_s` removed, refitted) | 1,808 | 0.38767 | `pred_C_matched_control` |

**Signed difference.** Control MAE − candidate MAE = 0.38767 − 0.36973 = **+0.01794 s**. A positive value means the candidate had lower MAE on these 1,808 rows. Against the fixed reference, A − B = +0.01698 s.

**Why C and not A as the control.** B adds two columns. C removes only `recent_std_s` and keeps the `short_history` indicator, so C − B isolates the variability value itself (Hito 1 plan). C alone is slightly *worse* than A (0.38767 vs 0.38671): the indicator by itself does not help (section 4.3).

**What this supports.** It meets the rule we wrote before building (≥ 0.01 s overall, no race worse), so the hypothesis is supported **for OLS, these inputs and these two validation races**.

**Mechanism (bounded hypothesis, `HITO1.md` §3) against the fitted model.** The expected mechanism was: after a one-off slow lap, `current_lap_s` and `recent_mean_s` overstate the next lap, and a negative coefficient on `recent_std_s` pulls the prediction back towards the driver's usual pace. The fitted model agrees with that reading. The coefficient of `recent_std_s` is negative (−0.264 s per training SD, about −0.58 s per second of std; `outputs/coefficients.csv`), and adding it moves weight from `current_lap_s` (3.49 → 2.85) to `recent_mean_s` (4.29 → 4.91). The bounds also show up: the shift is additive and does not know whether the odd lap was slow or fast, the gain is concentrated on a few rows after a large one-lap loss (below), and losses that first appear on lap t+1 stay uncorrected (section 4.2). This is a description of the fitted OLS, not a causal claim.

**Supplementary uncertainty (not part of the decision rule).** We resampled whole stints (112 driver-race stints, 2,000 replicates, seed 414), because laps in one stint are not independent. The 95% percentile interval of C − B is [+0.0088, +0.0286] s, and it is positive in 100% of the replicates (`outputs/bootstrap.csv`). This describes variation **within these two races**. It does not show that the gain holds in other races.

**One limit of the claim: the gain is concentrated** (`outputs/gain_concentration.csv`). Per-row gain = |control error| − |candidate error|. The candidate is better on 955 of 1,808 rows (53%). The top 10 rows give 36% of the total gain and the top 50 rows (2.8%) give 94.5%. Without those 50 rows, C − B is only +0.0010 s, and without the top 100 it is negative (−0.0077 s). So `recent_std_s` does not make typical predictions better. It fixes a small number of large errors right after an unusually slow lap and adds a little noise elsewhere. A validation set with fewer such incidents could show no gain at all.

**Prior checks and their result** (`outputs/checks.csv`, all written in Hito 1 before the code):

| Check | Expected / failure condition | Observed | Result |
| --- | --- | --- | --- |
| 1. Availability at t | Last lap used ends no later than t; no cross-stint window | All 7,580 rows; as-of recomputation identical | Pass |
| History convention (added after Hito 1 feedback) | Window = `recent_mean_s` window (last 3 laps, non-clean left out) | Rebuilt `recent_mean_s` / `recent_count` identical on all rows; worked history `2026-R8-1-L28` | Pass |
| 2. Same rows | Same 1,808 `pair_id`s and hash; no drops | Identical hash; A equals Hito 1 output | Pass |
| 3. Prior signal (train only) | Spearman(`recent_std_s`, \|OLS train residual\|) > 0, else expect no gain | ρ = 0.358 (n = 5,316) | Pass |
| 4. Support rule | C − B ≥ 0.01 s and ≥ 0 per race | +0.0179; +0.0128; +0.0253 | Supported |
| 5. Robustness slices | Per race, full vs short history | Saved; short history worse (section 4) | Done; reveals a limit |

## 4. Errors by context (C4)

### 4.1 By race (`outputs/race_table.csv`)

| Race | n (same IDs) | Control MAE (s) | Candidate MAE (s) | Control − candidate (s) | Reference MAE (s) |
| --- | --- | --- | --- | --- | --- |
| R8 (Austria) | 1,066 | 0.37163 | 0.35879 | **+0.01284** | 0.37357 |
| R9 (Great Britain) | 742 | 0.41071 | 0.38544 | **+0.02528** | 0.40558 |
| Pooled, weighted by n | 1,808 | 0.38767 | 0.36973 | **+0.01794** | 0.38671 |

Pooled values: (1,066 × 0.01284 + 742 × 0.02528) / 1,808 = 0.01794 s, equal to the direct pooled MAE difference (asserted in the code to 1e-12). **The races agree with the pooled result in sign.** The gain in R9 is about twice the gain in R8, and R9 has the higher error overall. R9 is not the "easy" race; it has more large errors to correct.

### 4.2 Inspected validation cases (`outputs/inspected_cases.csv`, raw laps in `outputs/inspected_cases_raw_laps.csv`)

We chose the cases by fixed rules written in the code, not by browsing.

| Rule | `pair_id` | Observed `next_lap_s` | Candidate pred | \|error\| cand. | Control pred | \|error\| ctrl. | Reference \|error\| |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Largest \|B − C\| (new input moved the prediction most) | `2026-R9-23-L7` | 97.882 | 99.121 | **1.239** | 102.110 | 4.228 | 4.152 |
| Largest candidate error in validation | `2026-R9-23-L6` | 105.128 | 96.874 | **8.254** | 97.354 | 7.774 | 7.825 |
| R9 short-history row where B lost most vs A | `2026-R9-81-L4` | 94.721 | 93.887 | **0.834** | 93.995 | 0.726 | 0.487 |

Check of the first row: |97.882 − 99.121| = 1.239 s (asserted in the code).

**One incident, two rows.** Albon (#23, Williams, hard tyres) lapped 96.299 s, 98.070 s, then **105.128 s on lap 7**. The track was green and the lap was accurate. The field median on lap 7 was 96.20 s and the next slowest car was 98.91 s, so this was an individual loss of about 9 s, not a track-wide event.
- At the end of lap 6 (`…-L6`) nothing in the history hinted at it, so every model predicted about 97 s. The 8.25 s miss is the **largest error in validation** and no lap-history input can foresee it.
- At the end of lap 7 (`…-L7`) the slow lap has happened. The control believes it and predicts 102.1 s. The candidate sees `recent_std_s` = 4.67 s (the highest in validation), discounts the slow lap and predicts 99.1 s. The real lap was 97.9 s, so the error falls from 4.23 s to 1.24 s.

### 4.3 Where the candidate is worse: short history (`outputs/slices.csv`)

| Slice | n | Control (s) | Candidate (s) | C − B (s) | Reference A (s) |
| --- | --- | --- | --- | --- | --- |
| Full history (2–3 clean laps) | 1,660 | 0.38252 | 0.36227 | +0.02025 | 0.38589 |
| Short history (1 clean lap) | 148 | 0.44545 | 0.45341 | −0.00795 | **0.39589** |
| R8 / short | 82 | 0.38305 | 0.37859 | +0.00446 | 0.39081 |
| R9 / short | 66 | 0.52299 | 0.54637 | −0.02337 | **0.40219** |
| `recent_std_s` Q4 (> 0.531 s, train edges) | 281 | 0.65901 | 0.53996 | **+0.11905** | 0.64609 |
| `recent_std_s` Q1–Q3 | 451 / 546 / 382 | – | – | +0.0020 / −0.0010 / −0.0005 | – |

On the 148 short-history rows, **both** B and C are worse than the reference A. The problem is R9: there, B is 0.144 s worse than A. The third case shows why. Piastri (#81, `2026-R9-81-L4`) had laps 1–2 under a non-green status and pitted on lap 3, so lap 4 was the only clean lap. In training, the lap after a short history is on average 0.37 s faster than the current lap (tyres and pace still coming in). The `short_history` indicator learned that offset and moved the prediction down to 93.89 s. In R9 that pattern did not hold: the mean change on short rows was +0.04 s, against −0.26 s in R8. The real lap was slower, 94.72 s.

### 4.4 Diagnosis and next checks

1. **Limitation (short history).** The short-history rule is the weak part of the design. The training offset learned by the `short_history` indicator holds in R8 and reverses in R9 (66 rows), so B is worse than the reference on those rows. *Next check:* trial D, below.
2. **Limitation (shocks at t+1).** The largest errors are sudden losses on lap t+1, like `…-L6`. Lap history cannot see them, and `recent_std_s` only helps on the lap *after* the incident. *Next check (final report):* a traffic proxy available at t. One option is the gap to the car that crossed the line just before our driver at the end of lap t, computed from other drivers' `end_time_s` ≤ t. Test it with the same A/B/C design, on the rows where |error| > 1 s (117 rows) and overall.

### 4.5 Next check executed: trial D (declared before running)

Before running it we wrote this down (`DECISION_LOG.md`, 2026-11-17): *if the short-history loss comes from the indicator, removing it should bring the short rows back to the reference level.* D = six inputs + `recent_std_s` (median fill), **without** `short_history`. Its matched control is the OLS reference A itself (shared run). Pass only if D's short-history MAE ≤ 0.401 s **and** A − D ≥ 0.01 s overall **and** ≥ 0 in each race.

| Population | n | A (s) | D (s) | A − D (s) | B (s) |
| --- | --- | --- | --- | --- | --- |
| All validation | 1,808 | 0.38671 | 0.36522 | +0.02148 | 0.36973 |
| R8 | 1,066 | 0.37357 | 0.35760 | +0.01597 | 0.35879 |
| R9 | 742 | 0.40558 | 0.37617 | +0.02941 | 0.38544 |
| Short history | 148 | 0.39589 | **0.41626** | −0.02037 | 0.45341 |
| Full history | 1,660 | 0.38589 | 0.36067 | +0.02522 | 0.36227 |

**Result: the rule fails** (0.4163 > 0.401 s). Removing the indicator recovers about two thirds of the short-row loss (B 0.453 → D 0.416), but D is still worse than A on those rows. The median fill plus the refit coefficients still hurts there. D is better overall (A − D = +0.0215 s, stint bootstrap interval [+0.0131, +0.0314] s), but its rule was written to fix short rows, and it did not. **Decision: keep B** as stated before running. D is logged as an unsuccessful trial and stays a candidate to revisit, with this selection history disclosed. *Next check (final report):* a declared fallback in which short-history rows use the reference prediction A. This is the "frozen reference fallback" the bonus rules allow, and it would be tested as its own trial against A.

## 5. Local SHAP explanation (C5)

| Item | Value |
| --- | --- |
| Model explained | **Candidate B** (fitted OLS, `run_hito2.py`). We chose it because the evidence supports keeping it and because it is the only model that contains `recent_std_s`, so it shows how the fitted model uses the new input. |
| Explainer | `shap.LinearExplainer` on the fitted `LinearRegression`, `shap.maskers.Independent` |
| Background | **All 5,772 training rows** (no subsampling), transformed by the train-fitted imputer, scaler and one-hot encoder |
| Row | Validation `2026-R9-23-L7` (the first inspected case, so the explanation and the error diagnosis use the same lap) |
| Units | Seconds of predicted `next_lap_s` |
| One-hot mapping | Contributions of one-hot columns are summed per original input (`outputs/shap_encoded_mapping.csv`). This is exact because the model is additive. |

`outputs/shap_local.csv`:

| Input | Value at t | Contribution (s) |
| --- | --- | --- |
| `recent_mean_s` | 99.832 | +8.1826 |
| `current_lap_s` | 105.128 | +6.6680 |
| `recent_std_s` | 4.671 | **−2.4671** |
| `current_compound` | HARD | +0.0425 |
| `current_lap_number` | 7 | −0.0315 |
| `short_history` | 0 | +0.0308 |
| `current_team` | Williams | −0.0268 |
| `current_tyre_life` | 6 | −0.0122 |
| **Base value** (mean training prediction) | | **86.7343** |
| Sum of contributions | | +12.3864 |
| **Base + sum** | | **99.1207** |
| Model prediction | | **99.1207** |

**Reconstruction.** 86.7343 + 12.3864 = 99.1207 s, the saved prediction. The difference is 0.0 at the printed precision. Across all 1,808 rows the largest difference is 1.4e-14 s, against a declared tolerance of 1e-6 s. We also recomputed the values by hand as coefficient × (x − training mean), and they are identical.

**Meaning.** Relative to the average training prediction (86.73 s), the high recent mean and the slow current lap push this prediction **up** by about 14.9 s, mostly because Silverstone laps (about 96 s) are slower than the average training lap. The unusually high variability (4.67 s against a training mean of 0.41 s) pulls it **down** by 2.47 s. That −2.47 s is how the model's association moves this prediction relative to the base. It is not an error and it is not a causal effect of variability on the lap.

**Observed error, computed separately.** Observed `next_lap_s` = 97.882 s; |97.882 − 99.121| = **1.239 s**. The model still over-predicts by 1.24 s. A negative contribution can coexist with an over-prediction, because the contribution is measured from the base value, not from the observed lap.

## 6. Global SHAP summary (C6)

| Item | Value |
| --- | --- |
| Model, explainer, background | Same as section 5 (B, LinearExplainer, all 5,772 training rows) |
| Declared sample | **All 1,808 validation rows** (rounds 8–9), also split by race |
| Aggregation | Mean of \|SHAP contribution\| per original input, in seconds (one-hot columns summed per input first). The mean signed value is reported next to it. |
| Files | `outputs/shap_global.csv`, `outputs/shap_global_bar.png`, `outputs/shap_beeswarm_numeric.png`, row-level values in `outputs/shap_values_validation.csv` |

| Rank | Input | Mean \|SHAP\| (s), all 1,808 | Mean signed (s) | R8 mean \|SHAP\| (n = 1,066) | R9 mean \|SHAP\| (n = 742) |
| --- | --- | --- | --- | --- | --- |
| 1 | `recent_mean_s` | 7.405 | −2.858 | 8.704 | 5.539 |
| 2 | `current_lap_s` | 4.273 | −1.629 | 5.005 | 3.220 |
| 3 | `recent_std_s` | 0.149 | +0.049 | 0.150 | 0.148 |
| 4 | `current_team` | 0.064 | −0.004 | 0.059 | 0.072 |
| 5 | `short_history` | 0.058 | −0.001 | 0.056 | 0.060 |
| 6 | `current_compound` | 0.031 | +0.007 | 0.037 | 0.024 |
| 7 | `current_lap_number` | 0.022 | −0.000 | 0.025 | 0.017 |
| 8 | `current_tyre_life` | 0.008 | −0.005 | 0.008 | 0.008 |

**What it suggests.** Most of the movement away from the base comes from the two pace-level inputs. In R8 their mean signed values are entirely negative (−8.70 s for `recent_mean_s`) and in R9 entirely positive (+5.54 s). They mostly place the prediction at the right **track pace** relative to the training average (86.7 s): Austria is faster and Silverstone slower. The beeswarm shows this as two separate clouds. `recent_std_s` is third, at about 0.15 s, with almost the same size in both races. It is small on average and very large on a few rows (down to −2.47 s): a correction that switches on after an erratic stretch. That agrees with the concentration found in section 3.

**Scope.** This ranking describes **how model B uses its inputs on these 1,808 validation rows from two races**, measured against a training background. A different background (for example, one track's laps) would shrink the pace-level contributions a lot. A ranking by mean |SHAP| is not a ranking of predictive value: `recent_std_s` ranks third, but its effect on MAE comes from the ablation (+0.018 s), not from this table. SHAP shows associations inside a fitted model. It does not show that variability *causes* faster or slower laps, and it does not generalise to other races or to non-clean laps.

## 7. Reproducibility (C7)

Command, environment, data manifest and the code-to-output map are in [README.md](README.md). One command regenerates every table and figure above in about 10 s. Two consecutive runs give byte-identical CSV and JSON outputs. A clean virtual environment built from `requirements.txt` reproduces them too.

## 8. Decision and limits

- **Keep** `recent_std_s` (candidate B). The decision follows the pre-declared ablation, C − B = +0.0179 s, positive in both races.
- **Tested scope:** OLS from `make_model`, the six reference inputs, clean pairs only, validation rounds 8 (Austria) and 9 (Great Britain). This says nothing about other model families, non-clean laps, live use (where nobody knows in advance whether lap t+1 will be clean) or the reserved final races.
- **Size of the evidence:** about 50 rows carry the gain. We used validation to choose B and to examine D, so these validation MAEs are selection evidence and are optimistic for unseen races.
- **Open issues for the final report:** a short-history fallback to the reference, and a traffic proxy for shocks at t+1, both with the same A/B/C design and per-race tables.
- No reserved final-evaluation data were accessed at any point.

## 9. Individual explanations

**Baptiste Vial.** I led the feature construction and anti-leakage verification for `recent_std_s`. Before trusting our rolling window, I rebuilt the reference columns `recent_mean_s` and `recent_count` from the raw snapshots and required an exact match across all 7,580 rows, proving our stint window aligns with the baseline. I also verified every row with an independent as-of recomputation using only laps ending at or before t (`end_time_s` ≤ t), which agreed completely (`checks.csv`, check 1). The main limitation in this setup is our short-history handling: on the 148 rows with only one clean lap in the window, median filling plus the `short_history` indicator underperforms the reference (0.453 s vs. 0.396 s), and dropping the indicator in trial D failed to resolve it. Next, I want to test falling back to the frozen reference prediction on short-history rows. Claude Code drafted the initial feature scripts, which I adjusted and validated through these exact-match and as-of checks rather than relying on visual code review alone.

**Vicente Rodríguez.** I executed the ablation study, error diagnosis, and SHAP analysis. Because candidate B introduces two columns, I evaluated it against matched control C rather than reference A so that C − B isolates the contribution of `recent_std_s` alone. That comparison yielded +0.0179 s overall, holding positive in both R8 (+0.0128 s) and R9 (+0.0253 s) (`race_table.csv`). Inspecting `2026-R9-23-L7` revealed how the feature works in practice: right after Albon's erratic 105.1 s lap, model B discounted the outlier and reduced the error from 4.23 s to 1.24 s. However, two limits stand out: 50 rows generate 94.5% of the total gain, and sudden shocks on lap t+1 such as `2026-R9-23-L6` (8.25 s error) remain invisible to lap history. For the final report, I plan to test a traffic proxy measured at the end of lap t. Claude Code and Gemini assisted with scripts and initial text drafts, which I verified by re-running the full pipeline, checking the pooled arithmetic and SHAP reconstruction by hand, and revising the prose directly.
