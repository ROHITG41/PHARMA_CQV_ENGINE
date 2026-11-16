[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](https://github.com)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-green.svg)](https://docs.pydantic.dev)
[![Compliance](https://img.shields.io/badge/GxP-EU%20GMP%20Annex%201%20%7C%20ISO%2014644-purple.svg)](https://github.com)

# PHARMA_CQV_ENGINE: Enterprise Pharma & Cleanroom CQV Decision-Support Agent

**Lead Architect:** Rohit Kumar, PMP, CEng (India), CEA, FSEr (TÜV)  
**Regulatory Alignment:** Designed with Draft EU GMP Annex 22's direction in mind (EMA 30 June – 1 July 2026 Workshop); EU GMP Annex 1 (2022) Tables 1, 2, 5, 6; ISO 14644-1:2015; ISO 14644-3:2019; GAMP 5 (2nd Ed.); 21 CFR Part 11-Aligned Demonstration Controls.

---

## 0. Intended Use, Non-Goals & Known Limitations
* **Assistive Decision-Support Pilot Only:** All compliance rulings execute inside deterministic Python functions (\pharma_cqv_core/\). Generative narratives are strictly \{{placeholder}}\-constrained and require mandatory Qualified Person (QP) / QA human-in-the-loop sign-off.
* **Synthetic Data Only:** Public deployments accept synthetic datasets only. Never upload real patient, batch, or proprietary facility records.
* **No PDF/OCR Extraction in v0.1/v0.2:** Structured telemetry inputs are validated via Pydantic v2 JSON contracts; protocol gap review accepts plain text wrapped in \<untrusted_protocol_document>\ sandbox tags.
* **No Formal GxP Validation Claim:** Gold labels (\cqv_cases_gold.json\) were authored by the principal architect and are structured for independent QA/CQV peer review prior to any commercial use.
* **Ephemeral Cloud Storage Disclosure:** On Streamlit Community Cloud, container storage is ephemeral; use the built-in **Download Signed State JSON** and **Import & Verify Session** buttons for durable record retention.

---

## Quickstart (Local IDE / VS Code / Cursor)
\\\ash
pip install -r requirements.lock
python tests/test_core.py
python tests/test_orchestration_and_mcp.py
streamlit run app_pharma_cqv_sentry.py
\\\

---

## Intellectual Property & Licensing Notice
**Copyright (c) 2026 Rohit Kumar. All Rights Reserved.**  
This software, core physics engines, schema models, and associated documentation are proprietary commercial assets. Unauthorized copying, modification, distribution, or commercial deployment of this code, via any medium, is strictly prohibited.
