# Adding Synthetic Patients to Your OSCAR Lab

Synthea generates realistic but fictional patient records in FHIR R4 format.
The import script reads those files and loads them into OSCAR with all the
required fields set correctly.

---

## Prerequisites

- Python 3.8+
- `pymysql` library: `pip install pymysql`
- Java 11+ (for Synthea)
- OSCAR lab running (`./setup/install.sh` completed)

---

## Step 1 — Download Synthea

```bash
curl -L https://github.com/synthetichealth/synthea/releases/latest/download/synthea-with-dependencies.jar \
     -o synthea.jar
```

---

## Step 2 — Generate Patients

Synthea uses US state geography. We use Massachusetts (the default) and
override the province to Ontario in the import script.

```bash
# Generate 20 patients
java -jar synthea.jar Massachusetts -p 20 --exporter.fhir.export=true

# Output lands in: output/fhir/
```

Options:
```bash
-p 50        # number of patients
--seed 12345 # reproducible output
```

---

## Step 3 — Import into OSCAR

OSCAR must be running first.

```bash
# Default (localhost:3306, password oscarlab)
python3 patients/synthea_oscar_import.py ./output/fhir/

# Custom DB connection (e.g. remote server)
OSCAR_DB_HOST=192.168.2.38 \
OSCAR_DB_PASS=lyn1iIyOSVA= \
python3 patients/synthea_oscar_import.py ./output/fhir/
```

Output:
```
Found 20 patient bundle(s) in ./output/fhir/

  Allegra Renner (2012-07-26, F) → demo #1  [12 dx, 3 meds]
  Antonio Watsica (1978-03-14, M) → demo #2  [8 dx, 5 meds]
  ...

✓ 20 patient(s) imported into OSCAR.
```

---

## Step 4 — Open an eChart

```
http://localhost:9090/oscar/oscarEncounter/IncomingEncounter.do
  ?case_program_id=10034&demographicNo=1&status=B
```

Change `demographicNo=1` to any number from the import output.

---

## Notes

- Each import run adds new patients (it does not check for duplicates).
  Re-running with the same files will create duplicate records.
- All patients are admitted to the OSCAR program (id 10034) automatically,
  which is required for eChart access.
- Province is set to `ON` (Ontario) regardless of Synthea's US geography.
- Health card numbers (HIN) are randomly generated for Ontario format.
