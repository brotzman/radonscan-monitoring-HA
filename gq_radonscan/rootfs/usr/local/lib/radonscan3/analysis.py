from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
import math
import random
import statistics
from typing import Iterable, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def parse_dt(value: object) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds") if dt else None



def _resolve_zone(name: str | None):
    candidate = (name or "UTC").strip()
    if candidate.lower() == "auto":
        candidate = "UTC"
    try:
        return ZoneInfo(candidate), candidate
    except (ZoneInfoNotFoundError, ValueError):
        return timezone.utc, "UTC"


def _geometric(values: Sequence[float]) -> tuple[float | None, float | None]:
    positive = [v for v in values if v > 0]
    if not positive or len(positive) != len(values):
        return None, None
    logs = [math.log(v) for v in positive]
    gm = math.exp(statistics.fmean(logs))
    gsd = math.exp(statistics.stdev(logs)) if len(logs) > 1 else None
    return gm, gsd


def _median_absolute_deviation(values: Sequence[float]) -> float | None:
    if not values:
        return None
    med = statistics.median(values)
    return statistics.median(abs(v - med) for v in values)


def _theil_sen(points: Sequence[tuple[datetime, float]], max_points: int = 500) -> float | None:
    if len(points) < 2:
        return None
    sample = list(points)
    if len(sample) > max_points:
        step = max(1, len(sample) // max_points)
        sample = sample[::step][:max_points]
    slopes: list[float] = []
    for i in range(len(sample) - 1):
        for j in range(i + 1, len(sample)):
            days = (sample[j][0] - sample[i][0]).total_seconds() / 86400.0
            if days > 0:
                slopes.append((sample[j][1] - sample[i][1]) / days)
    return statistics.median(slopes) if slopes else None



def _effective_sample_size(values: Sequence[float], max_lag: int = 168) -> dict[str, object]:
    n = len(values)
    if n < 4:
        return {"available": False, "reason": "insufficient_samples", "n_effective": None, "correlation_hours": None}
    ac = _autocorrelation(values, min(max_lag, n // 3))
    positive = []
    for item in ac:
        coefficient = float(item["coefficient"])
        if coefficient <= 0:
            break
        positive.append(coefficient)
    denominator = 1.0 + 2.0 * sum(positive)
    n_eff = max(1.0, min(float(n), n / denominator))
    return {
        "available": True,
        "n_observed": n,
        "n_effective": n_eff,
        "correlation_hours": len(positive),
        "method": "positive_sequence_autocorrelation",
    }


def _block_bootstrap_ci(values: Sequence[float], statistic, *, confidence: float = 0.95, resamples: int = 400) -> dict[str, object]:
    n = len(values)
    if n < 24:
        return {"available": False, "reason": "minimum_24_samples"}
    ess = _effective_sample_size(values)
    correlation_hours = int(ess.get("correlation_hours") or 1)
    block = max(2, min(24, correlation_hours + 1, n))
    rng = random.Random(4500 + n)
    results=[]
    for _ in range(resamples):
        sample=[]
        while len(sample) < n:
            start=rng.randrange(0, n)
            sample.extend(values[(start+j) % n] for j in range(block))
        results.append(float(statistic(sample[:n])))
    results.sort()
    alpha=(1.0-confidence)/2.0
    return {
        "available": True,
        "method": "moving_block_bootstrap",
        "confidence_percent": confidence*100.0,
        "block_hours": block,
        "resamples": resamples,
        "lower": percentile(results, alpha),
        "upper": percentile(results, 1.0-alpha),
    }


def _moments(values: Sequence[float]) -> dict[str, float | None]:
    n=len(values)
    if n < 3:
        return {"skewness": None, "excess_kurtosis": None}
    mean=statistics.fmean(values)
    m2=sum((v-mean)**2 for v in values)/n
    if m2 <= 0:
        return {"skewness": 0.0, "excess_kurtosis": 0.0}
    m3=sum((v-mean)**3 for v in values)/n
    m4=sum((v-mean)**4 for v in values)/n
    return {"skewness": m3/(m2**1.5), "excess_kurtosis": m4/(m2*m2)-3.0}


def _trimmed_mean(values: Sequence[float], proportion: float = 0.1) -> float | None:
    if not values:
        return None
    ordered=sorted(values); cut=int(len(ordered)*proportion)
    core=ordered[cut:len(ordered)-cut] if cut and len(ordered)>2*cut else ordered
    return statistics.fmean(core)


def _mann_kendall(points: Sequence[tuple[datetime,float]], max_points: int = 1000) -> dict[str, object]:
    if len(points) < 10:
        return {"available": False, "reason": "minimum_10_samples"}
    sample=list(points)
    if len(sample)>max_points:
        step=max(1,len(sample)//max_points); sample=sample[::step][:max_points]
    vals=[v for _,v in sample]; n=len(vals); score=0
    for i in range(n-1):
        vi=vals[i]
        for j in range(i+1,n):
            score += 1 if vals[j]>vi else -1 if vals[j]<vi else 0
    ties={v:vals.count(v) for v in set(vals)}
    variance=(n*(n-1)*(2*n+5)-sum(t*(t-1)*(2*t+5) for t in ties.values() if t>1))/18.0
    if variance <= 0:
        z=0.0
    elif score>0: z=(score-1)/math.sqrt(variance)
    elif score<0: z=(score+1)/math.sqrt(variance)
    else: z=0.0
    p=math.erfc(abs(z)/math.sqrt(2.0))
    return {"available": True, "tau": score/(n*(n-1)/2), "z": z, "p_value": p, "samples": n, "significant_05": p<0.05}


def _moving_robust(points: Sequence[tuple[datetime,float]], window: int = 24) -> list[dict[str, object]]:
    out=[]
    for i,(dt,_) in enumerate(points):
        vals=sorted(v for _,v in points[max(0,i-window+1):i+1])
        if len(vals)<max(3,window//2):
            continue
        out.append({"completed_at": iso(dt), "median_bq_m3": statistics.median(vals), "p25_bq_m3": percentile(vals,.25), "p75_bq_m3": percentile(vals,.75), "samples":len(vals)})
    return out


def _threshold_events(points: Sequence[tuple[datetime,float]], threshold: float) -> dict[str, object]:
    events=[]; current=[]
    def finish():
        nonlocal current
        if not current: return
        vals=[v for _,v in current]
        excess=sum(max(0.0,v-threshold) for v in vals)
        events.append({"start":iso(current[0][0]),"end":iso(current[-1][0]),"duration_hours":len(current),"maximum_bq_m3":max(vals),"mean_bq_m3":statistics.fmean(vals),"excess_area_bq_h_m3":excess})
        current=[]
    previous=None
    for dt,value in points:
        if previous is not None and (dt-previous).total_seconds()>5400: finish()
        if value>=threshold: current.append((dt,value))
        else: finish()
        previous=dt
    finish()
    return {"threshold_bq_m3":threshold,"events":events,"event_count":len(events),"total_excess_area_bq_h_m3":sum(e["excess_area_bq_h_m3"] for e in events)}


def _concentration_classes(values: Sequence[float]) -> list[dict[str, object]]:
    bounds=[(None,100.0,"below_100"),(100.0,200.0,"100_199"),(200.0,300.0,"200_299"),(300.0,None,"at_least_300")]
    result=[]
    for low,high,key in bounds:
        count=sum(1 for v in values if (low is None or v>=low) and (high is None or v<high))
        result.append({"key":key,"minimum":low,"maximum_exclusive":high,"hours":count,"percent":count/len(values)*100.0 if values else 0.0})
    return result


def _poisson_uncertainty(records: Sequence[dict[str, object]], values: Sequence[float]) -> dict[str, object]:
    """Estimate counting-statistical uncertainty from raw hourly counts.

    This is explicitly labelled as an estimate: it covers Poisson counting noise only,
    not calibration, environmental response or other systematic effects.
    """
    counts=[]
    for row in records:
        try:
            c=float(row.get("raw_cph"))
        except (TypeError, ValueError):
            continue
        if math.isfinite(c) and c >= 0:
            counts.append(c)
    if not counts or len(counts)!=len(values):
        return {"available": False, "reason": "raw_counts_unavailable"}
    total=sum(counts)
    if total <= 0:
        return {"available": False, "reason": "zero_total_counts"}
    mean=statistics.fmean(values) if values else None
    rel_1sigma=1.0/math.sqrt(total)
    abs_1sigma=(mean*rel_1sigma) if mean is not None else None
    return {
        "available": True,
        "method": "poisson_counting_estimate",
        "scope": "statistical_only",
        "total_counts": total,
        "relative_standard_uncertainty_percent": rel_1sigma*100.0,
        "standard_uncertainty_bq_m3": abs_1sigma,
        "expanded_uncertainty_95_bq_m3": (1.96*abs_1sigma) if abs_1sigma is not None else None,
        "coverage_factor": 1.96,
        "limitations": ["excludes_calibration_uncertainty", "excludes_systematic_effects"],
    }


def _autocorrelation(values: Sequence[float], max_lag: int = 24) -> list[dict[str, object]]:
    if len(values) < 4:
        return []
    mean=statistics.fmean(values)
    denom=sum((v-mean)**2 for v in values)
    if denom <= 0:
        return []
    out=[]
    for lag in range(1, min(max_lag, len(values)-2)+1):
        num=sum((values[i]-mean)*(values[i-lag]-mean) for i in range(lag,len(values)))
        out.append({"lag_hours": lag, "coefficient": num/denom, "pairs": len(values)-lag})
    return out


def _change_point(points: Sequence[tuple[datetime,float]], minimum_segment: int = 24) -> dict[str, object]:
    if len(points) < minimum_segment*2:
        return {"available": False, "reason": "insufficient_samples", "minimum_samples": minimum_segment*2}
    values=[v for _,v in points]
    best=None
    overall_mad=_median_absolute_deviation(values) or 1.0
    for i in range(minimum_segment, len(values)-minimum_segment+1):
        before=statistics.median(values[:i]); after=statistics.median(values[i:])
        score=abs(after-before)/max(overall_mad,1e-9)
        if best is None or score>best[0]: best=(score,i,before,after)
    score,i,before,after=best
    return {
        "available": True,
        "detected_at": iso(points[i][0]),
        "median_before_bq_m3": before,
        "median_after_bq_m3": after,
        "absolute_change_bq_m3": after-before,
        "relative_change_percent": ((after-before)/before*100.0) if before else None,
        "robust_score": score,
        "interpretation": "candidate_only",
    }


def _quality_flags(records: Sequence[dict[str, object]], points: Sequence[tuple[datetime,float]]) -> dict[str, object]:
    flags=[]
    invalid_factor=0; reconstructed=0; implausible=0; duplicates=0
    seen=set()
    for row,(dt,value) in zip(records,points):
        key=iso(dt)
        if key in seen: duplicates+=1
        seen.add(key)
        try: factor=float(row.get("factor"))
        except (TypeError,ValueError): factor=0
        if factor<=0: invalid_factor+=1
        if str(row.get("source") or '').lower() not in {"device","spir","radonscan"}: reconstructed+=1
        if value < 0 or value > 100000: implausible+=1
    if invalid_factor: flags.append({"code":"invalid_factor","count":invalid_factor,"severity":"error"})
    if reconstructed: flags.append({"code":"non_primary_source","count":reconstructed,"severity":"warning"})
    if implausible: flags.append({"code":"implausible_value","count":implausible,"severity":"error"})
    if duplicates: flags.append({"code":"duplicate_timestamp","count":duplicates,"severity":"warning"})
    return {"flags":flags,"flagged_records":sum(int(f["count"]) for f in flags),"status":"clean" if not flags else "review"}

def percentile(sorted_values: Sequence[float], p: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    p = max(0.0, min(1.0, float(p)))
    pos = (len(sorted_values) - 1) * p
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return float(sorted_values[lo])
    weight = pos - lo
    return float(sorted_values[lo] * (1.0 - weight) + sorted_values[hi] * weight)


def _linear_trend(points: Sequence[tuple[datetime, float]]) -> dict[str, float | None]:
    if len(points) < 2:
        return {"slope_bq_m3_per_day": None, "r_squared": None}
    origin = points[0][0]
    xs = [(dt - origin).total_seconds() / 86400.0 for dt, _ in points]
    ys = [value for _, value in points]
    x_mean = statistics.fmean(xs)
    y_mean = statistics.fmean(ys)
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom <= 0:
        return {"slope_bq_m3_per_day": None, "r_squared": None}
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom
    intercept = y_mean - slope * x_mean
    ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - y_mean) ** 2 for y in ys)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
    return {"slope_bq_m3_per_day": slope, "r_squared": max(0.0, min(1.0, r2))}


def _longest_gap(times: Sequence[datetime]) -> tuple[float, str | None, str | None]:
    if len(times) < 2:
        return 0.0, None, None
    longest = 0.0
    start = end = None
    for previous, current in zip(times, times[1:]):
        missing = max(0.0, (current - previous).total_seconds() / 3600.0 - 1.0)
        if missing > longest:
            longest = missing
            start = previous + timedelta(hours=1)
            end = current - timedelta(hours=1)
    return longest, iso(start), iso(end)


def _threshold_runs(points: Sequence[tuple[datetime, float]], threshold: float) -> dict[str, float | int | None]:
    total = 0
    events = 0
    longest = 0
    current = 0
    previous: datetime | None = None
    for measured_at, value in points:
        # A missing hour interrupts a continuous exceedance. This prevents
        # separate high readings around a data gap being reported as one run.
        if previous is not None and (measured_at - previous).total_seconds() > 5400:
            current = 0
        if value >= threshold:
            total += 1
            current += 1
            if current == 1:
                events += 1
            longest = max(longest, current)
        else:
            current = 0
        previous = measured_at
    return {
        "threshold_bq_m3": threshold,
        "hours": total,
        "percent": (total / len(points) * 100.0) if points else 0.0,
        "events": events,
        "longest_hours": longest,
    }


def _histogram(values: Sequence[float], bins: int | None = None) -> list[dict[str, float | int]]:
    if not values:
        return []
    low, high = min(values), max(values)
    if math.isclose(low, high):
        width = max(1.0, abs(low) * 0.1 or 1.0)
        low -= width / 2
        high += width / 2
    if bins is None:
        ordered=sorted(values); iqr=(percentile(ordered,.75) or 0)-(percentile(ordered,.25) or 0)
        width=2*iqr/(len(values)**(1/3)) if iqr>0 and len(values)>1 else 0
        bins=math.ceil((high-low)/width) if width>0 else round(math.sqrt(len(values)))
    bins = max(4, min(40, int(bins)))
    step = (high - low) / bins
    counts = [0] * bins
    for value in values:
        index = min(bins - 1, max(0, int((value - low) / step)))
        counts[index] += 1
    return [
        {
            "from": low + index * step,
            "to": low + (index + 1) * step,
            "count": count,
        }
        for index, count in enumerate(counts)
    ]


def _daily(points: Sequence[tuple[datetime, float]], zone) -> list[dict[str, object]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for dt, value in points:
        grouped[dt.astimezone(zone).date().isoformat()].append(value)
    result: list[dict[str, object]] = []
    for day in sorted(grouped):
        values = sorted(grouped[day])
        result.append(
            {
                "date": day,
                "samples": len(values),
                "coverage_percent": min(100.0, len(values) / 24.0 * 100.0),
                "mean_bq_m3": statistics.fmean(values),
                "median_bq_m3": statistics.median(values),
                "minimum_bq_m3": min(values),
                "maximum_bq_m3": max(values),
            }
        )
    return result


def _profiles(points: Sequence[tuple[datetime, float]], zone) -> tuple[list[dict[str, object]], list[dict[str, object]], list[list[dict[str, object]]]]:
    hourly: dict[int, list[float]] = defaultdict(list)
    weekday: dict[int, list[float]] = defaultdict(list)
    heat: dict[tuple[int, int], list[float]] = defaultdict(list)
    for dt, value in points:
        local = dt.astimezone(zone)
        hourly[local.hour].append(value)
        weekday[local.weekday()].append(value)
        heat[(local.weekday(), local.hour)].append(value)
    hourly_profile = [
        {"hour": hour, "samples": len(hourly[hour]), "mean_bq_m3": statistics.fmean(hourly[hour]) if hourly[hour] else None}
        for hour in range(24)
    ]
    weekday_profile = [
        {"weekday": day, "samples": len(weekday[day]), "mean_bq_m3": statistics.fmean(weekday[day]) if weekday[day] else None}
        for day in range(7)
    ]
    heatmap = [
        [
            {
                "weekday": day,
                "hour": hour,
                "samples": len(heat[(day, hour)]),
                "mean_bq_m3": statistics.fmean(heat[(day, hour)]) if heat[(day, hour)] else None,
            }
            for hour in range(24)
        ]
        for day in range(7)
    ]
    return hourly_profile, weekday_profile, heatmap


def analyse_records(
    records: Iterable[dict[str, object]],
    *,
    start: datetime | None = None,
    end: datetime | None = None,
    warning_threshold: float = 100.0,
    danger_threshold: float = 300.0,
    minimum_coverage_percent: float = 95.0,
    timezone_name: str = "UTC",
) -> dict[str, object]:
    zone, resolved_timezone = _resolve_zone(timezone_name)
    points: list[tuple[datetime, float]] = []
    normalized: list[dict[str, object]] = []
    for row in records:
        dt = parse_dt(row.get("completed_at"))
        value = row.get("bq_m3")
        if dt is None or value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(numeric):
            continue
        if start and dt < start:
            continue
        if end and dt > end:
            continue
        points.append((dt, numeric))
        normalized.append({**row, "completed_at": iso(dt), "bq_m3": numeric})
    order = sorted(range(len(points)), key=lambda i: points[i][0])
    points = [points[i] for i in order]
    normalized = [normalized[i] for i in order]
    values = [value for _, value in points]
    sorted_values = sorted(values)

    actual_start = points[0][0] if points else start
    actual_end = points[-1][0] if points else end
    requested_start = start or actual_start
    requested_end = end or actual_end
    if requested_start and requested_end and requested_end >= requested_start:
        expected = int(math.floor((requested_end - requested_start).total_seconds() / 3600.0)) + 1
    else:
        expected = len(points)
    expected = max(0, expected)
    coverage = min(100.0, len(points) / expected * 100.0) if expected else 0.0
    span_hours = ((actual_end - actual_start).total_seconds() / 3600.0) if actual_start and actual_end else 0.0
    sufficient = bool(values) and coverage >= minimum_coverage_percent

    longest_gap, gap_start, gap_end = _longest_gap([dt for dt, _ in points])
    daily = _daily(points, zone)
    hourly_profile, weekday_profile, heatmap = _profiles(points, zone)
    trend = _linear_trend(points)
    local_points = [(dt.astimezone(zone), v) for dt, v in points]
    weekdays = [v for dt, v in local_points if dt.weekday() < 5]
    weekends = [v for dt, v in local_points if dt.weekday() >= 5]
    daytime = [v for dt, v in local_points if 7 <= dt.hour < 19]
    nighttime = [v for dt, v in local_points if not 7 <= dt.hour < 19]
    geometric_mean, geometric_sd = _geometric(values)
    iqr = (percentile(sorted_values, 0.75) - percentile(sorted_values, 0.25)) if values else None

    uncertainty = _poisson_uncertainty(normalized, values)
    quality_flags = _quality_flags(normalized, points)
    autocorrelation = _autocorrelation(values)
    change_point = _change_point(points)
    effective_sample_size = _effective_sample_size(values)
    confidence_intervals = {
        "mean": _block_bootstrap_ci(values, statistics.fmean),
        "median": _block_bootstrap_ci(values, statistics.median),
    }
    moments = _moments(values)
    mann_kendall = _mann_kendall(points)
    moving_robust = _moving_robust(points)
    warning_events = _threshold_events(points, warning_threshold)
    danger_events = _threshold_events(points, danger_threshold)

    stats: dict[str, object] = {
        "samples": len(values),
        "expected_samples": expected,
        "missing_samples": max(0, expected - len(values)),
        "coverage_percent": coverage,
        "minimum_coverage_percent": minimum_coverage_percent,
        "sufficient": sufficient,
        "quality": "high" if coverage >= 98 and longest_gap <= 2 and quality_flags["status"] == "clean" else "good" if coverage >= 95 and longest_gap <= 6 and quality_flags["status"] == "clean" else "limited" if coverage >= 75 else "insufficient",
        "scientific_quality_class": "A" if coverage >= 98 and longest_gap <= 2 and quality_flags["status"] == "clean" and span_hours >= 720 else "B" if coverage >= 95 and longest_gap <= 6 and quality_flags["status"] == "clean" and span_hours >= 168 else "C" if coverage >= 75 and span_hours >= 24 else "D",
        "quality_reasons": ([f"coverage:{coverage:.1f}%"] if coverage < minimum_coverage_percent else []) + ([f"longest_gap:{longest_gap:.1f}h"] if longest_gap > 2 else []),
        "analysis_timezone": resolved_timezone,
        "period_start": iso(requested_start),
        "period_end": iso(requested_end),
        "actual_start": iso(actual_start),
        "actual_end": iso(actual_end),
        "data_span_hours": span_hours,
        "mean_bq_m3": statistics.fmean(values) if values else None,
        "median_bq_m3": statistics.median(values) if values else None,
        "minimum_bq_m3": min(values) if values else None,
        "maximum_bq_m3": max(values) if values else None,
        "standard_deviation_bq_m3": statistics.stdev(values) if len(values) > 1 else None,
        "variance_bq_m3": statistics.variance(values) if len(values) > 1 else None,
        "p05_bq_m3": percentile(sorted_values, 0.05),
        "p25_bq_m3": percentile(sorted_values, 0.25),
        "p75_bq_m3": percentile(sorted_values, 0.75),
        "p95_bq_m3": percentile(sorted_values, 0.95),
        "range_bq_m3": (max(values) - min(values)) if values else None,
        "interquartile_range_bq_m3": iqr,
        "median_absolute_deviation_bq_m3": _median_absolute_deviation(values),
        "geometric_mean_bq_m3": geometric_mean,
        "geometric_standard_deviation": geometric_sd,
        "theil_sen_slope_bq_m3_per_day": _theil_sen(points),
        "last_bq_m3": values[-1] if values else None,
        "longest_gap_hours": longest_gap,
        "longest_gap_start": gap_start,
        "longest_gap_end": gap_end,
        "weekday_mean_bq_m3": statistics.fmean(weekdays) if weekdays else None,
        "weekend_mean_bq_m3": statistics.fmean(weekends) if weekends else None,
        "day_mean_bq_m3": statistics.fmean(daytime) if daytime else None,
        "night_mean_bq_m3": statistics.fmean(nighttime) if nighttime else None,
        "exposure_index_bq_h_m3": sum(values),
        "trimmed_mean_10_bq_m3": _trimmed_mean(values, .10),
        "mean_median_ratio": (statistics.fmean(values)/statistics.median(values)) if values and statistics.median(values) else None,
        **moments,
        **trend,
    }
    return {
        "statistics": stats,
        "thresholds": {
            "warning": _threshold_runs(points, warning_threshold),
            "danger": _threshold_runs(points, danger_threshold),
        },
        "histogram": _histogram(values),
        "daily": daily,
        "hourly_profile": hourly_profile,
        "weekday_profile": weekday_profile,
        "weekly_heatmap": heatmap,
        "records": normalized,
        "uncertainty": uncertainty,
        "quality_control": quality_flags,
        "autocorrelation": autocorrelation,
        "change_point": change_point,
        "effective_sample_size": effective_sample_size,
        "confidence_intervals": confidence_intervals,
        "mann_kendall": mann_kendall,
        "moving_robust": moving_robust,
        "threshold_events": {"warning": warning_events, "danger": danger_events},
        "concentration_classes": _concentration_classes(values),
        "sensitivity": {
            "mean_bq_m3": statistics.fmean(values) if values else None,
            "median_bq_m3": statistics.median(values) if values else None,
            "trimmed_mean_10_bq_m3": _trimmed_mean(values,.10),
            "difference_mean_vs_trimmed_percent": ((statistics.fmean(values)-_trimmed_mean(values,.10)) / statistics.fmean(values)*100.0) if values and statistics.fmean(values) else None,
        },
        "methodology": {
            "measurement_basis": "completed_hourly_radonscan_records",
            "missing_data_imputed": False,
            "outliers_removed": False,
            "timezone": resolved_timezone,
            "uncertainty_scope": "counting_statistics_only_when_available",
        },
    }


def window_summary(
    records: Iterable[dict[str, object]],
    *,
    hours: int,
    end: datetime | None,
    minimum_coverage_percent: float,
) -> dict[str, object]:
    rows = list(records)
    if end is None:
        latest_times = [parse_dt(r.get("completed_at")) for r in rows]
        end = max((dt for dt in latest_times if dt), default=None)
    if end is None:
        return {
            "available": False,
            "reason": "no_data",
            "mean_bq_m3": None,
            "minimum_bq_m3": None,
            "maximum_bq_m3": None,
            "samples": 0,
            "required_samples": hours,
            "missing_samples": hours,
            "coverage_percent": 0.0,
            "period_start": None,
            "period_end": None,
            "data_span_hours": 0.0,
        }
    start = end - timedelta(hours=hours - 1)
    analysis = analyse_records(
        rows,
        start=start,
        end=end,
        minimum_coverage_percent=minimum_coverage_percent,
    )
    s = analysis["statistics"]
    span_ok = float(s["data_span_hours"] or 0.0) >= max(0.0, hours - 1.5)
    available = bool(s["samples"]) and bool(s["sufficient"]) and span_ok
    reason = None
    if not s["samples"]:
        reason = "no_data"
    elif not span_ok:
        reason = "period_not_reached"
    elif not s["sufficient"]:
        reason = "coverage_too_low"
    return {
        "available": available,
        "reason": reason,
        "mean_bq_m3": s["mean_bq_m3"] if available else None,
        "minimum_bq_m3": s["minimum_bq_m3"] if available else None,
        "maximum_bq_m3": s["maximum_bq_m3"] if available else None,
        "samples": s["samples"],
        "required_samples": hours,
        "missing_samples": max(0, hours - int(s["samples"])),
        "coverage_percent": min(100.0, int(s["samples"]) / hours * 100.0),
        "period_start": iso(start),
        "period_end": iso(end),
        "data_span_hours": s["data_span_hours"],
        "quality": s["quality"],
    }
