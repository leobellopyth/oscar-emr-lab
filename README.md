# oscar-emr-lab

A reproducible OSCAR EMR lab environment pre-loaded with Ontario synthetic patients,
built for primary care informatics research and education.

**What you get:**
- OSCAR 19 (Ontario) running in Docker on port 9090
- 787 synthetic Ontario patients with realistic demographics, diagnoses, medications, labs, and encounter history
- Natural language query tool (Groq SQL generation + MedGemma clinical interpretation)
- Fidelity report comparing the cohort to Statistics Canada 2021 Census and CCHS 2019–2020 Ontario data

---

## Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- Python 3.9+ with `pymysql` (`pip install pymysql`)
- 4 GB RAM available for Docker

---

## Setup

### 1. Clone and configure

```bash
git clone https://github.com/YOUR_USERNAME/oscar-emr-lab.git
cd oscar-emr-lab
cp .env.example .env
```

Edit `.env` and set a secure `MYSQL_ROOT_PASSWORD`.

### 2. Run the installer

**Linux / macOS:**
```bash
bash setup/install.sh
```

**Windows (PowerShell):**
```powershell
.\setup\install.ps1
```

The installer will:
1. Start the MariaDB and OSCAR containers
2. Wait for MariaDB to be ready
3. Seed the `oscardoc` provider account and the default CAISI program

### 3. Access OSCAR

Open `http://localhost:9090/oscar/` in your browser.

Login: **oscardoc** / **mac2002**

OSCAR takes about 60 seconds to fully start after the containers come up.

---

## Loading synthetic patients

After OSCAR is running, import the Ontario synthetic patients:

```bash
python3 patients/synthea_oscar_import.py /path/to/fhir/
```

See [patients/README.md](patients/README.md) for instructions on generating your own
cohort with Synthea, including the required PayerManager patch for Canadian configs.

The pre-built cohort used in development: 787 patients, 26k diagnoses, 22k medications,
53k measurements, 34k encounter notes.

---

## Natural language queries

`oscar_llm_query.py` lets you ask clinical questions in plain English:

```bash
pip install requests pymysql
python3 oscar_llm_query.py
```

```
Question: How many active patients have an HbA1c above 7?

[1/3] Groq generating SQL...
  SQL: SELECT COUNT(DISTINCT demographicNo) FROM measurements
       WHERE type = 'A1C' AND CAST(dataField AS DECIMAL(5,2)) > 7.0

  Run this query? (y/n): y

[2/3] Running against OSCAR MariaDB...
  1 rows returned

[3/3] MedGemma interpreting results...
  Of your 787 synthetic patients, 312 have at least one HbA1c measurement
  above 7.0%, indicating suboptimal glycemic control...
```

Requires a Groq API key (free tier available) and Ollama with MedGemma 4B installed locally.

---

## Repository structure

```
oscar-emr-lab/
├── README.md
├── docker-compose.yml          ← MariaDB + OSCAR containers
├── .env.example                ← Copy to .env, set password
├── volumes/
│   └── oscar.properties        ← Ontario billing region, program config
├── setup/
│   ├── install.sh              ← Linux/macOS one-command setup
│   ├── install.ps1             ← Windows PowerShell equivalent
│   └── seed.sql                ← Provider 999998 + program 10034
└── patients/
    ├── README.md               ← Synthea generation + import guide
    └── synthea_oscar_import.py ← FHIR R4 → OSCAR importer
```

---

## Fidelity

See [fidelity_report.md](fidelity_report.md) for a full comparison against population benchmarks.

| Dimension | Grade | Notes |
|---|---|---|
| Sex ratio | A | Within 3 pp of 2021 census |
| Age distribution | B+ | Slight child undercount |
| City rank order | B | Correct order, Toronto under-concentrated |
| Hypertension | A | −0.8 pp vs CCHS 2019–2020 |
| Diabetes T2 | A | −0.4 pp vs CCHS 2019–2020 |
| Obesity | A− | −2.9 pp (measurement vs self-report artefact) |
| COPD | C | +9.3 pp — apply age ≥35 filter |
| Depression | D | −8.6 pp — Synthea module limitation |

---

## Known limitations

- **2016 census weighting:** The synthea-international Canada configs use 2015/2016
  Statistics Canada data. Run `build_demographics_on.py` with the 2021 StatsCan
  Community Profiles CSV to update to 2021 data.
- **COPD overestimate:** Use `age >= 35` and medication cross-reference for any
  respiratory prevalence study.
- **Depression underestimate:** Do not use for mental health prevalence studies.
- **Synthetic data only:** This dataset is not derived from real patients and must
  not be used for clinical decisions or regulatory submissions.

---

## Roadmap

- [ ] Ontario clinical modules for Synthea (ColonCancerCheck, OBSP, ODB formulary)
- [ ] 2021 census demographics update
- [ ] Depression module reweighting PR to synthetichealth/synthea-international
- [ ] CIHI quality indicator calculator (DM, HTN, cancer screening)

---

## Capstone context

Built for the Health Informatics capstone project (April 2026). The pipeline addresses
the absence of publicly available Ontario-calibrated synthetic primary care data —
researchers currently rely on US Synthea datasets (Massachusetts) or wait months for
ICES ethics approval to access real Ontario data.

---

## License

OSCAR EMR is licensed under the GPL v2. Synthea is Apache 2.0.
This repository's scripts and configuration are MIT licensed.
