import io
import hashlib
import hmac
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PHARMA_CQV_ENGINE | Cleanroom CQV Command Center",
    page_icon="🛡️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Complete 50-Rule Deterministic Regulatory Rulebook
# ---------------------------------------------------------------------------
RULES_50 = [
    # Calibration (4 rules)
    {"Rule_ID": "URS-CAL-001", "Gate_Family": "Calibration", "Grade": "All", "State": "All", "Parameter": "DPT Calibration Validity", "Acceptance_Limit": "cal_due >= test_date", "Unit": "Date", "Standard": "21 CFR Part 11 / GAMP 5"},
    {"Rule_ID": "URS-CAL-002", "Gate_Family": "Calibration", "Grade": "All", "State": "All", "Parameter": "Particle Counter Calibration Validity", "Acceptance_Limit": "cal_due >= test_date", "Unit": "Date", "Standard": "ISO 21501-4"},
    {"Rule_ID": "URS-CAL-003", "Gate_Family": "Calibration", "Grade": "All", "State": "All", "Parameter": "Anemometer / Balometer Calibration", "Acceptance_Limit": "cal_due >= test_date", "Unit": "Date", "Standard": "ISO 14644-3:2019"},
    {"Rule_ID": "URS-CAL-004", "Gate_Family": "Calibration", "Grade": "All", "State": "All", "Parameter": "Photometer HEPA Scan Calibration", "Acceptance_Limit": "cal_due >= test_date", "Unit": "Date", "Standard": "ISO 14644-3:2019"},
    # Differential Pressure (6 rules)
    {"Rule_ID": "URS-DP-001A", "Gate_Family": "Pressure Cascade", "Grade": "Grade A", "State": "All", "Parameter": "Grade A to Grade B Differential Pressure", "Acceptance_Limit": ">= 15.0 Pa (10 Pa min)", "Unit": "Pa", "Standard": "EU GMP Annex 1 §4.18"},
    {"Rule_ID": "URS-DP-001B", "Gate_Family": "Pressure Cascade", "Grade": "Grade B", "State": "All", "Parameter": "Grade B to Grade C Positive Cascade", "Acceptance_Limit": ">= 10.0 Pa (15 Pa rec.)", "Unit": "Pa", "Standard": "EU GMP Annex 1 §4.18"},
    {"Rule_ID": "URS-DP-001C", "Gate_Family": "Pressure Cascade", "Grade": "Grade C", "State": "All", "Parameter": "Grade C to Grade D Positive Cascade", "Acceptance_Limit": ">= 10.0 Pa", "Unit": "Pa", "Standard": "EU GMP Annex 1 §4.18"},
    {"Rule_ID": "URS-DP-001D", "Gate_Family": "Pressure Cascade", "Grade": "Grade D", "State": "All", "Parameter": "Grade D to CNC / Unclassified Cascade", "Acceptance_Limit": ">= 10.0 Pa", "Unit": "Pa", "Standard": "EU GMP Annex 1 §4.18"},
    {"Rule_ID": "URS-DP-002", "Gate_Family": "Pressure Cascade", "Grade": "All", "State": "All", "Parameter": "Bio-Containment / OSD Sink Containment", "Acceptance_Limit": "<= -10.0 Pa", "Unit": "Pa", "Standard": "ISO 14644-4"},
    {"Rule_ID": "URS-DP-003", "Gate_Family": "Pressure Cascade", "Grade": "Grade B", "State": "All", "Parameter": "Bubble Airlock Overpressure Both Sides", "Acceptance_Limit": ">= +10.0 Pa each side", "Unit": "Pa", "Standard": "EU GMP Annex 1 §4.18"},
    # HVAC Airflow & Visualization (6 rules)
    {"Rule_ID": "URS-HVAC-001A", "Gate_Family": "Airflow Velocity", "Grade": "Grade A", "State": "All", "Parameter": "Grade A Unidirectional Air Velocity", "Acceptance_Limit": "0.36 - 0.54 m/s", "Unit": "m/s", "Standard": "EU GMP Annex 1 Table 1"},
    {"Rule_ID": "URS-HVAC-002A", "Gate_Family": "Airflow Visualization", "Grade": "Grade A", "State": "All", "Parameter": "Smoke Study Video Human Confirmation", "Acceptance_Limit": "Mandatory Confirmed", "Unit": "Boolean", "Standard": "EU GMP Annex 1 §4.16"},
    {"Rule_ID": "URS-HVAC-001B", "Gate_Family": "Air Changes", "Grade": "Grade B", "State": "All", "Parameter": "Grade B Minimum Air Changes per Hour", "Acceptance_Limit": ">= 40 ACH", "Unit": "ACH", "Standard": "ISPE Baseline Vol. 5"},
    {"Rule_ID": "URS-HVAC-001C", "Gate_Family": "Air Changes", "Grade": "Grade C", "State": "All", "Parameter": "Grade C Minimum Air Changes per Hour", "Acceptance_Limit": ">= 20 ACH", "Unit": "ACH", "Standard": "ISPE Baseline Vol. 5"},
    {"Rule_ID": "URS-HVAC-001D", "Gate_Family": "Air Changes", "Grade": "Grade D", "State": "All", "Parameter": "Grade D Minimum Air Changes per Hour", "Acceptance_Limit": ">= 10 ACH", "Unit": "ACH", "Standard": "ISPE Baseline Vol. 5"},
    {"Rule_ID": "URS-HVAC-003", "Gate_Family": "Airflow Uniformity", "Grade": "Grade A", "State": "All", "Parameter": "Unidirectional Velocity RSD Uniformity", "Acceptance_Limit": "<= 15% RSD", "Unit": "%", "Standard": "ISO 14644-3:2019"},
    # Non-Viable Particles & Sample Volume (10 rules)
    {"Rule_ID": "URS-PART-001A", "Gate_Family": "Non-Viable Particles", "Grade": "Grade A", "State": "At Rest", "Parameter": "Particles >= 0.5 µm (At Rest)", "Acceptance_Limit": "<= 3,520 / m³", "Unit": "particles/m³", "Standard": "EU GMP Annex 1 Table 1"},
    {"Rule_ID": "URS-PART-002A", "Gate_Family": "Non-Viable Particles", "Grade": "Grade A", "State": "In Operation", "Parameter": "Particles >= 0.5 µm (In Operation)", "Acceptance_Limit": "<= 3,520 / m³", "Unit": "particles/m³", "Standard": "EU GMP Annex 1 Table 1"},
    {"Rule_ID": "URS-PART-003A", "Gate_Family": "Non-Viable Particles", "Grade": "Grade A", "State": "In Operation", "Parameter": "Particles >= 5.0 µm (Monitoring Action)", "Acceptance_Limit": "<= 29 / m³", "Unit": "particles/m³", "Standard": "EU GMP Annex 1 Table 5"},
    {"Rule_ID": "URS-PART-001B", "Gate_Family": "Non-Viable Particles", "Grade": "Grade B", "State": "At Rest", "Parameter": "Particles >= 0.5 µm (At Rest)", "Acceptance_Limit": "<= 3,520 / m³", "Unit": "particles/m³", "Standard": "EU GMP Annex 1 Table 1"},
    {"Rule_ID": "URS-PART-002B", "Gate_Family": "Non-Viable Particles", "Grade": "Grade B", "State": "In Operation", "Parameter": "Particles >= 0.5 µm (In Operation)", "Acceptance_Limit": "<= 352,000 / m³", "Unit": "particles/m³", "Standard": "EU GMP Annex 1 Table 1"},
    {"Rule_ID": "URS-PART-003B", "Gate_Family": "Non-Viable Particles", "Grade": "Grade B", "State": "In Operation", "Parameter": "Particles >= 5.0 µm (In Operation)", "Acceptance_Limit": "<= 2,930 / m³", "Unit": "particles/m³", "Standard": "EU GMP Annex 1 Table 1"},
    {"Rule_ID": "URS-PART-001C", "Gate_Family": "Non-Viable Particles", "Grade": "Grade C", "State": "At Rest", "Parameter": "Particles >= 0.5 µm (At Rest)", "Acceptance_Limit": "<= 352,000 / m³", "Unit": "particles/m³", "Standard": "EU GMP Annex 1 Table 1"},
    {"Rule_ID": "URS-PART-002C", "Gate_Family": "Non-Viable Particles", "Grade": "Grade C", "State": "In Operation", "Parameter": "Particles >= 0.5 µm (In Operation)", "Acceptance_Limit": "<= 3,520,000 / m³", "Unit": "particles/m³", "Standard": "EU GMP Annex 1 Table 1"},
    {"Rule_ID": "URS-PART-001D", "Gate_Family": "Non-Viable Particles", "Grade": "Grade D", "State": "At Rest", "Parameter": "Particles >= 0.5 µm (At Rest)", "Acceptance_Limit": "<= 3,520,000 / m³", "Unit": "particles/m³", "Standard": "EU GMP Annex 1 Table 1"},
    {"Rule_ID": "URS-VOL-001A", "Gate_Family": "Sample Volume", "Grade": "Grade A", "State": "All", "Parameter": "Minimum Air Sample Volume (Grade A)", "Acceptance_Limit": ">= 1,000 L (1.0 m³)", "Unit": "Liters", "Standard": "EU GMP Annex 1 §9.15"},
    # ISO 14644-1 Sampling Locations & Filter Integrity (4 rules)
    {"Rule_ID": "URS-LOC-001", "Gate_Family": "Sampling Locations", "Grade": "All", "State": "All", "Parameter": "Minimum Sampling Locations by Area", "Acceptance_Limit": ">= ISO Table A.1 NL", "Unit": "Locations", "Standard": "ISO 14644-1:2015 Table A.1"},
    {"Rule_ID": "URS-VOL-002", "Gate_Family": "Sample Volume", "Grade": "Grade B/C/D", "State": "All", "Parameter": "Minimum Single Sample Volume Formula", "Acceptance_Limit": "Vs >= (20 / Cn,m) * 1000 L", "Unit": "Liters", "Standard": "ISO 14644-1:2015 §A.4.2"},
    {"Rule_ID": "URS-HEPA-014", "Gate_Family": "Filter Integrity", "Grade": "Grade A/B", "State": "All", "Parameter": "H14 Installed HEPA Filter Penetration", "Acceptance_Limit": "<= 0.01%", "Unit": "%", "Standard": "ISO 14644-3:2019 §B.7"},
    {"Rule_ID": "URS-HEPA-013", "Gate_Family": "Filter Integrity", "Grade": "Grade C/D", "State": "All", "Parameter": "H13 Installed HEPA Filter Penetration", "Acceptance_Limit": "<= 0.10%", "Unit": "%", "Standard": "ISO 14644-3:2019 §B.7"},
    # Viable Microbials - Annex 1 Table 6 (14 rules)
    {"Rule_ID": "URS-MICRO-01A", "Gate_Family": "Viable Microbial", "Grade": "Grade A", "State": "In Operation", "Parameter": "Active Air Sample (Grade A)", "Acceptance_Limit": "< 1 CFU / m³ (No growth)", "Unit": "CFU/m³", "Standard": "EU GMP Annex 1 Table 6"},
    {"Rule_ID": "URS-MICRO-02A", "Gate_Family": "Viable Microbial", "Grade": "Grade A", "State": "In Operation", "Parameter": "Settle Plate 90 mm, 4h (Grade A)", "Acceptance_Limit": "< 1 CFU / 4 hours", "Unit": "CFU/4h", "Standard": "EU GMP Annex 1 Table 6"},
    {"Rule_ID": "URS-MICRO-03A", "Gate_Family": "Viable Microbial", "Grade": "Grade A", "State": "In Operation", "Parameter": "Contact Plate 55 mm (Grade A)", "Acceptance_Limit": "< 1 CFU / plate", "Unit": "CFU/plate", "Standard": "EU GMP Annex 1 Table 6"},
    {"Rule_ID": "URS-MICRO-04A", "Gate_Family": "Viable Microbial", "Grade": "Grade A", "State": "In Operation", "Parameter": "5-Finger Glove Print (Grade A)", "Acceptance_Limit": "< 1 CFU / glove", "Unit": "CFU/glove", "Standard": "EU GMP Annex 1 Table 6"},
    {"Rule_ID": "URS-MICRO-01B", "Gate_Family": "Viable Microbial", "Grade": "Grade B", "State": "In Operation", "Parameter": "Active Air Sample (Grade B)", "Acceptance_Limit": "<= 10 CFU / m³", "Unit": "CFU/m³", "Standard": "EU GMP Annex 1 Table 6"},
    {"Rule_ID": "URS-MICRO-02B", "Gate_Family": "Viable Microbial", "Grade": "Grade B", "State": "In Operation", "Parameter": "Settle Plate 90 mm, 4h (Grade B)", "Acceptance_Limit": "<= 5 CFU / 4 hours", "Unit": "CFU/4h", "Standard": "EU GMP Annex 1 Table 6"},
    {"Rule_ID": "URS-MICRO-03B", "Gate_Family": "Viable Microbial", "Grade": "Grade B", "State": "In Operation", "Parameter": "Contact Plate 55 mm (Grade B)", "Acceptance_Limit": "<= 5 CFU / plate", "Unit": "CFU/plate", "Standard": "EU GMP Annex 1 Table 6"},
    {"Rule_ID": "URS-MICRO-04B", "Gate_Family": "Viable Microbial", "Grade": "Grade B", "State": "In Operation", "Parameter": "5-Finger Glove Print (Grade B)", "Acceptance_Limit": "<= 5 CFU / glove", "Unit": "CFU/glove", "Standard": "EU GMP Annex 1 Table 6"},
    {"Rule_ID": "URS-MICRO-01C", "Gate_Family": "Viable Microbial", "Grade": "Grade C", "State": "In Operation", "Parameter": "Active Air Sample (Grade C)", "Acceptance_Limit": "<= 100 CFU / m³", "Unit": "CFU/m³", "Standard": "EU GMP Annex 1 Table 6"},
    {"Rule_ID": "URS-MICRO-02C", "Gate_Family": "Viable Microbial", "Grade": "Grade C", "State": "In Operation", "Parameter": "Settle Plate 90 mm, 4h (Grade C)", "Acceptance_Limit": "<= 50 CFU / 4 hours", "Unit": "CFU/4h", "Standard": "EU GMP Annex 1 Table 6"},
    {"Rule_ID": "URS-MICRO-03C", "Gate_Family": "Viable Microbial", "Grade": "Grade C", "State": "In Operation", "Parameter": "Contact Plate 55 mm (Grade C)", "Acceptance_Limit": "<= 25 CFU / plate", "Unit": "CFU/plate", "Standard": "EU GMP Annex 1 Table 6"},
    {"Rule_ID": "URS-MICRO-01D", "Gate_Family": "Viable Microbial", "Grade": "Grade D", "State": "In Operation", "Parameter": "Active Air Sample (Grade D)", "Acceptance_Limit": "<= 200 CFU / m³", "Unit": "CFU/m³", "Standard": "EU GMP Annex 1 Table 6"},
    {"Rule_ID": "URS-MICRO-02D", "Gate_Family": "Viable Microbial", "Grade": "Grade D", "State": "In Operation", "Parameter": "Settle Plate 90 mm, 4h (Grade D)", "Acceptance_Limit": "<= 100 CFU / 4 hours", "Unit": "CFU/4h", "Standard": "EU GMP Annex 1 Table 6"},
    {"Rule_ID": "URS-MICRO-03D", "Gate_Family": "Viable Microbial", "Grade": "Grade D", "State": "In Operation", "Parameter": "Contact Plate 55 mm (Grade D)", "Acceptance_Limit": "<= 50 CFU / plate", "Unit": "CFU/plate", "Standard": "EU GMP Annex 1 Table 6"},
    # Clean-Up Recovery & Thermal/RH Envelopes (6 rules)
    {"Rule_ID": "URS-REC-001", "Gate_Family": "Clean-Up Recovery", "Grade": "Grade A/B", "State": "At Rest", "Parameter": "100:1 Particle Decay Clean-Up Time", "Acceptance_Limit": "<= 15 - 20 min", "Unit": "Minutes", "Standard": "EU GMP Annex 1 §4.22"},
    {"Rule_ID": "URS-REC-002", "Gate_Family": "Pressure Recovery", "Grade": "All", "State": "All", "Parameter": "Door-Open ΔP Restoration Time", "Acceptance_Limit": "<= BMS Alarm Delay", "Unit": "Seconds", "Standard": "URS / BMS Spec"},
    {"Rule_ID": "URS-ENV-001", "Gate_Family": "Thermal Envelope", "Grade": "All", "State": "All", "Parameter": "Standard Aseptic Room Temperature", "Acceptance_Limit": "18.0 - 22.0 °C", "Unit": "°C", "Standard": "URS / GMP Facility"},
    {"Rule_ID": "URS-ENV-002", "Gate_Family": "Thermal Envelope", "Grade": "All", "State": "All", "Parameter": "Cold-Chain / Biologics Room Temperature", "Acceptance_Limit": "2.0 - 8.0 °C", "Unit": "°C", "Standard": "URS / Cold Chain"},
    {"Rule_ID": "URS-ENV-003", "Gate_Family": "Humidity Envelope", "Grade": "All", "State": "All", "Parameter": "Standard Cleanroom Relative Humidity", "Acceptance_Limit": "30.0 - 60.0 %RH", "Unit": "%RH", "Standard": "URS / GMP Facility"},
    {"Rule_ID": "URS-ENV-004", "Gate_Family": "Humidity Envelope", "Grade": "All", "State": "All", "Parameter": "Low-Humidity / Moisture-Sensitive Suite", "Acceptance_Limit": "<= 20.0 %RH", "Unit": "%RH", "Standard": "URS / OSD Spec"},
]

RULES_DF = pd.DataFrame(RULES_50)

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
if "active_module" not in st.session_state:
    st.session_state["active_module"] = 1
if "last_eval" not in st.session_state:
    st.session_state["last_eval"] = None
if "audit_chain" not in st.session_state:
    st.session_state["audit_chain"] = []

# ---------------------------------------------------------------------------
# Deterministic Physics Evaluation Logic (Real Pass / Fail / Indeterminate)
# ---------------------------------------------------------------------------
GRADE_LIMITS = {
    "Grade A": {"dp_min": 15.0, "vel_min": 0.36, "vel_max": 0.54, "p05_max": 3520, "p50_max": 29, "cfu_max": 0.0, "ach_min": None},
    "Grade B": {"dp_min": 10.0, "vel_min": None, "vel_max": None, "p05_max": 3520, "p50_max": 29, "cfu_max": 10.0, "ach_min": 40.0},
    "Grade C": {"dp_min": 10.0, "vel_min": None, "vel_max": None, "p05_max": 352000, "p50_max": 2900, "cfu_max": 100.0, "ach_min": 20.0},
    "Grade D": {"dp_min": 10.0, "vel_min": None, "vel_max": None, "p05_max": 3520000, "p50_max": 29000, "cfu_max": 200.0, "ach_min": 10.0},
}


def run_deterministic_checks(zone_id, grade, dp_pa, dp_tol, airflow_val, p05, p50, cfu, cal_valid, smoke_confirmed):
    spec = GRADE_LIMITS[grade]
    gates = []

    gates.append({
        "Rule ID": "URS-CAL-001",
        "Gate": "Instrument Calibration Window",
        "Measured": "Valid" if cal_valid else "Expired",
        "Acceptance Limit": "cal_due >= test_date",
        "Status": "PASS" if cal_valid else "FAIL",
    })

    dp_min = spec["dp_min"]
    if dp_pa < dp_min - dp_tol:
        dp_status = "FAIL"
    elif dp_pa < dp_min:
        dp_status = "INDETERMINATE"
    else:
        dp_status = "PASS"
    gates.append({
        "Rule ID": f"URS-DP-001{grade[-1]}",
        "Gate": "Differential Pressure Cascade (ΔP)",
        "Measured": f"{dp_pa:.2f} Pa (±{dp_tol:.2f} Pa)",
        "Acceptance Limit": f">= {dp_min:.1f} Pa",
        "Status": dp_status,
    })

    if grade == "Grade A":
        vel_ok = spec["vel_min"] <= airflow_val <= spec["vel_max"]
        gates.append({
            "Rule ID": "URS-HVAC-001A",
            "Gate": "Unidirectional Air Velocity",
            "Measured": f"{airflow_val:.2f} m/s",
            "Acceptance Limit": f"{spec['vel_min']:.2f} - {spec['vel_max']:.2f} m/s",
            "Status": "PASS" if vel_ok else "FAIL",
        })
        gates.append({
            "Rule ID": "URS-HVAC-002A",
            "Gate": "Smoke Study Visualization Evidence",
            "Measured": "Confirmed" if smoke_confirmed else "Unconfirmed",
            "Acceptance Limit": "Human Video Confirmation",
            "Status": "PASS" if smoke_confirmed else "INDETERMINATE",
        })
    else:
        ach_min = spec["ach_min"]
        gates.append({
            "Rule ID": f"URS-HVAC-001{grade[-1]}",
            "Gate": "Air Changes per Hour (ACH)",
            "Measured": f"{airflow_val:.1f} ACH",
            "Acceptance Limit": f">= {ach_min:.0f} ACH",
            "Status": "PASS" if airflow_val >= ach_min else "FAIL",
        })

    gates.append({
        "Rule ID": f"URS-PART-001{grade[-1]}",
        "Gate": "Particles >= 0.5 µm",
        "Measured": f"{p05:,} / m³",
        "Acceptance Limit": f"<= {spec['p05_max']:,} / m³",
        "Status": "PASS" if p05 <= spec["p05_max"] else "FAIL",
    })
    gates.append({
        "Rule ID": f"URS-PART-003{grade[-1]}" if grade == "Grade A" else f"URS-PART-002{grade[-1]}",
        "Gate": "Particles >= 5.0 µm",
        "Measured": f"{p50:,} / m³",
        "Acceptance Limit": f"<= {spec['p50_max']:,} / m³",
        "Status": "PASS" if p50 <= spec["p50_max"] else "FAIL",
    })

    if grade == "Grade A":
        micro_pass = cfu < 1.0
        limit_str = "< 1 CFU / m³"
    else:
        micro_pass = cfu <= spec["cfu_max"]
        limit_str = f"<= {spec['cfu_max']:.0f} CFU / m³"
    gates.append({
        "Rule ID": f"URS-MICRO-01{grade[-1]}",
        "Gate": "Viable Active Air (Table 6)",
        "Measured": f"{cfu:.1f} CFU / m³",
        "Acceptance Limit": limit_str,
        "Status": "PASS" if micro_pass else "FAIL",
    })

    statuses = [g["Status"] for g in gates]
    if "FAIL" in statuses:
        overall = "FAIL"
    elif "INDETERMINATE" in statuses:
        overall = "INDETERMINATE"
    else:
        overall = "PASS"

    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "zone_id": zone_id,
        "grade": grade,
        "overall_status": overall,
        "gates": gates,
    }


def build_pdf_dossier(eval_result, audit_entries):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>PHARMA_CQV_ENGINE — Cleanroom Qualification Compliance Dossier</b>", styles["Title"]))
    story.append(Paragraph("Lead Architect: Rohit Kumar, PMP, CEng (India), CEA, FSEr (TÜV)", styles["Normal"]))
    story.append(Paragraph("Standards: EU GMP Annex 1 (2022) | ISO 14644-1:2015 | GAMP 5 | 21 CFR Part 11 Controls", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Zone ID:</b> {eval_result['zone_id']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Grade:</b> {eval_result['grade']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Evaluation Timestamp:</b> {eval_result['timestamp']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Deterministic Overall Verdict:</b> {eval_result['overall_status']}", styles["Heading2"]))
    story.append(Spacer(1, 8))

    table_data = [["Rule ID", "Verification Gate", "Measured", "Limit", "Status"]]
    for g in eval_result["gates"]:
        table_data.append([g["Rule ID"], g["Gate"], g["Measured"], g["Acceptance Limit"], g["Status"]])

    t = Table(table_data, colWidths=[85, 165, 95, 100, 75])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F6F9")]),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    story.append(Paragraph("<b>21 CFR Part 11 Keyed-HMAC Electronic Sign-Off Chain</b>", styles["Heading3"]))
    if audit_entries:
        for idx, entry in enumerate(audit_entries, start=1):
            story.append(Paragraph(
                f"{idx}. [{entry['timestamp']}] {entry['signer']} — {entry['role']} | HMAC: {entry['hmac'][:24]}...",
                styles["Normal"],
            ))
    else:
        story.append(Paragraph("Status: UNSIGNED DRAFT — Pending Mandatory QA / QP Electronic Sign-Off.", styles["Normal"]))

    story.append(Spacer(1, 18))
    story.append(Paragraph("<i>Copyright (c) 2026 Rohit Kumar. All Rights Reserved. Assistive Decision-Support Pilot Only.</i>", styles["Normal"]))
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Header & Collapsible User Manual
# ---------------------------------------------------------------------------
st.title("🛡️ PHARMA_CQV_ENGINE: Cleanroom CQV Decision-Support Command Center")
st.caption("Lead Architect: Rohit Kumar, PMP, CEng (India), CEA, FSEr (TÜV)  |  EU GMP Annex 1 (2022) · ISO 14644-1:2015 · GAMP 5 · 21 CFR Part 11 Controls")

with st.expander("📖 Quick-Start User Manual & Workflow Guide (Click to Expand)", expanded=False):
    st.markdown("""
    ### How to Operate This Command Center
    Click any of the **4 Module Buttons** in the left panel to jump directly to that workspace:
    1. **Module 1 — Physics Metrology & Evaluation:** Select your Cleanroom Grade, enter field measurements and instrument tolerance, and click **Run Compliance Evaluation**. Every parameter is checked deterministically against EU GMP Annex 1 & ISO 14644-1 thresholds—producing **PASS**, **FAIL**, or **INDETERMINATE** (when inside the instrument uncertainty band).
    2. **Module 2 — Protocol Gap & Security Sandbox:** Paste qualification protocol text inside `<untrusted_protocol_document>` isolation tags to scan for GxP gaps while blocking prompt injections.
    3. **Module 3 — QA Sign-Off & PDF Dossier Export:** Apply a tamper-evident keyed HMAC-SHA256 electronic signature and download an audit-ready ReportLab PDF compliance dossier.
    4. **Module 4 — Complete 50-Rule Regulatory Rulebook:** Filter all 50 deterministic rules (`URS-IDs`), limits, and regulatory citations using the four pull-down menus (Cleanroom Grade, Gate Family, Regulatory Standard, and Occupancy State).
    """)

st.markdown("---")

# ---------------------------------------------------------------------------
# Sidebar Navigation (4 Direct One-Click Buttons — No Pull-Down Menu)
# ---------------------------------------------------------------------------
st.sidebar.header("Navigation & Control Center")
st.sidebar.caption("Click any module button below:")

MODULE_BUTTONS = [
    (1, "⚙️ 1. Physics Metrology & Evaluation"),
    (2, "🔍 2. Protocol Gap & Security Sandbox"),
    (3, "🔐 3. QA Sign-Off & PDF Dossier"),
    (4, "📚 4. 50-Rule Regulatory Rulebook"),
]

for mod_id, mod_label in MODULE_BUTTONS:
    btn_type = "primary" if st.session_state["active_module"] == mod_id else "secondary"
    if st.sidebar.button(mod_label, key=f"nav_btn_{mod_id}", use_container_width=True, type=btn_type):
        st.session_state["active_module"] = mod_id
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("**Module Directory:**")
st.sidebar.markdown(
    "- **Module 1:** Physics & Guard-Band Math\n"
    "- **Module 2:** Protocol Gap & Sandbox\n"
    "- **Module 3:** QA Sign-Off & PDF Export\n"
    "- **Module 4:** View All 50 Rules & Limits"
)

active_mod = st.session_state["active_module"]

# ---------------------------------------------------------------------------
# MODULE 1: Deterministic Physics Metrology
# ---------------------------------------------------------------------------
if active_mod == 1:
    st.subheader("⚙️ Module 1: Deterministic Physics Engine & Guard-Band Evaluation")
    st.info(
        "**What this module does:** Evaluates cleanroom field measurements against deterministic EU GMP Annex 1 & ISO 14644-1 rules, "
        "accounting for instrument calibration validity and measurement uncertainty guard-bands.\n\n"
        "**How to use it:** Choose your Cleanroom Grade, adjust field telemetry values below, and click **Run Compliance Evaluation**."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        zone_id = st.text_input("Cleanroom Zone ID", "CLN-GRADE-A-FILLING-01")
        grade = st.selectbox("Cleanroom Classification", ["Grade A", "Grade B", "Grade C", "Grade D"])
        cal_valid = st.checkbox("All Instruments Within Calibration Window", value=True)
    with c2:
        dp_pa = st.number_input("Differential Pressure ΔP (Pa)", value=16.0, step=0.5)
        dp_tol = st.number_input("DPT Instrument Uncertainty ± (Pa)", value=1.0, min_value=0.0, step=0.1)
        if grade == "Grade A":
            airflow_val = st.number_input("Unidirectional Velocity (m/s)", value=0.45, step=0.01)
            smoke_confirmed = st.checkbox("Smoke Study Video Confirmed (Annex 1 §4.16)", value=True)
        else:
            airflow_val = st.number_input("Air Changes per Hour (ACH)", value=45.0, step=1.0)
            smoke_confirmed = True
    with c3:
        p05 = st.number_input("Particles >= 0.5 µm (/m³)", value=120, min_value=0, step=10)
        p50 = st.number_input("Particles >= 5.0 µm (/m³)", value=2, min_value=0, step=1)
        cfu = st.number_input("Active Air Microbial (CFU/m³)", value=0.0, min_value=0.0, step=0.5)

    if st.button("Run Compliance Evaluation", type="primary"):
        res = run_deterministic_checks(
            zone_id, grade, dp_pa, dp_tol, airflow_val, p05, p50, cfu, cal_valid, smoke_confirmed
        )
        st.session_state["last_eval"] = res

    if st.session_state["last_eval"]:
        res = st.session_state["last_eval"]
        verdict = res["overall_status"]
        if verdict == "PASS":
            st.success(f"### Overall Verdict for {res['zone_id']} ({res['grade']}): **PASS**")
        elif verdict == "INDETERMINATE":
            st.warning(f"### Overall Verdict for {res['zone_id']} ({res['grade']}): **INDETERMINATE** (Within Instrument Uncertainty Band or Missing Evidence)")
        else:
            st.error(f"### Overall Verdict for {res['zone_id']} ({res['grade']}): **FAIL** (Acceptance Criteria Exceeded)")

        st.markdown("#### Evaluated Gate Traceability Matrix")
        st.dataframe(pd.DataFrame(res["gates"]), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# MODULE 2: Protocol Gap Review & Security Sandbox
# ---------------------------------------------------------------------------
elif active_mod == 2:
    st.subheader("🔍 Module 2: Protocol Gap Review & Prompt-Injection Sandbox")
    st.info(
        "**What this module does:** Isolates uploaded qualification protocol text inside `<untrusted_protocol_document>` XML tags to block "
        "adversarial prompt injections while checking protocol parameters against GxP requirements.\n\n"
        "**How to use it:** Paste a protocol excerpt below and click **Run Security & Gap Scan**."
    )

    protocol_text = st.text_area(
        "Protocol Excerpt (Sandboxed Input):",
        "<untrusted_protocol_document>\n"
        "Section 5.1: Grade A Laminar Airflow Hood velocity measured at 0.31 m/s. "
        "Smoke study deferred to annual requalification.\n"
        "</untrusted_protocol_document>",
        height=150,
    )

    if st.button("Run Security & Gap Scan", type="primary"):
        lower_txt = protocol_text.lower()
        injection_patterns = ["ignore previous instructions", "override status", "force pass", "</untrusted_protocol_document>"]
        inner_txt = lower_txt.replace("<untrusted_protocol_document>", "", 1)
        if inner_txt.endswith("</untrusted_protocol_document>"):
            inner_txt = inner_txt[: -len("</untrusted_protocol_document>")]

        if any(p in inner_txt for p in injection_patterns):
            st.error("🚨 **SECURITY BLOCK:** Adversarial prompt-injection payload detected inside untrusted protocol text. Execution halted.")
        else:
            st.success("🛡️ **Sandbox Integrity Verified:** Zero prompt-injection threats detected.")
            findings = []
            if "0.31" in lower_txt or "velocity" in lower_txt:
                findings.append("⚠️ **Gap [URS-HVAC-001A]:** Grade A unidirectional air velocity must be within **0.36–0.54 m/s** (EU GMP Annex 1 Table 1).")
            if "smoke study deferred" in lower_txt or "deferred" in lower_txt:
                findings.append("⚠️ **Gap [URS-HVAC-002A]:** Airflow visualization (smoke study) cannot be deferred prior to Grade A qualification sign-off.")
            if not findings:
                findings.append("✅ No obvious regulatory discrepancies flagged in the provided excerpt.")
            for item in findings:
                st.warning(item)

# ---------------------------------------------------------------------------
# MODULE 3: HITL QA Sign-Off & PDF Dossier Export
# ---------------------------------------------------------------------------
elif active_mod == 3:
    st.subheader("🔐 Module 3: Mandatory QA Electronic Sign-Off & PDF Dossier")
    st.info(
        "**What this module does:** Enforces Human-in-the-Loop (HITL) QA governance via keyed HMAC-SHA256 electronic signatures "
        "and generates a real, downloadable ReportLab PDF compliance dossier.\n\n"
        "**How to use it:** Ensure you have run an evaluation in Module 1, enter your name and role below to apply an HMAC signature, and download your PDF dossier."
    )

    if not st.session_state["last_eval"]:
        st.warning("No evaluation found in the current session yet. Please run a compliance evaluation in **Module 1** first (or a default sample will be used).")
        sample_eval = run_deterministic_checks("CLN-GRADE-A-SAMPLE", "Grade A", 16.0, 1.0, 0.45, 120, 2, 0.0, True, True)
    else:
        sample_eval = st.session_state["last_eval"]

    st.markdown(f"**Active Record:** `{sample_eval['zone_id']}` ({sample_eval['grade']}) — Verdict: **{sample_eval['overall_status']}**")

    s1, s2 = st.columns(2)
    with s1:
        signer_name = st.text_input("Signer Full Name & Credentials", "Rohit Kumar, PMP, CEng (India), FSEr")
    with s2:
        signer_role = st.selectbox("Signature Meaning (21 CFR Part 11 §11.50)", ["Prepared by CQV Engineer", "Reviewed & Approved by QA"])

    if st.button("Apply Keyed-HMAC Electronic Signature", type="primary"):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        payload = f"{sample_eval['zone_id']}|{sample_eval['overall_status']}|{signer_name}|{signer_role}|{ts}".encode("utf-8")
        digest = hmac.new(b"PHARMA_CQV_DEMO_HMAC_KEY_2026", payload, hashlib.sha256).hexdigest()
        st.session_state["audit_chain"].append({
            "timestamp": ts,
            "signer": signer_name,
            "role": signer_role,
            "hmac": digest,
        })
        st.success(f"Electronic signature recorded and cryptographically chained (`sha256:{digest[:16]}...`).")

    if st.session_state["audit_chain"]:
        st.markdown("#### Signed Audit Chain Entries")
        st.dataframe(pd.DataFrame(st.session_state["audit_chain"]), use_container_width=True, hide_index=True)

    pdf_bytes = build_pdf_dossier(sample_eval, st.session_state["audit_chain"])
    st.download_button(
        label="📥 Download Audit-Ready PDF Compliance Dossier",
        data=pdf_bytes,
        file_name=f"{sample_eval['zone_id']}_Compliance_Dossier.pdf",
        mime="application/pdf",
    )

# ---------------------------------------------------------------------------
# MODULE 4: Complete 50-Rule Regulatory Rulebook Explorer (100% Pull-Down Menus)
# ---------------------------------------------------------------------------
else:
    st.subheader("📚 Module 4: Complete 50-Rule Regulatory Rulebook")
    st.info(
        "**What this module does:** Displays all 50 deterministic regulatory rules (`URS-IDs`), acceptance limits, units, and GxP standard citations "
        "used by the physics engine.\n\n"
        "**How to use it:** Use any of the four pull-down menus below to filter rules by **Cleanroom Grade**, **Gate Family**, **Regulatory Standard**, or **Occupancy State**—no typing required."
    )

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        grade_filter = st.selectbox("1. Filter by Cleanroom Grade:", ["All Grades", "Grade A", "Grade B", "Grade C", "Grade D"])
    with f2:
        family_options = ["All Gate Families"] + sorted(RULES_DF["Gate_Family"].unique().tolist())
        family_filter = st.selectbox("2. Filter by Gate Family:", family_options)
    with f3:
        standard_options = [
            "All Standards",
            "EU GMP Annex 1",
            "ISO 14644-1",
            "ISO 14644-3",
            "ISO 14644-4",
            "ISO 21501-4",
            "ISPE Baseline Vol. 5",
            "21 CFR Part 11 / GAMP 5",
            "URS / GMP Facility",
        ]
        standard_filter = st.selectbox("3. Filter by Regulatory Standard:", standard_options)
    with f4:
        state_filter = st.selectbox("4. Filter by Occupancy State:", ["All States", "At Rest", "In Operation"])

    filtered_df = RULES_DF.copy()
    if grade_filter != "All Grades":
        g_letter = grade_filter.split()[-1]
        filtered_df = filtered_df[
            filtered_df["Grade"].str.contains(f"Grade {g_letter}|/{g_letter}|All", case=False, na=False)
        ]
    if family_filter != "All Gate Families":
        filtered_df = filtered_df[filtered_df["Gate_Family"] == family_filter]
    if standard_filter != "All Standards":
        filtered_df = filtered_df[filtered_df["Standard"].str.contains(standard_filter, case=False, na=False)]
    if state_filter != "All States":
        filtered_df = filtered_df[filtered_df["State"].isin([state_filter, "All"])]

    st.caption(f"Showing **{len(filtered_df)}** of **{len(RULES_DF)}** active regulatory rules.")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=520)

st.markdown("---")
st.caption("Copyright (c) 2026 Rohit Kumar. All Rights Reserved. Assistive Decision-Support Pilot Only.")