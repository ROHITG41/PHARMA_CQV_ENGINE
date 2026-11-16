"""
pharma_cqv_core/guard_band.py — Simple-Acceptance Guard-Band & Calibration Engine
"""
from __future__ import annotations
import math
from datetime import date
from enum import Enum
from typing import Optional, Tuple

ROUND_DECIMALS = 6

class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INDETERMINATE = "INDETERMINATE"
    NOT_APPLICABLE = "NOT_APPLICABLE"

def _r(x: float) -> float:
    return round(float(x), ROUND_DECIMALS)

def _finite(*xs: Optional[float]) -> bool:
    return all(x is not None and math.isfinite(x) for x in xs)

def percent_half_width(pct: float, basis: str, reading_si: float, limit_si: Optional[float]) -> Optional[float]:
    base = reading_si if basis == "reading" else limit_si
    if not _finite(pct, base):
        return None
    return pct / 100.0 * abs(base)

def classify_lower(measured: float, limit: float, half_width: Optional[float]) -> Verdict:
    if not _finite(measured, limit):
        return Verdict.INDETERMINATE
    m, lim = _r(measured), _r(limit)
    if m >= lim:
        return Verdict.PASS
    if half_width is None or not _finite(half_width) or half_width < 0:
        return Verdict.INDETERMINATE
    return Verdict.INDETERMINATE if m >= _r(lim - half_width) else Verdict.FAIL

def classify_upper(measured: float, limit: float, half_width: Optional[float]) -> Verdict:
    if not _finite(measured, limit):
        return Verdict.INDETERMINATE
    m, lim = _r(measured), _r(limit)
    if m <= lim:
        return Verdict.PASS
    if half_width is None or not _finite(half_width) or half_width < 0:
        return Verdict.INDETERMINATE
    return Verdict.INDETERMINATE if m <= _r(lim + half_width) else Verdict.FAIL

def classify_two_sided(measured: float, lo: float, hi: float, half_width: Optional[float]) -> Verdict:
    if not _finite(measured, lo, hi) or lo > hi:
        return Verdict.INDETERMINATE
    m, lo_r, hi_r = _r(measured), _r(lo), _r(hi)
    if lo_r <= m <= hi_r:
        return Verdict.PASS
    if half_width is None or not _finite(half_width) or half_width < 0:
        return Verdict.INDETERMINATE
    return Verdict.INDETERMINATE if _r(lo_r - half_width) <= m <= _r(hi_r + half_width) else Verdict.FAIL

def band_and_margin(direction: str, measured: Optional[float], *, limit_min: Optional[float] = None,
                    limit_max: Optional[float] = None, half_width: Optional[float] = None) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    def edge(x: Optional[float], sign: int) -> Optional[float]:
        if x is None or half_width is None or not _finite(x, half_width) or half_width < 0:
            return None
        return _r(x + sign * half_width)

    if direction == "lower" and limit_min is not None:
        lo, hi = edge(limit_min, -1), _r(limit_min)
        margin = None if not _finite(measured) else _r(measured - limit_min)
    elif direction == "upper" and limit_max is not None:
        lo, hi = _r(limit_max), edge(limit_max, +1)
        margin = None if not _finite(measured) else _r(limit_max - measured)
    elif direction == "two-sided" and limit_min is not None and limit_max is not None:
        lo, hi = edge(limit_min, -1), edge(limit_max, +1)
        margin = None if not _finite(measured) else _r(min(measured - limit_min, limit_max - measured))
    else:
        return None, None, None
    if lo is None or hi is None:
        return None, None, margin
    return lo, hi, margin

def classify_evidence(confirmed: Optional[bool]) -> Verdict:
    if confirmed is None:
        return Verdict.INDETERMINATE
    return Verdict.PASS if confirmed else Verdict.FAIL

def classify(direction: str, measured: Optional[float], *, limit_min: Optional[float] = None,
             limit_max: Optional[float] = None, half_width: Optional[float] = None) -> Verdict:
    if direction == "not_applicable":
        return Verdict.NOT_APPLICABLE
    if measured is None:
        return Verdict.INDETERMINATE
    if direction == "lower":
        return classify_lower(measured, limit_min, half_width)
    if direction == "upper":
        return classify_upper(measured, limit_max, half_width)
    if direction == "two-sided":
        return classify_two_sided(measured, limit_min, limit_max, half_width)
    return Verdict.INDETERMINATE

def calibration_status(due: Optional[date], last: Optional[date], has_uncertainty: bool,
                       test_start: date, test_end: date) -> Tuple[Verdict, str]:
    if due is None:
        return Verdict.INDETERMINATE, "calibration due date missing"
    if due < test_end:
        return Verdict.FAIL, f"calibration expired {due.isoformat()} before test end {test_end.isoformat()}"
    if last is not None and last > test_start:
        return Verdict.INDETERMINATE, "last calibration date is after test start; verify record"
    if not has_uncertainty:
        return Verdict.INDETERMINATE, "uncertainty not provided"
    return Verdict.PASS, "calibration valid for full test window"
