# Decision log · NextLap · Team 1

Members: Vicente Rodríguez, Baptiste Vial. Entries are kept in order; earlier entries are not rewritten.

- **Part 1** reproduces the Hito 1 log exactly as submitted (`Hito1/DECISION_LOG.md`, commit `4883f92`), so the earlier entries stay visible in this submission. Its file paths (`outputs/…`, `run_references.py`) are relative to `Hito1/`; only the heading levels were changed.
- **Part 2** adds the Hito 2 entries. The revisions made after the Hito 1 instructor feedback are recorded in Part 2 ("Feedback received") and were also appended to `Hito1/DECISION_LOG.md`.

---

# Part 1 · Hito 1 entries (unchanged copy)

### Decisions

| Date | Decision | Evidence | Who |
| --- | --- | --- | --- |
| 2026-11-06 | Before the class results, we predicted persistence would be the best reference, because the lap-to-lap spread of clean laps is low. | Worksheet section 2 (prediction written before results). | Baptiste |
| 2026-11-06 | Revised the explanation after the results: OLS beats persistence slightly (0.387 vs 0.409 s) because it already contains the persistence signal (`current_lap_s`, `recent_mean_s`) and adds small corrections. This does not show any single extra input is useful on its own. | `outputs/reference_metrics.csv` | Baptiste |
| 2026-11-06 | Chose **recent pace history** as the primary direction: add the standard deviation of the last 3 clean laps (`recent_std_s`). | Hito 1 brief lists variability beyond the recent mean as an admissible direction; uses released data only. | Vicente |
| 2026-11-06 | Rejected `next_lap_s` as an input: it is the target and is not known at the end of lap t. | Brief: future-known `next_*` columns must not enter the model. | Vicente |
| 2026-11-06 | Rolling windows grouped by race, driver and stint; the model is still trained on all races and drivers of rounds 1–7. | Brief: driver/race/stint boundaries. | Vicente |
| 2026-11-12 | Reproduced the three references with our own run (`run_references.py`). | Same counts (5,772 / 1,808), same data SHA-256 and MAE identical to the instructor-supplied outputs (max difference 1e-16 s). | Baptiste |

### Revisions after feedback

| Earlier entry | Feedback | Revised entry |
| --- | --- | --- |
| Hypothesis: vary the window of the recent **mean** (x = 8 … 1 laps) and keep the x with the best MAE; alternatively add the standard deviation. | Varying the mean window does not test the variability hypothesis, and picking the best x on validation is an uncontrolled search. (Feedback from the AI assistant during worksheet review; see AI record.) | Kept only the standard-deviation feature with a fixed window of 3. A pace-slope (trend) feature is logged as a possible later, separate trial. |
| Short history: if fewer than 3 laps, use the std of the laps available; with 0 laps set it to 0. | A std of 0 means "perfectly stable", which is not the same as "unknown"; a std of 1 lap is undefined. | Std only with 2 or more clean laps; otherwise missing, filled by the training-fitted imputer, plus a `short_history` indicator. |
| Failure condition: "MAE stays very similar or gets much worse"; a worse MAE with an explanation would still be fine. | Not measurable before building, and explaining a worse result afterwards does not make it a success. | Failure: improvement below 0.01 s, or MAE gets worse. Plus pre-build checks (no NaN/cross-stint leaks, correlation with reference absolute error on training rows). |
| Grouping by race and driver. | Brief requires stint boundaries too. | Grouping by race, driver and stint. |

### Trials

| Trial | Status | Result |
| --- | --- | --- |
| A. Reference OLS, 6 inputs | Done | Val MAE 0.387 s (n = 1,808) |
| B. + `recent_std_s` + `short_history` | Planned for Hito 2 | – |
| C. + `short_history` only | Planned for Hito 2 | – |

### Member contributions

| Member | What they did and can explain |
| --- | --- |
| Baptiste Vial | Worksheet answers on the opening example, reference prediction and interpretation, short-history rule, fixed controls and failure condition; ran `run_references.py` and checked it against the supplied outputs. |
| Vicente Rodríguez | Chose the primary direction (recent pace history, standard deviation of the last 3 clean laps), rejected `next_lap_s` as an inadmissible future-known input, and defined the race/driver/stint grouping of the rolling windows. |

### AI use record

Tool: Claude Code (Anthropic, Claude Opus 5.5), used by Baptiste.

| Use | Adopted? | How we checked it |
| --- | --- | --- |
| Turned our spoken answers (Spanish) into English text in the worksheet and fixed typos. | Yes | We reviewed every answer against what we meant. |
| Pointed out that the opening example concerns evaluation rows, not training rows. | Yes | Re-read the example: the 1,000 / 600 rows are where MAE was measured. |
| Suggested the four revisions in "Revisions after feedback" (hypothesis scope, short-history rule, measurable failure threshold, stint boundary). | Yes, with the 0.01 s threshold chosen by us | Checked against the Hito 1 brief (stint boundaries, no uncontrolled search on validation) and against `nextlap_reference_v1.py` (`recent_mean_s` uses clean laps within driver/race/stint). |
| Adapted the class helper `probar_referencia_v1.py` into `run_references.py` and drafted `HITO1.md`, `README.md` and this log from our worksheet answers. | Yes | Ran the script ourselves; compared metrics, counts and SHA-256 values with the instructor-supplied outputs; read every section of the documents. |
| Checked whether a pace-slope variable already exists in the data. | Yes | Confirmed in `nextlap_reference_v1.py`: no slope/trend input is supplied; it would have to be built. |

### Responsibilities before Hito 2 (19 November)

| Member | Next action |
| --- | --- |
| Baptiste Vial | Build `recent_std_s` from the raw snapshots and run checks 1–2. |
| Vicente Rodríguez | Run trials B and C, per-race MAE and checks 3–5. |

### Blockers for Ángel

None.

---

# Part 2 · Hito 2 entries

Paths in this part are relative to `Hito2/`. All results come from `python run_hito2.py`. The submitted commit is the one tagged `Hito2` (see README).

## Entry 2026-11-17 (1) · Primary experiment: does `recent_std_s` help?

| Field | Entry |
| --- | --- |
| Date, authors, run | 2026-11-17 · Vicente Rodríguez, Baptiste Vial · `run_hito2.py`, outputs in `outputs/` |
| Question and change tested | Does recent pace variability (`recent_std_s`, std of the clean lap times among the last 3 laps of the stint up to t, the `recent_mean_s` window, within race/driver/stint) add information beyond the six reference inputs? Candidate B = six inputs + `recent_std_s` + `short_history`; matched control C = six inputs + `short_history`; reference A = six inputs. All OLS via `make_model`, train R1–7, same 1,808 validation IDs. |
| Check written before building | Hito 1 checks 1–5 (HITO1.md §4), unchanged except check 1 (revision below). Failure conditions: any missing or duplicated validation ID → stop before comparing; last lap used ending after t → reject the feature; C − B < 0.01 s overall, or < 0 in either race → does not meet the predeclared improvement criterion. |
| What happened | All checks pass (`outputs/checks.csv`). MAE A 0.38671, B 0.36973, C 0.38767 s (n = 1,808). **C − B = +0.01794 s** (R8 +0.01284, n = 1,066; R9 +0.02528, n = 742). Prior signal on training rows: Spearman ρ = 0.358. Availability: last lap used = lap t and ends no later than t on all 7,580 rows; the as-of recomputation is identical. |
| Decision and evidence | **Keep `recent_std_s`**; B is the working model. Evidence: pre-declared rule met (`race_table.csv`, `checks.csv` check 4). Claim limited to OLS, these inputs, clean pairs, R8–R9. |
| Limit, next check, owner | The gain is concentrated: the top 50 rows give 94.5% of it (`gain_concentration.csv`), and short-history rows get worse (`slices.csv`). Next check: trial D (entry 2), owner Vicente. |

## Entry 2026-11-17 (2) · Follow-up trial D: is the `short_history` indicator the problem?

**Written before running D** (a private timestamped copy was kept outside the repository):

> Observed in the primary run: on the 148 short-history rows A = 0.3959, C = 0.4455, B = 0.4534 s. R8/short (82): C better than A; R9/short (66): C much worse than A (0.523 vs 0.402). In training and R8 the lap after a short history is about 0.3 s faster than lap t; in R9 it is not.
> Hypothesis: the short-history loss comes from the `short_history` indicator, not from `recent_std_s`.
> Trial D: OLS, six inputs + `recent_std_s` (missing → training median), no indicator. Matched control = A (shared run).
> Pass if: MAE(D, short rows) ≤ 0.401 s AND A − D ≥ 0.01 s overall AND A − D ≥ 0 in R8 and in R9. Fail otherwise.
> Decision: D does not replace the primary B vs C test. If D passes, it becomes our working candidate for the final report; if it fails, we keep B.

| Field | Entry |
| --- | --- |
| What happened | D short-history MAE **0.4163 s** (> 0.401 → **fail**); A − D = +0.02148 s overall (R8 +0.01597, R9 +0.02941); stint bootstrap [+0.0131, +0.0314] s (`followup_D_table.csv`, `bootstrap.csv`, `checks.csv` row D). |
| Decision and evidence | **Keep B, as declared.** Removing the indicator recovers about two thirds of the short-row loss (0.453 → 0.416 s), but D is still worse than the reference on those rows, so the hypothesis "the indicator alone explains it" is only partly supported. D's better overall MAE is noted, but we do not switch to D after seeing it, because the rule was written first. |
| Limit, next check, owner | Short-history rows remain worse than the reference. Next check for the final report: a declared fallback in which short-history rows use the reference prediction, tested as its own trial against A (owner Baptiste). Also a traffic proxy available at t for sudden losses at t+1 (owner Vicente). |

## Trials (all settings tried in Hito 2)

All trials: OLS via `make_model`, categoricals `current_compound` + `current_team`, train R1–7 (5,772), validation R8–9 (same 1,808 IDs), seed 414, no hyperparameters. No other window, model family or setting was tried on validation.

| Trial | Numeric inputs beyond the four reference numerics | Role | Val MAE (s) | Outcome |
| --- | --- | --- | --- | --- |
| A | – | OLS reference (Hito 1, re-executed) | 0.38671 | Baseline; equals Hito 1 output |
| B | `recent_std_s`, `short_history` | Candidate | **0.36973** | Supported (C − B = +0.01794); **kept** |
| C | `short_history` | Matched control for B | 0.38767 | Indicator alone is slightly worse than A (−0.00096); **unsuccessful as an input** |
| D | `recent_std_s` | Follow-up, control = A | 0.36522 | Pre-declared rule **failed** on short rows; **not adopted** |

## Revision of a check after review

| Earlier entry (Hito 1, kept above) | Review | Revised entry |
| --- | --- | --- |
| Check 1: "for a **sample** of rows, confirm that the last lap used … ends ≤ the row's `end_time_s`, and that no window crosses a stint change." | During implementation we noted that a sample could miss rare stint-boundary cases, and checking every row costs a few seconds. A second, independent implementation also protects against a shared bug in one rolling function. | Check 1 on **all 7,580** train + validation rows, plus an as-of recomputation that only sees laps with `end_time_s` ≤ t. Also: rebuilt `recent_mean_s` / `recent_count` must equal the released columns exactly. Result: pass. |

## Retained design after checking

| Item | Why we kept it |
| --- | --- |
| Matched control C (with `short_history`) rather than A | B adds two columns. Only C isolates `recent_std_s`. Using A as the control would credit the indicator's (negative) effect to the variability feature. |
| The 0.01 s threshold and window 3 | Fixed in Hito 1 before any result. Changing them after seeing validation would be selection on validation. |
| B over D | See entry 2: the rule was written first and D failed it. |

## Feedback received

| Source | Feedback | What we changed or why we kept it |
| --- | --- | --- |
| Our own slice check (check 5) | Short-history rows are worse than the reference (0.453 vs 0.396 s, n = 148) | Designed and ran trial D with a rule written before running; kept B (entry 2). |
| Hito 1 instructor feedback (97/100), C3.1 | "Last three clean laps" and "window 3, same as `recent_mean_s`" can give different histories when an invalid lap occurs; specify the convention and show one worked history. | Convention stated: last 3 laps of the stint, non-clean laps left out, not replaced (the `recent_mean_s` window, which the code always used). Added a history-convention check and a worked history, `2026-R8-1-L28` (`history_convention.csv`, `history_convention_example.csv`). The two readings differ on 111 of 1,808 validation rows. `HITO1.md` §3 revised. |
| Hito 1 instructor feedback, C3.1 | The rationale motivates dispersion but does not say how the variable could correct the point prediction beyond the reference. | Mechanism stated as a bounded hypothesis in `HITO1.md` §3 (negative coefficient pulls the prediction back after a one-off slow lap; additive and direction-blind, so a small, concentrated gain). Compared with the fitted coefficients in HITO2.md §3. Written after the results were known, and disclosed as such. |
| Hito 1 instructor feedback, C4.4 | A gain below 0.01 s does not refute the broader claim that variability may contain information. | Kept the 0.01 s threshold; an outcome below it is now worded "does not meet the predeclared improvement criterion" (`HITO1.md` §4, entry 1 above, `checks.csv`). |
| Hito 1 instructor feedback, guidance for Hito 2 | Check that the implemented histories match the stated convention and keep the same `pair_id` set across comparisons. | Both checked: history-convention check and check 2 (same 1,808 `pair_id`s for A–D, SHA-256 equal to Hito 1) in `checks.csv`. |

## Member contributions (Hito 2)

The split follows the responsibilities agreed in Hito 1.

| Member | What they did and can explain | A decision they can defend |
| --- | --- | --- |
| Baptiste Vial | Feature construction and availability checks (`features.py`; checks 1–2): the exact rebuild of `recent_mean_s` / `recent_count`, the as-of recomputation, coverage and the missing-value rule. | Requiring the rebuilt reference columns to match exactly before trusting `recent_std_s`. |
| Vicente Rodríguez | Runs A–D, ablation, race table, slices, inspected cases, SHAP (`run_hito2.py`; checks 3–5, D). | Keeping C (not A) as the matched control, and keeping B after D failed its rule. |

## AI use record (Hito 2)

Tools: Claude Code (Anthropic), used by Baptiste and Vicente; Gemini (Google), used by Vicente.

| Use | Adopted? | How we checked it |
| --- | --- | --- |
| Drafted the revisions after the Hito 1 feedback (window convention, worked history `2026-R8-1-L28`, bounded mechanism, check 4 wording) and the history-convention check in `run_hito2.py` (ref: Hito 1 instructor feedback; logged in Part 2 "Feedback received" and in `Hito1/DECISION_LOG.md`). | Yes — accepted the convention text, worked example (`2026-R8-1-L28`), bounded mechanism framing, and code check; kept the earlier Hito 1 log entries unchanged and logged the revisions in a new dated section; the graded wording stays in the `Hito1` tag. | Checked the worked history against the raw R8 laps and the released `recent_mean_s` (`71.6705 s`); the new check passes and all other outputs stayed byte-identical. |
| Drafted `features.py` (`history_features` and `as_of_recompute`) to compute `recent_std_s` from raw lap snapshots and verify availability at lap `t` (ref: `HITO1.md` §4 & `nextlap_reference_v1.py`). | Yes — accepted the rolling window (`rolling(3, min_periods=2).std(ddof=1)`) within `(season, round, driver, stint)` and extended Check 1 from a sample to all 7,580 rows plus an independent as-of recomputation. | Confirmed that rebuilt `recent_mean_s` and `recent_count` match the official dataset columns identically on all 7,580 rows, and verified that `as_of_recompute` agrees with the rolling output on every row (`checks.csv`, check 1). |
| Drafted `run_hito2.py` to execute runs A, B, C, and post-hoc trial D, compute stint bootstrap and context slices, and generate local/global SHAP outputs (ref: `HITO1.md` §4 & pre-registered Trial D rule). | Yes — accepted the pipeline structure and strict anti-leakage assertions (`clean_pair`/`next_*` exclusion, 1:1 joins, hash lock); kept Candidate B when Trial D failed our pre-declared short-history rule (`0.41626 s > 0.401 s`). | Re-ran in a clean virtual environment (`requirements.txt`), verified byte-identical CSV/JSON outputs across runs, checked pooled MAE arithmetic and local SHAP reconstruction (`86.7343 + 12.3864 = 99.1207 s`) by hand, and verified all reported numbers against `outputs/`. |
| Drafted initial sections of `HITO2.md`, `README.md`, and `DECISION_LOG.md` from our Hito 2 outputs and trial logs (ref: `Hito2/outputs/` & Hito 2 brief). | Yes, with edits — accepted the evidence map and metric tables; manually rewrote both individual partner explanations in `HITO2.md` §9 in our own words and updated contributor/feedback entries in `DECISION_LOG.md`. | Reviewed every table against its mapped code section in `run_hito2.py`, verified all reported values against `outputs/`, and confirmed zero `TODO-TEAM` placeholders remained. |
| Audited Hito 2 documentation against the course rubric, generated a pre-commit checklist, and formatted this AI use record (prompt: *"Based on this and everything that must be done for the Hito 2, give me a step by step on what to do for the Hito 2, also give me a full analysis on what has been done"*). | Yes, with edits — accepted the pre-commit checklist and rubric audit; restricted the AI use table exclusively to Hito 2 records and added the unrecorded Hito 1 feedback revision row. | Verified every checklist item, file path, and metric directly against `HITO2.md`, `README.md`, `DECISION_LOG.md`, and `outputs/` before tagging the `Hito2` release. |

## Responsibilities before the Demo (20 Nov) and final report (22 Nov)

| Member | Next action |
| --- | --- |
| Baptiste Vial | Short-history fallback trial (short rows → reference prediction) with its own rule written before running. |
| Vicente Rodríguez | Traffic proxy at t (gap to the car ahead from other drivers' `end_time_s` ≤ t): availability check, then the A/B/C comparison. |

## Blockers for Ángel

None.
