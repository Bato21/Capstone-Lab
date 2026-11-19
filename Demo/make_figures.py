"""Demo figures (Team 1, 20 Nov): the two slide visuals that cannot be native PowerPoint charts.

Reads only the saved Hito 2 outputs and the released R9 snapshot, so every number on a slide
traces back to Hito2/outputs. The bar charts of the deck are native charts built by
build_deck.js from the same CSV files. Run from the repository root:
    .venv/Scripts/python Demo/make_figures.py
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_H2 = ROOT / 'Hito2' / 'outputs'
FIG = Path(__file__).resolve().parent / 'figures'
FIG.mkdir(exist_ok=True)

# Palette of the official Demo Day template: reference grey, control amber, candidate teal, observed ink.
COL = {'A': '#8A9BA3', 'C': '#C98A1B', 'B': '#006E5B', 'obs': '#102739', 'muted': '#3D5B66',
       'up': '#B5523B', 'down': '#3E9C82'}  # waterfall: pushes the prediction up (slower) / down (faster)
plt.rcParams.update({'font.family': 'Calibri', 'font.size': 15, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.edgecolor': '#3D5B66', 'axes.labelcolor': '#102739',
                     'xtick.color': '#3D5B66', 'ytick.color': '#3D5B66', 'figure.dpi': 200,
                     'figure.facecolor': '#F5F6F3', 'axes.facecolor': '#F5F6F3',
                     'savefig.bbox': 'tight', 'savefig.transparent': False})

preds = pd.read_csv(OUT_H2 / 'validation_predictions.csv').set_index('pair_id')
local = pd.read_csv(OUT_H2 / 'shap_local.csv')

# --- Albon, R9: one incident, two rows ------------------------------------------------
raw = pd.read_csv(ROOT / 'base_NextLap' / 'data' / 'race_2026_r09_laps_v2.csv', dtype={'driver_number': str})
alb = raw[(raw.driver_number == '23') & raw.lap_number.between(3, 10)]
field = raw[raw.lap_number.between(3, 10)].groupby('lap_number').lap_time_s.median()
fig, ax = plt.subplots(figsize=(8.2, 5.0))
ax.plot(field.index, field.values, ':', color=COL['A'], lw=2, label='Field median')
ax.plot(alb.lap_number, alb.lap_time_s, 'o-', color=COL['obs'], lw=2, ms=7, label='Albon, observed')
for pid, lap in [('2026-R9-23-L6', 7), ('2026-R9-23-L7', 8)]:
    ax.scatter(lap - 0.1, preds.loc[pid, 'pred_C_matched_control'], marker='s', s=110, color=COL['C'], zorder=3)
    ax.scatter(lap + 0.1, preds.loc[pid, 'pred_B_candidate'], marker='D', s=110, color=COL['B'], zorder=3)
ax.scatter([], [], marker='s', s=80, color=COL['C'], label='Control C prediction')
ax.scatter([], [], marker='D', s=80, color=COL['B'], label='Candidate B prediction')
ax.annotate('Lap 7: +9 s alone, green flag\nno lap history can see it', (7, 105.128), (3.05, 103.2),
            arrowprops=dict(arrowstyle='->', color=COL['muted']), fontsize=14, color=COL['obs'])
ax.annotate(f"Lap 8: C {preds.loc['2026-R9-23-L7', 'pred_C_matched_control']:.1f} s, "
            f"B {preds.loc['2026-R9-23-L7', 'pred_B_candidate']:.1f} s\nreal 97.9 s", (8.12, 99.2), (8.35, 102.3),
            arrowprops=dict(arrowstyle='->', color=COL['muted']), fontsize=14, color=COL['obs'])
ax.set_xlabel('Lap number, British GP (R9)')
ax.set_ylabel('Lap time (s)')
ax.set_xlim(2.8, 10.6)
ax.legend(frameon=False, fontsize=12, loc='upper center', bbox_to_anchor=(0.5, -0.17), ncol=4,
          handletextpad=0.4, columnspacing=1.2)
fig.savefig(FIG / 'albon_incident.png')
plt.close(fig)

# --- Local SHAP waterfall, candidate B, row 2026-R9-23-L7 -------------------------------
contrib = local[local.input_value.notna()]  # model inputs only; the footer rows carry no input value
base = float(local.loc[local.original_input.str.startswith('BASE VALUE'), 'shap_contribution_s'].iloc[0])
pred = float(local.loc[local.original_input == 'MODEL PREDICTION', 'shap_contribution_s'].iloc[0])
obs = float(local.loc[local.original_input == 'OBSERVED next_lap_s', 'shap_contribution_s'].iloc[0])
steps = list(zip(contrib.original_input.head(3), contrib.shap_contribution_s.head(3)))
steps.append(('5 other inputs', float(contrib.shap_contribution_s.iloc[3:].sum())))
assert abs(base + sum(v for _, v in steps) - pred) < 1e-6  # the chart must add up like the table
fig, ax = plt.subplots(figsize=(7.6, 5.0))
floor, level = 80, base
ax.bar(0, base - floor, bottom=floor, color=COL['A'], width=0.62)
ax.text(0, base + 0.5, f'{base:.2f}', ha='center', fontsize=14)
for k, (name, v) in enumerate(steps, start=1):
    ax.bar(k, v, bottom=level, color=COL['up'] if v > 0 else COL['down'], width=0.62)
    ax.text(k, max(level, level + v) + 0.5, (f'{v:+.2f}' if abs(v) >= 0.01 else f'{v:+.3f}').replace('-', '−'), ha='center', fontsize=14)
    level += v
ax.bar(len(steps) + 1, pred - floor, bottom=floor, color=COL['obs'], width=0.62)
ax.text(len(steps) + 1, pred + 0.5, f'{pred:.2f}', ha='center', fontsize=14, weight='bold')
ax.axhline(obs, color=COL['obs'], ls='--', lw=1.2)
ax.plot([-0.3, 0.25], [108.6, 108.6], '--', color=COL['obs'], lw=1.2)  # key for the dashed line
ax.text(0.35, 108.6, f'observed next lap {obs:.2f} s', va='center', fontsize=13, color=COL['obs'])
labels = ['Base', 'recent_mean_s', 'current_lap_s', 'recent_std_s', '5 others', 'Prediction']
ax.set_xticks(range(len(labels)), labels, fontsize=12, rotation=18, ha='right')
ax.set_ylim(floor, 111)
ax.set_ylabel('Predicted next lap (s)')
fig.savefig(FIG / 'shap_waterfall.png')
plt.close(fig)

print('Figures written to', FIG)

# --- Numbers for the native charts and text of the deck (read by build_deck.js) ------------
import json  # noqa: E402

metrics = pd.read_csv(OUT_H2 / 'comparison_metrics.csv').set_index(['run', 'population']).MAE_s
slices = pd.read_csv(OUT_H2 / 'slices.csv')
history = slices[slices.slice == 'history'].set_index('group')
conc = pd.read_csv(OUT_H2 / 'gain_concentration.csv').set_index('top_k_rows_by_gain')
glob = pd.read_csv(OUT_H2 / 'shap_global.csv')
glob_all = glob[glob['sample'] == 'all_validation'].set_index('original_input').mean_abs_shap_s
runs = {'A': 'A_OLS_reference', 'B': 'B_candidate', 'C': 'C_matched_control', 'D': 'D_followup_no_indicator'}
pops = ['all_validation', 'R8', 'R9']
data = {
    'source': 'Hito2/outputs (commit tagged Hito2)',
    'mae': {k: {p: round(float(metrics[r, p]), 5) for p in pops} for k, r in runs.items()},
    'c_minus_b': {p: round(float(metrics[runs['C'], p] - metrics[runs['B'], p]), 5) for p in pops},
    'concentration': {str(k): round(float(conc.loc[k, 'C_minus_B_without_top_k_s']), 4) for k in [0, 10, 50, 100]},
    'top50_share': round(float(conc.loc[50, 'share_of_total_gain']), 3),
    'history': {g: {k: round(float(history.loc[g, c]), 3) for k, c in
                    [('A', 'reference_MAE_s'), ('C', 'control_MAE_s'), ('B', 'candidate_MAE_s'), ('D', 'followup_D_MAE_s')]}
                for g in ['full (2-3 clean laps)', 'short (1 clean lap)']},
    'window_example': [{'lap': int(r.lap_number), 'time': float(r.lap_time_s), 'clean': bool(r.clean_at_own_end),
                        'in_window': bool(r['in_window_laps_t-2..t']), 'used': bool(r.used_by_recent_std_s),
                        'role': r.role if isinstance(r.role, str) else ''}
                       for _, r in pd.read_csv(OUT_H2 / 'history_convention_example.csv').iterrows()],
    'shap_global_mean_abs': {k: round(float(glob_all[k]), 3) for k in ['recent_mean_s', 'current_lap_s', 'recent_std_s']},
}
(FIG / 'deck_data.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
print(json.dumps(data, indent=1))
