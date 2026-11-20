# NextLap Demo Day script · Group 1 · Friday 20 November 2026

Slot (official programme): **11:25–11:32 presentation (7 min), 11:32–11:37 questions (5 min), 11:37–11:40 transition** (reserved for recording feedback and handing over to Group 2), Lab 033, RESB campus. Group 1 is the first team after the opening (11:10–11:25), so the laptop must be connected and tested before 11:10. Both partners answer the jury.

- Deck: `NextLap_Demo_Team1.pptx` (offline copy `NextLap_Demo_Team1.pdf`): the six slides of the official Demo Day template, then 6 backup slides for questions. The speaker notes of slides 1–6 are generated from this file.
- Split: **Vicente** (V) presents slides 1, 3 and 5 (the use, the result, the SHAP explanation). **Baptiste** (B) presents slides 2, 4 and 6 (the new input and its checks, where the model struggles, the decision).
- Every number comes from `Hito2/outputs/` (commit tagged `Hito2`). Nothing was recomputed for the demo.
- The jury includes guests outside machine learning. Say "average miss, in seconds" the first time you say MAE, and "a straight-line formula" with OLS.
- Preparation for the questions, including what not to claim: [PREP_GUIDE.md](PREP_GUIDE.md).

| Slide | Template slot | Who | Template question | Our answer in one line | Words |
| --- | --- | --- | --- | --- | ---: |
| 1 | 0:00–0:45 | V | Project and use | Predict the next lap so the pit wall can spot a lap that is off. | 105 |
| 2 | 0:45–1:45 | B | What changed in the model? | One new input, how erratic the last three laps were; only finished laps; same rows; matched control. | 129 |
| 3 | 1:45–3:25 | V | What did the comparison show? | +0.018 s against the matched control; rule met; but 50 laps carry the gain. | 141 |
| 4 | 3:25–4:40 | B | Where does the model struggle? | Both races agree; Albon's lap; worse right after a pit stop. | 128 |
| 5 | 4:40–6:00 | V | What drove a prediction? | SHAP on Albon's lap adds up to the prediction; −2.47 s is a shift, not an error. | 146 |
| 6 | 6:00–7:00 | B | What decision can you defend? | Keep it, for OLS, clean laps, two races; next: fallback after pit stops, traffic. | 120 |

About 770 spoken words: 6 min 25 s at 120 words per minute, 5 min 30 s at 140. That leaves room for a slower pace and one stumble without passing 7:00. Learn the "must say" phrases word for word; the rest can be said in your own words.

---

## Slide 1 · V · Project and use

**Must say:** "the same driver's next lap", "at the end of the current lap", "only what is already on the timing screen".

**Handover:** "Baptiste built the new input."

> Good morning. We are Group 1: I'm Vicente, and this is Baptiste. Picture a race engineer on the pit wall. At the end of every lap, they want to know how long their driver's next lap should take, so that a lap much slower than expected stands out as something to check: the tyres, traffic, or a problem with the car. That is what we predict: the same driver's next lap time, in seconds, at the end of the current lap, using only what is already on the timing screen. We tested it on two past races, so this is evidence, not a finished product.

## Slide 2 · B · What changed in the model?

**Must say:** "only laps that have already finished", "the lap we predict never enters", "the same 1,808 laps", "the same model, refitted without the new input".

**Handover:** "So, what did it change?"

> The course gave us a reference: a straight-line formula, called OLS, with six inputs such as the last lap time and the average of the last three laps. We added one input: how erratic those last three laps were, their standard deviation. After one unusually slow lap, the last lap time overstates the next one, so a high spread should pull the prediction back. It only uses laps that have already finished. Here, laps 24 to 26 were not green-flag laps, so they are left out, and lap 29, the one we predict, never enters. We trained on rounds 1 to 7, validated on rounds 8 and 9, and scored every model on the same 1,808 laps. Our matched control is the same model, refitted without the new input.

## Slide 3 · V · What did the comparison show?

**Must say:** "average miss, in seconds", "plus 0.018 seconds", "a rule written before running", "50 laps carry 94.5 percent".

**Handover:** "Baptiste, where does it struggle?"

> Here is the result on those same 1,808 laps. We measure the average miss, in seconds; lower is better. The reference misses by 0.387 seconds. The matched control, 0.388. Our candidate, 0.370. So control minus candidate is plus 0.018 seconds: about two hundredths of a second less per lap. Before running anything, we wrote the rule: at least 0.01 seconds better than the control, and no race worse. It was met. If we resample whole stints, the gain stays positive, between 0.009 and 0.029 seconds, but that only describes these two races. And there is a catch. The gain is not spread evenly: 50 laps, under three percent, carry 94.5 percent of it. Without them, the two models are practically tied. So the new input fixes a few big misses after an unusual lap. It does not improve the typical lap.

## Slide 4 · B · Where does the model struggle?

**Must say:** "both races positive", "from 4.23 to 1.24 seconds", "worse right after a pit stop".

**Handover:** "Vicente will show why the model said 99.1."

> First, by race. Austria: plus 0.013 seconds. Silverstone: plus 0.025. Both are positive, so neither race overturns the pooled result. Now one real lap. Albon, at Silverstone, lost nine seconds on lap 7, alone, under green flag. Nothing before it hinted at that: every model missed by about eight seconds, our largest error. One lap later, the control believes the slow lap and predicts 102.1 seconds. The candidate sees the highest spread in validation and predicts 99.1. The real lap was 97.9, so the error drops from 4.23 to 1.24 seconds. The weak spot is right after a pit stop or a yellow flag, when only one clean lap is in the window. On those 148 laps the candidate is worse than the reference: 0.453 against 0.396 seconds.

## Slide 5 · V · What drove a prediction?

**Must say:** "base plus contributions equals the prediction", "a shift, not an error and not a cause", "the error is computed separately".

**Handover:** "Baptiste, the decision."

> Why did the model predict 99.1 seconds for Albon? SHAP splits one prediction into pieces that add up. We applied it to our candidate, on that same lap, with all training laps as the background. It starts from the average training prediction, 86.73 seconds. The two pace inputs add about 15 seconds, because Silverstone is a slow track. The spread pulls it down by 2.47 seconds. Base plus contributions gives 99.12, exactly the model's prediction, and we checked that on all 1,808 laps. That minus 2.47 is how the model moved its prediction: not an error, and not a cause. The error itself, 1.24 seconds, we compute separately. Over all validation laps, the pace inputs dominate because they place the track; the spread averages 0.15 seconds, small on most laps and large on a few. SHAP explains the output; the gain is measured by the comparison.

## Slide 6 · B · What decision can you defend?

**Must say:** "we keep", "a linear model, clean laps, two races", "optimistic", "it missed the rule we wrote before running it", one next check.

**Handover:** (to the jury) "Thank you. We're happy to take questions."

> So, our decision: we keep the new input. It beat its matched control by 0.018 seconds on the same laps, and in both races, as our rule required. This applies to a linear model, on clean laps, in Austria and Silverstone. We used those races to choose, so the numbers are optimistic, and they say nothing about other races or live use. We tried one fix for the pit-stop weakness, removing the flag. It missed the rule we wrote before running it, so we kept the candidate. Our next checks: after a pit stop, fall back to the reference prediction; and for sudden losses, a traffic signal, the gap to the car ahead. Thank you. We're happy to take questions.

---

## Rehearsal

1. **Read-through (both, 10 min).** Read the script aloud once with the slides open. Mark any sentence you trip over and say it your own way; keep the numbers and the "must say" phrases.
2. **Timed run (7 min).** Use presenter view and a timer. Checkpoints: Vicente finishes slide 1 by 0:50, Baptiste finishes slide 2 by 1:55, slide 3 ends by 3:25, slide 4 by 4:40, slide 5 by 6:00. If you are more than 15 s late at a checkpoint, use the short version below for the next slide.
3. **Second timed run without reading.** Notes only for the numbers.
4. **Question drill (15 min).** One partner reads random questions from the [preparation guide](PREP_GUIDE.md); the other answers in under 30 s. Swap.

**Short versions, if late:**

- Slide 3: drop the bootstrap sentence ("If we resample whole stints…").
- Slide 5: drop the global sentence ("Over all validation laps…") and go straight to "SHAP explains the output; the gain is measured by the comparison."

**On the day:** whoever is not speaking clicks for the speaker, or each presenter clicks their own slides; agree which before the session. During the questions, whoever is not answering writes down the jury's feedback word for word. In the 11:37–11:40 transition, unplug first, then together complete the notes while they are fresh: who said it, the exact words, and which slide it was about. It goes to `FinalReport/DECISION_LOG.md`, "Feedback received", and becomes the Demo Day priority of the final report.

## Plain-language glossary

- **MAE:** the average size of the miss, in seconds.
- **OLS:** a straight-line formula fitted to the training laps.
- **Clean lap:** a green-flag, accurate lap that is not a pit lap and was not deleted.
- **Matched control:** the same model, on the same laps, refitted without the one thing we changed.
- **SHAP:** splits one prediction into additive pieces, one per input, starting from the average prediction.
