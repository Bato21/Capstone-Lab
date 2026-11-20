# Decision log · NextLap · Group 1 · Part 3 (Demo Day and final report)

Members: Vicente Rodríguez, Baptiste Vial. This part continues [Hito2/DECISION_LOG.md](../Hito2/DECISION_LOG.md), which holds the Hito 1 entries (unchanged copy) and the Hito 2 entries. Entries are kept in order; earlier entries are not rewritten. On 20 November this folder was renamed from `Final/` to `FinalReport/` when the report moved to its own branch; paths below were updated, nothing else.

## Demo Day (20 November 2026)

Presented the Hito 2 decisions with the official Demo Day template (`Demo/NextLap_Demo_Team1.pptx`; script `Demo/SCRIPT.md`, question preparation `Demo/PREP_GUIDE.md`). Every number on the slides is read from `Hito2/outputs/` at the commit tagged `Hito2`; nothing was recomputed for the demo.

| Member | Presented | Defended in questions |
| --- | --- | --- |
| Vicente Rodríguez | Use (slide 1), comparison (slide 3), SHAP (slide 5) | Matched control C rather than A; keeping B after D failed |
| Baptiste Vial | New input and checks (slide 2), errors by context (slide 4), decision (slide 6) | Window convention and availability checks; short-history limitation |

## Feedback received

The Demo Day jury had not given written feedback when we submitted; the revision answers the Hito 2 priority.

| Source | Feedback (as received) | Priority? | What we changed or why we kept it |
| --- | --- | --- | --- |
| Hito 2 instructor feedback, received 20 Nov (100/100) | "Evidence verified. The matched control isolates recent_std_s on the same 1,808 rows. I reproduced the 0.01794 s MAE gain, the R8/R9 results and the SHAP reconstruction." | No (confirmation) | Nothing to change: the comparison, race table and SHAP stay as submitted. |
| Hito 2 instructor feedback, received 20 Nov | Priority correction: "Focus the final revision on short history. B reached 0.453 s versus 0.396 s for reference A on 148 rows. D reduced that gap and still missed your 0.401 s target." Check for the final report: "Predeclare a short-history fallback to the frozen reference. Check the 148-row slice and both races using the same IDs, then freeze the choice before final evaluation." | **Yes** | Trial E below: rule written first, then run; the frozen choice is recorded in the entry. |

## Entry 2026-11-20 · Priority revision: trial E, short-history fallback to the frozen reference

**Written before running E** (this paragraph and the rule were saved before `FinalReport/run_final.py` existed):

> Feedback addressed: the Hito 2 priority correction above (short history, 148 rows: B 0.453 s vs A 0.396 s; D 0.416 s missed the 0.401 s target).
>
> Trial E: on rows with `short_history = 1` (fewer than two clean laps in the window, so `recent_std_s` is undefined) use the frozen reference prediction A; on every other row keep candidate B. Both models are the ones fitted at the commit tagged `Hito2` (OLS, `make_model`, train R1–R7, seed 414); nothing is refitted or tuned. The switch uses only `short_history`, which is known at the end of lap t.
>
> Comparison: against the frozen reference A on the same 1,808 validation `pair_id`s, as declared in the Hito 2 log (entry 2026-11-17 (2)). The rule is the rule of trial D, unchanged, so that it is not chosen after the fact: **pass if MAE(E) on the 148 short-history rows ≤ 0.401 s AND A − E ≥ 0.01 s overall AND A − E ≥ 0 in R8 and in R9; fail otherwise.**
>
> Also reported, without a threshold: the isolated effect of the fallback, B − E, overall and per race, and A, B and E on the short-history rows of each race (same IDs). E differs from B only on the 148 short-history rows.
>
> Decision fixed in advance: if E passes, E is frozen as our final model and nominated for the improvement bonus; if it fails, B stays frozen. The choice is frozen at the commit tagged `Final` and not revisited after the instructor's final evaluation.
>
> Disclosure: this is not a blind test. E's predictions are combinations of saved Hito 2 predictions, and the per-slice MAEs in `Hito2/outputs/slices.csv` already imply most of its result. On 19 November one of us derived from those slices, in private notes, approximately E = 0.365 s overall, with the fallback slightly worse than B in R8 (about −0.001 s, because there B beat A on the short rows) and better in R9. That is why we reuse D's rule word for word instead of writing a new one.

| Field | Entry |
| --- | --- |
| Date, authors, run | 2026-11-20 · Baptiste Vial (owner of the follow-up, declared in Hito 2), Vicente Rodríguez · `FinalReport/run_final.py` → `FinalReport/outputs/` |
| Feedback addressed | Hito 2 priority correction, quoted in "Feedback received" |
| Check written before running | The block above |
| What happened | **Pass.** Short-history MAE(E) = **0.39589 s** ≤ 0.401 (n = 148; equal to A by construction). A − E = **+0.02169 s** overall (n = 1,808), **+0.01384** in R8 (1,066), **+0.03296** in R9 (742). Isolated effect of the fallback, B − E: **+0.00471 s** overall, −0.00094 in R8, +0.01282 in R9; on the short-history rows +0.05752 (148), −0.01223 in R8 (82), +0.14418 in R9 (66). Supplementary stint bootstrap (112 stints, 2,000 replicates, seed 414): A − E [+0.0124, +0.0321] s, B − E [+0.0018, +0.0076] s. Same 1,808 `pair_id`s (SHA-256 equal to Hito 1). Outputs: `FinalReport/outputs/trial_E_checks.csv`, `trial_E_table.csv`, `trial_E_bootstrap.csv`, `validation_predictions_E.csv`. |
| Decision and evidence | **E is frozen as our final model**, as fixed before the run, and nominated for the improvement bonus. It keeps the tested change (`recent_std_s`, supported by C − B = +0.01794 s in Hito 2) on the 1,660 rows where it is defined and uses the frozen reference where it is not, so the 148 short-history rows are no longer worse than the reference. `FinalReport/predict.py` refits A and B on rounds 1–7 from the released files, computes the features from an as-of history view and reproduces E's saved predictions on all 1,808 rows (largest difference 7.7e-13 s; `FinalReport/outputs/predict_self_check.json`). |
| Limit, next check, owner | Not a blind test (see the disclosure above). In R8 the fallback costs 0.012 s on the 82 short-history rows, where B was better than A; the net R8 effect is −0.00094 s, and the rule compares E with A, not with B. Validation rounds 8–9 chose B and now E, so these MAEs are selection evidence; only the instructor's final evaluation can show whether E generalises. Next check after the freeze: the traffic proxy at t for sudden losses (owner Vicente), with the same design. |

## Member contributions (Demo Day and final report)

| Member | What they did and can explain | A decision they can defend, with its result or check |
| --- | --- | --- |
| Baptiste Vial | [ ] | [ ] |
| Vicente Rodríguez | [ ] | [ ] |

## AI use record (after Hito 2)

[To be completed by the team.]

| Use | Adopted? | How we checked it |
| --- | --- | --- |
| | | |

## Blockers

None.
