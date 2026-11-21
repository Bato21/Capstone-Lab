# NextLap final report

**Team and both names:** Group 1 · Vicente Rodríguez and Baptiste Vial  
**Repository URL:** https://github.com/Bato21/Capstone-Lab  
**Exact commit SHA:** <!--SHA-->the commit tagged `Final` (the full SHA is printed here in the submitted PDF and given in the Canvas submission)<!--/SHA-->

Every number below is read from saved outputs at that commit. Paths are relative to the repository root. The Hito 2 run (`Hito2/run_hito2.py`) produced the comparison, error and SHAP results, unchanged since the commit tagged `Hito2`; the instructor's Hito 2 feedback reports reproducing its 0.01794 s gain, the R8/R9 results and the SHAP reconstruction. `Demo/` holds the Demo Day deck and script. `FinalReport/` holds this report, the revision after feedback (`FinalReport/run_final.py`, section 4) and the frozen final model (`FinalReport/predict.py`). Reserved final-evaluation data were never accessed.

## 1. Recommendation and use

At the end of lap t, the model predicts `next_lap_s`, the duration in seconds of the same driver's next lap (t+1), using only information available when lap t ends. The intended reader is a race engineer on the pit wall: a lap that comes in much slower than predicted flags something to check (tyres, traffic, a car problem). The prediction alone does not say when to pit or which compound to fit.

**Decision: keep the tested change.** Adding recent pace variability, `recent_std_s`, lowered the validation MAE from 0.38767 s (matched control) to 0.36973 s (candidate) on the same 1,808 clean validation pairs: **control − candidate = +0.01794 s**, positive in both validation races. This met the rule we fixed in Hito 1 before running (≥ 0.01 s overall and ≥ 0 in each race).

**Final frozen model.** After the Hito 2 feedback we added one declared fallback (section 4): on the 148 rows where the window holds fewer than two clean laps, so `recent_std_s` does not exist, the model returns the frozen reference prediction instead of the candidate's. This model, E, passed a rule written before running it: 0.36502 s against 0.38671 s for the reference (+0.02169 s on the same 1,808 rows, positive in both races), with the short-history rows no longer worse than the reference. E is frozen at the submitted commit and nominated for the improvement bonus.

**Main limitation.** The gain is concentrated: the candidate is better than its control on only 955 of 1,808 rows (53%), and 50 rows (2.8%) carry 94.5% of the gain, almost all right after an unusually slow lap. Rounds 8–9 were used to choose both the candidate and the fallback, so every validation MAE here is selection evidence, optimistic for unseen races.

## 2. Experiment and valid comparison

**Input tested.** `recent_std_s` is the sample standard deviation (ddof = 1) of the clean lap times among the last three laps of the current stint, laps t−2, t−1 and t, which is the same window as the reference input `recent_mean_s`. A lap is clean at its own end under the reference rule (lap > 1, accurate, not pit in or out, not deleted, green flag). Non-clean laps inside the window are left out and not replaced by older laps, so the window holds 3, 2, 1 or 0 clean times. Source: the released timing snapshots `base_NextLap/data/race_2026_r0{1..9}_laps_v2.csv`, with their SHA-256 values checked against the release manifest. No external data.

**History on the original timeline through t.** `Hito2/features.py` (`history_features`) builds the value on the full lap timeline before the clean-pair filter, grouped by season, round, driver and stint, then joins it to the released pairs by `pair_id`. Lap t is the last lap used and lap t+1 never enters. Worked history `2026-R8-1-L28` (`Hito2/outputs/history_convention_example.csv`): laps 24–26 were not under green flag and are left out, so the window holds laps 27 and 28 (71.773 s, 71.568 s) and `recent_std_s` = 0.145 s. Lap 29 (71.843 s) is the target and is never used.

**Availability checks** (`Hito2/outputs/checks.csv`, check 1). On all 7,580 training and validation rows, the last lap used ends no later than the row's own `end_time_s`. An independent as-of recomputation, which only sees laps ended by t, gives identical values and the same missing pattern. Our rebuild of the released `recent_mean_s` and `recent_count` matches them exactly on every row, so `recent_std_s` uses the same laps as the reference's own recent mean.

**Missing history.** With fewer than two clean laps the standard deviation is undefined, so the value is left missing (not 0, which would mean "perfectly stable"). The pipeline's median imputer, fitted on training rows only, fills 0.2579 s, and a binary `short_history` indicator is added. Coverage: 92.1% observed in training, 91.8% in validation (148 rows filled); no row is dropped (`Hito2/outputs/coverage.csv`).

**Evaluation population.** Development validation is rounds 8 (Austria) and 9 (Great Britain), 1,808 clean pairs. The retrospective `clean_pair` filter keeps pairs whose laps t and t+1 are both clean racing laps in the same stint. It uses t+1 information, so it defines which rows are scored and is never a predictor. The results describe clean racing laps only, not all laps or live use, where nobody knows in advance whether lap t+1 will be clean. The target, every `next_*` field and `clean_pair` are asserted absent from every model's inputs.

**Split and fitting.** Training on rounds 1–7 (5,772 pairs) and validation on rounds 8–9 (1,808); `pair_id` is unique in each and the sets are disjoint (asserted). Every run is OLS from the supplied `make_model`; its imputer, scaler and one-hot encoder sit inside the pipeline, `.fit` sees training rows only and validation is only transformed (`Hito2/run_hito2.py`, section 3). Seed 414.

**Common validation IDs** (`checks.csv`, check 2). Every run predicts exactly the same 1,808 unique `pair_id`s, with a 1:1 join. The SHA-256 of the sorted IDs equals the Hito 1 value, and run A reproduces the saved Hito 1 OLS predictions (largest difference 2.8e-14 s).

| Run | Model, inputs and settings | Common validation n | MAE (s) | Saved output or run ID |
| --- | --- | ---: | ---: | --- |
| Six-input OLS reference | OLS (`make_model`), six published inputs, train R1–R7, seed 414 | 1,808 | 0.38671 | `A_OLS_reference` in `Hito2/outputs/comparison_metrics.csv`; `pred_A_OLS_reference` in `validation_predictions.csv` |
| Candidate | Same + `recent_std_s` + `short_history` | 1,808 | **0.36973** | `B_candidate`; `pred_B_candidate` |
| Matched control without the change | Same + `short_history` only: the candidate with `recent_std_s` removed, refitted | 1,808 | 0.38767 | `C_matched_control`; `pred_C_matched_control` |

The candidate adds two columns, so the OLS reference is **not** the matched control. Control C keeps the `short_history` indicator and removes only `recent_std_s`, so C − B isolates the variability value. C alone is slightly worse than A (0.38767 vs 0.38671 s): the indicator by itself does not help.

**Matched control MAE − candidate MAE (s):** 0.38767 − 0.36973 = **+0.01794 s** on the 1,808 common rows. Positive means the candidate's average miss was smaller. It meets the pre-declared rule, so the hypothesis is supported **for OLS, these inputs, clean pairs and these two races**. A supplementary bootstrap that resamples whole stints (112 stints, 2,000 replicates, seed 414) gives a 95% interval of [+0.0088, +0.0286] s (`bootstrap.csv`); it describes variation within these two races only. We used these races to choose the candidate, so the validation MAEs are selection evidence and optimistic for unseen races.

## 3. Errors by context and model interpretation

| Validation context | Common n | Control MAE (s) | Candidate MAE (s) | Control − candidate (s) |
| --- | ---: | ---: | ---: | ---: |
| R8 | 1,066 | 0.37163 | 0.35879 | +0.01284 |
| R9 | 742 | 0.41071 | 0.38544 | +0.02528 |

Source: `Hito2/outputs/race_table.csv`. Both races agree in sign with the pooled result, so neither overturns it. Weighted by row counts, (1,066 × 0.01284 + 742 × 0.02528) / 1,808 = 0.01794 s, equal to the direct pooled difference (asserted in the code to 1e-12). The gain in R9 is about twice the R8 gain. R9 has the higher error overall: it is not an easier race, it has more large errors for the new input to correct.

**Inspected case.** `2026-R9-23-L7` (Albon, Williams, R9, end of lap 7; `Hito2/outputs/inspected_cases.csv`). Observed `next_lap_s` = **97.882 s**; candidate prediction **99.121 s**; absolute error |97.882 − 99.121| = **1.239 s** (asserted in the code). The matched control predicted 102.110 s (error 4.228 s). The row has full history, so the final model E gives the same 99.121 s (`FinalReport/outputs/validation_predictions_E.csv`). On lap 7, Albon lost about 9 s alone under green flag (105.128 s against a field median of 96.20 s). The control took the slow lap at face value, while the candidate saw the highest `recent_std_s` in validation (4.67 s) and pulled its prediction back. The lap before shows the limit: at the end of lap 6 (`2026-R9-23-L6`) nothing in the history hinted at the loss, and the candidate missed by 8.254 s, the largest error in validation. The example motivates checking whether the gain depends on a few such incidents. It did: without the top 50 rows by gain, C − B falls to +0.0010 s, and without the top 100 it is −0.0077 s (`gain_concentration.csv`). It leaves uncertain whether races with fewer incidents would show any gain at all.

**Where the model is worse.** On the 148 short-history rows the candidate scores 0.45341 s, against 0.39589 s for the reference (`slices.csv`); the loss comes from R9 (66 rows: 0.546 vs 0.402 s). The `short_history` indicator learned a training offset (the lap after a short history is about 0.37 s faster) that held in R8 but not in R9. Follow-up trial D removed the indicator under a rule written before running (short-history MAE ≤ 0.401 s); it reached 0.41626 s and **failed**, so we kept B (`followup_D_table.csv`).

**Scope and next checks.** Two observed failures bound the finding. First, short history: the candidate loses to the reference on the 148 rows with one clean lap, and the loss comes from one race (R9), so the gain of `recent_std_s` only holds for rows with at least two clean laps of history. Second, sudden losses on lap t+1: the largest error, `2026-R9-23-L6` (8.254 s), comes from a loss that no lap-history input can see, and `recent_std_s` only helps on the following row. The claim is therefore limited to OLS, clean pairs, rows with full history and rounds 8–9, and the validation MAEs are selection evidence. The Hito 2 decision log declared one follow-up check for each failure ([Hito2/DECISION_LOG.md](../Hito2/DECISION_LOG.md), entry 2026-11-17 (2)):

1. **Short-history fallback** (owner Baptiste): rows with `short_history = 1` use the frozen reference prediction A, all other rows keep B, tested against A with a rule written before running. The Hito 2 feedback made this the priority; it was run and passed (section 4).
2. **Traffic proxy at t** (owner Vicente), still open: the gap to the car that crossed the line just before our driver at the end of lap t, computed only from other drivers' `end_time_s` ≤ the row's `end_time_s`, tested with the same matched-control design overall and on the 117 validation rows where the candidate misses by more than 1 s. It targets the second failure, which the fallback does not touch: E still misses `2026-R9-23-L6` by 8.254 s.

**SHAP local.** Model: the fitted candidate B (OLS pipeline). Row: `2026-R9-23-L7`. E returns B's prediction on this full-history row, so this is also the explanation of the final model's output here. Explainer: `shap.LinearExplainer` with an independent masker and the 5,772 training rows as background, after the train-fitted preprocessing; one-hot contributions are summed per original input (`Hito2/outputs/shap_local.csv`, `shap_encoded_mapping.csv`).

| Input | Value at t | Contribution (s) |
| --- | --- | ---: |
| Base value (mean training prediction) | | 86.7343 |
| `recent_mean_s` | 99.832 | +8.1826 |
| `current_lap_s` | 105.128 | +6.6680 |
| `recent_std_s` | 4.671 | −2.4671 |
| Five other inputs (compound, lap number, `short_history`, team, tyre life) | | +0.0028 |
| **Base + contributions** | | **99.1207** |
| Model prediction | | 99.1207 |

The reconstruction is exact: 86.7343 + 12.3864 = 99.1207 s. Across all 1,808 rows the largest gap is 1.4e-14 s (check in `checks.csv`). In output units, `recent_std_s` moves this prediction 2.47 s below where the base and the other inputs would put it, because the window was unusually erratic (4.67 s against a training mean of 0.41 s). That is a shift relative to the base value, not an error and not a causal effect. The observed error is computed separately: 1.239 s, an over-prediction. A negative contribution can coexist with an over-prediction because contributions are measured from the base, not from the observed lap.

**SHAP global.** Same model, explainer and training background, over a declared sample of **all 1,808 validation rows**, also split by race. Aggregation: mean |SHAP| per original input in seconds (`Hito2/outputs/shap_global.csv`, `shap_global_bar.png`, `shap_beeswarm_numeric.png`). `recent_mean_s` (7.41 s) and `current_lap_s` (4.27 s) dominate: they place each prediction at the right track pace relative to the training average, negative in R8 and positive in R9. `recent_std_s` ranks third at 0.15 s, with the same size in both races, small on most rows and large on a few (down to −2.47 s). That pattern matches the concentration above. SHAP ranks how the model moves its output inside this sample; it does not rank predictive value. The contribution to performance comes from the ablation: removing `recent_std_s` (control C) raises MAE by 0.01794 s. The summary describes B; on the 148 short-history rows, where `recent_std_s` is only the training median, the final model E uses the reference instead, so the summary applies to E on the other 1,660 rows.

## 4. Revision after feedback

We presented the Hito 2 evidence at the Demo Day on 20 November (deck and script in [Demo/](../Demo/README.md)) and received the Hito 2 feedback the same day. At the Demo Day the jury asked one question, which we answered, and gave no written feedback, so the priority comes from the Hito 2 feedback alone. It is quoted as received in [FinalReport/DECISION_LOG.md](DECISION_LOG.md), "Feedback received"; the rule we wrote before running, the result and the decision are in the same log, entry 2026-11-20.

| Feedback source and priority | Change or justified decision to keep | Check, result and output |
| --- | --- | --- |
| Hito 2 feedback, priority correction: "Focus the final revision on short history." Check asked: "Predeclare a short-history fallback to the frozen reference. Check the 148-row slice and both races using the same IDs, then freeze the choice before final evaluation." | **Change.** Trial E: rows with `short_history = 1` use the frozen reference prediction A; all other rows keep candidate B. No refit and nothing tuned: A and B are the models fitted at the commit tagged `Hito2`, and the switch uses only `short_history`, which is known at the end of lap t. E passed its rule, so it is **frozen as our final model** and nominated for the bonus. | Rule written in the log before `FinalReport/run_final.py` existed: trial D's rule, unchanged, with control A: short-history MAE ≤ 0.401 s and A − E ≥ 0.01 s overall and ≥ 0 in R8 and R9. Result: 0.39589 s (n = 148); A − E = +0.02169 s (1,808), +0.01384 s (R8, 1,066), +0.03296 s (R9, 742): **pass**. Same 1,808 `pair_id`s as Hito 1 (SHA-256 check). `FinalReport/outputs/trial_E_checks.csv`, `trial_E_table.csv`. |

| Population (same pair IDs) | n | A reference MAE (s) | B candidate MAE (s) | E final MAE (s) | A − E (s) | B − E (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| All validation | 1,808 | 0.38671 | 0.36973 | **0.36502** | **+0.02169** | +0.00471 |
| R8 | 1,066 | 0.37357 | 0.35879 | 0.35973 | +0.01384 | −0.00094 |
| R9 | 742 | 0.40558 | 0.38544 | 0.37261 | +0.03296 | +0.01282 |
| Short history, both races | 148 | 0.39589 | 0.45341 | 0.39589 | 0 | +0.05752 |
| Short history, R8 | 82 | 0.39081 | 0.37859 | 0.39081 | 0 | −0.01223 |
| Short history, R9 | 66 | 0.40219 | 0.54637 | 0.40219 | 0 | +0.14418 |

Source: `FinalReport/outputs/trial_E_table.csv`. E differs from B only on the 148 short-history rows, where it equals A by construction, so B − E isolates the fallback. Weighted by row counts, (1,066 × 0.01384 + 742 × 0.03296) / 1,808 = 0.02169 s, equal to the pooled A − E (asserted in the script).

**Why this priority.** It was the only correction in the Hito 2 feedback; the rest confirmed the evidence. It is also the one place where our recommendation was worse than the reference it claims to improve on, and the rows involved (the lap after a pit stop or a yellow flag) occur in every race and must stay in any final evaluation: the bonus rules forbid dropping difficult rows.

**Result and decision.** The fallback removes the short-history loss: on those 148 rows E scores 0.39589 s, the reference's own value, against 0.45341 s for B, and the overall MAE falls from 0.36973 s (B) to 0.36502 s. Per race the slice tells two stories. In R9 the fallback recovers 0.144 s per short-history row (66 rows), because there the `short_history` offset learned in training was wrong. In R8 it costs 0.012 s per row (82 rows), because there B had been better than A; the net R8 effect is −0.00094 s. The rule compares E with the frozen reference, as declared in Hito 2, and E beats A in both races, so E passes. Resampling whole stints (112 stints, 2,000 replicates, seed 414, as in Hito 2) gives A − E in [+0.0124, +0.0321] s and B − E in [+0.0018, +0.0076] s (`trial_E_bootstrap.csv`); like every interval here, it describes these two races only. What does not change: the decision to keep `recent_std_s`, which rests on C − B = +0.01794 s (section 2), and the SHAP evidence of section 3, which explains B on a full-history row that E leaves untouched.

**Verification and its limit.** `FinalReport/run_final.py` checks the row identity, that A still equals the saved Hito 1 predictions, that `short_history` equals the missing pattern of `recent_std_s`, the pooled arithmetic and that its A − B bootstrap reproduces the saved Hito 2 interval. `FinalReport/predict.py` refits A and B on rounds 1–7 from the released files, rebuilds the features from an as-of history view and reproduces E's saved predictions on all 1,808 rows (largest difference 7.7e-13 s; `FinalReport/outputs/predict_self_check.json`). This was **not a blind test**: E combines saved Hito 2 predictions, and its result was largely implied by the saved slice table, which we had read. To keep the rule from being fitted to the result, we reused trial D's rule word for word and recorded this before running.

## 5. Reproduce the result

| What a reviewer needs | Location or instruction |
| --- | --- |
| Repository access and frozen commit | https://github.com/Bato21/Capstone-Lab (public; it opens without signing in). Commit tagged `Final`; full SHA on page one. The Hito 2 run is unchanged since the commit tagged `Hito2`. |
| Data version and manifest | `IIT414W_Capstone_NextLap_StudentData_v1.zip` from Canvas (not redistributed), extracted into `base_NextLap/`. SHA-256 of every input in [Hito2/README.md](../Hito2/README.md) and `Hito2/outputs/run_manifest.json`; the script stops if any differs. |
| Environment and seed | Python 3.11.9 with the exact versions in [Hito2/requirements.txt](../Hito2/requirements.txt), used by every script; `RANDOM_SEED = 414` (numpy, stint bootstraps, beeswarm jitter; OLS itself has no randomness). |
| Exact run command | From the repository root: `python -m venv .venv`, activate it, `pip install -r Hito2/requirements.txt`, then `cd Hito2`, `python run_hito2.py` (about 10 s) and `cd ..`. Revision: `python FinalReport/run_final.py` (reads the saved outputs only, about 1 s). Final model: `python FinalReport/predict.py --self-check` (about 30 s), or `python FinalReport/predict.py --requests R.csv --history H.csv --out P.csv` for new requests. |
| Code and output map | Comparison, error tables and SHAP: [Hito2/README.md, evidence map](../Hito2/README.md); interpretation in [Hito2/HITO2.md](../Hito2/HITO2.md). Revision and final model: [FinalReport/README.md](README.md), outputs in `FinalReport/outputs/`. Demo Day deck, script and the scripts that rebuild them from the saved outputs: [Demo/README.md](../Demo/README.md). |
| Decision and AI record | [Hito2/DECISION_LOG.md](../Hito2/DECISION_LOG.md) (Hito 1 and Hito 2 entries) and [FinalReport/DECISION_LOG.md](DECISION_LOG.md) (Demo Day, final revision, AI use after Hito 2). |

**Trial log.** Every configuration we fitted, all OLS from `make_model`, trained on rounds 1–7 and scored on the same validation rows (`FinalReport/outputs/trial_log.csv`, assembled from `Hito2/outputs/comparison_metrics.csv`, `slices.csv` and trial E):

| Run | Inputs | MAE all (1,808) | R8 (1,066) | R9 (742) | Short history (148) | Rule it was judged by | Outcome |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| A | Six reference inputs | 0.38671 | 0.37357 | 0.40558 | 0.39589 | Fixed reference | Reference |
| B | Six + `recent_std_s` + `short_history` | 0.36973 | 0.35879 | 0.38544 | 0.45341 | Hito 1: C − B ≥ 0.01 s overall, ≥ 0 per race | Supported, kept |
| C | Six + `short_history` | 0.38767 | 0.37163 | 0.41071 | 0.44545 | Matched control of B | Control |
| D | Six + `recent_std_s`, no indicator | 0.36522 | 0.35760 | 0.37617 | 0.41626 | Short MAE ≤ 0.401 s; A − D ≥ 0.01 s overall, ≥ 0 per race | Failed, B kept |
| E | B, with A on short-history rows | **0.36502** | 0.35973 | 0.37261 | 0.39589 | D's rule, unchanged | **Passed, frozen** |

**Unsuccessful trials and adjustments.** Control C showed that the `short_history` indicator alone does not help (MAE 0.38767 vs 0.38671 s for A). Follow-up D failed the rule we wrote before running it (short-history MAE 0.41626 > 0.401 s), so we kept B even though D's overall MAE was lower. That number is disclosed but not used to switch. Trial E, after the Hito 2 feedback, passed the same rule and replaced B as the frozen model; in R8 it is slightly worse than B (−0.00094 s). Adjustments made after seeing validation results are labelled post-hoc: trials D and E, the stint bootstraps and the gain-concentration table. After the Hito 1 feedback we clarified the window convention, added a convention check, and stated the mechanism as a bounded hypothesis written after the results; the code, the 0.01 s threshold and every Hito 1 number were unchanged. No window, model family or setting was searched on validation.

**AI use.** Claude Code (Anthropic) and Gemini (Google) were used. Adopted suggestions and how each was checked are recorded in `Hito2/DECISION_LOG.md` (AI use record) and `FinalReport/DECISION_LOG.md` (after Hito 2). Up to Hito 2: the feature code, accepted only after the exact rebuild of `recent_mean_s` and the as-of recomputation agreed on every row, and the run script, re-run in a clean environment with byte-identical outputs, checking the pooled arithmetic and the SHAP reconstruction by hand. After Hito 2 (Claude Code): checking the Demo Day deck and script against the closeout guide, the programme and the slide template; rebuilding the deck on the template; tuning the script to the template timings; and drafting `run_final.py`, `predict.py` and this report. We dropped one unsupported claim it drafted ("two dry races"), and a script matched every decimal on the slides and in this report to the saved outputs.

**Contributions.**

- **Baptiste Vial** built `recent_std_s` and its availability checks (`Hito2/features.py`; checks 1, 2 and the history convention). Decision: require the rebuilt `recent_mean_s` and `recent_count` to match the released columns exactly before trusting the new input. Result: identical on 7,580/7,580 rows, with the as-of recomputation agreeing on every value.
- **Vicente Rodríguez** ran runs A–D, the ablation, race and slice tables, inspected cases and SHAP (`Hito2/run_hito2.py`; checks 3–5 and D). Decision: use C, not A, as the matched control, and keep B after D failed its rule. Result: C − B = +0.01794 s, positive in R8 and R9; D short-history MAE 0.41626 s > 0.401 s.
- **After Hito 2.** Baptiste presented slides 2, 4 and 6 at the Demo Day and owned the short-history fallback declared in Hito 2, which became trial E: it switches on `short_history` only, known at t (short-history MAE 0.39589 s ≤ 0.401 s). Vicente presented slides 1, 3 and 5, built the Demo Day material, ran trial E and wrote `predict.py` and this report: E was frozen only after passing D's unchanged rule (A − E = +0.02169 s, positive in both races). Details in `FinalReport/DECISION_LOG.md`.

### Optional bonus nomination

**Nominated model: E**, frozen at the submitted commit: candidate B (OLS via `make_model`, six reference inputs + `recent_std_s` + `short_history`), with the frozen six-input OLS reference as the declared fallback on rows with fewer than two clean laps in the window. Both models train on the released rounds 1–7 only; preprocessing is fitted on training rows inside the pipeline; seed 414 (OLS has no randomness).

- **Run command** (repository root, Hito 2 environment, released data in `base_NextLap/`): `python FinalReport/predict.py --requests REQUESTS.csv --history HISTORY.csv --out predictions.csv`.
- **Required inputs:** the prediction requests of the input contract (`pair_id`, `season`, `round`, `driver_number`, `stint`, `end_time_s` and the six reference inputs) and the as-of history view in the timing-snapshot schema. For each request the script reads only laps of the same driver, race and stint with `end_time_s` ≤ the request's `end_time_s`; it uses no other source.
- **Output:** one finite prediction per requested `pair_id` (asserted: none missing or duplicated), and a JSON summary with the fallback counts: rows from B, rows on the reference fallback, rows with no history found (also on the fallback) and inputs filled by training medians. On validation: 1,660 from B, 148 on the fallback, 0 without history.
- **Validation evidence (selection evidence, rounds 8–9 chose B and then E):** MAE 0.36502 s against 0.38671 s for the reference on the same 1,808 rows, gain +0.02169 s; per race +0.01384 s (R8) and +0.03296 s (R9). The added information is tested separately in sections 2 and 4.
- **Prior access:** none. The reserved final-evaluation data were never accessed; all selection used rounds 8–9 only.
