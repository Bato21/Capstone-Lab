"""Final report · Team 1 · Priority revision after the Hito 2 feedback: trial E.

Trial E (rule written in FinalReport/DECISION_LOG.md before this script existed):
    rows with short_history = 1 (fewer than two clean laps in the window, so recent_std_s is
    undefined) use the frozen reference prediction A; every other row keeps candidate B.
Both A and B are the models fitted at the commit tagged `Hito2` (OLS via make_model, train
rounds 1-7, seed 414). Nothing is refitted or tuned here: E is assembled row by row from the
saved Hito 2 predictions, and the switch uses only short_history, which is known at the end of lap t.

Pass rule (the rule of follow-up D, unchanged, control = frozen reference A):
    MAE(E) on the short-history rows <= 0.401 s
    AND A - E >= 0.01 s overall AND A - E >= 0 in R8 and in R9.
Also reported without a threshold: B - E (the isolated effect of the fallback, since E differs
from B only on the short-history rows), overall, per race and on the short-history rows of each race.

Usage (from the repository root, Hito 2 environment):
    python FinalReport/run_final.py
Reads Hito2/outputs/ and Hito1/outputs/ only; needs no data and no randomness.
No reserved final-evaluation data are accessed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

SHORT_TARGET_S = 0.401  # trial D's target on the short-history rows, reused unchanged
THRESHOLD_S = 0.01      # Hito 1 / trial D threshold, reused unchanged
ROOT = Path(__file__).resolve().parent.parent
H2 = ROOT / 'Hito2' / 'outputs'
OUT = Path(__file__).resolve().parent / 'outputs'
OUT.mkdir(exist_ok=True)


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_rows(ids):
    return hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest()


def mae(err):
    return float(np.mean(np.abs(err)))


# =============================================================================
# 1. Frozen Hito 2 predictions, same rows as Hito 1 and Hito 2
# =============================================================================
pred = pd.read_csv(H2 / 'validation_predictions.csv', dtype={'driver_number': str})
assert len(pred) == 1808 and pred.pair_id.is_unique
assert set(pred['round']) == {8, 9}
h1_hash = json.loads((ROOT / 'Hito1' / 'outputs' / 'reference_run.json').read_text())['validation_pair_id_sha256']
val_hash = sha256_rows(pred.pair_id)
assert val_hash == h1_hash, 'validation pair_ids differ from Hito 1'

# Frozen reference A must still equal the saved Hito 1 OLS predictions row by row.
h1 = pred[['pair_id']].merge(pd.read_csv(ROOT / 'Hito1' / 'outputs' / 'validation_reference_predictions.csv'),
                             on='pair_id', how='left', validate='1:1')
max_dev_A = float(np.abs(h1.OLS_reference.to_numpy() - pred.pred_A_OLS_reference.to_numpy()).max())
assert max_dev_A < 1e-6, max_dev_A

# short_history is the train-time rule "fewer than 2 clean laps in the window", known at t.
assert pred.short_history.isin([0, 1]).all()
assert (pred.short_history.eq(1) == pred.recent_std_s.isna()).all()
assert (pred.short_history.eq(1) == pred.recent_count.lt(2)).all()

# =============================================================================
# 2. Trial E: frozen reference A on short-history rows, candidate B elsewhere
# =============================================================================
short = pred.short_history.eq(1).to_numpy()
pred['pred_E_short_history_fallback'] = np.where(short, pred.pred_A_OLS_reference, pred.pred_B_candidate)
pred['E_source'] = np.where(short, 'A (fallback)', 'B')
y = pred.y_true_next_lap_s.to_numpy()
P = {'A': pred.pred_A_OLS_reference.to_numpy(), 'B': pred.pred_B_candidate.to_numpy(),
     'E': pred.pred_E_short_history_fallback.to_numpy()}
assert np.isfinite(P['E']).all()
for k in P:
    pred[f'abs_err_{k}'] = np.abs(y - P[k])

rounds = pred['round'].to_numpy()
POPS = [('all_validation', np.ones(len(pred), bool)), ('R8', rounds == 8), ('R9', rounds == 9),
        ('short_history', short), ('short_history R8', short & (rounds == 8)),
        ('short_history R9', short & (rounds == 9)), ('full_history', ~short)]
rows = []
for label, m in POPS:
    a, b, e = (mae(y[m] - P[k][m]) for k in 'ABE')
    rows.append({'population': label, 'n': int(m.sum()), 'A_reference_MAE_s': a, 'B_candidate_MAE_s': b,
                 'E_fallback_MAE_s': e, 'A_minus_E_s': a - e, 'B_minus_E_s': b - e})
table = pd.DataFrame(rows)
T = table.set_index('population')

# Consistency: the pooled values equal the n-weighted race values, and E equals B on full-history rows.
for c in ['A_reference_MAE_s', 'B_candidate_MAE_s', 'E_fallback_MAE_s']:
    pooled = (T.loc['R8', c] * T.loc['R8', 'n'] + T.loc['R9', c] * T.loc['R9', 'n']) / T.loc['all_validation', 'n']
    assert abs(pooled - T.loc['all_validation', c]) < 1e-12, c
assert T.loc['full_history', 'B_minus_E_s'] == 0
assert abs(T.loc['short_history', 'E_fallback_MAE_s'] - T.loc['short_history', 'A_reference_MAE_s']) < 1e-12
# The Hito 2 saved metrics are reproduced from the saved predictions.
h2m = pd.read_csv(H2 / 'comparison_metrics.csv').set_index(['run', 'population']).MAE_s
for run, k in [('A_OLS_reference', 'A'), ('B_candidate', 'B')]:
    for pop in ['all_validation', 'R8', 'R9']:
        assert abs(h2m[run, pop] - T.loc[pop, f'{k}_{"reference" if k == "A" else "candidate"}_MAE_s']) < 1e-9

table.to_csv(OUT / 'trial_E_table.csv', index=False)

# Supplementary stint bootstrap, identical to Hito 2 (driver-race stints, 2,000 replicates, seed 414).
# It describes the spread within these two races only and is not part of the pass rule.
feat = pd.read_csv(H2 / 'features_recent_std.csv', dtype={'driver_number': str}).query('split == "validation"')
stint = pred[['pair_id']].merge(feat[['pair_id', 'stint']], on='pair_id', how='left', validate='1:1').stint
cluster = (pred['round'].astype(str) + '-' + pred.driver_number + '-' + stint.astype(str)).to_numpy()
ids, inv = np.unique(cluster, return_inverse=True)


def cluster_bootstrap(control, candidate):
    rng = np.random.default_rng(414)  # same resamples as every Hito 2 comparison
    sums = [np.bincount(inv, w, len(ids)) for w in [np.abs(y - P[control]), np.abs(y - P[candidate]), np.ones(len(y))]]
    boot = np.empty(2000)
    for k in range(2000):
        pick = np.bincount(rng.integers(0, len(ids), len(ids)), minlength=len(ids))
        boot[k] = (pick @ sums[0] - pick @ sums[1]) / (pick @ sums[2])
    return {'comparison': f'{control} - {candidate}', 'clusters (driver-race stints)': int(len(ids)),
            'replicates': 2000, 'seed': 414, 'point_s': mae(y - P[control]) - mae(y - P[candidate]),
            'p2.5_s': float(np.percentile(boot, 2.5)), 'p97.5_s': float(np.percentile(boot, 97.5)),
            'share_positive': float((boot > 0).mean())}


boots = pd.DataFrame([cluster_bootstrap('A', 'E'), cluster_bootstrap('B', 'E'), cluster_bootstrap('A', 'B')])
# The A - B row must reproduce the saved Hito 2 bootstrap exactly (same stints, same resamples).
h2b = pd.read_csv(H2 / 'bootstrap.csv').set_index('comparison').loc['A_OLS_reference - B_candidate']
assert len(ids) == h2b['clusters (driver-race stints)']
assert np.allclose(boots.iloc[2][['p2.5_s', 'p97.5_s']].astype(float), h2b[['p2.5_s', 'p97.5_s']].astype(float), atol=1e-12)
boots.to_csv(OUT / 'trial_E_bootstrap.csv', index=False)
pred[['pair_id', 'round', 'driver_number', 'current_lap_number', 'recent_count', 'short_history',
      'y_true_next_lap_s', 'pred_A_OLS_reference', 'pred_B_candidate', 'pred_E_short_history_fallback',
      'E_source', 'abs_err_A', 'abs_err_B', 'abs_err_E']].to_csv(OUT / 'validation_predictions_E.csv', index=False)

# =============================================================================
# 3. The pre-declared rule, applied mechanically
# =============================================================================
c_short = T.loc['short_history', 'E_fallback_MAE_s'] <= SHORT_TARGET_S
c_all = T.loc['all_validation', 'A_minus_E_s'] >= THRESHOLD_S
c_r8 = T.loc['R8', 'A_minus_E_s'] >= 0
c_r9 = T.loc['R9', 'A_minus_E_s'] >= 0
passed = bool(c_short and c_all and c_r8 and c_r9)
checks = pd.DataFrame([
    {'condition': 'MAE(E) on short-history rows <= 0.401 s', 'n': int(T.loc['short_history', 'n']),
     'observed': f"{T.loc['short_history', 'E_fallback_MAE_s']:.5f} s", 'passed': bool(c_short)},
    {'condition': 'A - E >= 0.01 s overall', 'n': int(T.loc['all_validation', 'n']),
     'observed': f"{T.loc['all_validation', 'A_minus_E_s']:+.5f} s", 'passed': bool(c_all)},
    {'condition': 'A - E >= 0 in R8', 'n': int(T.loc['R8', 'n']),
     'observed': f"{T.loc['R8', 'A_minus_E_s']:+.5f} s", 'passed': bool(c_r8)},
    {'condition': 'A - E >= 0 in R9', 'n': int(T.loc['R9', 'n']),
     'observed': f"{T.loc['R9', 'A_minus_E_s']:+.5f} s", 'passed': bool(c_r9)},
    {'condition': 'TRIAL E (all four conditions)', 'n': int(T.loc['all_validation', 'n']),
     'observed': 'PASS -> E is frozen as the final model' if passed else 'FAIL -> B stays frozen',
     'passed': passed},
    {'condition': 'same 1,808 validation pair_ids as Hito 1 (SHA-256)', 'n': len(pred),
     'observed': f'{val_hash[:12]}... equals Hito 1; A equals Hito 1 predictions (max |diff| {max_dev_A:.1e} s)',
     'passed': True},
])
checks.to_csv(OUT / 'trial_E_checks.csv', index=False)

# =============================================================================
# 4. Trial log: every configuration tried, on the same rows (A-D from Hito 2, E from above)
# =============================================================================
sl = pd.read_csv(H2 / 'slices.csv').set_index(['slice', 'group']).loc[('history', 'short (1 clean lap)')]
assert int(sl.n) == int(short.sum())
assert abs(sl.reference_MAE_s - T.loc['short_history', 'A_reference_MAE_s']) < 1e-12
assert abs(sl.candidate_MAE_s - T.loc['short_history', 'B_candidate_MAE_s']) < 1e-12
short_mae = {'A_OLS_reference': sl.reference_MAE_s, 'B_candidate': sl.candidate_MAE_s,
             'C_matched_control': sl.control_MAE_s, 'D_followup_no_indicator': sl.followup_D_MAE_s}
LOG = [  # run, inputs, rule it was judged by, outcome (rules quoted from the decision logs)
    ('A_OLS_reference', 'six reference inputs', 'fixed reference', 'reference for every comparison'),
    ('B_candidate', 'six + recent_std_s + short_history', 'Hito 1: C - B >= 0.01 s overall, >= 0 per race',
     'supported; kept'),
    ('C_matched_control', 'six + short_history', 'matched control of B', 'control; slightly worse than A'),
    ('D_followup_no_indicator', 'six + recent_std_s (median fill, no indicator)',
     'Hito 2: short MAE <= 0.401 s, A - D >= 0.01 s overall, >= 0 per race', 'failed (short MAE); B kept'),
    ('E_short_history_fallback', 'B; frozen A on short_history rows', 'final: trial D rule, unchanged',
     'passed; frozen final model' if passed else 'failed; B kept'),
]
log_rows = []
for run, inputs, rule, outcome in LOG:
    if run == 'E_short_history_fallback':
        vals = [T.loc[p, 'E_fallback_MAE_s'] for p in ['all_validation', 'R8', 'R9', 'short_history']]
    else:
        vals = [h2m[run, p] for p in ['all_validation', 'R8', 'R9']] + [short_mae[run]]
    log_rows.append({'run': run, 'inputs': inputs, 'MAE_all_s (n=1808)': vals[0], 'MAE_R8_s (n=1066)': vals[1],
                     'MAE_R9_s (n=742)': vals[2], 'MAE_short_history_s (n=148)': vals[3],
                     'gain_vs_A_s': h2m['A_OLS_reference', 'all_validation'] - vals[0], 'rule': rule,
                     'outcome': outcome})
pd.DataFrame(log_rows).to_csv(OUT / 'trial_log.csv', index=False)

manifest = {
    'script': 'FinalReport/run_final.py',
    'inputs_sha256': {str(p.relative_to(ROOT)).replace('\\', '/'): sha256_file(p) for p in [
        H2 / 'validation_predictions.csv', H2 / 'comparison_metrics.csv',
        ROOT / 'Hito1' / 'outputs' / 'validation_reference_predictions.csv',
        ROOT / 'Hito1' / 'outputs' / 'reference_run.json']},
    'validation_pair_id_sha256': val_hash,
    'short_history_rows': int(short.sum()),
    'trial_E_passed': passed,
    'frozen_final_model': 'E (B with short-history fallback to A)' if passed else 'B (candidate)',
}
(OUT / 'run_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')

pd.set_option('display.width', 200)
print(table.round(5).to_string(index=False))
print(checks.to_string(index=False))
print(boots.to_string(index=False))
