"""Hito 1 · Team 1 · Reproduce the three NextLap references on the common validation rows.

Adapted from the class helper `probar_referencia_v1.py` (IIT414W, v1) and uses the
supplied `base_NextLap/nextlap_reference_v1.py` (make_model, NUMERIC, CATEGORICAL, TARGET).
Changes from the helper: configurable data location, outputs written to ./outputs,
per-race MAE table and an explicit check that every model is scored on the same pair_id set.

No reserved final-evaluation data are accessed.

Usage (from this folder):
    python run_references.py                       # expects ../base_NextLap
    python run_references.py --base PATH/TO/base_NextLap
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import mean_absolute_error

RANDOM_SEED = 414
HERE = Path(__file__).resolve().parent

parser = argparse.ArgumentParser()
parser.add_argument('--base', default=str(HERE.parent / 'base_NextLap'),
                    help='Folder of the released base_NextLap data (default: ../base_NextLap)')
args = parser.parse_args()
BASE = Path(args.base).resolve()
if not (BASE / 'nextlap_reference_v1.py').is_file():
    sys.exit(f'base_NextLap not found at {BASE}. See DATA_MANIFEST.md.')

sys.path.insert(0, str(BASE))
from nextlap_reference_v1 import CATEGORICAL, NUMERIC, TARGET, make_model  # noqa: E402

np.random.seed(RANDOM_SEED)

train = pd.read_csv(BASE / 'train_clean_v1.csv')
val = pd.read_csv(BASE / 'validation_clean_v1.csv')

# --- Data checks (expected values written before running) -------------------
assert len(train) == 5772, len(train)
assert len(val) == 1808, len(val)
assert set(train['round']) == set(range(1, 8))
assert set(val['round']) == {8, 9}
assert train.pair_id.is_unique and val.pair_id.is_unique
assert not set(train.pair_id) & set(val.pair_id), 'pair_id overlap between train and validation'

features = NUMERIC + CATEGORICAL
assert TARGET not in features
assert not any(c.startswith('next_') for c in features), 'future-known column used as input'

# --- References -------------------------------------------------------------
# Preprocessing (imputer + scaler + one-hot) lives inside the Pipeline, so it is
# fitted only on training rows by .fit(train, ...) and only applied to validation.
ols = make_model('OLS').fit(train[features], train[TARGET])

preds = {
    'train_median': np.full(len(val), train[TARGET].median()),
    'persistence': val['current_lap_s'].to_numpy(),
    'OLS_reference': ols.predict(val[features]),
}
for name, p in preds.items():
    assert len(p) == len(val) and np.isfinite(p).all(), name

populations = [('all_validation', np.ones(len(val), dtype=bool))]
for rnd in sorted(val['round'].unique()):
    populations.append((f'round_{rnd}', val['round'].eq(rnd).to_numpy()))

rows = []
for name, p in preds.items():
    for label, mask in populations:
        rows.append({'model': name, 'population': label, 'n': int(mask.sum()),
                     'MAE_s': float(mean_absolute_error(val.loc[mask, TARGET], p[mask]))})
metrics = pd.DataFrame(rows)

# --- Outputs ----------------------------------------------------------------
out = HERE / 'outputs'
out.mkdir(exist_ok=True)
metrics.to_csv(out / 'reference_metrics.csv', index=False)
pred_table = pd.DataFrame({'pair_id': val.pair_id, 'round': val['round'],
                           'y_true': val[TARGET], **preds})
pred_table.to_csv(out / 'validation_reference_predictions.csv', index=False)

# Same rows for every model: one prediction per validation pair_id, no drops.
assert pred_table.pair_id.is_unique and set(pred_table.pair_id) == set(val.pair_id)

report = {
    'train_rows': len(train), 'validation_rows': len(val),
    'train_rounds': sorted(int(r) for r in train['round'].unique()),
    'validation_rounds': sorted(int(r) for r in val['round'].unique()),
    'validation_pair_id_sha256': hashlib.sha256(
        '\n'.join(sorted(val.pair_id)).encode()).hexdigest(),
    'test_used': False, 'seed': RANDOM_SEED, 'features': features, 'target': TARGET,
    'preprocessing_fit_on': 'training rows only (Pipeline.fit on train)',
    'results': rows,
    'versions': {'python': platform.python_version(), 'numpy': np.__version__,
                 'pandas': pd.__version__, 'sklearn': sklearn.__version__},
    'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
               [BASE / 'train_clean_v1.csv', BASE / 'validation_clean_v1.csv',
                BASE / 'nextlap_reference_v1.py']},
}
(out / 'reference_run.json').write_text(json.dumps(report, indent=2), encoding='utf-8')

print(metrics.to_string(index=False))
print(f'\nTrain rows: {len(train)} (rounds 1-7) | Validation rows: {len(val)} (rounds 8-9)')
print('Outputs written to', out)
print('No reserved test data used.')
