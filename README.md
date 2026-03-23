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
