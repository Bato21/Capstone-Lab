// NextLap Demo Day deck, Group 1 (20 Nov 2026). Builds Demo/NextLap_Demo_Team1.pptx.
//
// Follows the official Demo Day slide template (NextLap Student Closeout Pack): the same six
// questions, timings, colours, fonts and footer, with the bracketed prompts replaced by our results.
//
// Inputs (nothing is typed by hand twice):
//   figures/deck_data.json, figures/*.png   written by make_figures.py from Hito2/outputs
//   SCRIPT.md                               spoken text -> speaker notes of each slide
// Run from the repository root (pptxgenjs is installed outside the repository):
//   .venv/Scripts/python Demo/make_figures.py
//   NODE_PATH=<folder with node_modules> APPLY_THEME=<path to apply_theme.js> node Demo/build_deck.js
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.APPLY_THEME);  // pptx skill helper: writes THEME into the deck

const HERE = __dirname;
const D = JSON.parse(fs.readFileSync(path.join(HERE, "figures", "deck_data.json"), "utf8"));
const OUT = path.join(HERE, "NextLap_Demo_Team1.pptx");

// ---- Speaker notes: the quoted lines, "Must say" and "Handover" of each "## Slide N" block in SCRIPT.md ----
const pitch = fs.readFileSync(path.join(HERE, "SCRIPT.md"), "utf8").replace(/\r/g, "");
const NOTES = {};
for (const block of pitch.split(/^## Slide /m).slice(1)) {
  const n = parseInt(block, 10);
  const head = block.split("\n")[0];                       // "2 · B · What changed in the model?"
  const who = head.includes("· V ·") ? "VICENTE" : "BAPTISTE";
  const must = (block.match(/^\*\*Must say:\*\* (.*)$/m) || [, ""])[1];
  const hand = (block.match(/^\*\*Handover:\*\* (.*)$/m) || [, ""])[1];
  const said = block.split("\n").filter(l => l.startsWith("> ")).map(l => l.slice(2)).join(" ");
  NOTES[n] = { who, text: `${who}\n\n${said}` + (must ? `\n\nMust say: ${must}` : "") +
    (hand ? `\n\nHandover: ${hand}` : "") };
}

// ---- Theme: the template's navy, off-white and teal ------------------------------------------
const THEME = {
  name: "NextLap Demo Day",
  headFontFace: "Aptos Display",
  bodyFontFace: "Aptos",
  colors: {
    dk1: "102739", lt1: "FFFFFF", dk2: "112A3B", lt2: "F5F6F3",
    accent1: "006E5B",  // template accent; candidate B
    accent2: "C98A1B",  // matched control C
    accent3: "8A9BA3",  // OLS reference A
    accent4: "4F6D8F",  // follow-up D
    accent5: "B5523B",  // non-clean lap, limit, negative
    accent6: "3D5B66",  // template muted text
    hlink: "006E5B", folHlink: "3D5B66",
  },
};
const HEX = { A: "8A9BA3", B: "006E5B", C: "C98A1B", D: "4F6D8F", red: "B5523B", rule: "CCD8D5",
  ink: "102739", muted: "3D5B66" };
const AMBER = "FFD092", MINT = "D7EAE2";  // template text tints on the dark slides
const MONO = "Consolas";                    // lap-time chips, like a timing screen

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";  // 13.333 x 7.5 in, as the template
pres.title = "NextLap Demo Day · Group 1";
pres.author = "Vicente Rodríguez, Baptiste Vial";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const S = pres.shapes;

// ---- Layouts: template geometry (title y 1.02, prompt y 2.13, rule y 6.91, footer y 7.03) ------
const FOOTER = "IIT414W   /   NEXTLAP DEMO DAY   /   GROUP 1";
function layout(title, dark) {
  const ink = dark ? C.background1 : C.text1, sub = dark ? MINT : C.accent6;
  pres.defineSlideMaster({
    title,
    background: { color: dark ? C.text2 : C.background2 },
    margin: [0.5, 0.76, 0.6, 0.76],
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.76, y: 1.0, w: 11.8, h: 1.0, fontSize: 40,
          bold: true, color: ink, valign: "middle", align: "left", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.77, y: 2.06, w: 11.7, h: 0.62, fontSize: 21,
          color: sub, valign: "top", align: "left", margin: 0 }, text: "" } },
      { line: { x: 0.76, y: 6.91, w: 11.8, h: 0, line: { color: dark ? HEX.muted : HEX.rule, width: 0.75 } } },
      { text: { text: FOOTER, options: { x: 0.76, y: 7.03, w: 9, h: 0.21, fontSize: 10, color: sub, margin: 0 } } },
    ],
  });
}
// Template numbers its slides "01", "02"…; a slideNumber field cannot pad, so each slide gets a text box.
let slideCount = 0;
function addSlide(masterName, sectionTitle) {
  const s = pres.addSlide({ masterName, sectionTitle });
  s.addText(String(++slideCount).padStart(2, "0"), { x: 11.7, y: 7.03, w: 0.86, h: 0.21, fontSize: 10, margin: 0,
    align: "right", color: masterName === "DARK" ? MINT : HEX.muted, isTextBox: true, objectName: `number_${slideCount}` });
  return s;
}
layout("LIGHT", false);
layout("DARK", true);

// ---- Small builders -------------------------------------------------------------------------
let shapeId = 0;
const nm = (s) => `${s}_${++shapeId}`;

function text(slide, runs, opts) {
  slide.addText(runs, { margin: 0, isTextBox: true, valign: "top", color: C.text1, fontSize: 16,
    objectName: nm("text"), ...opts });
}

// Template's top line: the slot of the slide, and who presents it.
function slot(slide, time, n, dark = false) {
  const who = typeof n === "number" ? NOTES[n].who : n;
  text(slide, `${time}   ·   ${who}`, { x: 0.76, y: 0.5, w: 11.8, h: 0.32, fontSize: 13, bold: true,
    color: dark ? AMBER : C.accent1, charSpacing: 1 });
}

function chip(slide, { x, y, w, h, top, main, fill, color, line, dash, mainSize = 17 }) {
  slide.addShape(S.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.1, fill,
    line: line ? { color: line, width: 1.5, dashType: dash ? "dash" : "solid" } : { type: "none" },
    objectName: nm("chip") });
  slide.addText([
    { text: top, options: { fontSize: 11, color, breakLine: true } },
    { text: main, options: { fontSize: mainSize, bold: true, color, fontFace: MONO } },
  ], { x, y, w, h, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: nm("chip_text") });
}

function card(slide, { x, y, w, h, fill = C.background1, line = HEX.rule }) {
  slide.addShape(S.RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: line, width: 0.75 },
    objectName: nm("card") });
}

function rule(slide, y, x = 0.76, w = 11.8) {
  slide.addShape(S.LINE, { x, y, w, h: 0, line: { color: HEX.rule, width: 0.75 }, objectName: nm("rule") });
}

// Template row: a teal label column and a text column, separated by thin rules.
function row(slide, y, label, body, { h = 0.7, x = 0.76, w = 11.8, labelW = 2.7, size = 17 } = {}) {
  rule(slide, y, x, w);
  text(slide, label, { x: x + 0.01, y: y + 0.1, w: labelW, h, fontSize: 18, bold: true, color: C.accent1 });
  text(slide, body, { x: x + labelW + 0.1, y: y + 0.1, w: w - labelW - 0.1, h, fontSize: size });
}

// Template table: navy header, white body, light rules.
function table(slide, rows, { x = 0.77, y, colW, fontSize = 16, rowH = 0.46, bold = [] }) {
  const head = rows[0].map(t => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text1 } } }));
  const body = rows.slice(1).map((r, i) => r.map(c => {
    const cell = typeof c === "object" ? c : { text: String(c), options: {} };
    return { text: cell.text, options: { fill: { color: C.background1 }, bold: bold.includes(i), ...cell.options } };
  }));
  slide.addTable([head, ...body], { x, y, w: colW.reduce((a, b) => a + b), colW, rowH, fontSize, color: C.text1,
    border: { type: "solid", pt: 0.75, color: HEX.rule }, margin: [0.04, 0.12, 0.04, 0.12], valign: "middle",
    objectName: nm("table") });
}

const sgn = (v, d = 3) => (v >= 0 ? "+" : "−") + Math.abs(v).toFixed(d);
const f3 = (v) => v.toFixed(3);
const R = (v) => ({ text: v, options: { align: "right" } });
const M = D.mae, CB = D.c_minus_b;
const chartText = { catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
  legendFontFace: "+mn-lt", titleFontFace: "+mn-lt", catAxisLabelColor: HEX.muted, valAxisLabelColor: HEX.muted,
  dataLabelColor: HEX.ink, catAxisLabelFontSize: 13, valAxisLabelFontSize: 12, dataLabelFontSize: 13,
  legendFontSize: 13, valGridLine: { color: HEX.rule, size: 0.75 }, catGridLine: { style: "none" } };

// =============================================================================================
pres.addSection({ title: "Presentation (7 min)" });
const SEC = "Presentation (7 min)";

// ---- 1. Title (0:00-0:45) ----------------------------------------------------------------------
{
  const s = addSlide("DARK", SEC);
  slot(s, "0:00–0:45", 1, true);
  s.addText("NextLap: is the next lap off?", { placeholder: "title" });
  s.addText("A next-lap estimate helps a race engineer spot a lap slower than expected, and check why.",
    { placeholder: "body" });
  text(s, "Vicente Rodríguez and Baptiste Vial   /   Group 1", { x: 0.77, y: 3.05, w: 11.7, h: 0.5, fontSize: 26,
    bold: true, color: AMBER });
  text(s, "We predict the same driver's next lap time, in seconds, at the end of the current lap, " +
    "to help the pit wall spot laps worth checking.", { x: 0.77, y: 3.75, w: 11.6, h: 1.1, fontSize: 26,
    color: C.background1 });
  // Albon at Silverstone, laps 5-8: the lap the talk comes back to.
  const laps = [["Lap 5", "96.299"], ["Lap 6", "98.070"], ["Lap 7", "105.128"], ["Lap 8", "?"]];
  laps.forEach(([top, main], i) => {
    const odd = i === 2, next = i === 3;
    chip(s, { x: 0.77 + i * 1.95, y: 5.15, w: 1.75, h: 0.95, top, main, mainSize: 19,
      fill: { color: odd ? C.accent5 : next ? C.accent1 : C.accent6 }, color: C.background1 });
  });
  text(s, "Albon, British GP 2026 (validation): what should we predict after lap 7?", { x: 8.65, y: 5.3, w: 3.9,
    h: 0.7, fontSize: 14, italic: true, color: MINT, valign: "middle" });
  s.addNotes(NOTES[1].text);
}

// ---- 2. What changed in the model? (0:45-1:45) --------------------------------------------------
{
  const s = addSlide("LIGHT", SEC);
  slot(s, "0:45–1:45", 2);
  s.addText("What changed in the model?", { placeholder: "title" });
  s.addText("One new input: how erratic the driver's last three laps were (recent_std_s).", { placeholder: "body" });
  // Worked history 2026-R8-1-L28: the window and what it leaves out.
  const ex = D.window_example;
  const x0 = 0.77, cw = 1.5, gap = 0.2, cy = 3.2, ch = 0.82;
  ex.forEach((l, i) => {
    const x = x0 + i * (cw + gap);
    const target = l.role.startsWith("t+1");
    const top = target ? `Lap ${l.lap} · t+1` : l.role === "t" ? `Lap ${l.lap} · t` : `Lap ${l.lap}`;
    const main = l.time.toFixed(3);
    if (target) chip(s, { x, y: cy, w: cw, h: ch, top, main, fill: { color: C.background2 }, color: C.accent6,
      line: HEX.muted, dash: true });
    else if (l.used) chip(s, { x, y: cy, w: cw, h: ch, top, main, fill: { color: C.accent1 }, color: C.background1 });
    else if (!l.clean) chip(s, { x, y: cy, w: cw, h: ch, top, main, fill: { color: C.accent5, transparency: 75 },
      color: C.text1 });
    else chip(s, { x, y: cy, w: cw, h: ch, top, main, fill: { color: C.background1 }, color: C.text1, line: HEX.rule });
    const tag = target ? "predicted, never used" : !l.clean ? "not green: left out" : l.used ? "used" : "outside window";
    text(s, tag, { x: x - 0.05, y: cy + ch + 0.04, w: cw + 0.1, h: 0.26, fontSize: 11, align: "center", color: C.accent6 });
  });
  const wi = ex.findIndex(l => l.in_window);
  const wx = x0 + wi * (cw + gap), ww = 3 * cw + 2 * gap;
  [[wx, cy - 0.1, ww, 0], [wx, cy - 0.1, 0, 0.08], [wx + ww, cy - 0.1, 0, 0.08]].forEach(([x, y, w, h]) =>
    s.addShape(S.LINE, { x, y, w, h, line: { color: C.accent1, width: 2.25 }, objectName: nm("bracket") }));
  text(s, "window = laps t−2 … t, same as recent_mean_s → std(71.773, 71.568) = 0.145 s", { x: wx - 1.6, y: cy - 0.45,
    w: ww + 3.3, h: 0.3, fontSize: 13, bold: true, color: C.accent1, align: "center" });
  text(s, "2026-R8-1-L28 (Austria)", { x: x0, y: cy - 0.45, w: 3, h: 0.3, fontSize: 12, color: C.accent6 });
  row(s, 4.45, "New input or change", "Spread of the clean lap times in laps t−2…t, all finished by the end of lap t. " +
    "Fewer than 2 clean laps → training median + short_history flag.", { size: 16 });
  row(s, 5.23, "Evaluation", "Train R1–R7 (5,772 laps), validate R8–R9. Same 1,808 pair_ids in every run (hash = Hito 1). " +
    "Rebuilt recent_mean_s = official column on 7,580/7,580 rows.", { size: 16 });
  row(s, 6.01, "Matched control", "Same OLS, same rows and pipeline, refitted without recent_std_s (it keeps the flag).",
    { size: 16 });
  s.addNotes(NOTES[2].text);
}

// ---- 3. What did the comparison show? (1:45-3:25) -----------------------------------------------
{
  const s = addSlide("LIGHT", SEC);
  slot(s, "1:45–3:25", 3);
  s.addText("What did the comparison show?", { placeholder: "title" });
  s.addText("The candidate missed by 0.018 s less than its matched control, on the same 1,808 laps.",
    { placeholder: "body" });
  table(s, [
    ["Run", "Model and inputs (OLS, train R1–R7)", "n", "MAE (s)"],
    ["Reference OLS (A)", "Six published inputs", R("1,808"), R(f3(M.A.all_validation))],
    [{ text: "Candidate (B)", options: { color: C.accent1, bold: true } }, "Six + recent_std_s + short_history",
      R("1,808"), { text: f3(M.B.all_validation), options: { align: "right", bold: true, color: C.accent1 } }],
    ["Matched control (C)", "Six + short_history (B without the spread)", R("1,808"), R(f3(M.C.all_validation))],
  ], { y: 2.95, colW: [2.75, 5.6, 1.4, 2.0], fontSize: 17, rowH: 0.48 });
  text(s, [
    { text: "Matched control MAE − candidate MAE = ", options: {} },
    { text: `${f3(M.C.all_validation)} − ${f3(M.B.all_validation)} = ${sgn(CB.all_validation)} s`, options: { bold: true } },
  ], { x: 0.78, y: 5.0, w: 11.7, h: 0.45, fontSize: 21, color: C.accent1, bold: true });
  const cards = [
    ["Rule fixed in Hito 1: met", "≥ 0.010 s overall and ≥ 0 in each race (R8 " + sgn(CB.R8) + ", R9 " + sgn(CB.R9) + " s)."],
    ["Stint bootstrap", "95% interval +0.009 to +0.029 s. Describes these two races only."],
    ["Concentrated", `${(D.top50_share * 100).toFixed(1)}% of the gain comes from 50 of 1,808 laps; without them ${sgn(D.concentration["50"])} s.`],
  ];
  cards.forEach(([head, body], i) => {
    const x = 0.77 + i * 3.97;
    card(s, { x, y: 5.62, w: 3.8, h: 0.98 });
    text(s, [{ text: head, options: { bold: true, color: i === 2 ? C.accent5 : C.accent1, breakLine: true } },
      { text: body, options: { fontSize: 13 } }], { x: x + 0.15, y: 5.7, w: 3.5, h: 0.85, fontSize: 15 });
  });
  s.addNotes(NOTES[3].text);
}

// ---- 4. Where does the model struggle? (3:25-4:40) ----------------------------------------------
{
  const s = addSlide("LIGHT", SEC);
  slot(s, "3:25–4:40", 4);
  s.addText("Where does the model struggle?", { placeholder: "title" });
  s.addText("Both races agree. What remains: sudden losses, and laps right after a pit stop.", { placeholder: "body" });
  table(s, [
    ["Race", "Common n", "Control MAE (s)", "Candidate MAE (s)", "Control − candidate (s)"],
    ["R8 Austria", R("1,066"), R(f3(M.C.R8)), R(f3(M.B.R8)), R(sgn(CB.R8))],
    ["R9 Great Britain", R("742"), R(f3(M.C.R9)), R(f3(M.B.R9)), R(sgn(CB.R9))],
    [{ text: "Pooled (weighted by n)", options: { color: C.accent6 } }, R("1,808"), R(f3(M.C.all_validation)),
      R(f3(M.B.all_validation)), { text: sgn(CB.all_validation), options: { align: "right", bold: true } }],
  ], { y: 2.85, colW: [2.65, 1.65, 2.15, 2.3, 3.0], fontSize: 16, rowH: 0.44 });
  // Template line: pair_id, observed, predicted, absolute error.
  text(s, [
    { text: "2026-R9-23-L7", options: { fontFace: MONO } },
    { text: "   Observed 97.882 s   /   Predicted 99.121 s   /   Absolute error 1.239 s", options: {} },
  ], { x: 0.78, y: 4.88, w: 11.7, h: 0.4, fontSize: 19, bold: true });
  text(s, "Albon, lap after a 9 s one-off loss. Control predicted 102.110 s (error 4.228 s); the spread pulled the candidate back.",
    { x: 0.78, y: 5.3, w: 11.7, h: 0.35, fontSize: 14, color: C.accent6 });
  const h = D.history["short (1 clean lap)"];
  const cards = [
    ["Largest miss: 2026-R9-23-L6, 8.25 s", "Albon's 9 s loss on lap 7 itself. No lap history can see it coming."],
    ["After a pit stop (1 clean lap, n = 148)", `Candidate ${f3(h.B)} s vs reference ${f3(h.A)} s: worse than the reference.`],
  ];
  cards.forEach(([head, body], i) => {
    const x = 0.77 + i * 5.95;
    card(s, { x, y: 5.8, w: 5.8, h: 0.9 });
    text(s, [{ text: head, options: { bold: true, color: C.accent5, breakLine: true } },
      { text: body, options: { fontSize: 14 } }], { x: x + 0.15, y: 5.88, w: 5.5, h: 0.78, fontSize: 15 });
  });
  s.addNotes(NOTES[4].text);
}

// ---- 5. What drove a prediction? (4:40-6:00) ----------------------------------------------------
{
  const s = addSlide("LIGHT", SEC);
  slot(s, "4:40–6:00", 5);
  s.addText("What drove a prediction?", { placeholder: "title" });
  s.addText("SHAP on candidate B, lap 2026-R9-23-L7: the pieces add up to its 99.12 s prediction.", { placeholder: "body" });
  s.addImage({ path: path.join(HERE, "figures", "shap_waterfall.png"), x: 0.7, y: 2.75, w: 5.85, h: 3.95,
    altText: "SHAP waterfall: base 86.73, recent_mean_s +8.18, current_lap_s +6.67, recent_std_s -2.47, others +0.003, prediction 99.12",
    objectName: nm("waterfall") });
  const g = D.shap_global_mean_abs;
  const rows = [
    ["Local explanation", "Base 86.73 s. recent_mean_s +8.18, current_lap_s +6.67 (Silverstone is slow), recent_std_s −2.47, five others +0.003."],
    ["Prediction check", "86.73 + 12.39 = 99.12 s = prediction (largest gap over 1,808 rows: 1.4e-14 s). Observed 97.88 s → absolute error 1.24 s, computed separately."],
    ["Global context", `All 1,808 validation laps, LinearExplainer, background = 5,772 training laps. Mean |SHAP|: recent_mean_s ${g.recent_mean_s.toFixed(2)}, current_lap_s ${g.current_lap_s.toFixed(2)}, recent_std_s ${g.recent_std_s.toFixed(2)} s.`],
  ];
  rows.forEach(([label, body], i) => {
    const y = 2.8 + i * 1.24;
    rule(s, y, 6.85, 5.71);
    text(s, [{ text: label, options: { bold: true, color: C.accent1, fontSize: 16, breakLine: true } },
      { text: body, options: { fontSize: 14 } }], { x: 6.86, y: y + 0.08, w: 5.7, h: 1.2 });
  });
  text(s, "SHAP explains the output; the ablation (+0.018 s) measures the gain.", { x: 6.86, y: 6.5, w: 5.7, h: 0.3,
    fontSize: 13, italic: true, color: C.accent6 });
  s.addNotes(NOTES[5].text);
}

// ---- 6. What decision can you defend? (6:00-7:00) -----------------------------------------------
{
  const s = addSlide("DARK", SEC);
  slot(s, "6:00–7:00", 6, true);
  s.addText("What decision can you defend?", { placeholder: "title" });
  s.addText("Keep the new input: it beat its matched control on the same laps, in both races.", { placeholder: "body" });
  text(s, `We would keep recent_std_s because it beat its matched control by ${f3(CB.all_validation)} s on the same ` +
    `1,808 laps, in both races, as our Hito 1 rule required.`,
    { x: 0.77, y: 2.95, w: 11.7, h: 0.95, fontSize: 22, bold: true, color: AMBER });
  text(s, "This conclusion applies to a linear (OLS) model on clean laps in Austria and Silverstone. We chose with these " +
    "races, so the numbers are optimistic; other races and live use are not shown.", { x: 0.77, y: 4.2, w: 11.7, h: 1.0,
    fontSize: 20, color: C.background1 });
  text(s, `Our next check would be a fallback to the reference after a pit stop (trial D, without the flag, missed its rule: ` +
    `${f3(D.history["short (1 clean lap)"].D)} > 0.401 s), then a traffic signal at the end of lap t.`,
    { x: 0.77, y: 5.35, w: 11.7, h: 1.0, fontSize: 20, color: C.background1 });
  text(s, "Thank you. Questions?", { x: 0.77, y: 6.4, w: 8, h: 0.4, fontSize: 18, bold: true, color: AMBER });
  s.addNotes(NOTES[6].text);
}

// =============================================================================================
pres.addSection({ title: "Backup (questions)" });
const backup = (title, sub) => {
  const s = addSlide("LIGHT", "Backup (questions)");
  slot(s, "BACKUP", "QUESTIONS");
  s.addText(title, { placeholder: "title" });
  s.addText(sub, { placeholder: "body" });
  return s;
};
const src = (s, t) => text(s, `Source: ${t}`, { x: 0.77, y: 6.55, w: 11, h: 0.28, fontSize: 11, color: C.accent6 });

{
  const s = backup("One incident, two rows", "Albon at Silverstone: the miss nobody could foresee, and the next lap.");
  s.addImage({ path: path.join(HERE, "figures", "albon_incident.png"), x: 0.7, y: 2.7, w: 6.0, h: 3.7,
    altText: "Albon's lap times at Silverstone, laps 3 to 10, with control and candidate predictions for laps 7 and 8",
    objectName: nm("albon") });
  const cases = [
    ["2026-R9-23-L6 · predicting lap 7", "8.25 s error", "Largest error in validation. Track green, lap accurate, field median 96.20 s.", C.accent5],
    ["2026-R9-23-L7 · predicting lap 8", "4.23 s → 1.24 s", "Control 102.110, candidate 99.121, real 97.882 s. recent_std_s = 4.67 s, the highest in validation.", C.accent1],
  ];
  cases.forEach(([id, big, small, col], i) => {
    const y = 2.85 + i * 1.75;
    card(s, { x: 7.0, y, w: 5.56, h: 1.5 });
    text(s, [{ text: id, options: { fontSize: 12, fontFace: MONO, color: C.accent6, breakLine: true } },
      { text: big, options: { fontSize: 24, bold: true, color: col, breakLine: true } },
      { text: small, options: { fontSize: 13 } }], { x: 7.2, y: y + 0.12, w: 5.2, h: 1.45 });
  });
  src(s, "Hito2/outputs/inspected_cases.csv, validation_predictions.csv");
  s.addNotes("BACKUP · answered by BAPTISTE (errors and the case)\n\n" +
    "Why this lap? Picked by a fixed rule in the code: the row where the new input moved the prediction the most.\n\n" +
    "Lap 7 (L6 row): 8.25 s, the largest error. Green flag, accurate lap, 9 s slower than the field. We don't know why; " +
    "no lap history can see it coming.\n\n" +
    "Lap 8 (L7 row): control 102.110 believed the slow lap; spread 4.67 s, the highest in validation, pulled the " +
    "candidate to 99.121; real 97.882. Error 4.228 to 1.239 s.");
}
{
  const s = backup("A concentrated gain, and the pit-stop laps", "Where the +0.018 s comes from, and the slice where the candidate loses.");
  const k = D.concentration;
  s.addChart(pres.charts.BAR, [{ name: "Control − candidate (s)", labels: ["All 1,808", "Without top 10", "Without top 50", "Without top 100"],
    values: [k["0"], k["10"], k["50"], k["100"]] }], {
    x: 0.7, y: 2.7, w: 5.9, h: 3.8, barDir: "col", chartColors: [HEX.B], invertedColors: [HEX.red], barGapWidthPct: 60,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "+0.000;−0.000", showLegend: false,
    showTitle: true, title: `${(D.top50_share * 100).toFixed(1)}% of the gain sits in 50 of 1,808 laps`, titleFontSize: 14,
    titleColor: HEX.ink, valAxisMinVal: -0.01, valAxisMaxVal: 0.025, valAxisMajorUnit: 0.01, valAxisLabelFormatCode: "0.00",
    ...chartText, objectName: nm("chart_concentration") });
  const h = D.history["short (1 clean lap)"];
  const lab = ["Short history (n = 148)"];
  s.addChart(pres.charts.BAR, [
    { name: "A reference", labels: lab, values: [h.A] }, { name: "C control", labels: lab, values: [h.C] },
    { name: "B candidate", labels: lab, values: [h.B] }, { name: "D, flag removed", labels: lab, values: [h.D] },
  ], {
    x: 6.85, y: 2.7, w: 5.75, h: 3.8, barDir: "col", chartColors: [HEX.A, HEX.C, HEX.B, HEX.D], barGapWidthPct: 40,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000", showLegend: true, legendPos: "b",
    showTitle: true, title: "After a pit stop (1 clean lap): MAE (s), axis from 0.30", titleFontSize: 14, titleColor: HEX.ink,
    valAxisMinVal: 0.3, valAxisMaxVal: 0.48, valAxisMajorUnit: 0.05, valAxisLabelFormatCode: "0.00",
    ...chartText, objectName: nm("chart_short_history") });
  src(s, "Hito2/outputs/gain_concentration.csv, slices.csv");
  s.addNotes("BACKUP · left chart VICENTE (concentration), right chart BAPTISTE (short history)\n\n" +
    "Left: 50 of 1,808 laps carry 94.5% of the gain; without them +0.001 s, without the top 100 −0.008 s. " +
    "Candidate better than control on only 955 laps (53%). Real on those laps, and concentrated.\n\n" +
    "Right: 148 laps with one clean lap (after a pit stop or a yellow). Candidate 0.453 s vs reference 0.396 s. " +
    "Trial D (flag removed) reached 0.416 s; its rule, written first, was 0.401 s or less, so it failed and we kept B.");
}
{
  const s = backup("Checks written in Hito 1, and what happened", "All written before the code; all saved in checks.csv.");
  const h = D.history["short (1 clean lap)"];
  table(s, [
    ["Check", "Expected / failure condition", "Observed", "Result"],
    ["1. Availability at t", "Last lap used ends ≤ t; no cross-stint window", "All 7,580 rows; as-of recomputation identical", "Pass"],
    ["History convention", "Window = recent_mean_s window", "Rebuilt recent_mean_s / recent_count identical", "Pass"],
    ["2. Same rows", "Same 1,808 pair_ids and hash", "Hash = Hito 1; A = Hito 1 predictions", "Pass"],
    ["3. Prior signal (train)", "Spearman with |OLS residual| > 0", "ρ = 0.358, n = 5,316", "Pass"],
    ["4. Support rule", "C − B ≥ 0.01 s overall, ≥ 0 per race", `${sgn(CB.all_validation, 4)}; ${sgn(CB.R8, 4)}; ${sgn(CB.R9, 4)}`, "Supported"],
    ["5. Robustness slices", "Per race; full vs short history", "Short history worse than reference", "Done; a limit"],
    ["D. Follow-up", "Short MAE ≤ 0.401; A − D ≥ 0.01, ≥ 0 per race", `Short MAE ${f3(h.D)} s`, "Failed; kept B"],
  ], { y: 2.75, colW: [2.75, 3.75, 3.6, 1.65], fontSize: 14, rowH: 0.42 });
  src(s, "Hito2/outputs/checks.csv, followup_D_table.csv");
  s.addNotes("BACKUP · checks 1–2 and history BAPTISTE, checks 3–5 and D VICENTE\n\n" +
    "Leakage: the last lap used ends at t on all 7,580 rows; a second implementation that sees only finished laps " +
    "gives identical values. Same rows: identical 1,808 pair_ids, hash equal to Hito 1.\n\n" +
    "Rule: written in Hito 1 before any code; C − B ≥ 0.01 s overall and ≥ 0 in each race. Met.");
}
{
  const s = backup("All runs on the same 1,808 validation laps", "All OLS from make_model, train R1–R7, same pipeline, seed 414.");
  const r = (k, name, inputs) => [name, inputs, ...["all_validation", "R8", "R9"].map(p => R(M[k][p].toFixed(5)))];
  table(s, [
    ["Run", "Inputs", "All (1,808)", "R8 (1,066)", "R9 (742)"],
    r("A", "A · OLS reference", "6 published inputs"),
    r("C", "C · matched control", "6 + short_history"),
    r("B", "B · candidate (kept)", "6 + recent_std_s + short_history"),
    r("D", "D · follow-up, control = A", "6 + recent_std_s (no flag)"),
  ], { y: 2.75, colW: [2.9, 3.85, 1.65, 1.65, 1.65], fontSize: 15, rowH: 0.44 });
  text(s, [{ text: "Stint bootstrap (112 stints, 2,000 replicates, seed 414): ", options: { bold: true } },
    { text: "95% interval of C − B = [+0.009, +0.029] s. Variation inside these two races only." }],
    { x: 0.77, y: 5.15, w: 11.7, h: 0.4, fontSize: 15 });
  text(s, [{ text: "Why C, not A, is the control: ", options: { bold: true } },
    { text: "B adds two columns. C keeps short_history and drops only recent_std_s, so C − B isolates the spread." }],
    { x: 0.77, y: 5.65, w: 11.7, h: 0.7, fontSize: 15 });
  src(s, "Hito2/outputs/comparison_metrics.csv, bootstrap.csv");
  s.addNotes("BACKUP · answered by VICENTE (the comparison)\n\n" +
    "Why C, not A: B adds two columns; C keeps the flag and drops only the spread, so C − B measures the spread alone.\n\n" +
    "Why C is worse than A (0.388 vs 0.387): C is A plus the flag; the flag alone does not help.\n\n" +
    "Bootstrap: whole stints, because laps in a stint are not independent. Never say \"significant\"; it describes " +
    "these two races only.");
}
{
  const s = backup("Hito 1 feedback and what we changed", "Answered in Hito 2; HITO1.md revised and the revision disclosed.");
  table(s, [
    ["Feedback (97/100)", "What we did"],
    ["C3.1: “last 3 clean laps” vs “window 3, same as recent_mean_s”", "Convention stated: last 3 laps of the stint, non-clean ones left out. Checked on every row; worked history 2026-R8-1-L28. The readings differ on 111 of 1,808 rows."],
    ["C3.1: how could the spread correct the prediction?", "Bounded hypothesis: a negative coefficient pulls the prediction back after a one-off slow lap; additive and blind to direction. Written after the results, and disclosed."],
    ["C4.4: < 0.01 s does not refute the idea", "Threshold kept; such a result is worded “does not meet the predeclared improvement criterion”."],
    ["For Hito 2: convention and same pair_ids", "Both checked (history convention; check 2, hash = Hito 1)."],
  ], { y: 2.75, colW: [4.3, 7.45], fontSize: 14, rowH: 0.5 });
  src(s, "Hito2/DECISION_LOG.md (Feedback received), Hito1/DECISION_LOG.md");
  s.addNotes("BACKUP · window convention BAPTISTE, threshold VICENTE\n\n" +
    "Window: last 3 laps of the stint, the recent_mean_s window; non-clean laps left out, not replaced. Reaching back " +
    "would change 111 of 1,808 rows.\n\n" +
    "Threshold 0.01 s: our own judgement in Hito 1, before any result. Kept after the feedback.");
}
{
  const s = backup("What this evidence does not show", "Each open question, what we can say, and the check that would answer it.");
  const h = D.history["short (1 clean lap)"];
  table(s, [
    ["Question", "What we can say now", "Check that would answer it"],
    ["Other races or tracks", "Not shown: two races, also used to choose", "Same A/B/C comparison on new races, same rule"],
    ["Live use on the pit wall", "Not shown: only clean laps, chosen after the fact", "Score every lap, without the clean-pair filter"],
    ["Other model families", "Not tested: OLS only, to isolate one change", "The same matched-control design"],
    ["Does variability cause slow laps?", "Not claimed: OLS and SHAP show associations", "Outside what lap timing can show"],
    ["Laps after a pit stop", `Worse than the reference: ${f3(h.B)} vs ${f3(h.A)} s (n = 148)`, "Fallback to the reference, rule written first"],
    ["Sudden losses (Albon, lap 7)", "Invisible to lap history: 8.25 s miss", "A traffic signal at the end of lap t"],
    ["Reserved final races", "Never accessed", "Run by the instructor"],
  ], { y: 2.75, colW: [3.2, 4.6, 3.95], fontSize: 14, rowH: 0.43 });
  src(s, "Hito2/HITO2.md §8, slices.csv, inspected_cases.csv");
  s.addNotes("BACKUP · whoever owns the topic answers\n\n" +
    "Formula: \"We didn't test that. What our evidence shows is ___. The check that would answer it is ___.\"\n\n" +
    "Never: a number for the fallback, a cause for Albon's loss, \"significant\", a percentage accuracy, " +
    "or a promise of what a suggested idea would show.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("Wrote", OUT);
})();
