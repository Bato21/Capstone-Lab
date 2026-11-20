"""Final report · Team 1 · Frozen final model E, scored from the bonus input contract.

Model E (frozen after trial E passed its pre-declared rule, FinalReport/DECISION_LOG.md):
    B  OLS via make_model, six reference inputs + recent_std_s + short_history, train rounds 1-7
    A  OLS via make_model, six reference inputs (the fixed reference),        train rounds 1-7
    prediction = B, except on rows with short_history = 1 (fewer than two clean laps in the
    window, so recent_std_s is undefined), which use A: the declared frozen-reference fallback.

Inputs (bonus rules v2, "Input contract for the common evaluation"):
    --requests  CSV, one row per prediction request at the end of lap t: pair_id, season, round,
                driver_number, stint, end_time_s and the six reference inputs (current_lap_s,
                recent_mean_s, current_lap_number, current_tyre_life, current_compound, current_team).
    --history   CSV in the released timing-snapshot schema (season, round, driver_number, lap_number,
                lap_time_s, end_time_s, stint, track_status, is_accurate, pit_in, pit_out, deleted, ...).
                For each request only laps of the same driver, race and stint whose end_time_s is
                <= the request's end_time_s are read, so a wider table cannot leak later laps.
Training uses only the released rounds 1-7 (train_clean_v1.csv and the r01-r07 snapshots), with every
file checked against its released SHA-256. Validation rounds are never added to training.

Output: one finite prediction in seconds per requested pair_id (no missing or duplicated IDs), and a
JSON summary with the fallback counts.

Usage (from the repository root, Hito 2 environment, data in base_NextLap/):
    python FinalReport/predict.py --requests REQUESTS.csv --history HISTORY.csv --out predictions.csv
    python FinalReport/predict.py --self-check
--self-check builds the requests and the history view from the released validation rounds 8-9 and
asserts that the predictions equal trial E's saved predictions (FinalReport/outputs/validation_predictions_E.csv).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'Hito2'))
from features import MIN_CLEAN_LAPS, WINDOW, current_clean, history_features  # noqa: E402

RANDOM_SEED = 414  # OLS has no randomness; recorded for the bonus rules
REQUEST_COLS = ['pair_id', 'season', 'round', 'driver_number', 'stint', 'end_time_s']
EXPECTED_SHA256 = {  # released files, same values as Hito2/run_hito2.py
    'train_clean_v1.csv': '43544f38cc9ef32b44886e6751e03522601265160086fe3a4956f04b87bd5c13',
    'validation_clean_v1.csv': 'b19efb6a908af12a5d2c6bdde29aa40984295e62ce0f187a201b579278db7ee8',
    'nextlap_reference_v1.py': 'f6c58925cd4a477bf3e1a5a2b3968e67df3a1cffabecee9e89701c3ac2d5f994',
}
BOOLEAN = ['is_accurate', 'pit_in', 'pit_out', 'deleted']

parser = argparse.ArgumentParser()
parser.add_argument('--base', default=str(ROOT / 'base_NextLap'), help='released base_NextLap folder')
parser.add_argument('--requests', help='prediction requests CSV')
parser.add_argument('--history', help='as-of lap history CSV (timing-snapshot schema)')
parser.add_argument('--out', default=str(ROOT / 'FinalReport' / 'outputs' / 'predictions.csv'))
parser.add_argument('--self-check', action='store_true', help='score validation rounds 8-9 and compare with trial E')
args = parser.parse_args()
if not args.self_check and not (args.requests and args.history):
    parser.error('give --requests and --history, or --self-check')

BASE = Path(args.base).resolve()
for fname, digest in EXPECTED_SHA256.items():
    assert hashlib.sha256((BASE / fname).read_bytes()).hexdigest() == digest, f'{fname} differs from the release'
sys.path.insert(0, str(BASE))
from nextlap_reference_v1 import CATEGORICAL, NUMERIC, TARGET, load_snapshots, make_model  # noqa: E402

INPUTS_A = NUMERIC + CATEGORICAL
INPUTS_B = NUMERIC + ['recent_std_s', 'short_history'] + CATEGORICAL


def read_history(path):
    """Read a history view in the snapshot schema with the same types as load_snapshots."""
    frame = pd.read_csv(path, dtype={'driver_number': str, 'track_status': str})
    for column in BOOLEAN:
        frame[column] = frame[column].astype(str).str.lower().eq('true')
    return frame


def as_of_features(requests, history):
    """recent_std_s, clean-lap count and short_history for each request, from laps ended by t only."""
    history = history.copy()
    history['is_clean'] = current_clean(history)
    by_stint = {k: g.sort_values('end_time_s') for k, g in
                history.groupby(['season', 'round', 'driver_number', 'stint'], sort=False)}
    std, count, found = np.full(len(requests), np.nan), np.zeros(len(requests), int), np.zeros(len(requests), bool)
    for i, r in enumerate(requests[REQUEST_COLS].itertuples(index=False)):
        laps = by_stint.get((r.season, r.round, r.driver_number, r.stint))
        if laps is None:
            continue
        window = laps[laps.end_time_s <= r.end_time_s].tail(WINDOW)  # laps t-2..t of the stint
        found[i] = len(window) > 0
        times = window.lap_time_s[window.is_clean].to_numpy()
        count[i] = len(times)
        if len(times) >= MIN_CLEAN_LAPS:
            std[i] = np.std(times, ddof=1)
    return pd.DataFrame({'recent_std_s': std, 'clean_laps_in_window': count,
                         'short_history': (count < MIN_CLEAN_LAPS).astype(int), 'history_found': found},
                        index=requests.index)


# =============================================================================
# 1. Fit A and B on the released rounds 1-7 only
# =============================================================================
train = pd.read_csv(BASE / 'train_clean_v1.csv', dtype={'driver_number': str})
assert set(train['round']) == set(range(1, 8)) and len(train) == 5772 and train.pair_id.is_unique
raw, _ = load_snapshots(BASE)  # verifies every snapshot SHA-256 against the release manifest
hist_train = history_features(raw[raw['round'] <= 7])
train = train.merge(hist_train[['pair_id', 'recent_std_s', 'short_history']], on='pair_id', how='left',
                    validate='1:1')
assert train.short_history.notna().all()
model_A = make_model('OLS', numeric=NUMERIC, categorical=CATEGORICAL).fit(train[INPUTS_A], train[TARGET])
model_B = make_model('OLS', numeric=NUMERIC + ['recent_std_s', 'short_history'],
                     categorical=CATEGORICAL).fit(train[INPUTS_B], train[TARGET])

# =============================================================================
# 2. Requests and as-of history
# =============================================================================
if args.self_check:
    val = pd.read_csv(BASE / 'validation_clean_v1.csv', dtype={'driver_number': str})
    requests = val[REQUEST_COLS + NUMERIC + CATEGORICAL].copy()  # no next_lap_s, next_* or clean_pair
    history = raw[raw['round'].isin([8, 9])].copy()
else:
    requests = pd.read_csv(args.requests, dtype={'driver_number': str})
    history = read_history(args.history)
missing = [c for c in REQUEST_COLS + NUMERIC + CATEGORICAL if c not in requests.columns]
assert not missing, f'requests lack columns {missing}'
assert requests.pair_id.notna().all() and requests.pair_id.is_unique, 'missing or duplicated pair_id in requests'

feats = as_of_features(requests, history)
X = pd.concat([requests, feats[['recent_std_s', 'short_history']]], axis=1)
pred_A, pred_B = model_A.predict(X[INPUTS_A]), model_B.predict(X[INPUTS_B])
short = feats.short_history.eq(1).to_numpy()
pred = np.where(short, pred_A, pred_B)
assert len(pred) == len(requests) and np.isfinite(pred).all(), 'non-finite prediction'

out = pd.DataFrame({'pair_id': requests.pair_id, 'prediction_s': pred,
                    'source': np.where(short, 'A (short-history fallback)', 'B')})
summary = {
    'model': 'E: candidate B, frozen-reference A on short_history rows; both OLS, train rounds 1-7',
    'requests': int(len(out)), 'predictions_finite': int(np.isfinite(pred).sum()),
    'from_B': int((~short).sum()), 'fallback_to_A_short_history': int(short.sum()),
    'of_which_no_history_laps_found': int((~feats.history_found).sum()),
    'other_missing_inputs_filled_by_train_medians': {c: int(requests[c].isna().sum()) for c in NUMERIC + CATEGORICAL
                                                     if requests[c].isna().any()},
}

if args.self_check:
    saved = pd.read_csv(ROOT / 'FinalReport' / 'outputs' / 'validation_predictions_E.csv')
    m = out.merge(saved[['pair_id', 'pred_E_short_history_fallback', 'short_history']], on='pair_id',
                  how='left', validate='1:1')
    assert m.pred_E_short_history_fallback.notna().all() and len(m) == 1808
    max_dev = float(np.abs(m.prediction_s - m.pred_E_short_history_fallback).max())
    same_flag = bool((short.astype(int) == m.short_history.to_numpy()).all())
    assert same_flag and max_dev < 1e-9, (same_flag, max_dev)
    y = val.set_index('pair_id').loc[out.pair_id, TARGET].to_numpy()
    summary['self_check'] = {'rows': 1808, 'same_short_history_flags': same_flag,
                             'max_abs_diff_vs_trial_E_s': max_dev,
                             'validation_MAE_s': float(np.mean(np.abs(y - pred)))}
    args.out = str(ROOT / 'FinalReport' / 'outputs' / 'predict_self_check.csv')

Path(args.out).parent.mkdir(parents=True, exist_ok=True)
out.to_csv(args.out, index=False)
Path(args.out).with_suffix('.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
