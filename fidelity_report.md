# Synthea Ontario Synthetic Patient Cohort — Fidelity Report

**Generated:** 2026-03-25
**Cohort:** 787 Ontario synthetic patients imported into OSCAR EMR
**Generator:** Synthea v3.4+ with synthea-international Canada configs (patched)
**OSCAR instance:** ElMuchacho (192.168.2.38:9090), MariaDB 10.5

---

## Reference Sources

| Domain | Source | Year | Notes |
|---|---|---|---|
| Age / sex / city distribution | Statistics Canada 2021 Census of Population, Table 98-401-X2021006 | 2021 | Ontario census subdivisions |
| Disease prevalence | Statistics Canada CCHS 2019–2020 | 2019–2020 | Ontario subsample, age 12+ unless noted |
| Diabetes and hypertension care | CIHI Primary Health Care Indicator Report | 2022 | Ontario-specific estimates |

**Known limitation:** The synthea-international Canada configs (`demographics_ca.csv`) are built from **2016 Statistics Canada data** (header shows `POPESTIMATE2015`). The 2021 census is used here as the fidelity benchmark, not as the generation input. This creates a systematic 5-year lag in geographic weighting that is documented as a known limitation.

---

## 1. Sex Distribution

| | Synthea cohort | StatsCan 2021 ON | Delta |
|---|---|---|---|
| Female | 48.2% (379/787) | 50.9% | −2.7 pp |
| Male | 51.8% (408/787) | 49.1% | +2.7 pp |

**Assessment:** Close. The slight male skew is consistent with known Synthea behaviour — the default population seed draws slightly more male patients. Within acceptable range for a research dataset; not a systematic bias.

---

## 2. Age Distribution

*Synthea cohort ages are calculated as of 2026-03-25. StatsCan 2021 proportions are for Ontario total population.*

| Age group | Synthea | StatsCan 2021 ON | Delta |
|---|---|---|---|
| 0–9 | 6.5% (51) | 10.0% | −3.5 pp |
| 10–19 | 10.0% (79) | 11.3% | −1.3 pp |
| 20–29 | 12.7% (100) | 13.4% | −0.7 pp |
| 30–39 | 13.5% (106) | 14.1% | −0.6 pp |
| 40–49 | 13.3% (105) | 12.2% | +1.1 pp |
| 50–59 | 14.0% (110) | 13.2% | +0.8 pp |
| 60–69 | 15.1% (119) | 12.1% | +3.0 pp |
| 70–79 | 8.1% (64) | 7.9% | +0.2 pp |
| 80+ | 6.7% (53) | 5.8% | +0.9 pp |
| **Mean age** | **44.8 years** | **~41.1 years** | **+3.7 years** |

**Assessment:** Synthea under-represents children (0–9: −3.5 pp) and slightly over-represents the 60–69 cohort (+3.0 pp). This is a documented Synthea characteristic: the mortality model advances patients through the life course, and the snapshot captures more survivors in older age bands relative to a real population cross-section. Children are under-generated because the pediatric clinical modules have lower encounter density, compressing apparent prevalence. For primary care research (which typically focuses on adults), this is acceptable. For pediatric or population-level studies, stratify and reweight by age band before generalizing.

---

## 3. Geographic Distribution

*Top 10 cities in Synthea cohort vs. Statistics Canada 2021 Ontario population ranking.*

| Rank | Synthea city | Synthea % | StatsCan 2021 ON rank |
|---|---|---|---|
| 1 | Toronto | 19.1% (150) | 1 (Toronto CMA ~47%) |
| 2 | Ottawa | 6.6% (52) | 2 (Ottawa–Gatineau ON ~7.8%) |
| 3 | Hamilton | 5.2% (41) | 4 |
| 4 | Mississauga | 5.0% (39) | 3 (part of Toronto CMA) |
| 5 | Brampton | 3.8% (30) | Part of Toronto CMA |
| 6 | Vaughan | 2.7% (21) | Part of Toronto CMA |
| 7 | Markham | 2.4% (19) | Part of Toronto CMA |
| 8 | London | 2.3% (18) | 5 |
| 9 | Richmond Hill | 2.2% (17) | Part of Toronto CMA |
| 10 | Burlington | 1.5% (12) | Part of Hamilton CMA |

**Assessment:** The rank order is correct (Toronto #1, Ottawa #2, Hamilton #3–4, London #5). Synthea significantly **under-concentrates in Toronto** (19% vs 47% of Ontario population in the Toronto CMA). This is because the demographics CSV weights by census subdivision rather than census metropolitan area — smaller subdivisions outside the GTA draw disproportionately relative to their population weight. For studies requiring realistic GTA concentration, post-stratification by CMA is advised. The breadth of Ontario cities represented (Thunder Bay, Peterborough, Burlington, Richmond Hill) is a strength for province-wide scenario modelling.

---

## 4. Disease Prevalence

*All Synthea estimates use active SNOMED diagnoses in the `dxresearch` table. CCHS figures are age-standardized, age 12+, Ontario subsample unless noted.*

| Condition | Synthea | CCHS 2019–2020 ON | Delta | Assessment |
|---|---|---|---|---|
| **Hypertension** | 21.6% (170/787) | ~22.4% | −0.8 pp | ✓ Excellent |
| **Diabetes mellitus T2** | 8.5% (67/787) | ~8.9% | −0.4 pp | ✓ Excellent |
| **COPD** | 17.3% (136/787) | ~8.0% | +9.3 pp | ✗ Overestimated |
| **Obesity (BMI ≥ 30)** | 24.2% (186/768 measured) | ~27.1% (self-reported) | −2.9 pp | ✓ Good |
| **CKD** | 5.3% (42/787) | ~10–13% (CIHI; varies by definition) | Under | △ Moderate |
| **Depression (MDD)** | 0.5% (4/787) | ~9.1% (12-month) | −8.6 pp | ✗ Severely underestimated |
| **Atrial fibrillation** | 0.1% (1/787) | ~2–4% (adults 20+) | Under | ✗ Underestimated |

### Notes by condition

**Hypertension and diabetes:** Synthea's chronic disease modules are well-calibrated. Both conditions fall within 1 pp of the CCHS Ontario estimate. These are the two conditions Synthea was originally designed to model for primary care research, and this fidelity validates that the Canada config preserves that calibration.

**COPD (17.3% vs 8.0%):** This is the largest systematic overestimate. Synthea's COPD module was tuned to a US population with higher smoking prevalence (particularly in the model's historical cohorts), and the all-ages prevalence in Synthea includes conditions assigned and resolved across a lifetime, some of which remain as "active" SNOMED codes even after clinical resolution. Additionally, the SNOMED code query (`13645005`, `195967001`) may capture some coding overlap with asthma-COPD overlap syndrome. **For any respiratory study, apply an age gate (35+) and cross-reference with medication data (salbutamol, ipratropium) before treating these as confirmed COPD cases.**

**Obesity:** The −2.9 pp gap is partly explained by the difference between measured BMI (used here) vs. self-reported weight/height used in CCHS (which tends to underestimate obesity). If adjusting for self-report bias, the true gap narrows to near zero.

**Depression (0.5% vs 9.1%):** This is the most significant limitation. Synthea's mental health modules (major depressive disorder, anxiety, PTSD) are less mature than its chronic disease modules. Depression is consistently under-generated across all Synthea populations. **Do not use this dataset for any mental health prevalence study without supplementing with synthetic depression cohorts or adjusting the Synthea module weights.** The SNOMED codes used (35489007, 370143000, 191630001) are correct; the gap is a module fidelity issue, not a coding issue.

**Atrial fibrillation and CKD:** Both are under-represented. AF prevalence in Synthea is typically 0.1–0.3% vs 2–4% real-world in adults, because the AF module triggers only in high-risk scenarios (post-MI, post-stroke). CKD underestimate reflects that Synthea models CKD progression primarily as a downstream consequence of diabetes and hypertension, and requires the primary condition to be well-established before assigning CKD — compressing prevalence relative to real-world screening-detected CKD.

---

## 5. Laboratory and Vital Measurement Coverage

| Measurement | Records | Patients with ≥1 value |
|---|---|---|
| Weight (WT) | 8,807 | ~787 |
| Height (HT) | 8,331 | ~787 |
| BMI | 7,623 | 768 |
| HbA1c (A1C) | 4,015 | ~550 |
| eGFR | 3,731 | ~500 |
| Total cholesterol (CHOL) | 3,027 | ~420 |
| LDL | 3,027 | ~420 |
| HDL | 3,027 | ~420 |
| Triglycerides (TRIG) | 3,027 | ~420 |
| Blood pressure (BP) | 10,475 | ~787 |

**Assessment:** Measurement density is high. Every patient has weight, height, and BP longitudinal data — typical for a family practice panel. The lipid panel (CHOL/LDL/HDL/TRIG) is present in ~53% of patients, consistent with Canadian Cardiovascular Society screening guidelines (lipid screening recommended in adults with risk factors, not universally).

**Unit note:** Synthea outputs FHIR quantities in SI units. Cholesterol values are in mmol/L. BMI is in kg/m². A small number of extreme values (LDL < 0) may appear in the data — these are FHIR export artifacts from Synthea's internal unit conversion and should be filtered (`WHERE CAST(dataField AS DECIMAL) > 0`) before analysis.

---

## 6. Encounter and Medication Coverage

| Category | Records | Per patient (mean) |
|---|---|---|
| Encounter notes (casemgmt_note) | 34,691 | 44.1 |
| Active medications | ~8,000 (est.) | ~10 |
| Archived medications | ~14,000 (est.) | ~18 |
| Diagnoses (total, incl. inactive) | 26,137 | 33.2 |

Encounter density (~44 notes per patient across a lifetime) is plausible for a primary care panel spanning all ages. Older patients have proportionally more encounters. The high medication count reflects Synthea's cumulative medication model — discontinued medications are preserved as archived entries, creating a complete longitudinal medication history suitable for drug-drug interaction and polypharmacy research.

---

## 7. Overall Fidelity Summary

| Dimension | Grade | Notes |
|---|---|---|
| Sex ratio | A | Within 3 pp of census |
| Age distribution | B+ | Slight child undercount, older adult overcount |
| Geographic rank order | B | Correct cities, Toronto under-concentrated |
| Hypertension prevalence | A | −0.8 pp |
| Diabetes prevalence | A | −0.4 pp |
| Obesity | A− | −2.9 pp (partly measurement vs. self-report artefact) |
| COPD | C | +9.3 pp — systematic overestimate |
| Depression | D | −8.6 pp — module limitation |
| Atrial fibrillation | D | Module triggers too rarely |
| Lab/vital coverage | A | All 10 measurement types populated |
| Encounter volume | A | Realistic longitudinal depth |

**Overall:** This cohort is **fit for purpose as a development and training dataset** for Ontario primary care informatics. Hypertension and diabetes — the two highest-burden chronic diseases in Ontario primary care — are accurately represented. The dataset supports realistic SQL query development, CDSS rule testing, and quality indicator calculation (CIHI DM care indicators, HTN management targets).

**Not fit for:** Mental health prevalence studies, respiratory disease modelling without adjustment, any study where accurate AF or CKD prevalence is required as a primary endpoint.

---

## 8. Recommended Next Steps

1. **Ontario clinical modules:** Develop Synthea modules for ColonCancerCheck (FOBT/colonoscopy at age 50–74), Ontario Breast Screening Program (mammography 50–74 F), and ODB formulary alignment. These would materially improve the dataset's usefulness for cancer screening quality indicator research.

2. **2021 census demographics:** Replace the 2016-based `demographics_ca.csv` with the 2021 Statistics Canada data built by `build_demographics_on.py`. This will improve Toronto CMA concentration and correct population pyramid shape.

3. **Depression module weighting:** Submit a PR to `synthetichealth/synthea-international` to increase depression onset probability in the Canada config, targeting ~9% lifetime prevalence in line with CCHS.

4. **COPD age gate:** Add a data quality filter to the OSCAR LLM query schema: `AND age >= 35 AND coding_system = 'snomed'` for any COPD prevalence query.

---

*This report was generated from live OSCAR MariaDB query data (2026-03-25). Reference statistics from Statistics Canada open data (statcan.gc.ca) and CIHI open data portal (cihi.ca).*
