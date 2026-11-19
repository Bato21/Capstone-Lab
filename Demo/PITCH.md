# NextLap Demo Day · Group 1 · Friday 20 November 2026

Slot (official programme): **11:25–11:32 presentation (7 min), 11:32–11:37 questions (5 min)**, Lab 033, RESB campus. Group 1 opens the session. Both partners answer the jury.

- Deck: `NextLap_Demo_Team1.pptx`, built on the official Demo Day template (same six questions and timings), plus 5 backup slides for questions. Offline copy: `NextLap_Demo_Team1.pdf`. Speaker notes in the deck are generated from this file.
- Split: **Vicente** (V) presents slides 1, 3 and 5 (the use, the result, the SHAP explanation). **Baptiste** (B) presents slides 2, 4 and 6 (the new input and its checks, where the model struggles, the decision). Each slide alternates, so the handovers are short.
- Every number comes from `Hito2/outputs/` (commit tagged `Hito2`). The deck reads `figures/deck_data.json`, written by `make_figures.py` from those files.
- The jury includes guests outside machine learning. Say "average miss in seconds" with MAE the first time, and "a straight-line formula" with OLS.

| Slide | Time | Who | Template question | Our answer in one line |
| --- | --- | --- | --- | --- |
| 1 | 0:00–0:45 | V | Project and use | Predict the next lap so the pit wall can spot a lap that is off. |
| 2 | 0:45–1:45 | B | What changed in the model? | One new input: how erratic the last three laps were. Only finished laps; same rows; matched control. |
| 3 | 1:45–3:25 | V | What did the comparison show? | +0.018 s against the matched control; rule met; but 50 laps carry the gain. |
| 4 | 3:25–4:40 | B | Where does the model struggle? | Both races agree; Albon's case; worse right after a pit stop. |
| 5 | 4:40–6:00 | V | What drove a prediction? | SHAP on Albon's lap adds up to the prediction; −2.47 s is a shift, not an error. |
| 6 | 6:00–7:00 | B | What decision can you defend? | Keep it, within OLS, clean laps, two races; next: fallback after pit stops, traffic. |

Spoken text below: about 860 words (Vicente 420, Baptiste 436), about 6 min 20 s at 135 words per minute, which leaves about 40 s of slack. Rehearse once with a timer in presenter view. The "must say" phrases are the parts not to drop.

---

## Slide 1 · V · Project and use

**Must say:** "same driver's next lap", "end of the current lap", "only what is on the timing screen".

> Good morning. We are Group 1: I'm Vicente, and this is Baptiste. Picture a race engineer on the pit wall. At the end of every lap they want to know how long their driver's next lap should take, so that a lap that comes in much slower stands out as something to check: the tyres, traffic, or a problem with the car. That is what we predict: the same driver's next lap time, in seconds, made at the end of the current lap, using only what is already on the timing screen. We tested it on two past races, so we are not claiming it is ready for a real pit wall.

## Slide 2 · B · What changed in the model?

**Must say:** "only laps that have already finished", "the lap we predict never enters", "same 1,808 laps", "the control is the same model without the new input".

> The course gave us a reference: a straight-line formula, ordinary least squares, with six inputs such as the last lap time and the average of the last three laps. We added one input: how erratic those last three laps were, their standard deviation. The idea is that after one unusually slow lap, the last lap time overstates the next one, so a high spread should pull the prediction back. It only uses laps that have already finished. In this example, laps 24 to 26 were not under green flag, so they are left out, and lap 29, the one we predict, never enters. With only one clean lap the spread does not exist, so we fill the training median and add a flag. We trained on rounds 1 to 7 and validated on rounds 8 and 9, and every model is scored on the same 1,808 laps. To isolate the new input, our matched control is the same model, refitted without it.

## Slide 3 · V · What did the comparison show?

**Must say:** "average miss", "plus 0.018 seconds", "rule written before running", "50 laps carry 94.5 percent".

> Here is the result on those same 1,808 laps. We measure the average miss in seconds; lower is better. The reference misses by 0.387 seconds. The matched control, 0.388. Our candidate, 0.370. So control minus candidate is plus 0.018 seconds: the candidate misses by about two hundredths of a second less per lap. Before running anything, we wrote the rule: at least 0.01 seconds better than the control, and no race worse. It was met. If we resample whole stints, the gain stays positive, between 0.009 and 0.029 seconds, but that only describes these two races. And there is a catch. The gain is not spread evenly: 50 laps, under three percent, carry 94.5 percent of it. Without them, the two models are practically tied. So what the evidence supports is this: the new input fixes a few big misses after an unusual lap. It does not improve the typical lap.

## Slide 4 · B · Where does the model struggle?

**Must say:** "both races positive", "4.23 to 1.24 seconds", "worse after a pit stop".

> First, by race. Austria: plus 0.013 seconds. Silverstone: plus 0.025. Both are positive, so neither race overturns the pooled result; Silverstone simply had more big misses to correct. Now one real lap. Albon, at Silverstone, lost nine seconds on lap 7, alone, under green flag. At the end of lap 6 nothing hinted at it: every model missed by about eight seconds, our largest error. One lap later, the control believes the slow lap and predicts 102.1 seconds. The candidate sees the highest spread in validation and predicts 99.1. The real lap was 97.9, so the absolute error drops from 4.23 to 1.24 seconds. The weak spot is right after a pit stop or a yellow flag, when only one clean lap is in the window. On those 148 laps the candidate is worse than the reference: 0.453 against 0.396 seconds.

## Slide 5 · V · What drove a prediction?

**Must say:** "base plus contributions equals the prediction", "a shift, not an error and not a cause", "the error is computed separately".

> Why did the model predict 99.1 seconds for Albon? SHAP splits one prediction into contributions that add up. We applied it to our candidate, on that same lap, with all training laps as the background. It starts from the average training prediction, 86.73 seconds. The two pace inputs add about 15 seconds, because Silverstone is a slow track. The spread pulls it down by 2.47 seconds. Base plus contributions gives 99.12, exactly the model's prediction, and we checked that on all 1,808 rows. That minus 2.47 is how the model moved its prediction: it is not an error and not a cause. The actual error, 1.24 seconds, we compute separately. Over all validation laps, the pace inputs dominate because they place the track. The spread averages 0.15 seconds: small on most laps and large on a few, which matches the concentration we saw. SHAP explains the output; the gain itself is measured by the comparison, plus 0.018.

## Slide 6 · B · What decision can you defend?

**Must say:** "keep", "linear model, clean laps, two races", "optimistic", "D missed its rule", one next check.

> So, our decision: we keep the new input, because it beat its matched control by 0.018 seconds on the same laps, and in both races, as our rule required. This applies to a linear model, on clean laps, in Austria and Silverstone. We used those races to choose, so the numbers are optimistic, and they say nothing about other races or live use. We also tried one fix for the pit-stop weakness, removing the flag. We wrote its rule before running it; it improved overall but missed its rule, so we kept the candidate. Our next checks: after a pit stop, fall back to the reference prediction; and for shocks that no lap history can see, a traffic signal, the gap to the car ahead. Thank you. We are happy to take questions.

---

## Questions (5 min): who answers what

The template asks each partner to defend **one decision, with a result or check, and one limitation**. Answer in under 30 seconds, then point to a backup slide if needed.

| Partner | Decision to defend | Result or check | Limitation to name |
| --- | --- | --- | --- |
| Baptiste | The window is the last 3 laps of the stint (same as `recent_mean_s`), non-clean laps left out, no reach-back | Rebuilt `recent_mean_s` equals the official column on 7,580/7,580 rows; as-of recomputation identical; worked lap `2026-R8-1-L28` | Short history: 148 rows, candidate 0.453 s vs reference 0.396 s; trial D missed its rule |
| Vicente | Compare against matched control C, not the reference A, and keep B | C − B = +0.018 s; R8 +0.013, R9 +0.025; rule from Hito 1 met | 50 of 1,808 laps carry 94.5% of the gain; shocks on lap t+1 (Albon lap 7, 8.25 s) are invisible |

| Likely question | Who | Short answer | Backup |
| --- | --- | --- | --- |
| Could the new input see the future? | B | No. It uses laps t−2 to t only; lap t+1 is the target. Checked on every row and with a second implementation that only sees finished laps. | 9 |
| Why compare with C and not the reference? | V | The candidate adds two columns. C keeps the flag and drops only the spread, so C − B measures the spread alone. | 10 |
| D was better overall: why not keep D? | B | D's rule was written to fix the pit-stop laps, and it did not (0.416 > 0.401). Switching after seeing the overall number would be choosing on validation. | 10 |
| Is 0.018 s meaningful? | V | Small on average, large where it matters: Albon's next lap went from 4.23 to 1.24 s. But 50 laps carry it, so another race could show nothing. | 8 |
| Is the spread the most important input? | V | No. It ranks third by SHAP (0.15 s). The pace inputs place the track. Importance in SHAP is not predictive value; the comparison measures that. | 5 |
| Would it work live? | B | Not shown. We evaluate clean laps chosen after the fact; live, you don't know whether the next lap will be clean. | – |
| How did you use AI? | both | Claude Code drafted scripts and text; we checked with exact-match and as-of checks, the pooled arithmetic, and SHAP reconstruction. Recorded in the decision log. | – |

Backup slides: 7 Albon incident chart · 8 concentration and short history · 9 checks written in Hito 1 · 10 all runs, D and bootstrap · 11 Hito 1 feedback.

## Handover cues

- V → B (slide 2): "Baptiste built the new input."
- B → V (slide 3): "So, what did it change?"
- V → B (slide 4): "Baptiste, where does it struggle?"
- B → V (slide 5): "Vicente will show why the model said 99.1."
- V → B (slide 6): "Baptiste, the decision."

## Plain-language glossary (if a guest asks)

- **MAE:** the average size of the miss, in seconds.
- **OLS:** a straight-line formula fitted to the training laps.
- **Clean lap:** a green-flag, accurate lap that is not a pit lap and was not deleted.
- **Matched control:** the same model, same laps, refitted without the one thing we changed.
- **SHAP:** splits one prediction into additive pieces, one per input, starting from the average prediction.
