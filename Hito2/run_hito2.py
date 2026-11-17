"""Hito 2 · Team 1 · Executed comparison, ablation, errors by context and SHAP.

Hypothesis (Hito 1, unchanged): recent pace variability `recent_std_s` adds information
beyond the six reference inputs.

Runs, all OLS via the supplied `make_model`, fitted on training rounds 1-7 only and scored
on the same 1,808 validation pair_ids (rounds 8-9):
    A  OLS reference      six published inputs                              (Hito 1 run, re-executed)
    B  candidate          six inputs + recent_std_s + short_history
    C  matched control    six inputs + short_history   (B with recent_std_s removed)
The contribution of recent_std_s is read from C - B (control MAE minus candidate MAE).

Follow-up (post-hoc next check, declared in DECISION_LOG.md before it was run):
    D  follow-up          six inputs + recent_std_s, no short_history indicator
       Its matched control is A itself (same OLS setup without the change, shared run).
D was added after the slice table of the primary run showed the short-history rows getting
worse. It does not change the pre-declared B vs C decision.

Checks 1-5 were written in Hito 1 (HITO1.md section 4) before this code existed; the
observed results are saved to outputs/checks.csv.

Usage (from this folder):
    python run_hito2.py                            # expects ../base_NextLap
    python run_hito2.py --base PATH/TO/base_NextLap
No reserved final-evaluation data are accessed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # headless: plots are written to files only
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import sklearn
from sklearn.metrics import mean_absolute_error

from features import (MIN_CLEAN_LAPS, WINDOW, as_of_recompute, current_clean, history_features,
                      last_clean_laps_std)

RANDOM_SEED = 414
THRESHOLD_S = 0.01   # Hito 1 support rule: C - B >= 0.01 s overall and no race worse
N_BOOT = 2000        # supplementary cluster bootstrap, not part of the pre-declared decision
HERE = Path(__file__).resolve().parent

parser = argparse.ArgumentParser()
parser.add_argument('--base', default=str(HERE.parent / 'base_NextLap'),
                    help='Folder of the released base_NextLap data (default: ../base_NextLap)')
args = parser.parse_args()
BASE = Path(args.base).resolve()
if not (BASE / 'nextlap_reference_v1.py').is_file():
    sys.exit(f'base_NextLap not found at {BASE}. See README.md, section "Data".')

sys.path.insert(0, str(BASE))
from nextlap_reference_v1 import (CATEGORICAL, NUMERIC, TARGET, load_snapshots,  # noqa: E402
                                  make_model)

np.random.seed(RANDOM_SEED)
OUT = HERE / 'outputs'
OUT.mkdir(exist_ok=True)
checks = []  # one row per pre-declared check: what we expected, what we observed, pass/fail


def check(name, defined_in, expected, observed, passed):
    checks.append({'check': name, 'defined_in': defined_in, 'expected': expected,
                   'observed': observed, 'passed': bool(passed)})
    print(f"[{'PASS' if passed else 'FAIL'}] {name}: {observed}")


def sha256_rows(ids):
    return hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest()


def mae(y, p):
    return float(mean_absolute_error(y, p))


# =============================================================================
# 1. Data: released clean pairs + original timing snapshots
# =============================================================================
EXPECTED_SHA256 = {  # released files of IIT414W_Capstone_NextLap_StudentData_v1 (same as Hito 1)
    'train_clean_v1.csv': '43544f38cc9ef32b44886e6751e03522601265160086fe3a4956f04b87bd5c13',
    'validation_clean_v1.csv': 'b19efb6a908af12a5d2c6bdde29aa40984295e62ce0f187a201b579278db7ee8',
    'nextlap_reference_v1.py': 'f6c58925cd4a477bf3e1a5a2b3968e67df3a1cffabecee9e89701c3ac2d5f994',
}
for fname, digest in EXPECTED_SHA256.items():
    assert hashlib.sha256((BASE / fname).read_bytes()).hexdigest() == digest, f'{fname} differs from the release'

train = pd.read_csv(BASE / 'train_clean_v1.csv', dtype={'driver_number': str})
val = pd.read_csv(BASE / 'validation_clean_v1.csv', dtype={'driver_number': str})
raw, manifest = load_snapshots(BASE)  # verifies every snapshot SHA-256 against the manifest

assert len(train) == 5772 and len(val) == 1808, (len(train), len(val))
assert set(train['round']) == set(range(1, 8)) and set(val['round']) == {8, 9}
assert train.pair_id.is_unique and val.pair_id.is_unique
assert not set(train.pair_id) & set(val.pair_id), 'pair_id overlap between train and validation'
assert train.clean_pair.all() and val.clean_pair.all()
check('race split', 'Hito 2 brief / C1',
      'train rounds 1-7 (5,772), validation rounds 8-9 (1,808), disjoint pair_ids',
      f"train rounds {sorted(train['round'].unique().tolist())} n={len(train)}; "
      f"validation rounds {sorted(val['round'].unique().tolist())} n={len(val)} "
      f"(R8={int(val['round'].eq(8).sum())}, R9={int(val['round'].eq(9).sum())}); overlap=0", True)

# =============================================================================
# 2. Feature construction on the original timeline, then join by pair_id
# =============================================================================
gaps = raw.sort_values(['season', 'round', 'driver_number', 'lap_number']).groupby(
    ['season', 'round', 'driver_number', 'stint']).lap_number.diff()
assert not (gaps > 1).any(), 'lap-number gap inside a stint: rolling rows != rolling laps'

hist = history_features(raw)
assert hist.pair_id.is_unique


def attach(frame, label):
    """Left join on pair_id; every released pair must find exactly one history row."""
    joined = frame.merge(hist.drop(columns=['season', 'round', 'driver_number', 'stint', 'end_time_s']),
                         on='pair_id', how='left', validate='1:1', indicator=True)
    assert len(joined) == len(frame) and joined['_merge'].eq('both').all(), f'{label}: join gap'
    # The released recent_mean_s / recent_count were built by the instructor's build_pairs.
    # Recomputing them with our window and matching exactly proves we use the same timeline,
    # grouping and window as the reference input.
    assert np.allclose(joined.recent_mean_s, joined.recent_mean_check_s, atol=1e-9, rtol=0), label
    assert joined.recent_count.eq(joined.recent_count_check).all(), label
    assert joined.lap_number.eq(joined.current_lap_number).all(), label
    return joined.drop(columns=['_merge'])


train, val = attach(train, 'train'), attach(val, 'validation')
check('join coverage', 'Hito 2 brief / C1',
      'every released pair joins exactly one history row; recent_mean_s and recent_count rebuilt exactly',
      f'train {len(train)}/5772, validation {len(val)}/1808 joined 1:1; '
      'max |recent_mean_s - rebuilt| <= 1e-9 and recent_count identical', True)

# --- Check 1 (Hito 1): availability at t ---------------------------------------
both = pd.concat([train.assign(split='train'), val.assign(split='validation')], ignore_index=True)
used = both.last_end_time_used_s.notna()
ok_time = (both.loc[used, 'last_end_time_used_s'] <= both.loc[used, 'end_time_s']).all()
ok_lap = (both.loc[used, 'last_lap_used'] <= both.loc[used, 'current_lap_number']).all()
ok_window = (both.first_lap_in_window >= both.current_lap_number - (WINDOW - 1)).all()
as_of = as_of_recompute(raw, both)
same_nan = both.recent_std_s.isna().eq(as_of.isna()).all()
same_val = np.allclose(both.recent_std_s.dropna(), as_of.dropna(), atol=1e-9, rtol=0)
lag = both.loc[used, 'end_time_s'] - both.loc[used, 'last_end_time_used_s']
check('1. availability at t', 'HITO1.md section 4, check 1 (extended from a sample to all rows)',
      "last lap used has end_time_s <= row end_time_s; window stays in the row's stint; "
      'value equals an as-of recomputation that only sees laps ended by t',
      f'{len(both)} rows: last used end_time <= row end_time: {ok_time}; last lap used <= t: {ok_lap}; '
      f'window within laps t-2..t of the same stint: {ok_window}; as-of recomputation identical '
      f'(missing pattern {same_nan}, values {same_val}); lap t itself is the last lap used in '
      f'{int((lag == 0).sum())}/{int(used.sum())} rows',
      ok_time and ok_lap and ok_window and same_nan and same_val)
assert ok_time and ok_lap and ok_window and same_nan and same_val

feat_cols = ['pair_id', 'round', 'driver_number', 'stint', 'current_lap_number', 'end_time_s',
             'recent_count', 'recent_std_s', 'short_history', 'first_lap_in_window',
             'last_lap_used', 'last_end_time_used_s']
both[['split'] + feat_cols].assign(recent_std_as_of=as_of.values).to_csv(
    OUT / 'features_recent_std.csv', index=False)

# --- History convention (Hito 1 feedback, C3.1) ------------------------------------
# Our convention: last 3 laps of the stint, non-clean laps left out (= recent_mean_s window).
# Alternative: last 3 clean laps, reaching back past a non-clean lap. Not used by any model;
# we only count where the two disagree and save one worked history chosen by a fixed rule.
alt = both[['split', 'pair_id', 'recent_count', 'recent_std_s']].merge(
    last_clean_laps_std(raw), on='pair_id', how='left', validate='1:1')
agree = ((alt.recent_std_s.isna() & alt.last3clean_std_s.isna())
         | np.isclose(alt.recent_std_s, alt.last3clean_std_s, atol=1e-9, rtol=0))
alt['conventions_differ'] = ~agree
convention = alt.groupby('split', sort=False).agg(
    rows=('pair_id', 'size'), rows_where_conventions_differ=('conventions_differ', 'sum'),
    short_history_rows=('recent_std_s', lambda s: int(s.isna().sum())),
    short_rows_with_value_under_alternative=(
        'recent_std_s', lambda s: int((s.isna() & alt.loc[s.index, 'last3clean_std_s'].notna()).sum())))
convention['share_differ'] = convention.rows_where_conventions_differ / convention.rows
convention.reset_index().to_csv(OUT / 'history_convention.csv', index=False)

# Worked example, fixed rule: first validation pair (release order) whose window holds exactly
# one non-clean lap and where the alternative would reach back to a third clean lap.
ex_id = alt[(alt.split == 'validation') & alt.recent_count.eq(2) & alt.conventions_differ
            & alt.last3clean_n.eq(3)].pair_id.iloc[0]
ex = val.loc[val.pair_id == ex_id].iloc[0]
laps = raw[(raw['round'] == ex['round']) & (raw.driver_number.astype(str) == str(ex.driver_number))
           & (raw.stint == ex.stint) & raw.lap_number.between(ex.current_lap_number - 5, ex.current_lap_number + 1)
           ].sort_values('lap_number').copy()
clean = current_clean(laps)
reasons = {'lap 1': laps.lap_number.le(1), 'no lap time': ~laps.lap_time_s.gt(0), 'pit_in': laps.pit_in,
           'pit_out': laps.pit_out, 'deleted': laps.deleted, 'not accurate': ~laps.is_accurate.astype(bool), 'track_status != 1': laps.track_status.ne('1')}
laps['clean_at_own_end'] = clean
laps['why_not_clean'] = [', '.join(r for r, m in reasons.items() if m.loc[i]) if not clean.loc[i] else ''
                         for i in laps.index]
t = ex.current_lap_number
laps['in_window_laps_t-2..t'] = laps.lap_number.between(t - 2, t)
laps['used_by_recent_std_s'] = laps['in_window_laps_t-2..t'] & clean
alt_laps = laps[clean & laps.lap_number.le(t)].lap_number.tail(WINDOW)
laps['used_by_last_3_clean_laps'] = laps.lap_number.isin(alt_laps)
laps['role'] = np.select([laps.lap_number.eq(t + 1), laps.lap_number.eq(t)], ['t+1 (target, never used)', 't'], '')
ours = float(np.std(laps.loc[laps.used_by_recent_std_s, 'lap_time_s'], ddof=1))
theirs = float(np.std(laps.loc[laps.used_by_last_3_clean_laps, 'lap_time_s'], ddof=1))
assert np.isclose(ours, ex.recent_std_s) and np.isclose(theirs, alt.set_index('pair_id').at[ex_id, 'last3clean_std_s'])
laps.insert(0, 'example_pair_id', ex_id)
laps[['lap_number', 'stint']] = laps[['lap_number', 'stint']].astype(int)
laps[['example_pair_id', 'lap_number', 'role', 'lap_time_s', 'end_time_s', 'stint', 'track_status',
      'is_accurate', 'pit_in', 'pit_out', 'deleted', 'clean_at_own_end', 'why_not_clean',
      'in_window_laps_t-2..t', 'used_by_recent_std_s', 'used_by_last_3_clean_laps']].to_csv(
    OUT / 'history_convention_example.csv', index=False)
v_conv = convention.loc['validation']
check('history convention', 'Hito 1 feedback C3.1 / HITO1.md section 3',
      'recent_std_s uses the recent_mean_s window (last 3 laps of the stint, non-clean laps left out)',
      f'window equals the rebuilt recent_mean_s / recent_count window on every row; the "last 3 clean laps" '
      f'reading would differ on {int(v_conv.rows_where_conventions_differ)}/{int(v_conv.rows)} validation rows; '
      f'worked example {ex_id}: ours {ours:.4f} s from 2 clean laps, alternative {theirs:.4f} s from 3', True)

# =============================================================================
# 3. Fit A, B, C on training rows only; predict the same validation rows
# =============================================================================
RUNS = {  # name -> (role, numeric inputs); categoricals and family are identical everywhere
    'A_OLS_reference': ('OLS reference', NUMERIC),
    'B_candidate': ('candidate', NUMERIC + ['recent_std_s', 'short_history']),
    'C_matched_control': ('matched control', NUMERIC + ['short_history']),
    'D_followup_no_indicator': ('follow-up candidate (control = A)', NUMERIC + ['recent_std_s']),
}
models, preds = {}, {}
for name, (_, numeric) in RUNS.items():
    cols = numeric + CATEGORICAL
    assert TARGET not in cols and 'clean_pair' not in cols
    assert not any(c.startswith('next_') for c in cols), 'future-known column used as input'
    # Imputer, scaler and one-hot are inside the Pipeline: .fit sees training rows only,
    # validation is only transformed. Nothing is fitted on validation.
    models[name] = make_model('OLS', numeric=numeric, categorical=CATEGORICAL).fit(train[cols], train[TARGET])
    preds[name] = models[name].predict(val[cols])
    assert len(preds[name]) == len(val) and np.isfinite(preds[name]).all(), name

# Hito 1 reference code re-executed: A must equal the saved Hito 1 predictions row by row.
h1 = pd.read_csv(HERE.parent / 'Hito1' / 'outputs' / 'validation_reference_predictions.csv')
h1 = val[['pair_id']].merge(h1, on='pair_id', how='left', validate='1:1')
assert h1.OLS_reference.notna().all()
max_dev = float(np.abs(h1.OLS_reference.to_numpy() - preds['A_OLS_reference']).max())
assert max_dev < 1e-6, max_dev
h1_hash = json.loads((HERE.parent / 'Hito1' / 'outputs' / 'reference_run.json').read_text())['validation_pair_id_sha256']

# --- Check 2 (Hito 1): same rows ---------------------------------------------------
val_hash = sha256_rows(val.pair_id)
check('2. same validation rows', 'HITO1.md section 4, check 2',
      'every run (A-D) predicts exactly the 1,808 validation pair_ids; SHA-256 unchanged from Hito 1; no drops',
      f'1 finite prediction per pair_id for each run; SHA-256 {val_hash[:12]}... equals Hito 1: '
      f'{val_hash == h1_hash}; A equals saved Hito 1 OLS predictions (max |diff| {max_dev:.1e} s)',
      val_hash == h1_hash and val.pair_id.is_unique)

# Coverage of the new input and the train-fitted fill value actually used by B.
imputer = models['B_candidate'].named_steps['prepare'].named_transformers_['numeric'].named_steps['fill']
fill_value = float(imputer.statistics_[RUNS['B_candidate'][1].index('recent_std_s')])
coverage = pd.DataFrame([{'split': s, 'rows': len(f), 'recent_std_observed': int(f.recent_std_s.notna().sum()),
                          'recent_std_missing_short_history': int(f.recent_std_s.isna().sum()),
                          'coverage_pct': 100 * f.recent_std_s.notna().mean(),
                          'fill_value_s (train median)': fill_value}
                         for s, f in [('train', train), ('validation', val)]])
assert (train.recent_std_s.isna() == train.short_history.eq(1)).all()
assert (val.recent_std_s.isna() == val.short_history.eq(1)).all()
coverage.to_csv(OUT / 'coverage.csv', index=False)

# --- Check 3 (Hito 1): prior signal on training rows only ---------------------------
train_abs_res = np.abs(train[TARGET] - models['A_OLS_reference'].predict(train[NUMERIC + CATEGORICAL]))
has_std = train.recent_std_s.notna()
rho = float(pd.Series(train.loc[has_std, 'recent_std_s']).corr(
    pd.Series(train_abs_res[has_std]), method='spearman'))
check('3. prior signal (training rows only)', 'HITO1.md section 4, check 3',
      'Spearman correlation of recent_std_s with |OLS reference residual| on training rows > 0',
      f'Spearman rho = {rho:.3f} on {int(has_std.sum())} training rows with observed recent_std_s', rho > 0)

# =============================================================================
# 4. Metric comparison (pooled and by race)
# =============================================================================
y = val[TARGET].to_numpy()
rounds = val['round'].to_numpy()
rows = []
for name, (role, numeric) in RUNS.items():
    for label, mask in [('all_validation', np.ones(len(val), bool)), ('R8', rounds == 8), ('R9', rounds == 9)]:
        rows.append({'run': name, 'role': role, 'inputs': '+'.join(numeric + CATEGORICAL),
                     'population': label, 'n': int(mask.sum()), 'MAE_s': mae(y[mask], preds[name][mask])})
metrics = pd.DataFrame(rows)
metrics.to_csv(OUT / 'comparison_metrics.csv', index=False)
M = metrics.set_index(['run', 'population']).MAE_s

race = []
for label in ['R8', 'R9']:
    n = int(metrics.query('run == "B_candidate" and population == @label').n.iloc[0])
    race.append({'race': label, 'n': n, 'control_MAE_s': M['C_matched_control', label],
                 'candidate_MAE_s': M['B_candidate', label],
                 'control_minus_candidate_s': M['C_matched_control', label] - M['B_candidate', label],
                 'reference_MAE_s': M['A_OLS_reference', label]})
race = pd.DataFrame(race)
# Pooled values recomputed from race-level MAEs weighted by row counts must equal the direct MAE.
pooled = {c: float((race[c] * race.n).sum() / race.n.sum())
          for c in ['control_MAE_s', 'candidate_MAE_s', 'control_minus_candidate_s', 'reference_MAE_s']}
assert abs(pooled['candidate_MAE_s'] - M['B_candidate', 'all_validation']) < 1e-12
assert abs(pooled['control_MAE_s'] - M['C_matched_control', 'all_validation']) < 1e-12
race = pd.concat([race, pd.DataFrame([{'race': 'pooled (n-weighted)', 'n': int(race.n.sum()), **pooled}])],
                 ignore_index=True)
race.to_csv(OUT / 'race_table.csv', index=False)

diff_all = M['C_matched_control', 'all_validation'] - M['B_candidate', 'all_validation']
diff_r8, diff_r9 = race.control_minus_candidate_s.iloc[0], race.control_minus_candidate_s.iloc[1]
supported = diff_all >= THRESHOLD_S and diff_r8 >= 0 and diff_r9 >= 0
check('4. support rule', 'HITO1.md section 4, check 4',
      f'C - B >= {THRESHOLD_S} s overall AND C - B >= 0 in R8 and in R9 (else: does not meet the predeclared improvement criterion)',
      f'C - B = {diff_all:+.5f} s overall (R8 {diff_r8:+.5f}, R9 {diff_r9:+.5f}) -> '
      f"{'SUPPORTED' if supported else 'NOT SUPPORTED'}", supported)

# Prediction table with row identities (the evidence for every MAE above).
pred_table = pd.DataFrame({
    'pair_id': val.pair_id, 'round': val['round'], 'driver_number': val.driver_number,
    'current_lap_number': val.current_lap_number, 'current_compound': val.current_compound,
    'recent_count': val.recent_count, 'recent_std_s': val.recent_std_s, 'short_history': val.short_history,
    'y_true_next_lap_s': y, 'persistence': val.current_lap_s,
    **{f'pred_{k}': v for k, v in preds.items()},
})
for k in preds:
    pred_table[f'abs_err_{k}'] = np.abs(y - preds[k])
pred_table['pred_B_minus_C_s'] = pred_table.pred_B_candidate - pred_table.pred_C_matched_control
pred_table.to_csv(OUT / 'validation_predictions.csv', index=False)

# =============================================================================
# 5. Errors by context: declared slices (check 5) and a supplementary bootstrap
# =============================================================================
std_edges = np.nanquantile(train.recent_std_s, [0.25, 0.5, 0.75])  # quartile edges fitted on train
std_bin = pd.cut(val.recent_std_s, [-np.inf, *std_edges, np.inf],
                 labels=['Q1 (lowest)', 'Q2', 'Q3', 'Q4 (highest)']).astype(str).where(
    val.recent_std_s.notna(), 'missing (short history)')
slices = {
    'history': np.where(val.short_history.eq(1), 'short (1 clean lap)', 'full (2-3 clean laps)'),
    'recent_std quartile (train edges)': std_bin.to_numpy(),
    'compound': val.current_compound.to_numpy(),
    'race x history': (val['round'].map({8: 'R8', 9: 'R9'}) + ' / ' +
                       np.where(val.short_history.eq(1), 'short', 'full')).to_numpy(),
}
slice_rows = []
for sname, labels in slices.items():
    for lab in sorted(pd.unique(labels)):
        m = labels == lab
        c, b, a, d = (mae(y[m], preds[k][m]) for k in
                      ['C_matched_control', 'B_candidate', 'A_OLS_reference', 'D_followup_no_indicator'])
        slice_rows.append({'slice': sname, 'group': lab, 'n': int(m.sum()), 'control_MAE_s': c,
                           'candidate_MAE_s': b, 'control_minus_candidate_s': c - b, 'reference_MAE_s': a,
                           'followup_D_MAE_s': d, 'reference_minus_D_s': a - d})
slice_df = pd.DataFrame(slice_rows)
slice_df.to_csv(OUT / 'slices.csv', index=False)
check('5. robustness slices', 'HITO1.md section 4, check 5',
      'MAE by race with counts, and for full vs short history',
      'saved in race_table.csv and slices.csv (counts per group sum to 1,808 within each slice)',
      all(slice_df.groupby('slice').n.sum() == len(val)))
print(f'Train quartile edges of recent_std_s (s): {np.round(std_edges, 4).tolist()}')

# Cluster bootstrap over driver-race stints (laps of one stint are not independent).
# Supplementary: it describes the spread of C - B on these two races; it was not part of the
# Hito 1 decision rule and does not change it.
cluster = (val['round'].astype(str) + '-' + val.driver_number + '-' + val.stint.astype(str)).to_numpy()
ids, inv = np.unique(cluster, return_inverse=True)


def cluster_bootstrap(control, candidate):
    """Percentiles of (control MAE - candidate MAE) when whole stints are resampled."""
    rng = np.random.default_rng(RANDOM_SEED)  # same resamples for every comparison
    sums = [np.bincount(inv, w, len(ids)) for w in
            [np.abs(y - preds[control]), np.abs(y - preds[candidate]), np.ones(len(y))]]
    boot = np.empty(N_BOOT)
    for k in range(N_BOOT):
        pick = np.bincount(rng.integers(0, len(ids), len(ids)), minlength=len(ids))
        boot[k] = (pick @ sums[0] - pick @ sums[1]) / (pick @ sums[2])
    return {'comparison': f'{control} - {candidate}', 'clusters (driver-race stints)': int(len(ids)),
            'replicates': N_BOOT, 'seed': RANDOM_SEED,
            'point_s': M[control, 'all_validation'] - M[candidate, 'all_validation'],
            'p2.5_s': float(np.percentile(boot, 2.5)), 'p97.5_s': float(np.percentile(boot, 97.5)),
            'share_positive': float((boot > 0).mean())}


boots = pd.DataFrame([cluster_bootstrap('C_matched_control', 'B_candidate'),
                      cluster_bootstrap('A_OLS_reference', 'D_followup_no_indicator'),
                      cluster_bootstrap('A_OLS_reference', 'B_candidate')])
boots.to_csv(OUT / 'bootstrap.csv', index=False)
print(boots.to_string(index=False))

# How concentrated is C - B? Per-row gain = |err control| - |err candidate|; its mean is C - B.
row_gain = np.sort(np.abs(y - preds['C_matched_control']) - np.abs(y - preds['B_candidate']))[::-1]
assert abs(row_gain.mean() - diff_all) < 1e-12
concentration = pd.DataFrame([{'top_k_rows_by_gain': k, 'share_of_total_gain': row_gain[:k].sum() / row_gain.sum(),
                               'C_minus_B_without_top_k_s': row_gain[k:].mean(),
                               'rows_with_positive_gain_of_1808': int((row_gain > 0).sum())}
                              for k in [0, 1, 10, 50, 100]])
concentration.to_csv(OUT / 'gain_concentration.csv', index=False)
print(concentration.to_string(index=False))

# --- Follow-up D (next check declared in DECISION_LOG.md before running) -----------
short = val.short_history.eq(1).to_numpy()
followup = []
for label, m in [('all_validation', np.ones(len(val), bool)), ('R8', rounds == 8), ('R9', rounds == 9),
                 ('short history', short), ('full history', ~short)]:
    a, d = mae(y[m], preds['A_OLS_reference'][m]), mae(y[m], preds['D_followup_no_indicator'][m])
    followup.append({'population': label, 'n': int(m.sum()), 'control_A_MAE_s': a, 'followup_D_MAE_s': d,
                     'A_minus_D_s': a - d, 'B_candidate_MAE_s': mae(y[m], preds['B_candidate'][m])})
followup = pd.DataFrame(followup).set_index('population')
followup.to_csv(OUT / 'followup_D_table.csv')
d_pass = (followup.loc['short history', 'followup_D_MAE_s'] <= 0.401
          and followup.loc['all_validation', 'A_minus_D_s'] >= THRESHOLD_S
          and followup.loc['R8', 'A_minus_D_s'] >= 0 and followup.loc['R9', 'A_minus_D_s'] >= 0)
check('D. follow-up: indicator removed', 'DECISION_LOG.md, entry 2026-11-17 (written before running D)',
      'D short-history MAE <= 0.401 s AND A - D >= 0.01 s overall AND A - D >= 0 in R8 and R9',
      f"D short-history MAE {followup.loc['short history', 'followup_D_MAE_s']:.4f} s (A "
      f"{followup.loc['short history', 'control_A_MAE_s']:.4f}); A - D = "
      f"{followup.loc['all_validation', 'A_minus_D_s']:+.5f} s overall (R8 {followup.loc['R8', 'A_minus_D_s']:+.5f}, "
      f"R9 {followup.loc['R9', 'A_minus_D_s']:+.5f}) -> {'PASS' if d_pass else 'FAIL'}", d_pass)

# =============================================================================
# 6. Inspected validation cases (rules declared here, applied mechanically)
# =============================================================================
#   case_moved_most     : row where adding recent_std_s moved the prediction most (|B - C| max)
#   case_short_history_R9 : R9 short-history row where the candidate lost most against the
#                           reference (abs_err_B - abs_err_A max); R9/short is the worst slice
#   case_worst_error    : largest candidate absolute error in validation
r9_short = pred_table[pred_table['round'].eq(9) & pred_table.short_history.eq(1)]
case_ids = {
    'case_moved_most': pred_table.loc[pred_table.pred_B_minus_C_s.abs().idxmax(), 'pair_id'],
    'case_short_history_R9': r9_short.loc[(r9_short.abs_err_B_candidate
                                           - r9_short.abs_err_A_OLS_reference).idxmax(), 'pair_id'],
    'case_worst_error': pred_table.loc[pred_table.abs_err_B_candidate.idxmax(), 'pair_id'],
}
case_rows = []
for rule, pid in case_ids.items():
    r = pred_table.set_index('pair_id').loc[pid]
    case_rows.append({'rule': rule, 'pair_id': pid, 'round': int(r['round']),
                      'current_lap_number': int(r.current_lap_number), 'recent_count': int(r.recent_count),
                      'recent_std_s': r.recent_std_s, 'current_lap_s (persistence)': r.persistence,
                      'observed_next_lap_s': r.y_true_next_lap_s,
                      'pred_candidate_s': r.pred_B_candidate, 'abs_err_candidate_s': r.abs_err_B_candidate,
                      'pred_control_s': r.pred_C_matched_control, 'abs_err_control_s': r.abs_err_C_matched_control,
                      'pred_reference_s': r.pred_A_OLS_reference,
                      'abs_err_reference_s': r.abs_err_A_OLS_reference,
                      'pred_followup_D_s': r.pred_D_followup_no_indicator,
                      'abs_err_followup_D_s': r.abs_err_D_followup_no_indicator})
    # Arithmetic check of the saved absolute errors.
    assert abs(abs(r.y_true_next_lap_s - r.pred_B_candidate) - r.abs_err_B_candidate) < 1e-12
cases = pd.DataFrame(case_rows)
cases.to_csv(OUT / 'inspected_cases.csv', index=False)

# Raw laps around each inspected case, as they appear in the original timing.
ctx = []
for pid in case_ids.values():
    r = val.set_index('pair_id').loc[pid]
    lap = int(r.current_lap_number)
    laps = raw[(raw['round'] == r['round']) & (raw.driver_number == r.driver_number)
               & raw.lap_number.between(lap - 3, lap + 1)].copy()
    laps['pair_id_inspected'] = pid
    laps['role'] = np.where(laps.lap_number == lap + 1, 't+1 (target, not an input)',
                            np.where(laps.lap_number == lap, 't', 'history'))
    ctx.append(laps)
pd.concat(ctx).to_csv(OUT / 'inspected_cases_raw_laps.csv', index=False)

# =============================================================================
# 7. SHAP on a fitted model from this experiment
# =============================================================================
# We explain the candidate B: it is the only model that contains recent_std_s, so it shows how
# the fitted model uses the new input. Performance claims about recent_std_s come from the
# ablation (section 4), not from SHAP.
EXPLAIN = 'B_candidate'
model = models[EXPLAIN]
cols = RUNS[EXPLAIN][1] + CATEGORICAL
prep, reg = model.named_steps['prepare'], model.named_steps['regression']
X_bg = prep.transform(train[cols])   # background: ALL 5,772 training rows, transformed by the train-fitted prep
X_val = prep.transform(val[cols])
enc_names = prep.get_feature_names_out()


def original_input(enc):
    """Map an encoded column back to the original input (one-hot columns -> their category input)."""
    body = enc.split('__', 1)[1]
    for c in CATEGORICAL:
        if body.startswith(c + '_'):
            return c
    return body


mapping = pd.DataFrame({'encoded_input': enc_names, 'original_input': [original_input(e) for e in enc_names],
                        'coefficient': reg.coef_})
mapping.to_csv(OUT / 'shap_encoded_mapping.csv', index=False)

# max_samples = all rows, so shap does not subsample the background.
masker = shap.maskers.Independent(X_bg, max_samples=len(X_bg))
explainer = shap.LinearExplainer(reg, masker)
sv = explainer(X_val)
phi, base = sv.values, float(np.ravel(sv.base_values)[0])

# Checks: (i) base + contributions = prediction for every row; (ii) for a linear model with an
# independent masker phi_j = w_j (x_j - mean_bg_j), so we recompute it by hand.
recon = base + phi.sum(axis=1)
recon_err = float(np.abs(recon - preds[EXPLAIN]).max())
manual_err = float(np.abs(phi - reg.coef_ * (X_val - X_bg.mean(axis=0))).max())
base_vs_train_mean = abs(base - float(model.predict(train[cols]).mean()))
assert recon_err < 1e-6 and manual_err < 1e-6 and base_vs_train_mean < 1e-6, (recon_err, manual_err)

phi_orig = pd.DataFrame(phi, columns=enc_names).T.groupby(mapping.original_input.values).sum().T
phi_orig.insert(0, 'pair_id', val.pair_id.values)
phi_orig['base_value_s'] = base
phi_orig['prediction_s'] = preds[EXPLAIN]
phi_orig['observed_s'] = y
phi_orig.to_csv(OUT / 'shap_values_validation.csv', index=False)

# Local explanation: the first inspected case, so the SHAP row and the error diagnosis coincide.
local_id = case_ids['case_moved_most']
i = int(np.flatnonzero(val.pair_id.to_numpy() == local_id)[0])
raw_vals = val.iloc[i][cols]
local = pd.DataFrame([{'original_input': c, 'input_value': raw_vals[c],
                       'shap_contribution_s': float(phi_orig.iloc[i][c])} for c in cols])
local = local.reindex(local.shap_contribution_s.abs().sort_values(ascending=False).index)
total = float(local.shap_contribution_s.sum())
footer = pd.DataFrame([
    {'original_input': 'BASE VALUE (mean training prediction)', 'input_value': '', 'shap_contribution_s': base},
    {'original_input': 'SUM OF CONTRIBUTIONS', 'input_value': '', 'shap_contribution_s': total},
    {'original_input': 'BASE + SUM (reconstructed prediction)', 'input_value': '', 'shap_contribution_s': base + total},
    {'original_input': 'MODEL PREDICTION', 'input_value': '', 'shap_contribution_s': float(preds[EXPLAIN][i])},
    {'original_input': 'RECONSTRUCTION ERROR', 'input_value': '', 'shap_contribution_s': base + total - float(preds[EXPLAIN][i])},
    {'original_input': 'OBSERVED next_lap_s', 'input_value': '', 'shap_contribution_s': float(y[i])},
    {'original_input': 'ABSOLUTE ERROR |observed - prediction|', 'input_value': '', 'shap_contribution_s': abs(float(y[i]) - float(preds[EXPLAIN][i]))},
])
pd.concat([local, footer], ignore_index=True).assign(model=EXPLAIN, pair_id=local_id).to_csv(
    OUT / 'shap_local.csv', index=False)

# Global summary over a declared sample: all 1,808 validation rows, also split by race.
glob_rows = []
for label, mask in [('all_validation', np.ones(len(val), bool)), ('R8', rounds == 8), ('R9', rounds == 9)]:
    block = phi_orig.loc[mask, cols]
    for c in cols:
        glob_rows.append({'sample': label, 'n': int(mask.sum()), 'original_input': c,
                          'mean_abs_shap_s': float(block[c].abs().mean()),
                          'mean_signed_shap_s': float(block[c].mean())})
glob = pd.DataFrame(glob_rows)
glob['rank_in_sample'] = glob.groupby('sample').mean_abs_shap_s.rank(ascending=False).astype(int)
glob.sort_values(['sample', 'rank_in_sample']).to_csv(OUT / 'shap_global.csv', index=False)

g_all = glob[glob['sample'] == 'all_validation'].sort_values('mean_abs_shap_s')
fig, ax = plt.subplots(figsize=(7, 4))
ax.barh(g_all.original_input, g_all.mean_abs_shap_s, color='#3b6ea5')
ax.set_xlabel('mean |SHAP contribution| (s), 1,808 validation rows')
ax.set_title(f'{EXPLAIN}: global SHAP (LinearExplainer, background = 5,772 train rows)', fontsize=9)
for yy, v in enumerate(g_all.mean_abs_shap_s):
    ax.text(v, yy, f' {v:.3f}', va='center', fontsize=8)
fig.tight_layout()
fig.savefig(OUT / 'shap_global_bar.png', dpi=150)
plt.close(fig)

num_idx = [list(enc_names).index(f'numeric__{c}') for c in RUNS[EXPLAIN][1]]
with warnings.catch_warnings():  # shap's jitter uses the global RNG seeded above; the notice is harmless
    warnings.simplefilter('ignore', FutureWarning)
    shap.summary_plot(phi[:, num_idx], X_val[:, num_idx], feature_names=RUNS[EXPLAIN][1], show=False)
plt.title(f'{EXPLAIN}: SHAP per validation row (numeric inputs, scaled values for colour)', fontsize=9)
plt.tight_layout()
plt.savefig(OUT / 'shap_beeswarm_numeric.png', dpi=150)
plt.close('all')

shap_meta = {'model_explained': EXPLAIN, 'explainer': 'shap.LinearExplainer on the fitted LinearRegression',
             'masker': 'shap.maskers.Independent', 'background': 'all 5,772 training rows (rounds 1-7), '
             'transformed by the train-fitted imputer/scaler/one-hot', 'explained_sample': 'all 1,808 validation rows',
             'units': 'seconds of predicted next_lap_s', 'base_value_s': base,
             'max_reconstruction_error_s': recon_err, 'max_diff_vs_manual_w(x-mean)_s': manual_err,
             'one_hot_aggregation': 'contributions of one-hot columns summed per original input (exact: model is additive)',
             'local_pair_id': local_id}
check('SHAP reconstruction', 'Hito 2 brief section 3 / C5',
      'base value + signed contributions = prediction (tolerance 1e-6 s) on every validation row',
      f'max |base + sum(phi) - prediction| = {recon_err:.1e} s over 1,808 rows; '
      f'equals manual w*(x - train mean) within {manual_err:.1e} s', recon_err < 1e-6)

# =============================================================================
# 8. Saved evidence: coefficients, checks, run manifest
# =============================================================================
coef = pd.concat([pd.DataFrame({'run': k, 'encoded_input': m.named_steps['prepare'].get_feature_names_out(),
                                'coefficient_s_per_sd_or_dummy': m.named_steps['regression'].coef_})
                  .pipe(lambda d: pd.concat([d, pd.DataFrame([{'run': k, 'encoded_input': 'intercept',
                        'coefficient_s_per_sd_or_dummy': m.named_steps['regression'].intercept_}])]))
                  for k, m in models.items()], ignore_index=True)
coef.to_csv(OUT / 'coefficients.csv', index=False)
pd.DataFrame(checks).to_csv(OUT / 'checks.csv', index=False)

run = {
    'command': 'python run_hito2.py (from Hito2/)', 'seed': RANDOM_SEED, 'test_used': False,
    'train_rows': len(train), 'validation_rows': len(val),
    'train_rounds': sorted(int(r) for r in train['round'].unique()),
    'validation_rounds': sorted(int(r) for r in val['round'].unique()),
    'validation_pair_id_sha256': val_hash, 'matches_hito1_hash': val_hash == h1_hash,
    'feature': {'name': 'recent_std_s', 'window_laps': WINDOW, 'min_clean_laps': MIN_CLEAN_LAPS, 'ddof': 1,
                'grouping': 'season, round, driver_number, stint', 'timeline': 'original snapshots before clean-pair filter',
                'window_convention': 'last 3 laps of the stint (t-2..t); non-clean laps left out, not replaced by earlier clean laps (same as recent_mean_s)',
                'missing_rule': 'NaN when < 2 clean laps; filled by train-fitted median imputer; short_history = 1',
                'train_fill_value_s': fill_value},
    'runs': {k: {'role': r, 'family': 'OLS (make_model)', 'numeric': n, 'categorical': CATEGORICAL}
             for k, (r, n) in RUNS.items()},
    'results': {'MAE_s': {f'{k[0]}|{k[1]}': v for k, v in M.items()},
                'C_minus_B_s': {'all': diff_all, 'R8': diff_r8, 'R9': diff_r9},
                'B_minus_A_s': M['B_candidate', 'all_validation'] - M['A_OLS_reference', 'all_validation'],
                'hito1_rule_supported': bool(supported),
                'followup_D': {'A_minus_D_s': followup.A_minus_D_s.to_dict(), 'predeclared_rule_passed': bool(d_pass)},
                'cluster_bootstrap': boots.to_dict('records')},
    'shap': shap_meta,
    'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__,
                 'sklearn': sklearn.__version__, 'shap': shap.__version__, 'matplotlib': matplotlib.__version__},
    'sha256': {**{p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                  [BASE / 'train_clean_v1.csv', BASE / 'validation_clean_v1.csv', BASE / 'nextlap_reference_v1.py']},
               'snapshots': {e['file']: e['sha256'] for e in manifest['events']}},
}
(OUT / 'run_manifest.json').write_text(json.dumps(run, indent=2, default=float), encoding='utf-8')

print('\n' + metrics.to_string(index=False))
print('\n' + race.to_string(index=False))
print('\n' + cases.T.to_string())
print('\n' + glob[glob['sample'] == 'all_validation'].sort_values('rank_in_sample').to_string(index=False))
print('\n' + followup.to_string())
print(f'\nC - B overall = {diff_all:+.5f} s | Hito 1 rule supported: {supported} | '
      f'follow-up D rule passed: {d_pass}')
print('Outputs written to', OUT, '| No reserved test data used.')
