"""
setup_repo.py — PHARMA_CQV_ENGINE Complete Automated Setup Script
Creates all required folders and files for the production repository.
"""

import os
import json

# Define directory structure
DIRS = [
    "pharma_cqv_core",
    "tests",
    "evals",
    "data",
    ".github/workflows"
]

for d in DIRS:
    os.makedirs(d, exist_ok=True)
    print(f"Created directory: {d}/")

# 1. acceptance_criteria.json
acceptance_criteria = {
  "schema_version": "1.2.0",
  "criteria_version": "2026.11-v1.2-DRAFT",
  "effective_date": "2026-11-16",
  "author": "Rohit Kumar, PMP, CEng (India), CEA, FSEr (TÜV)",
  "independent_reviewer": "PENDING_QA_CQV_PEER_REVIEW",
  "guard_band_policy": {
    "rule_type": "simple_acceptance",
    "rounding_decimals": 6,
    "default_percent_basis": "reading",
    "missing_uncertainty_below_limit": "INDETERMINATE",
    "verdict_combiner": "Any FAIL -> FAIL; else any INDETERMINATE -> INDETERMINATE; else PASS (NOT_APPLICABLE ignored)"
  },
  "calibration_policy": {
    "expired_urs_id": "URS-CAL-001",
    "missing_date_urs_id": "URS-CAL-002",
    "missing_uncertainty_urs_id": "URS-CAL-003",
    "unlinked_reading_urs_id": "URS-CAL-004",
    "source_type": "ALCOA_PLUS"
  },
  "iso_14644_1_2015_table_a1": {
    "urs_id": "URS-PART-001",
    "source": "ISO 14644-1:2015 Annex A, Table A.1",
    "source_type": "REGULATORY_REFERENCED_ISO",
    "limit_direction": "lower",
    "area_to_min_locations": [
      {"max_area_m2": 2, "min_locations": 1},
      {"max_area_m2": 4, "min_locations": 2},
      {"max_area_m2": 6, "min_locations": 3},
      {"max_area_m2": 8, "min_locations": 4},
      {"max_area_m2": 10, "min_locations": 5},
      {"max_area_m2": 24, "min_locations": 6},
      {"max_area_m2": 28, "min_locations": 7},
      {"max_area_m2": 32, "min_locations": 8},
      {"max_area_m2": 36, "min_locations": 9},
      {"max_area_m2": 52, "min_locations": 10},
      {"max_area_m2": 56, "min_locations": 11},
      {"max_area_m2": 64, "min_locations": 12},
      {"max_area_m2": 68, "min_locations": 13},
      {"max_area_m2": 72, "min_locations": 14},
      {"max_area_m2": 76, "min_locations": 15},
      {"max_area_m2": 104, "min_locations": 16},
      {"max_area_m2": 108, "min_locations": 17},
      {"max_area_m2": 116, "min_locations": 18},
      {"max_area_m2": 148, "min_locations": 19},
      {"max_area_m2": 156, "min_locations": 20},
      {"max_area_m2": 192, "min_locations": 21},
      {"max_area_m2": 232, "min_locations": 22},
      {"max_area_m2": 276, "min_locations": 23},
      {"max_area_m2": 352, "min_locations": 24},
      {"max_area_m2": 436, "min_locations": 25},
      {"max_area_m2": 636, "min_locations": 26},
      {"max_area_m2": 1000, "min_locations": 27}
    ],
    "above_1000_m2_formula": "ceil(27 * (area_m2 / 1000.0))",
    "sample_volume_rules": {
      "urs_id": "URS-PART-002",
      "grade_a_override_liters": 1000.0,
      "grade_a_source": "EU GMP Annex 1 (2022) Section 4 (Cleanroom Qualification: 1 m³ minimum sample volume per location for Grade A)",
      "iso_formula": "Vs = (20 / Cn_m) * 1000 liters (minimum 2 liters and 60 seconds per sample)",
      "iso_source": "ISO 14644-1:2015 Annex A",
      "limit_direction": "lower"
    }
  },
  "criteria": [
    {
      "urs_id": "URS-DP-001",
      "title": "Positive cascade dP between different grades",
      "quantity_kind": "pressure",
      "unit": "Pa",
      "limit_direction": "lower",
      "limit_min": 10.0,
      "limit_max": None,
      "tolerance_source": "linked_instrument",
      "applies_to_grades": ["Grade A", "Grade B", "Grade C", "Grade D"],
      "applies_to_states": None,
      "applies_to_phases": None,
      "applies_to_zone_types": None,
      "applies_to_pressure_intents": ["positive_cascade"],
      "source": "EU GMP Annex 1 (2022) Section 4 (guidance minimum 10 Pa between different grades)",
      "source_type": "REGULATORY_GUIDANCE",
      "verification_status": "UNVERIFIED",
      "verified_on": None,
      "notes": "dP = P_room - P_neighbor. Engine applies only when neighbour grade differs."
    }
  ]
}

with open("pharma_cqv_core/acceptance_criteria.json", "w", encoding="utf-8") as f:
    json.dump(acceptance_criteria, f, indent=2)

# 2. guard_band.py
guard_band_code = '''"""
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
'''

with open("pharma_cqv_core/guard_band.py", "w", encoding="utf-8") as f:
    f.write(guard_band_code)

# 3. requirements.lock
with open("requirements.lock", "w", encoding="utf-8") as f:
    f.write("pydantic==2.13.4\nstreamlit>=1.38.0\nreportlab>=4.2.0\n")

print("setup_repo.py completed successfully for PHARMA_CQV_ENGINE!")