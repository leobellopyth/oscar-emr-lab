# oscar-emr-lab

**A one-command research and learning environment for OSCAR EMR 19**

OSCAR is the second-largest EMR in Ontario (~20% of family physicians).
In March 2026, Ontario announced a provincewide EMR consolidation — making
this an important moment to study, understand, and build on OSCAR's
clinical data architecture.

This package gives clinicians, informaticists, and students a fully working
OSCAR instance in minutes — no source compilation, no Bitbucket access,
no prior sysadmin experience required.

---

## What you get

- ✅ OSCAR EMR 19 running in Docker (pre-built image — no compilation)
- ✅ Login pre-configured (`oscardoc` / `mac2002` / PIN `1117`)
- ✅ CAISI program enrollment seeded (required for eChart access)
- ✅ eChart working out of the box
- ✅ Synthea patient import pipeline included
- ✅ Post-install bug fixes applied automatically

---

## Prerequisites

- [Docker Desktop](https://docs.docker.com/get-docker/) (Windows / Mac / Linux)
- That's it.

---

## Quick Start

```bash
git clone https://github.com/leobellopyth/oscar-emr-lab.git
cd oscar-emr-lab
bash setup/install.sh        # Linux / Mac
# or: .\setup\install.ps1    # Windows PowerShell
```

First run pulls ~620 MB from Docker Hub and starts Tomcat (~60–90 s).
No source compilation. No Bitbucket.

When done:

```
✓ OSCAR EMR 19 is running.

  Login:   http://localhost:9090/oscar/
  User:    oscardoc
  Pass:    mac2002
  PIN:     1117
```

---

## Adding Synthetic Patients (Synthea)

```bash
# 1. Download Synthea
curl -L https://github.com/synthetichealth/synthea/releases/latest/download/synthea-with-dependencies.jar \
     -o synthea.jar

# 2. Generate patients
java -jar synthea.jar Massachusetts -p 20

# 3. Import into OSCAR
pip install pymysql
python3 patients/synthea_oscar_import.py ./output/fhir/
```

Full guide: [patients/README.md](patients/README.md)

---

## Opening an eChart

After importing patients, open an eChart via:

```
http://localhost:9090/oscar/oscarEncounter/IncomingEncounter.do
  ?case_program_id=10034&demographicNo=1&status=B
```

Change `demographicNo=1` to any patient number from the import output.

---

## Stopping / Resetting

```bash
docker compose down          # stop (keeps data)
docker compose down -v       # full reset (wipes all data)
```

---

## ⚠️ Security Warning (Public Servers)

This package is designed for **local research and learning only**.

If you deploy on a VPS, cloud server, or any machine with a public IP:

- Port `9090` will be publicly accessible by default
- Default credentials (`mac2002`) are well-known
- There is no HTTPS, no firewall, no 2FA configured

**Before exposing publicly:**
1. Change the default password via OSCAR's admin panel
2. Add a firewall rule: `sudo ufw allow from YOUR_IP to any port 9090`
3. Put a reverse proxy (nginx) in front with HTTPS
4. Enable 2FA in OSCAR Admin → Security

For a home network behind a router with no port forwarding, the default setup is fine.

---

## Repository Structure

```
oscar-emr-lab/
├── docker-compose.yml        ← Minimal lab setup (db + oscar, port 9090)
├── .env.example              ← Copy to .env before first run
├── volumes/
│   └── oscar.properties      ← Pre-configured Ontario lab settings
├── setup/
│   ├── install.sh            ← One-command setup (Linux/Mac)
│   ├── install.ps1           ← One-command setup (Windows)
│   ├── seed.sql              ← Seeds CAISI program + provider enrollment
│   └── patch_forward_jsp.sh  ← Fixes eChart session bug
└── patients/
    ├── README.md             ← How to generate and import Synthea patients
    └── synthea_oscar_import.py
```

---

## Why This Exists

The official [open-osp](https://github.com/open-osp/open-osp) project is
production-grade and requires compiling OSCAR from source (30–60 min build).
This package is purpose-built for **research and learning**:

| | open-osp | oscar-emr-lab |
|---|---|---|
| Source compilation | Required | Not required |
| Setup time | 30–60 min | 5–10 min |
| Target audience | Sysadmins | Clinicians / researchers |
| Post-install fixes | Manual | Automated |
| Patient import | Not included | Synthea pipeline included |
| eChart working OOTB | No | Yes |

---

## Research Context

This lab was built to study OSCAR's clinical data model, FHIR mapping gaps,
and cognitive load in EMR workflows — from a nursing informatics perspective.

Key schema tables documented through this work:

| Table | Clinical meaning |
|---|---|
| `demographic` | Patient demographics (DOB split across 3 columns) |
| `dxresearch` | Problem list / diagnoses (SNOMED or ICD10) |
| `drugs` | Medications / prescriptions |
| `casemgmt_note` | Encounter / SOAP notes |
| `admission` | CAISI program enrollment per patient |
| `measurements` | Vitals and clinical measurements |

---

## Known Issues / Bugs Fixed

| Bug | Root cause | Fix |
|---|---|---|
| Drug profile 500 error | Hibernate null primitive on boolean columns | `install.sh` sets all to 0 |
| "Not in your program domain" | Patient not admitted to CAISI program | `seed.sql` + import auto-admits |
| eChart session crash | `case_program_id` null in session | `patch_forward_jsp.sh` |

---

## Using Claude Code (AI) to Explore OSCAR

This entire lab environment was built and debugged using
[Claude Code](https://claude.ai/code) — Anthropic's AI coding assistant —
as a learning and development tool alongside a clinician-researcher.

Claude Code was used to:
- Trace Java stack traces and identify root causes in a 20-year-old codebase
- Map the OSCAR database schema to clinical concepts
- Write and debug the Synthea import pipeline
- Identify and patch JSP session bugs without recompiling
- Connect OSCAR's architecture to FHIR and Ontario health policy context

### Suggested prompts to explore OSCAR with Claude Code

Once your lab is running, paste these into a Claude Code session:

```
"I have OSCAR EMR running at localhost:9090 with MariaDB at localhost:3306
(root / oscarlab). Help me understand how the CPP (Cumulative Patient
Profile) is stored in the database."
```

```
"Write a SQL query against my OSCAR database to find all patients
with more than 3 active medications and no encounter in the past year."
```

```
"Explain what the CAISI program_provider and admission tables do
clinically, and how they control eChart access in OSCAR."
```

```
"I want to understand how OSCAR stores encounter notes. Walk me through
the casemgmt_note table and how it relates to issues and the CPP."
```

Claude Code can read your local files, run queries, and explain what it
finds in clinical terms — useful if you're a clinician learning informatics
or an informaticist learning clinical context.

---

## License

MIT — see [LICENSE](LICENSE)

OSCAR EMR is licensed under GPL v2 by McMaster University / open-osp.
This repo contains only tooling and configuration — no OSCAR source code.

---

## Author

Built by [@leobellopyth](https://github.com/leobellopyth) —
Registered Nurse (RN) · Currently completing a Graduate Certificate
in Health Informatics at George Brown College (April 2026) ·
Clinical Informatics researcher

---

## Ontario Synthetic Patient Cohort

The repo includes a validated pipeline for generating Ontario-calibrated synthetic
patients using Synthea with the synthea-international Canada configs.

**Cohort (787 patients):** 26k diagnoses, 22k medications, 53k measurements
(BP, A1C, WT, HT, BMI, lipid panel, eGFR), 34k encounter notes.

### Fidelity vs. Statistics Canada 2021 + CCHS 2019–2020 Ontario

| Dimension | Grade | Notes |
|---|---|---|
| Sex ratio | A | Within 3 pp of 2021 census |
| Age distribution | B+ | Slight child undercount |
| Hypertension | A | 21.6% vs 22.4% reference (−0.8 pp) |
| Diabetes T2 | A | 8.5% vs 8.9% reference (−0.4 pp) |
| Obesity | A− | 24.2% vs 27.1% (measurement vs self-report gap) |
| COPD | C | Overestimated — apply age ≥35 filter |
| Depression | D | Underestimated — Synthea module limitation |

Full analysis: [fidelity_report.md](fidelity_report.md)

### Ontario geography fix (Synthea PayerManager patch)

The unmodified Synthea JAR crashes with a `NullPointerException` when using
Canadian configs. See [patients/README.md](patients/README.md) for the one-line patch.
