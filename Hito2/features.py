"""Hito 2 · Team 1 · Pace-variability feature built from the released timing snapshots.

recent_std_s = sample standard deviation (ddof=1) of the driver's clean lap times in the
last 3 laps up to and including lap t, within season, round, driver and stint.

The definition mirrors the supplied `recent_mean_s` in `nextlap_reference_v1.build_pairs`:
- same timeline: the original lap snapshots, before the retrospective clean-pair filter;
- same "clean" rule for a lap that has already ended (`current_clean`);
- same window: rolling over the last 3 laps of the stint, lap t included, lap t+1 never.

Window convention (Hito 1 feedback, C3.1): the window is the last 3 *laps* of the stint
(t-2, t-1, t), not the last 3 *clean* laps. A non-clean lap inside the window is left out and
is NOT replaced by an earlier clean lap, so the window can hold 3, 2, 1 or 0 clean times.
This is exactly how the reference builds `recent_mean_s` / `recent_count`, which the run
script rebuilds and matches on every row. `last_clean_laps_std` computes the other
convention only to count and show where the two disagree.
Only the aggregation changes (std instead of mean) and the minimum number of clean laps is 2,
because a standard deviation of one lap is undefined (Hito 1 short-history rule).

Two independent implementations are provided:
- `history_features`: vectorised rolling window on the full timeline (used by the models);
- `as_of_recompute`: for every pair, keeps only laps whose end_time_s <= the pair's end_time_s
  (the "as-of" view of the bonus input contract) and recomputes the value with plain numpy.
The run script asserts that both agree on every row, which is the availability-at-t check.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

KEYS = ['season', 'round', 'driver_number']
STINT_KEYS = KEYS + ['stint']
WINDOW = 3          # same window as recent_mean_s; fixed in Hito 1, not searched on validation
MIN_CLEAN_LAPS = 2  # below this the std is undefined -> missing, filled by the train-fitted imputer


def _pair_id(frame: pd.DataFrame, lap_col: str = 'lap_number') -> pd.Series:
    # Same format as nextlap_reference_v1.build_pairs: 2026-R8-1-L2
    return (frame['season'].astype(str) + '-R' + frame['round'].astype(str) + '-'
            + frame['driver_number'].astype(str) + '-L' + frame[lap_col].astype(int).astype(str))


def current_clean(raw: pd.DataFrame) -> pd.Series:
    """Copy of the reference rule for an already-ended lap (uses lap t fields only)."""
    return (raw.lap_number.gt(1) & raw.lap_time_s.gt(0) & raw.is_accurate & ~raw.pit_in
            & ~raw.pit_out & ~raw.deleted & raw.track_status.eq('1'))


def history_features(raw: pd.DataFrame) -> pd.DataFrame:
    """One row per original lap with the history features observable at the end of that lap."""
    data = raw.sort_values(KEYS + ['lap_number']).reset_index(drop=True).copy()
    data['history_value'] = data.lap_time_s.where(current_clean(data))
    grouped = data.groupby(STINT_KEYS, dropna=False, sort=False)['history_value']

    # Rolling over rows = rolling over laps here: run_hito2.py asserts there are no lap-number gaps
    # inside a stint, so the last 3 rows of a stint are laps t-2, t-1 and t.
    data['recent_std_s'] = grouped.transform(
        lambda s: s.rolling(WINDOW, min_periods=MIN_CLEAN_LAPS).std(ddof=1))
    # Recomputed (not read from the CSV) so the run can prove our window equals the reference one.
    data['recent_mean_check_s'] = grouped.transform(lambda s: s.rolling(WINDOW, min_periods=1).mean())
    data['recent_count_check'] = grouped.transform(lambda s: s.rolling(WINDOW, min_periods=1).count())
    # Short history is defined from the clean-lap count that is itself known at t.
    data['short_history'] = (data['recent_count_check'] < MIN_CLEAN_LAPS).astype(int)

    # Provenance of the window: the latest clean lap actually used and its end time.
    clean_lap = data.lap_number.where(data.history_value.notna())
    clean_end = data.end_time_s.where(data.history_value.notna())
    data['last_lap_used'] = clean_lap.groupby([data[k] for k in STINT_KEYS], sort=False).transform(
        lambda s: s.rolling(WINDOW, min_periods=1).max())
    data['last_end_time_used_s'] = clean_end.groupby([data[k] for k in STINT_KEYS], sort=False).transform(
        lambda s: s.rolling(WINDOW, min_periods=1).max())
    data['first_lap_in_window'] = data.groupby(STINT_KEYS, sort=False).lap_number.transform(
        lambda s: s.rolling(WINDOW, min_periods=1).min())

    data['pair_id'] = _pair_id(data)
    cols = ['pair_id', 'season', 'round', 'driver_number', 'stint', 'lap_number', 'end_time_s',
            'recent_std_s', 'short_history', 'recent_mean_check_s', 'recent_count_check',
            'first_lap_in_window', 'last_lap_used', 'last_end_time_used_s']
    return data[cols]


def last_clean_laps_std(raw: pd.DataFrame) -> pd.DataFrame:
    """Alternative convention, NOT used by any model: std of the last 3 *clean* laps of the stint.

    It reaches back past an invalid lap to an earlier clean one, so it can differ from our
    window convention (last 3 laps, invalid ones left out). Computed only to count and show
    where the two conventions disagree (Hito 1 feedback, C3.1).
    """
    data = raw.sort_values(KEYS + ['lap_number']).reset_index(drop=True).copy()
    clean_times = data.lap_time_s.where(current_clean(data))
    out = pd.Series(np.nan, index=data.index)
    n_used = pd.Series(0, index=data.index)
    for _, idx in data.groupby(STINT_KEYS, dropna=False, sort=False).groups.items():
        seen = []
        for i in idx:
            if not np.isnan(clean_times[i]):
                seen.append(clean_times[i])
            last = seen[-WINDOW:]
            n_used[i] = len(last)
            if len(last) >= MIN_CLEAN_LAPS:
                out[i] = np.std(last, ddof=1)
    return pd.DataFrame({'pair_id': _pair_id(data), 'last3clean_std_s': out, 'last3clean_n': n_used})


def as_of_recompute(raw: pd.DataFrame, pairs: pd.DataFrame) -> pd.Series:
    """Independent, loop-based recomputation from an as-of history view.

    For each pair, the history contains only laps of the same driver and race whose
    end_time_s <= the pair's end_time_s (laps already ended at t). From that view we keep
    the same stint, take the last WINDOW laps and the std of their clean times.
    """
    data = raw.sort_values(KEYS + ['lap_number']).copy()
    data['is_clean'] = current_clean(data)
    by_driver = {k: g for k, g in data.groupby(KEYS, sort=False)}
    out = np.full(len(pairs), np.nan)
    for i, row in enumerate(pairs[KEYS + ['stint', 'end_time_s']].itertuples(index=False)):
        laps = by_driver[(row.season, row.round, row.driver_number)]
        seen = laps[(laps.end_time_s <= row.end_time_s) & (laps.stint == row.stint)]
        window = seen.tail(WINDOW)
        times = window.lap_time_s[window.is_clean].to_numpy()
        if len(times) >= MIN_CLEAN_LAPS:
            out[i] = np.std(times, ddof=1)
    return pd.Series(out, index=pairs.index, name='recent_std_as_of')
