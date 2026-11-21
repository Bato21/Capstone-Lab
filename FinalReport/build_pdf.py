"""Export FINAL_REPORT.md to the PDF submitted in Canvas.

The commit SHA cannot be written inside the commit it names, so it is inserted here at export
time, and every relative link becomes a GitHub link pinned to that commit. Run from the
repository root after the final commit is pushed:
    python FinalReport/build_pdf.py --sha <full commit SHA> --out <path>.pdf
Without --sha it writes a draft marked "SHA pending". Needs the `markdown` package and
Microsoft Edge (headless print to PDF).

Layout only: the text, tables and numbers come from FINAL_REPORT.md. The key-result tiles on
page one are read from the saved outputs (never typed), and figures are embedded from the
repository files the report links to.
"""
import argparse
import base64
import csv
import html as htmllib
import re
import subprocess
import tempfile
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO_URL = 'https://github.com/Bato21/Capstone-Lab'
EDGE = Path(r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')

parser = argparse.ArgumentParser()
parser.add_argument('--sha', help='full 40-character SHA of the submitted commit')
parser.add_argument('--out', default=str(HERE / 'NextLap_Final_Report_Group1.pdf'))
args = parser.parse_args()
if args.sha and not re.fullmatch(r'[0-9a-f]{40}', args.sha):
    parser.error('--sha must be the full 40-character commit hash')

md = (HERE / 'FINAL_REPORT.md').read_text(encoding='utf-8')
sha_text = (f'[`{args.sha}`]({REPO_URL}/commit/{args.sha})' if args.sha
            else '**SHA pending (draft export)**')
md, n = re.subn(r'<!--SHA-->.*?<!--/SHA-->', sha_text, md)
assert n == 1, 'SHA marker missing in FINAL_REPORT.md'


# ---- Key results on page one, read from the saved outputs ----------------------------------------
def rows(path):
    with open(ROOT / path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


race = {r['race']: r for r in rows('Hito2/outputs/race_table.csv')}
trial = {r['population']: r for r in rows('FinalReport/outputs/trial_E_table.csv')}
conc = {r['top_k_rows_by_gain']: r for r in rows('Hito2/outputs/gain_concentration.csv')}
f = lambda x, d=5: f'{float(x):.{d}f}'  # noqa: E731
s = lambda x, d=5: f'{float(x):+.{d}f}'.replace('-', '−')  # noqa: E731
TILES = [
    ('teal', 'Tested change kept', f"{s(race['pooled (n-weighted)']['control_minus_candidate_s'])} s",
     f"Matched control − candidate MAE on 1,808 common rows; R8 {s(race['R8']['control_minus_candidate_s'])}, "
     f"R9 {s(race['R9']['control_minus_candidate_s'])} s"),
    ('navy', 'Final frozen model E', f"{f(trial['all_validation']['E_fallback_MAE_s'])} s",
     f"MAE against {f(trial['all_validation']['A_reference_MAE_s'])} s for the OLS reference: "
     f"{s(trial['all_validation']['A_minus_E_s'])} s, positive in R8 and R9"),
    ('teal', 'Hito 2 priority fixed', f"{f(trial['short_history']['B_candidate_MAE_s'], 3)} → "
     f"{f(trial['short_history']['E_fallback_MAE_s'], 3)} s",
     f"Short-history rows (n = {trial['short_history']['n']}): candidate → final model, "
     f"equal to the reference"),
    ('amber', 'Main limitation', f"{100 * float(conc['50']['share_of_total_gain']):.1f}%",
     'of the tested gain comes from 50 of 1,808 rows; validation rounds were used to choose'),
]
tiles = ''.join(f'<div class="tile {c}"><div class="t-label">{a}</div><div class="t-value">{v}</div>'
                f'<div class="t-note">{htmllib.escape(note)}</div></div>' for c, a, v, note in TILES)
md = md.replace('<!--KEY-RESULTS-->', f'<div class="tiles">{tiles}</div>')
md = re.sub(r'<!--.*?-->\n?', '', md, flags=re.S)  # editing notes are not part of the report

# ---- Figures: embedded from the repository, numbered, captioned with their alt text -------------
fig_no = 0
FIG_WIDTH = {'albon_incident.png': 47, 'shap_global_bar.png': 58}  # % of the text width


def figure(match):
    global fig_no
    fig_no += 1
    alt, target = match.group(1), match.group(2)
    data = base64.b64encode((HERE / target).resolve().read_bytes()).decode()
    width = FIG_WIDTH.get(Path(target).name, 60)
    return (f'<figure style="width:{width}%"><img src="data:image/png;base64,{data}" alt="">'
            f'<figcaption><b>Figure {fig_no}.</b> {htmllib.escape(alt)}</figcaption></figure>')


md = re.sub(r'^!\[([^\]]*)\]\(([^)\s]+)\)$', figure, md, flags=re.M)


def pin(match):
    """Relative link -> GitHub link at the submitted commit (or at main for a draft)."""
    text, target = match.group(1), match.group(2)
    if re.match(r'[a-z]+://', target):
        return match.group(0)
    path = (HERE / target).resolve().relative_to(HERE.parent).as_posix()
    return f'[{text}]({REPO_URL}/blob/{args.sha or "main"}/{path})'


md = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', pin, md)
body = markdown.markdown(md, extensions=['tables', 'sane_lists'])

# ---- Structure: cover, numbered headings, callouts, sources, table widths ------------------------
m = re.search(r'<h1>(.*?)</h1>\s*<p>(.*?)</p>', body, flags=re.S)
meta = ''.join(f'<div class="m-row"><span class="m-key">{k}</span><span class="m-val">{v.strip()}</span></div>'
               for k, v in re.findall(r'<strong>(.*?):</strong>(.*?)(?:<br />|$)', m.group(2), flags=re.S))
cover = (f'<header class="cover"><div class="kicker">IIT414W AI Workshop · NextLap capstone · '
         f'Universidad del Desarrollo · November 2026</div><h1>{m.group(1)}</h1>'
         f'<div class="subtitle">Predicting the same driver\'s next lap at the end of lap t: one tested input, '
         f'one declared fallback, one frozen model</div><div class="meta">{meta}</div></header>')
body = body[:m.start()] + cover + body[m.end():]

body = re.sub(r'<h2>(\d+)\. (.*?)</h2>', r'<h2><span class="num">\1</span>\2</h2>', body)
body = re.sub(r'<h3>(\d+\.\d+) (.*?)</h3>', r'<h3><span class="num">\1</span>\2</h3>', body)
body = body.replace('<p>Every number below', '<p class="note">Every number below', 1)
CALLOUTS = {'Decision: keep the tested change.': 'teal', 'Final frozen model.': 'navy',
            'Main limitation.': 'amber', 'This was not a blind test.': 'amber',
            'Matched control MAE − candidate MAE (s):': 'result'}
for label, kind in CALLOUTS.items():
    body, k = re.subn(rf'<p><strong>{re.escape(label)}</strong>', f'<p class="callout {kind}"><strong>{label}</strong>', body)
    assert k == 1, label
body = body.replace('<p>Source:', '<p class="source">Source:')

WIDTHS = {  # first header cell -> column widths (%), so long text columns get room
    'Run|Model, inputs and settings': [17, 29, 10, 9, 35],
    'Input|Value at t': [58, 18, 24],
    'Feedback source and priority': [29, 34, 37],
    'What a reviewer needs': [19, 81],
    'Run|Inputs': [5, 23, 9, 8, 8, 9, 24, 14],
    'Population (same pair IDs)': [25, 7, 14, 14, 13, 13, 14],
    'Validation context': [24, 14, 20, 20, 22],
}

FLOW = {'Input|Value at t'}  # may continue on the next page (header repeats) instead of leaving a gap


def widths(match):
    heads = re.findall(r'<th[^>]*>(.*?)</th>', match.group(0))
    for key, cols in WIDTHS.items():
        if '|'.join(heads[:key.count('|') + 1]) == key:
            group = ''.join(f'<col style="width:{w}%">' for w in cols)
            cls = ' class="flow"' if key in FLOW else ''
            return match.group(0).replace('<table>', f'<table{cls}><colgroup>{group}</colgroup>', 1)
    return match.group(0)


body = re.sub(r'<table>.*?</table>', widths, body, flags=re.S)

CSS = """
@page { size: A4; margin: 17mm 16mm 18mm 16mm;
  @bottom-left { content: "NextLap final report · Group 1 · Vicente Rodríguez and Baptiste Vial";
    font-family: Calibri, sans-serif; font-size: 8pt; color: #5B7480; }
  @bottom-right { content: "Page " counter(page) " of " counter(pages);
    font-family: Calibri, sans-serif; font-size: 8pt; color: #5B7480; } }
@page :first { margin-top: 12mm; }
* { box-sizing: border-box; }
body { font-family: Calibri, Arial, sans-serif; font-size: 9.9pt; line-height: 1.38; color: #18303F; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
p { margin: 0 0 6pt; text-align: left; orphans: 3; widows: 3; }
strong { color: #102739; }
a { color: #006E5B; text-decoration: none; }
code { font-family: Consolas, monospace; font-size: 8.6pt; color: #24414F; background: #EEF3F1;
  padding: 0.5px 3px; border-radius: 3px; }

/* cover */
.cover { background: #112A3B; color: #fff; border-radius: 7px; padding: 15pt 18pt 13pt; margin: 0 0 10pt; }
.cover .kicker { font-family: Bahnschrift, Calibri, sans-serif; font-size: 8.3pt; letter-spacing: 1.2px;
  text-transform: uppercase; color: #FFD092; }
.cover h1 { font-family: Bahnschrift, Calibri, sans-serif; font-weight: 600; font-size: 25pt; line-height: 1.1;
  margin: 5pt 0 3pt; color: #fff; }
.cover .subtitle { font-size: 10.6pt; color: #D7EAE2; margin-bottom: 10pt; }
.cover .meta { border-top: 1px solid #3D5B66; padding-top: 7pt; }
.cover .m-row { display: flex; gap: 10pt; font-size: 9.6pt; margin: 1.5pt 0; }
.cover .m-key { width: 112pt; flex: none; color: #9FC3B8; }
.cover .m-val { color: #fff; }
.cover a, .cover a code { color: #FFD092; background: transparent; padding: 0; }

/* key results */
.tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 7pt; margin: 0 0 9pt; break-inside: avoid; }
.tile { border-radius: 6px; padding: 8pt 9pt 8pt; background: #F3F6F4; border-top: 3px solid #006E5B; }
.tile.navy { border-top-color: #112A3B; }
.tile.amber { border-top-color: #C98A1B; }
.t-label { font-family: Bahnschrift, Calibri, sans-serif; font-size: 7.6pt; text-transform: uppercase;
  letter-spacing: 0.8px; color: #3D5B66; }
.t-value { font-family: Bahnschrift, Calibri, sans-serif; font-size: 17pt; font-weight: 600; color: #006E5B;
  margin: 2pt 0 2pt; white-space: nowrap; }
.tile.navy .t-value { color: #112A3B; }
.tile.amber .t-value { color: #A86F0E; }
.t-note { font-size: 8.1pt; line-height: 1.3; color: #3D5B66; }
.note { font-size: 9.2pt; color: #3D5B66; border-left: 2px solid #CCD8D5; padding: 1pt 0 1pt 8pt; margin-bottom: 4pt; }

/* headings */
h2 { font-family: Bahnschrift, Calibri, sans-serif; font-weight: 600; font-size: 15pt; color: #112A3B;
  margin: 14pt 0 7pt; padding-bottom: 4pt; border-bottom: 1.5px solid #006E5B; display: flex; align-items: center; }
h2 .num { display: inline-block; min-width: 19pt; height: 19pt; line-height: 19pt; text-align: center;
  background: #006E5B; color: #fff; border-radius: 4px; font-size: 11pt; margin-right: 8pt; }
h3 { font-family: Bahnschrift, Calibri, sans-serif; font-weight: 600; font-size: 11.4pt; color: #112A3B;
  margin: 12pt 0 5pt; }
h3 .num { color: #006E5B; margin-right: 6pt; }
h2, h3 { break-after: avoid-page; page-break-after: avoid; }

/* callouts */
.callout { background: #F3F6F4; border-left: 3.5px solid #006E5B; border-radius: 0 5px 5px 0;
  padding: 6pt 9pt; margin: 0 0 6pt; break-inside: avoid; }
.callout.navy { border-left-color: #112A3B; background: #EEF1F4; }
.callout.amber { border-left-color: #C98A1B; background: #FBF5EA; }
.callout.result { border-left-color: #006E5B; background: #E6F1EC; font-size: 10.6pt; }

/* tables */
table { border-collapse: collapse; width: 100%; margin: 4pt 0 7pt; font-size: 8.6pt; line-height: 1.3;
  break-inside: avoid; page-break-inside: avoid; table-layout: fixed; }
th { background: #112A3B; color: #fff; text-align: left; font-weight: 600; padding: 4.5pt 5pt; vertical-align: bottom; }
th:first-child { border-top-left-radius: 4px; } th:last-child { border-top-right-radius: 4px; }
td { border-bottom: 0.75px solid #D5E0DC; padding: 3pt 5pt; vertical-align: top; overflow-wrap: anywhere; }
tbody tr:nth-child(even) td { background: #F6F9F7; }
td code { font-size: 8pt; }
th code { background: transparent; color: inherit; }
table.flow { break-inside: auto; page-break-inside: auto; }
tr { break-inside: avoid; }
thead { display: table-header-group; }
.source { font-size: 8.3pt; color: #5B7480; margin: -3pt 0 7pt; }

/* figures */
figure { margin: 4pt auto 10pt; break-inside: avoid; page-break-inside: avoid; }
figure img { width: 100%; border: 0.75px solid #D5E0DC; border-radius: 4px; }
figcaption { font-size: 8pt; line-height: 1.3; color: #5B7480; margin-top: 4pt; text-align: center; }

ul, ol { margin: 0 0 6.5pt; padding-left: 16pt; }
li { margin-bottom: 3.5pt; }
"""
html = f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}</body></html>'

out = Path(args.out).resolve()
with tempfile.TemporaryDirectory() as tmp:
    page = Path(tmp) / 'report.html'
    page.write_text(html, encoding='utf-8')
    subprocess.run([str(EDGE), '--headless', '--disable-gpu', '--no-pdf-header-footer',
                    f'--print-to-pdf={out}', page.as_uri()], check=True, capture_output=True, timeout=120)
assert out.is_file() and out.stat().st_size > 10_000, 'PDF was not written'
print('Wrote', out, '(draft)' if not args.sha else f'at commit {args.sha}')
