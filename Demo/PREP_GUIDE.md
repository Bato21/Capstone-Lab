# Demo Day preparation guide · Group 1

For the 5 minutes of questions (11:32–11:37). The closeout guide asks that **both partners can explain a decision, show its supporting evidence and name a limitation**, and that we use terms a guest outside machine learning can follow. The jury answers are individual, so each of us must be able to stand alone on our own part.

Every number below is in `Hito2/outputs/` (commit tagged `Hito2`) unless the row says otherwise. Slide numbers refer to `NextLap_Demo_Team1.pptx` (1–6 the talk, 7–12 backup).

Contents: [1. The project in 30 seconds](#1-the-project-in-30-seconds) · [2. Numbers to know by heart](#2-numbers-to-know-by-heart) · [3. Understand each idea](#3-understand-each-idea) · [4. How to answer](#4-how-to-answer) · [5. What not to answer, and what to say instead](#5-what-not-to-answer-and-what-to-say-instead) · [6. Question bank](#6-question-bank) · [7. On the day](#7-on-the-day)

---

## 1. The project in 30 seconds

Both of us should be able to say this without the slides:

> At the end of each lap we predict how long the same driver's next lap will take, using only what is on the timing screen at that moment. We added one input to the course's straight-line model: how erratic the driver's last three laps were. On 1,808 laps from two races it reduced the average miss by 0.018 seconds compared with the same model without it, in both races, which met the rule we set in advance. But that gain comes almost entirely from about 50 laps right after an unusually slow lap, and the new model is worse right after a pit stop. So we keep it, for this model, clean laps and these two races only.

## 2. Numbers to know by heart

| What | Number | Slide |
| --- | --- | --- |
| Validation laps (same rows for every model) | 1,808 (Austria R8 1,066 · Silverstone R9 742) | 10 |
| Training laps | 5,772 (rounds 1–7) | 10 |
| Average miss: reference A / control C / candidate B | 0.387 / 0.388 / **0.370** s | 10 |
| Control − candidate | **+0.018 s** (Austria +0.013, Silverstone +0.025) | 10 |
| Rule set in Hito 1 | ≥ 0.01 s better overall **and** not worse in either race | 9 |
| Stint bootstrap, 95% interval | +0.009 to +0.029 s (these two races only) | 10 |
| Concentration | 50 laps (2.8%) carry 94.5% of the gain; without them +0.001 s; without the top 100, −0.008 s | 8 |
| Candidate better than control on | 955 of 1,808 laps (53%) | – |
| Short history (1 clean lap, mostly after a pit stop or a yellow) | 148 laps: candidate 0.453 s vs reference 0.396 s | 8 |
| Trial D (flag removed), short-history MAE | 0.416 s, rule was ≤ 0.401 s → **failed**, kept B | 8, 9 |
| Albon `2026-R9-23-L7` | real 97.882 s · candidate 99.121 s (error 1.239 s) · control 102.110 s (error 4.228 s) | 7 |
| Largest error in validation, `2026-R9-23-L6` | 8.25 s (Albon's 9 s loss on lap 7 itself) | 7 |
| SHAP on Albon's lap | base 86.73 + 8.18 + 6.67 − 2.47 + 0.003 = **99.12 s** | 5 |
| Global mean \|SHAP\| | recent mean 7.41 s · current lap 4.27 s · spread 0.15 s (3rd) | 5 |
| Short-history fill | training median 0.258 s, plus the `short_history` flag | – |
| Simple "next lap = last lap" guess (Hito 1) | misses by 0.409 s on the same rows | – |
| Typical lap length | Austria about 73 s, Silverstone about 95 s | – |

Two numbers people mix up: **0.387** is the reference A, **0.388** is the control C. The control is slightly *worse* than the reference: the flag alone does not help.

## 3. Understand each idea

Each idea has the plain version for a guest and the precise version for the instructor. If you can say both, you can answer any follow-up.

**What we predict.** *Plain:* the next lap time of the same driver, given at the end of the current lap. *Precise:* `next_lap_s` at lap t+1, from inputs available when lap t ends.

**MAE.** *Plain:* the average size of the miss, in seconds, ignoring whether we were too high or too low. *Precise:* mean absolute error over the 1,808 common validation pairs. Lower is better. Our 0.370 s means that on laps of 73 to 95 s we miss by under four tenths of a second on average.

**OLS.** *Plain:* a straight-line formula: each input gets a weight and the prediction is the weighted sum. *Precise:* `LinearRegression` inside the course's `make_model` pipeline (median imputer, scaler, one-hot encoder), fitted on rounds 1–7 only.

**Clean laps and the evaluation population.** *Plain:* we only score laps with nothing unusual: green flag, timed accurately, not a pit lap, not deleted. *Precise:* `clean_pair` keeps pairs where both lap t and lap t+1 are clean and in the same stint. It uses lap t+1 information, so it only decides which rows are scored; it is never an input. Consequence: our numbers describe clean racing laps, not all laps, and not live use, where you don't know in advance whether the next lap will be clean.

**The new input, `recent_std_s`.** *Plain:* how erratic the driver's last three laps were. *Precise:* the sample standard deviation of the clean lap times among laps t−2, t−1 and t of the current stint, the same window as the course's `recent_mean_s`. Non-clean laps in the window are left out and not replaced by older laps.

**Why it should help.** After one unusually slow lap, the last lap time and the recent average both overstate the next lap. A high spread signals "that lap was a one-off", and the fitted weight on the spread is negative, so it pulls the prediction back down. It is additive and does not know whether the odd lap was slow or fast; that is why the gain is small and concentrated.

**Availability at t (no leakage).** *Plain:* the input only uses laps that have already finished. *Precise:* checked on all 7,580 rows that the last lap used ends no later than lap t; a second, independent implementation that only sees laps finished by t gives identical values. Our rebuild of the course's `recent_mean_s` matches the official column on 7,580/7,580 rows, which proves our window is the same.

**Missing history.** With one clean lap, a spread does not exist. We leave it missing (0 would wrongly mean "perfectly stable"), the pipeline fills the training median 0.258 s, and the `short_history` flag marks the row. 148 validation rows. This is our weak spot.

**Matched control.** *Plain:* the same model, on the same laps, refitted without the one thing we changed, so the difference can only come from that change. *Precise:* the candidate B adds two columns (`recent_std_s` and `short_history`). The control C keeps `short_history` and drops only `recent_std_s`, so C − B isolates the spread. The reference A is not the control because it lacks the flag too.

**The pre-declared rule.** Written in Hito 1, before any code: B must beat C by at least 0.01 s overall and not lose in either race. Writing it first stops us from moving the goalposts after seeing the results. It was met (+0.018; +0.013; +0.025).

**Stint bootstrap.** *Plain:* we redrew the data many times, picking whole stints at random, to see how much the gain wobbles. *Precise:* 112 driver-race stints, 2,000 replicates, seed 414; whole stints because laps in one stint are not independent. Interval [+0.009, +0.029] s. It describes variation **inside these two races**; it does not show the gain holds elsewhere. Do not call it "statistically significant".

**Concentration.** The candidate is better on only 53% of laps. The top 50 laps by gain give 94.5% of it; remove them and the two models tie. So the input fixes a few big misses and slightly hurts typical laps. (Understanding only, not in a saved table: from `validation_predictions.csv`, the median miss is 0.253 s for B against 0.241 s for C. The typical lap is not better.)

**Albon's two laps.** Lap 7 at Silverstone: 105.1 s against a field median of 96.2 s, green flag, accurate lap, so an individual loss of about 9 s. Predicting lap 7 (at the end of lap 6): nothing hinted at it, every model missed by about 8 s. Predicting lap 8 (at the end of lap 7): the control believed the slow lap (102.1 s); the candidate saw a spread of 4.67 s, the highest in validation, and said 99.1 s; real 97.9 s. We do not know *why* Albon lost 9 s; the data only show it was green and accurate.

**Short history and trial D.** On the 148 one-clean-lap rows, the flag learned that in training the next lap is about 0.37 s faster (tyres coming in after a stop). That held in Austria and reversed at Silverstone. Trial D removed the flag under a rule written first (short-history MAE ≤ 0.401 s). It reached 0.416 s and failed, so we kept B, even though D's overall MAE (0.365 s) is lower. Switching after seeing that number would be choosing on validation.

**SHAP, local.** *Plain:* it splits one prediction into pieces, one per input, that add up to the prediction, starting from the average prediction. *Precise:* `shap.LinearExplainer` on the fitted candidate, background = all 5,772 training rows after preprocessing; exact for a linear model. Base 86.73 s is the average training prediction over rounds 1–7, many of them faster tracks; Silverstone is slow, so the pace inputs add about 15 s. The −2.47 s from the spread is how the model moved its prediction relative to the base. It is not an error (the error 1.24 s is measured against the real lap) and not a cause.

**SHAP, global.** Mean |SHAP| over all 1,808 validation laps. The pace inputs dominate because they place each track's pace relative to the training average. The spread is third at 0.15 s: small on most laps, large on a few. A SHAP ranking is how the model uses its inputs, not how much each one improves accuracy; the ablation (+0.018 s) measures that.

**Optimism.** We used rounds 8–9 to decide (B over C, and to examine D). Numbers used to choose are optimistic for unseen races. The reserved final races were never accessed.

## 4. How to answer

**The 30-second shape:** short answer → the number and where it is → the limit → stop.

> "Yes, it only uses finished laps. We checked every one of the 7,580 rows, and a second implementation agrees on every value. The limit is that we only checked our own feature, on clean laps."

**Rules that keep answers safe:**

1. **Repeat or rephrase the question if it is unclear.** "Do you mean on average, or for the laps after a pit stop?" It also buys three seconds.
2. **Answer the question asked, then stop.** Five minutes hold four to six questions. A long answer takes time from your partner.
3. **The partner who owns the topic answers first** (table in section 6). The other adds only if invited or if a number was wrong, and then only the correct number.
4. **Always end with the limit.** The jury rewards it, and it protects you from the follow-up "but does that always hold?"
5. **Point to a backup slide** when a number is asked: "It's on backup slide 8." Whoever is not talking navigates.
6. **If the question is in Spanish, answer in Spanish** (glossary at the end).

## 5. What not to answer, and what to say instead

Some questions invite a claim we cannot support. Answering them with a guess loses more than saying "we didn't test that". The safe formula:

> **"We didn't test that. What our evidence shows is \_\_\_. The check that would answer it is \_\_\_."**

| If asked… | Do not say | Say instead |
| --- | --- | --- |
| Would it work at another track, in the rain, at Monaco, in 2027? | "It should generalise" / "probably yes" | "Not shown. We tested two races, and used them to choose. The check is the same A/B/C comparison on new races, with the same rule." |
| Would a team use it live? | "Yes, it is ready" | "Not shown. We score clean laps chosen after the fact; live, you don't know whether the next lap will be clean." |
| Is the result statistically significant? | "Yes, significant" | "Inside these two races, resampling whole stints keeps it positive, +0.009 to +0.029 s. That says nothing about other races." |
| So the model is X% accurate? | Any percentage | "It misses by 0.37 s on average, on laps of 73 to 95 s." |
| So the spread is the most important input? | "Yes" | "No. It ranks third in SHAP. Its value comes from the comparison, +0.018 s." |
| So high variability *causes* slower laps? | Any causal claim | "No. SHAP and OLS show associations inside the model, not causes." |
| Why did Albon lose 9 seconds? | A guess (spin, traffic, damage…) | "We don't know. The data show a green-flag, accurate lap, 9 s slower than the field. That's why no lap history could see it." |
| Would random forest / boosting / a neural network do better? | "Yes" or "No" | "We didn't try other model families. We kept OLS to isolate one change. The same matched-control design would test it." |
| D was better overall, so would you switch now? | "Yes, we'll use D" | "Not on this evidence. D's rule was to fix the pit-stop laps, and it didn't. Switching after seeing the overall number would be choosing on validation." |
| What happens if you use the reference after a pit stop (the fallback)? | Any number for it | "That is our next check, with its own rule written before we run it." (Some of it can be inferred from saved slices, but it was not run as a trial; do not quote a number.) |
| How did it do on the final test races? | Anything | "We never accessed the reserved races. The instructor runs them." |
| Could it help decide when to pit? | "Yes" | "It doesn't decide strategy. It gives an expected lap time; a slower real lap is a flag to check." |
| A question about your partner's part | Your own answer first | "Baptiste built that, he'll explain" (or "Vicente ran that…"). Then let them answer. |
| A question you don't understand | A guess at what they meant | "Do you mean \_\_\_ or \_\_\_?" |
| A suggestion from the jury ("have you thought about…?") | A promise of what it will show | "We haven't tested it. We would add it the same way: matched control, same laps, a rule written first." Then write it down: it is feedback for the final report. |
| How exactly did the AI write X? | Details you are unsure of | What the decision log records: what was drafted and how it was checked (section 6, G3). |

**Never:** invent a number, round a number differently from the slide, quote a number from memory you are not sure of ("it's on backup slide 10" is better), argue with a juror, or change the decision on the spot.

## 6. Question bank

**Default owner:** Baptiste takes data, the new input, leakage, missing history, short history, trial D and the fallback. Vicente takes the use, MAE, the comparison, the rule, bootstrap, concentration, SHAP and the traffic proxy. Each partner answers for their own AI use.

**What each of us defends** (the closeout guide's decision + evidence + limitation):

| Partner | Decision | Evidence | Limitation |
| --- | --- | --- | --- |
| Baptiste | The window is the last 3 laps of the stint (the `recent_mean_s` window), non-clean laps left out, no reach-back, and the feature was trusted only after the rebuild matched | Rebuilt `recent_mean_s` = official column on 7,580/7,580 rows; as-of recomputation identical; worked lap `2026-R8-1-L28` | Short history: 148 laps, candidate 0.453 s vs reference 0.396 s; D missed its rule |
| Vicente | Compare against matched control C, not reference A, and keep B | C − B = +0.018 s; Austria +0.013, Silverstone +0.025; Hito 1 rule met | 50 of 1,808 laps carry 94.5% of the gain; sudden losses like Albon's lap 7 (8.25 s) are invisible |

### A. Use and framing (Vicente)

**A1. Why would anyone need this?** A race engineer compares each real lap with what was expected; a lap much slower than expected is worth checking. We give the expected lap. It does not decide strategy.

**A2. How good is it in plain terms?** It misses by 0.37 s on average on laps of 73 to 95 s. Simply repeating the last lap misses by 0.41 s, so most of the skill comes from the last laps themselves; our input trims a little more.

**A3. Why only 0.018 s? Is that worth anything?** Small on average, large where it matters: on Albon's lap the error went from 4.23 to 1.24 s. But 50 laps carry it, so a race with fewer incidents could show no gain. Backup 8.

**A4. Why did you choose this input?** The hypothesis from Hito 1: after a one-off slow lap, the recent laps overstate the next one; variability flags that. A training-only check before validation (check 3) showed the spread is related to the reference's errors (Spearman 0.358).

### B. Data and the new input (Baptiste)

**B1. Could the input see the future?** No. It uses laps t−2 to t only; lap t+1 is the target. Checked on all 7,580 rows, plus a second implementation that only sees finished laps. Backup 9.

**B2. What is a clean lap and why only those?** Green flag, accurate timing, not a pit lap, not deleted, same stint. The course defines the evaluation on clean pairs, because pit stops and yellows disrupt laps in ways lap history cannot predict. Limit: results hold for clean laps only.

**B3. Why three laps?** It is the window of the course's own `recent_mean_s`, fixed in Hito 1 before any result. We did not try other windows: tuning it on validation would be choosing on validation.

**B4. Why standard deviation and not the range or a trend?** It was our hypothesis, fixed in advance. We did not test the others, so we can't say they are worse.

**B5. What if a lap in the window is not clean?** It is left out and not replaced by an older lap, exactly like `recent_mean_s`. Reaching back would give a different value on 111 of 1,808 validation rows. Worked example on slide 2.

**B6. What happens with only one clean lap?** The spread doesn't exist; we leave it missing, fill the training median (0.258 s) and add a flag. Not 0, because 0 would mean "perfectly stable". This is where the model is weakest. Backup 8.

**B7. Why is it worse after a pit stop?** The flag learned from training that the lap after a short history is about 0.37 s faster. That held in Austria and reversed at Silverstone. Trial D removed the flag and improved those laps (0.453 → 0.416 s) but missed its rule (≤ 0.401 s).

**B8. How do you know your window is right?** We rebuilt the course's `recent_mean_s` and `recent_count` with our code; they match the official columns exactly on every row.

**B9. Did any data come from outside the course?** No. Only the released timing snapshots, with their SHA-256 checked against the release manifest.

### C. The comparison (Vicente)

**C1. Why compare with C and not the reference?** The candidate adds two columns. C keeps the flag and removes only the spread, so C − B measures the spread alone. Against A, we would credit the flag's (negative) effect to the spread. Backup 10.

**C2. Why is the control worse than the reference?** C is the reference plus the flag. The flag alone does not help (0.388 vs 0.387 s); it is only there so that C differs from B in one thing.

**C3. Is it significant?** We don't use that word. Resampling whole stints inside these two races keeps the gain positive (+0.009 to +0.029 s). It does not say the gain holds in other races.

**C4. Did you tune anything on validation?** No. The window, the 0.01 s threshold, the model and the inputs were fixed in Hito 1. Trial D was added after seeing the slices, with its rule written before running it, and it is disclosed. The bootstrap and the concentration table are labelled post-hoc.

**C5. Where does the 0.01 s threshold come from?** Our own choice in Hito 1, before any result, to turn "MAE stays very similar" into a failure condition we could measure (`Hito1/DECISION_LOG.md`). It is a judgement, not derived from data. We kept it after the Hito 1 feedback; a result below it would read "does not meet the predeclared criterion", not "variability is useless".

**C6. Why OLS and not a better model?** OLS is the course reference, and a simple model lets one change be isolated. Other model families were not tested.

**C7. Is the gain real or a few lucky laps?** Both readings are honest: it is real on those laps (Albon), and it is concentrated. Without the top 50 laps the models tie; without the top 100 the candidate is behind. Backup 8.

**C8. Why is Silverstone's gain bigger?** Silverstone has more large misses to correct; it is the harder race (higher error for every model), not the easier one.

### D. Errors and the case (Baptiste)

**D1. Why did you pick Albon's lap?** By a fixed rule in the code: the row where the new input moved the prediction the most. We didn't browse for a nice example.

**D2. What did the model get most wrong?** Albon's lap 7 itself, 8.25 s. At the end of lap 6 nothing in the history hinted at it. No lap-history input can foresee a sudden loss on the next lap.

**D3. Does the candidate make anything worse?** Yes: the 148 short-history laps (0.453 vs 0.396 s for the reference), mostly at Silverstone, and slightly the typical lap (better than the control on only 53% of laps).

### E. SHAP (Vicente)

**E1. What is SHAP, for a guest?** A way to split one prediction into pieces, one per input, that add up exactly to the prediction, starting from the average prediction.

**E2. Why is the base 86.73 s when Silverstone laps are about 95 s?** The base is the average prediction over training rounds 1–7, which include faster tracks. The pace inputs move it up to the Silverstone level.

**E3. The spread contributes −2.47 s, yet the model still over-predicts. Contradiction?** No. Contributions are measured from the base, not from the real lap. The model said 99.12 and the real lap was 97.88, an over-prediction of 1.24 s, measured separately.

**E4. Is the spread the most important input?** No, third (0.15 s on average). The pace inputs place the track. SHAP shows how the model uses inputs, not how much each improves accuracy; the comparison measures that.

**E5. Why `LinearExplainer` and the training background?** The model is linear, so the explanation is exact. The background is the full training set, so contributions are relative to what the model learned. We checked base plus contributions equals the prediction on all 1,808 rows (largest gap 1.4e-14 s).

### F. Decision and next steps (Baptiste)

**F1. Would you deploy it?** No. We would keep it as the working model for the next test. Not shown for other races, other models or live use.

**F2. What would make you drop it?** The same rule on new races: if the control beats it, or it loses in a race, we would report that it does not generalise.

**F3. What would you do next?** Baptiste: after a pit stop, fall back to the reference prediction, with its own rule written first. Vicente: a traffic signal available at the end of lap t, the gap to the car ahead, tested the same way on the laps with errors above 1 s and overall.

**F4. Why not use D?** See section 5: the rule was written first and D failed it.

### G. Process (both)

**G1. How did you split the work?** Baptiste built the feature and its checks (`Hito2/features.py`, checks 1–2, the history convention). Vicente ran the models, the ablation, the error tables and SHAP (`Hito2/run_hito2.py`, checks 3–5 and D). Each of us can defend the other's main number.

**G2. Can someone reproduce it?** One command, `python run_hito2.py`, about 10 s, from a clean environment; two runs give byte-identical outputs. Data instructions and hashes in `Hito2/README.md`.

**G3. How did you use AI?** Answer for your own use, as recorded in `Hito2/DECISION_LOG.md` (AI use record). In short: Claude Code (both) and Gemini (Vicente) drafted scripts and text; we adopted them only after the checks: the exact rebuild of `recent_mean_s`, the as-of recomputation, the pooled arithmetic and the SHAP reconstruction by hand, and a clean-environment rerun. Don't add uses that aren't in the record.

**G4. What was hardest / what would you do differently?** Answer personally. Honest options: the window wording ("last 3 laps" vs "last 3 clean laps") looked trivial and changed 111 rows; we would declare the concentration check in advance, since it turned out to be the main limit.

## 7. On the day

**Before 11:10**

- Laptop charged, with the deck open in presenter view and the PDF as a fallback. Copies on a USB stick and in the cloud. Bring an HDMI / USB-C adapter.
- If the lab PC lacks the Aptos font, PowerPoint substitutes it; if a slide looks shifted, present from the PDF.
- Agree who clicks. Phone timer on silent.

**During the 7 minutes:** watch the checkpoints in the [script](SCRIPT.md#rehearsal); if late, use the short versions.

**During the 5 minutes of questions:** the partner not answering writes the jury's feedback word for word, with who said it. Right after, copy it into `Final/DECISION_LOG.md` ("Feedback received"): it is the Demo Day priority for the final report.

**Spanish glossary, if a question comes in Spanish**

| English | Español |
| --- | --- |
| next lap time | tiempo de la próxima vuelta |
| average miss (MAE) | error absoluto medio, el error promedio en segundos |
| straight-line formula (OLS) | regresión lineal (mínimos cuadrados) |
| matched control | control emparejado: el mismo modelo sin el cambio |
| clean lap | vuelta limpia: bandera verde, cronometrada, sin pits ni borrada |
| spread of the last three laps | dispersión (desviación estándar) de las últimas tres vueltas |
| rule written before running | regla declarada antes de correr |
| short history (one clean lap) | historial corto (una sola vuelta limpia) |
| stint | tanda entre paradas en pits |
| leakage | fuga de información del futuro |
| optimistic (used to choose) | optimista, porque se usó para elegir |
