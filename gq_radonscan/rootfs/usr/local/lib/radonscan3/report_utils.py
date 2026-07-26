from __future__ import annotations

from math import ceil
from typing import Iterable


def peak_preserving_downsample(records: Iterable[dict[str, object]], max_points: int = 1800) -> list[dict[str, object]]:
    """Reduce a time series while retaining local minima and maxima.

    Statistical calculations continue to use all records. This helper is only for
    drawing long PDF time series efficiently and without hiding short peaks.
    """
    rows = list(records)
    if max_points < 4 or len(rows) <= max_points:
        return rows

    # Two representatives per bucket (min and max), plus first and last.
    interior = rows[1:-1]
    target_buckets = max(1, (max_points - 2) // 2)
    bucket_size = max(1, ceil(len(interior) / target_buckets))
    sampled: list[dict[str, object]] = [rows[0]]

    for offset in range(0, len(interior), bucket_size):
        bucket = interior[offset : offset + bucket_size]
        numeric = [
            (index, item, float(item["bq_m3"]))
            for index, item in enumerate(bucket)
            if item.get("bq_m3") is not None
        ]
        if not numeric:
            sampled.append(bucket[0])
            continue
        minimum = min(numeric, key=lambda entry: entry[2])
        maximum = max(numeric, key=lambda entry: entry[2])
        selected = sorted({minimum[0]: minimum[1], maximum[0]: maximum[1]}.items())
        sampled.extend(item for _, item in selected)

    sampled.append(rows[-1])
    if len(sampled) > max_points:
        # Deterministic final thinning is only needed for rounding edge cases.
        step = (len(sampled) - 1) / (max_points - 1)
        sampled = [sampled[round(index * step)] for index in range(max_points)]
    return sampled
