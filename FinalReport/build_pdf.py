"""Export FINAL_REPORT.md to the PDF submitted in Canvas.

The commit SHA cannot be written inside the commit it names, so it is inserted here at export
time, and every relative link becomes a GitHub link pinned to that commit. Run from the
repository root after the final commit is pushed:
    python FinalReport/build_pdf.py --sha <full commit SHA> --out <path>.pdf
Without --sha it writes a draft marked "SHA pending". Needs the `markdown` package and
Microsoft Edge (headless print to PDF).
"""
import argparse
import re
import subprocess
import tempfile
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
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
md = re.sub(r'<!--.*?-->\n?', '', md, flags=re.S)  # editing notes are not part of the report


def pin(match):
    """Relative link -> GitHub link at the submitted commit (or at main for a draft)."""
    text, target = match.group(1), match.group(2)
    if re.match(r'[a-z]+://', target):
        return match.group(0)
    path = (HERE / target).resolve().relative_to(HERE.parent).as_posix()
    return f'[{text}]({REPO_URL}/blob/{args.sha or "main"}/{path})'


md = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', pin, md)
body = markdown.markdown(md, extensions=['tables', 'sane_lists'])

CSS = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
body { font-family: Calibri, Arial, sans-serif; font-size: 10.5pt; line-height: 1.38; color: #102739; }
h1 { font-size: 20pt; margin: 0 0 6pt; color: #102739; }
h2 { font-size: 13.5pt; margin: 16pt 0 5pt; padding-bottom: 2pt; border-bottom: 1.5px solid #006E5B; color: #102739; }
h3 { font-size: 11.5pt; margin: 12pt 0 4pt; }
p { margin: 0 0 6pt; }
ul { margin: 0 0 6pt; padding-left: 18pt; }
li { margin-bottom: 3pt; }
a { color: #006E5B; text-decoration: none; }
code { font-family: Consolas, monospace; font-size: 9pt; background: #F1F4F2; padding: 0 2px; border-radius: 2px; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 9pt; font-size: 9.2pt; page-break-inside: avoid; }
th { background: #102739; color: #fff; text-align: left; padding: 4pt 5pt; }
td { border-bottom: 0.75px solid #CCD8D5; padding: 3.5pt 5pt; vertical-align: top; }
td code { font-size: 8.4pt; }
th code { background: transparent; color: inherit; }
h2, h3 { break-after: avoid-page; page-break-after: avoid; }
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
