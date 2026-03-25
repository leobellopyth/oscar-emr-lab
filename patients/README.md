# Synthetic Ontario Patients

This directory contains the FHIR → OSCAR import script for loading Synthea-generated
Ontario patients into the lab OSCAR instance.

## Quick start

```bash
pip install pymysql
python3 synthea_oscar_import.py /path/to/fhir/
```

The script reads FHIR R4 bundles and inserts into OSCAR's MariaDB:

| FHIR resource | OSCAR table | Notes |
|---|---|---|
| Patient | demographic | Ontario postal codes, HIN generated |
| Condition | dxresearch | SNOMED CT coding |
| MedicationRequest | drugs | active/discontinued status preserved |
| Observation | measurements | BP, A1C, WT, HT, BMI, lipid panel, eGFR |
| Encounter | casemgmt_note | encounter type as note text |
| (all patients) | admission | enrolled in program 10034 |

## Generating patients with Synthea

### Prerequisites
- Java 17+ (OpenJDK)
- Synthea JAR with PayerManager patch (see below)
- synthea-international Canada configs

### PayerManager patch (required for Canadian configs)

Synthea's `PayerManager.loadPayers()` calls `Location.getAbbreviation()` with Canadian
province names, which returns null. Apply this one-line patch before building:

In `src/main/java/org/mitre/synthea/world/agents/PayerManager.java`, line ~137:

```java
// Before (crashes with NPE on Canadian province codes):
String abbreviation = Location.getAbbreviation(location.state).toUpperCase();

// After:
String rawAbbr = Location.getAbbreviation(location.state);
String abbreviation = (rawAbbr != null ? rawAbbr : location.state).toUpperCase();
```

Also replace all `States Covered` values in
`src/main/resources/payers/insurance_companies_ca.csv` with `MA` (any valid US
state code — the payer data is not used in FHIR output).

### Generate 500 Ontario patients

```bash
java -jar synthea-with-dependencies.jar -p 500 Ontario \
  --exporter.baseDirectory=./output/ \
  --generate.demographics.default_file=/path/to/ca/geography/demographics_ca.csv \
  --generate.geography.zipcodes.default_file=/path/to/ca/geography/zipcodes_ca.csv \
  --generate.geography.timezones.default_file=/path/to/ca/geography/timezones_ca.csv \
  --generate.payers.insurance_companies.default_file=/path/to/ca/payers/insurance_companies_ca.csv \
  --generate.providers.hospitals.default_file=/path/to/ca/providers/hospitals_ca.csv \
  --generate.providers.primarycare.default_file=/path/to/ca/providers/primarycare_ca.csv
```

Then import:
```bash
python3 patients/synthea_oscar_import.py ./output/fhir/
```

## Configuration

Edit the top of `synthea_oscar_import.py` to match your OSCAR instance:

```python
DB_HOST     = '192.168.2.38'   # MariaDB host (use 127.0.0.1 if running locally)
DB_PORT     = 3306
DB_USER     = 'root'
DB_PASS     = 'your_password'
PROVIDER_NO = '999998'         # Must match a row in the provider table
```

## Fidelity

See `fidelity_report.md` at the repo root for a comparison of the generated cohort
against Statistics Canada 2021 Census and CCHS 2019-2020 Ontario prevalence data.

Key findings:
- Hypertension: 21.6% vs 22.4% reference (-0.8 pp)
- Diabetes T2: 8.5% vs 8.9% reference (-0.4 pp)
- COPD: overestimated (~17% vs ~8%) — apply age ≥35 filter for prevalence studies
- Depression: underestimated (0.5% vs ~9%) — known Synthea module limitation
