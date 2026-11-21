# Decision log · NextLap · Group 1 · Part 3 (Demo Day and final report)

Members: Vicente Rodríguez, Baptiste Vial. This part continues [Hito2/DECISION_LOG.md](../Hito2/DECISION_LOG.md), which holds the Hito 1 entries (unchanged copy) and the Hito 2 entries. Entries are kept in order; earlier entries are not rewritten. On 20 November this folder was renamed from `Final/` to `FinalReport/` when the report moved to its own branch; paths below were updated, nothing else.

## Demo Day (20 November 2026)

Presented the Hito 2 decisions with the official Demo Day template (`Demo/NextLap_Demo_Team1.pptx`; script `Demo/SCRIPT.md`, question preparation `Demo/PREP_GUIDE.md`). Every number on the slides is read from `Hito2/outputs/` at the commit tagged `Hito2`; nothing was recomputed for the demo.

| Member | Presented | Defended in questions |
| --- | --- | --- |
| Vicente Rodríguez | Use (slide 1), comparison (slide 3), SHAP (slide 5) | Matched control C rather than A; keeping B after D failed |
| Baptiste Vial | New input and checks (slide 2), errors by context (slide 4), decision (slide 6) | Window convention and availability checks; short-history limitation |

The split above is how it was presented. The talk ran without problems, and the jury asked one question, which we answered; no written feedback was given.

## Feedback received

The Demo Day jury asked one question, which we answered, and gave no written feedback; the revision answers the Hito 2 priority.

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
| Baptiste Vial | Presented slides 2, 4 and 6 at the Demo Day and defended the window convention, the availability checks and the short-history limitation. Owner of the short-history fallback follow-up declared in Hito 2 (short-history rows → frozen reference prediction, own rule written first), which became trial E. | The fallback switches on `short_history` only, which is known at the end of lap t, and returns the frozen reference rather than a refitted model. Result: short-history MAE 0.39589 s ≤ 0.401 s on the 148 rows; `short_history` equals the missing pattern of `recent_std_s` on every row (asserted in `FinalReport/run_final.py`). |
| Vicente Rodríguez | Presented slides 1, 3 and 5 at the Demo Day and defended the matched control and keeping B after D. Built the Demo Day deck, script and question guide (`Demo/`), ran trial E (`FinalReport/run_final.py`), wrote the frozen-model script for the bonus (`FinalReport/predict.py`) and the final report. The traffic proxy he owns is still open. | Reuse trial D's rule word for word for E and freeze E only if it passed. Result: A − E = +0.02169 s overall, +0.01384 s in R8 and +0.03296 s in R9; `predict.py` reproduces E on all 1,808 rows (largest difference 7.7e-13 s). |

## AI use record (after Hito 2)

Tool: Claude Code (Anthropic), used by Vicente for the Demo Day material and the final report.

| Use | Adopted? | How we checked it |
| --- | --- | --- |
| Checked that the Demo Day material met the requirements: the closeout guide (7 min + 5 min, both partners explain a decision, its evidence and a limitation, terms a guest can follow, an offline copy), the official programme (our 11:25–11:37 slot) and the prompts and speaker notes of the official slide template. | Yes — added a handover line per slide, an "evidence does not show" backup slide and the offline PDF; dropped an unsupported claim it had drafted ("two dry races": we have no weather evidence). | We re-read the guide, the programme and each template note against the final slides; the talk ran in its slot without problems. |
| Rebuilt the deck on the official template (`Demo/build_deck.js`, `Demo/make_figures.py`); the template file itself did not open in PowerPoint, so the same geometry, colours, fonts, footer, questions and timings were reproduced from its XML. | Yes | Compared the deck with the template element by element; validated the file; rendered and inspected every slide; a script matched every decimal on the slides and in the notes to `Hito2/outputs/` (none unmatched). |
| Drafted and tuned the script (`Demo/SCRIPT.md`): one speaker per slide, "must say" phrases, handovers, and cuts from about 856 to about 770 words so each slot fits the template timings. | Yes, with edits — we said the text in our own words and kept the numbers and "must say" phrases. | Word count per slot against the template timings (about 6 min 25 s at 120 words per minute); timing checkpoints per slide; numbers checked against `Hito2/outputs/` by the same script. |
| Drafted the question guide (`Demo/PREP_GUIDE.md`): numbers to know, each idea explained plainly and precisely, what not to claim and what to say instead, a question bank with an owner per topic. | Yes | Every number checked against `Hito2/outputs/`; the threshold answer was corrected to say the 0.01 s rule was our own judgement. We answered the jury's one question. |
| Proposed reusing trial D's rule unchanged for trial E, and drafted `FinalReport/run_final.py`. | Yes | The rule was saved in this log before the script existed (with a private timestamped copy); the script asserts the 1,808 IDs match Hito 1, that A still equals the Hito 1 predictions and the pooled arithmetic; its A − B bootstrap reproduces the saved Hito 2 interval; two runs give byte-identical outputs. |
| Drafted `FinalReport/predict.py`, the frozen model E in the bonus input format. | Yes | `--self-check` refits A and B on rounds 1–7 and reproduces E on all 1,808 validation rows (largest difference 7.7e-13 s); also run from shuffled request and history CSV files, with the same result. |
| Drafted and revised the final report and this log from the saved outputs. | Yes, with edits | A script matched every decimal in the report, this log and `FinalReport/README.md` to a saved output (none unmatched); all relative links resolve and every link in the PDF opens at the submitted commit. |

## Blockers

None.
