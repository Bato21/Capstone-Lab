# Capstone NextLap · Hito 1 · Team 1

IIT414W · Team 1 · Members: Vicente Rodríguez, Baptiste Vial · Due 12 November 2026, 23:59

Run instructions are in [README.md](README.md). Decisions, feedback and AI use are in [DECISION_LOG.md](DECISION_LOG.md).

> **Revised on 17 November 2026 after the Hito 1 feedback** (C3.1 and C4.4). Changed: the window convention and a worked history (section 3), the expected mechanism written as a bounded hypothesis (section 3), and the wording of check 4 (section 4). The plan, the threshold, the code and every number are unchanged. The mechanism text was written after the Hito 2 results were known, so it is a clarification of the hypothesis, not a prediction made in advance; the predeclared rule that decides it (check 4) was not changed. The graded version is the `Hito1` tag and release (commit `4883f92`). The changes are logged in [DECISION_LOG.md](DECISION_LOG.md), "Revisions after the Hito 1 instructor feedback".

## 1. Problem and decision value

| Item | Definition |
| --- | --- |
| Target | `next_lap_s`: duration of the same driver's next lap (t+1). |
| Unit | Seconds. Metric: MAE in seconds. |
| Prediction time | At the end of lap t, using only information observed up to the end of lap t. |
| Intended reader | A race engineer or strategist on the pit wall who monitors their driver's pace lap by lap. |
| Decision it informs | Compare the expected next lap with the lap actually completed. A lap much slower than expected flags something to investigate, such as tyre degradation, traffic or a car problem. The estimate is also one input when projecting gaps to rivals over the next laps. |
| What it cannot establish | A lap-time prediction on its own does not say when to pit, which compound to fit or how many positions a strategy will gain. Those decisions need models of pit loss, rival behaviour and race events that are outside this task. |

**Limit of the clean-pair setting.** The common evaluation uses only clean pairs: 1,808 of the 2,327 observed consecutive pairs (77.7%) in validation rounds 8–9. `clean_pair` excludes pit in/out laps, deleted or inaccurate laps, non-green track status and stint changes, and it uses t+1 information to do so. It is a retrospective, conditional population. Our MAE therefore describes clean racing laps only. It is not evidence about all race laps or live use, where nobody knows in advance whether the next lap will be clean.

## 2. Reproduced reference

| Item | Value |
| --- | --- |
| Data version | `IIT414W_Capstone_NextLap_StudentData_v1` (`train_clean_v1.csv`, `validation_clean_v1.csv`); SHA-256 values in `outputs/reference_run.json` match the released files. |
| Split | Train: rounds 1–7 of 2026, 5,772 clean pairs. Validation: rounds 8–9, 1,808 clean pairs. `pair_id` is unique in each set and the two sets are disjoint (asserted in the script). No reserved final-evaluation data used. |
| Features | `current_lap_s`, `recent_mean_s`, `current_lap_number`, `current_tyre_life` (numeric); `current_compound`, `current_team` (categorical). No `next_*` column enters the model (asserted). |
| Fit/transform separation | The median imputer, standard scaler and one-hot encoder are inside the `make_model('OLS')` Pipeline. `.fit` is called only on training rows; validation is only transformed and predicted. The training median is computed on training rows only. |
| Command | `python run_references.py` (from `Hito1/`). Seed 414. |
| Environment of our run | Python 3.10.4, numpy 1.26.4, pandas 2.2.3, scikit-learn 1.7.2. |

**Own run** (`outputs/reference_metrics.csv`). All three models are scored on the same 1,808 validation `pair_id`s (`outputs/validation_reference_predictions.csv`).

| Model | All validation (n = 1,808) | Round 8 (n = 1,066) | Round 9 (n = 742) |
| --- | --- | --- | --- |
| Training median | 11.376 s | 11.716 s | 10.888 s |
| Persistence (`current_lap_s`) | 0.409 s | 0.401 s | 0.422 s |
| OLS reference | **0.387 s** | **0.374 s** | **0.406 s** |

Our numbers agree with the instructor-supplied outputs to within 1e-16 s, with identical row counts and data hashes. The supplied outputs were used only as a cross-check; the table above comes from our own execution.

**One comparison explained.** Before seeing results we expected persistence to be the best reference, because consecutive clean laps of the same driver are usually very close. Persistence is indeed far better than the training median (0.41 s vs 11.38 s), since a single median ignores track and pace. OLS improves on persistence by about 0.023 s overall, and in both races. OLS already includes `current_lap_s` and `recent_mean_s`, so it starts from the persistence signal and adds small corrections from tyre life, lap number, compound and team. This does **not** show that any of those extra inputs is useful on its own. The gain comes from the set of inputs on top of a strong persistence base, and it is measured on clean pairs only.

## 3. Primary hypothesis

Direction: **recent pace history**.

| Item | Definition |
| --- | --- |
| Proposed feature | `recent_std_s`: sample standard deviation (ddof = 1) of the driver's clean lap times among the last 3 laps of the current stint (laps t−2, t−1 and t), lap t included. Added to the six reference inputs. |
| Window convention *(revised)* | The window is the same as the reference `recent_mean_s`: the last 3 **laps** of the stint, not the last 3 **clean** laps. A non-clean lap inside the window (for example a lap under yellow flag or a virtual safety car) is left out and is **not** replaced by an earlier clean lap, so the window holds 3, 2, 1 or 0 clean times. Reason: the reference input already uses this window, so B and C differ only in the aggregation (std instead of mean), and the history never reaches back across a neutralised period. Our earlier wording "last 3 clean laps" was shorthand; the two readings give different values on 111 of the 1,808 validation rows (6.1%). |
| Worked history *(revised)* | Pair `2026-R8-1-L28` (driver 1, McLaren, Austria, stint 2): lap 23 = 72.148 s (clean), laps 24–26 non-clean (track status not green, not accurate), lap 27 = 71.773 s (clean), lap 28 = t = 71.568 s (clean). Window = laps 26–28 → clean times 71.773 and 71.568 → `recent_std_s` = 0.145 s from 2 clean laps (`recent_count` = 2, the same laps as the released `recent_mean_s` = 71.6705 s). The "last 3 clean laps" reading would reach back past the neutralised laps to lap 23 and give 0.294 s. Lap 29 (t+1, 71.843 s) is the target and is never used. Data: `Hito2/outputs/history_convention_example.csv`. |
| Expected mechanism *(revised as a bounded hypothesis)* | `recent_mean_s` says where the pace is, but not how stable it is. The reference OLS predicts the next lap mainly from `current_lap_s` and `recent_mean_s`. When lap t (or another lap in the window) was a one-off loss, for example traffic or a small mistake, both inputs are pulled away from the driver's usual pace, and the next clean lap tends to return towards it. A high `recent_std_s` marks exactly those windows. **Hypothesis:** with `recent_std_s` added, OLS learns a negative coefficient, so after an erratic window it predicts a faster next lap than the reference does, closer to the driver's usual pace, and this lowers MAE. **Bounds:** OLS can only add a shift proportional to `recent_std_s`; it cannot tell whether the odd lap was slow or fast, and it cannot reweight the laps row by row. We therefore expect a small gain, concentrated on rows right after a large one-lap deviation, and none where the recent laps are stable. It also cannot anticipate a loss that first appears on lap t+1. |
| Source | Released timing snapshots in `base_NextLap/data/race_2026_r0X_laps_v2.csv` (`lap_time_s`, `stint`, `track_status`, `is_accurate`, `pit_in`, `pit_out`, `deleted`). No external source, so no external fallback is needed. |
| Availability at t | Computed only from laps that have already ended at the end of lap t (lap t included, lap t+1 never). Rolling windows are grouped by season, round, driver and stint, so they never cross races, drivers (and therefore teams) or tyre stints. As with `recent_mean_s`, only already-observed clean laps feed the history; a bad lap does not become a hidden input. History is built on the original timeline **before** the retrospective clean-pair filter, then merged by `pair_id`. |
| Not admissible | `next_lap_s` or any `next_*` field: it is the target or future-known at t. |
| Short-history rule | With 2 or 3 clean laps in the window, use their standard deviation. With fewer than 2 the value is left **missing**, not 0 (0 would falsely mean perfectly stable pace). The Pipeline's median imputer, fitted on training rows only, fills it, and a binary `short_history` indicator is added. In validation, 148 of 1,808 rows have only 1 clean lap of history (`recent_count = 1`) and would use this rule. |

## 4. Experiment plan

**Fixed controls (identical across every run):** target `next_lap_s`; MAE in seconds; model family OLS via `make_model`; the six reference inputs; training rows (rounds 1–7, 5,772) and validation rows (rounds 8–9, the same 1,808 `pair_id`s, checked by hash); preprocessing fitted on training rows only; seed 414.

| Run | Information | Model | Rows and split | Metric | What it isolates |
| --- | --- | --- | --- | --- | --- |
| A. Fixed reference | 6 reference inputs | OLS | Train R1–7 / Val R8–9, same `pair_id`s | Val MAE (s), overall and per race | Baseline (already reproduced: 0.387 s) |
| B. Extension | 6 inputs + `recent_std_s` + `short_history` | OLS | Same | Same | Effect of adding pace variability |
| C. Without the added information | 6 inputs + `short_history` only | OLS | Same | Same | Whether any gain comes from the variability value itself, not from the short-history indicator |

The contribution of `recent_std_s` is read from **B vs C**; B vs A gives the total change from the extension.

**Planned checks, written before implementation:**

1. *Availability:* for a sample of rows, confirm that the last lap used by `recent_std_s` has `end_time_s` ≤ the row's `end_time_s`, and that no window crosses a stint change.
2. *Same rows:* the validation `pair_id` set and its SHA-256 are unchanged between A, B and C; no rows dropped by the new feature.
3. *Prior signal (training rows only):* `recent_std_s` should show a positive correlation with the absolute error of the reference OLS. If there is no relationship at all, we expect no gain.
4. *Support rule:* the hypothesis is **supported** if B improves validation MAE over C by at least 0.01 s overall **and** does not get worse in either validation race. If the improvement is below 0.01 s, or MAE gets worse in either race, the result **does not meet the predeclared improvement criterion**. That outcome would not refute the broader idea that variability may contain information; it would only say that this feature, in this OLS model, did not give the improvement we required. A negative result will be reported, not hidden. *(Wording revised after the Hito 1 feedback; the 0.01 s threshold is unchanged.)*
5. *Robustness:* MAE by validation race with counts (round 8, round 9), and separately for rows with full vs short history.

**Search plan.** One pre-declared candidate: window 3 (same as `recent_mean_s`), minimum 2 clean laps, sample standard deviation. No search over windows or models on validation. Any further variant (for example, a pace-slope/trend feature) is a separate, logged trial with its own A/B/C comparison, and every trial is recorded in `DECISION_LOG.md`, including unsuccessful ones.

**Validation and test.** Validation rounds 8–9 are used only to compare the pre-declared runs above. Reserved final-evaluation data are never used for choosing features, parameters or models; we have had no access to them. Any broader-population analysis (`observed_pairs_train_validation_v1.csv`) will be reported separately from the fixed common comparison.

**What would remain unsupported even if B wins:** that the gain holds outside clean pairs or in live use; that it transfers to the final evaluation races or to other models; that variability *causes* slower or faster next laps. Execution, ablation, contextual errors and SHAP are planned for Hito 2.

## 5. Traceability and next steps

Actual contributions, AI record, the revision after feedback, responsibilities before Hito 2 and blockers are recorded in [DECISION_LOG.md](DECISION_LOG.md).
