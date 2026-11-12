# Decision log · NextLap · Team 1

Members: Vicente Rodríguez, Baptiste Vial. Entries are kept in order; earlier entries are not rewritten.

## Decisions

| Date | Decision | Evidence | Who |
| --- | --- | --- | --- |
| 2026-11-06 | Before the class results, we predicted persistence would be the best reference, because the lap-to-lap spread of clean laps is low. | Worksheet section 2 (prediction written before results). | Baptiste |
| 2026-11-06 | Revised the explanation after the results: OLS beats persistence slightly (0.387 vs 0.409 s) because it already contains the persistence signal (`current_lap_s`, `recent_mean_s`) and adds small corrections. This does not show any single extra input is useful on its own. | `outputs/reference_metrics.csv` | Baptiste |
| 2026-11-06 | Chose **recent pace history** as the primary direction: add the standard deviation of the last 3 clean laps (`recent_std_s`). | Hito 1 brief lists variability beyond the recent mean as an admissible direction; uses released data only. | Vicente |
| 2026-11-06 | Rejected `next_lap_s` as an input: it is the target and is not known at the end of lap t. | Brief: future-known `next_*` columns must not enter the model. | Vicente |
| 2026-11-06 | Rolling windows grouped by race, driver and stint; the model is still trained on all races and drivers of rounds 1–7. | Brief: driver/race/stint boundaries. | Vicente |
| 2026-11-12 | Reproduced the three references with our own run (`run_references.py`). | Same counts (5,772 / 1,808), same data SHA-256 and MAE identical to the instructor-supplied outputs (max difference 1e-16 s). | Baptiste |

## Revisions after feedback

| Earlier entry | Feedback | Revised entry |
| --- | --- | --- |
| Hypothesis: vary the window of the recent **mean** (x = 8 … 1 laps) and keep the x with the best MAE; alternatively add the standard deviation. | Varying the mean window does not test the variability hypothesis, and picking the best x on validation is an uncontrolled search. (Feedback from the AI assistant during worksheet review; see AI record.) | Kept only the standard-deviation feature with a fixed window of 3. A pace-slope (trend) feature is logged as a possible later, separate trial. |
| Short history: if fewer than 3 laps, use the std of the laps available; with 0 laps set it to 0. | A std of 0 means "perfectly stable", which is not the same as "unknown"; a std of 1 lap is undefined. | Std only with 2 or more clean laps; otherwise missing, filled by the training-fitted imputer, plus a `short_history` indicator. |
| Failure condition: "MAE stays very similar or gets much worse"; a worse MAE with an explanation would still be fine. | Not measurable before building, and explaining a worse result afterwards does not make it a success. | Failure: improvement below 0.01 s, or MAE gets worse. Plus pre-build checks (no NaN/cross-stint leaks, correlation with reference absolute error on training rows). |
| Grouping by race and driver. | Brief requires stint boundaries too. | Grouping by race, driver and stint. |

## Trials

| Trial | Status | Result |
| --- | --- | --- |
| A. Reference OLS, 6 inputs | Done | Val MAE 0.387 s (n = 1,808) |
| B. + `recent_std_s` + `short_history` | Planned for Hito 2 | – |
| C. + `short_history` only | Planned for Hito 2 | – |

## Member contributions

| Member | What they did and can explain |
| --- | --- |
| Baptiste Vial | Worksheet answers on the opening example, reference prediction and interpretation, short-history rule, fixed controls and failure condition; ran `run_references.py` and checked it against the supplied outputs. |
| Vicente Rodríguez | Chose the primary direction (recent pace history, standard deviation of the last 3 clean laps), rejected `next_lap_s` as an inadmissible future-known input, and defined the race/driver/stint grouping of the rolling windows. |

## AI use record

Tool: Claude Code (Anthropic, Claude Opus 5.5), used by Baptiste.

| Use | Adopted? | How we checked it |
| --- | --- | --- |
| Turned our spoken answers (Spanish) into English text in the worksheet and fixed typos. | Yes | We reviewed every answer against what we meant. |
| Pointed out that the opening example concerns evaluation rows, not training rows. | Yes | Re-read the example: the 1,000 / 600 rows are where MAE was measured. |
| Suggested the four revisions in "Revisions after feedback" (hypothesis scope, short-history rule, measurable failure threshold, stint boundary). | Yes, with the 0.01 s threshold chosen by us | Checked against the Hito 1 brief (stint boundaries, no uncontrolled search on validation) and against `nextlap_reference_v1.py` (`recent_mean_s` uses clean laps within driver/race/stint). |
| Adapted the class helper `probar_referencia_v1.py` into `run_references.py` and drafted `HITO1.md`, `README.md` and this log from our worksheet answers. | Yes | Ran the script ourselves; compared metrics, counts and SHA-256 values with the instructor-supplied outputs; read every section of the documents. |
| Checked whether a pace-slope variable already exists in the data. | Yes | Confirmed in `nextlap_reference_v1.py`: no slope/trend input is supplied; it would have to be built. |

## Responsibilities before Hito 2 (19 November)

| Member | Next action |
| --- | --- |
| Baptiste Vial | Build `recent_std_s` from the raw snapshots and run checks 1–2. |
| Vicente Rodríguez | Run trials B and C, per-race MAE and checks 3–5. |

## Blockers for Ángel

None.
