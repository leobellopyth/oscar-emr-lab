#!/usr/bin/env python3
"""
Synthea FHIR R4 → OSCAR EMR importer
-------------------------------------
Reads Synthea FHIR R4 bundles and inserts synthetic patients into OSCAR:
  - Patient          → demographic
  - Condition        → dxresearch
  - MedicationRequest→ drugs
  - Auto-admission   → admission (program 10034, required for eChart access)

Usage:
  python3 synthea_oscar_import.py /path/to/synthea/output/fhir/

  Or set environment variables to override DB connection:
  OSCAR_DB_HOST, OSCAR_DB_PORT, OSCAR_DB_USER, OSCAR_DB_PASS, OSCAR_DB_NAME
"""
import json, os, re, random, string, sys
from datetime import datetime, date
import pymysql

# ── Config (override via env vars or edit here) ───────────────────────────
DB_HOST     = os.environ.get('OSCAR_DB_HOST', 'localhost')
DB_PORT     = int(os.environ.get('OSCAR_DB_PORT', '3306'))
DB_USER     = os.environ.get('OSCAR_DB_USER', 'root')
DB_PASS     = os.environ.get('OSCAR_DB_PASS', 'oscarlab')
DB_NAME     = os.environ.get('OSCAR_DB_NAME', 'oscar')
PROVIDER_NO = '999998'   # oscardoc
PROGRAM_ID  = 10034      # OSCAR program (required for eChart)

# ── Helpers ───────────────────────────────────────────────────────────────
def strip_num(s):
    return re.sub(r'\d+$', '', s or '').strip() or 'Unknown'

def parse_date(ds):
    if not ds: return None
    try: return datetime.fromisoformat(ds[:10]).date()
    except: return None

ON_PREFIXES = ['K','L','M','N','P']
LETTERS = [c for c in string.ascii_uppercase if c not in 'DFIOQU']

def on_postal():
    p  = random.choice(ON_PREFIXES)
    d1 = random.randint(1,9)
    c1 = random.choice(LETTERS)
    d2 = random.randint(0,9)
    c2 = random.choice(LETTERS)
    d3 = random.randint(0,9)
    return f"{p}{d1}{c1} {d2}{c2}{d3}"

def on_hin():
    return ''.join(str(random.randint(0,9)) for _ in range(10))

# ── Main ──────────────────────────────────────────────────────────────────
def main():
    fhir_dir = sys.argv[1] if len(sys.argv) > 1 else '/synthea_out/fhir'

    if not os.path.isdir(fhir_dir):
        print(f"Error: FHIR directory not found: {fhir_dir}")
        print("Usage: python3 synthea_oscar_import.py /path/to/synthea/output/fhir/")
        sys.exit(1)

    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASS, database=DB_NAME,
        cursorclass=pymysql.cursors.Cursor
    )
    cur = conn.cursor()

    files = sorted([
        f for f in os.listdir(fhir_dir)
        if f.endswith('.json')
        and 'hospitalInformation' not in f
        and 'practitionerInformation' not in f
    ])

    print(f"Found {len(files)} patient bundle(s) in {fhir_dir}")
    print()

    imported = 0
    for fname in files:
        with open(os.path.join(fhir_dir, fname)) as f:
            bundle = json.load(f)

        entries = bundle.get('entry', [])
        resources = {rt: [] for rt in ['Patient','Condition','MedicationRequest']}
        for e in entries:
            rt = e['resource']['resourceType']
            if rt in resources:
                resources[rt].append(e['resource'])

        if not resources['Patient']:
            continue
        pt = resources['Patient'][0]

        # ── Demographics ──────────────────────────────────────────────────
        name = next((n for n in pt.get('name',[]) if n.get('use')=='official'),
                    pt.get('name',[{}])[0])
        last   = strip_num(name.get('family',''))
        given  = name.get('given', ['Unknown'])
        first  = strip_num(given[0])
        middle = strip_num(given[1]) if len(given) > 1 else ''

        dob   = parse_date(pt.get('birthDate',''))
        yob   = str(dob.year)  if dob else ''
        mob   = str(dob.month) if dob else ''
        dob_d = str(dob.day)   if dob else ''

        sex    = 'M' if pt.get('gender') == 'male' else 'F'
        addr   = pt.get('address', [{}])[0]
        street = (addr.get('line') or [''])[0]
        city   = addr.get('city','Toronto')
        postal = on_postal()
        phone  = next((t['value'] for t in pt.get('telecom',[])
                       if t.get('system')=='phone'), '')
        email  = next((t['value'] for t in pt.get('telecom',[])
                       if t.get('system')=='email'), '')
        hin    = on_hin()

        cur.execute("""
            INSERT INTO demographic
              (last_name, first_name, middleNames, address, city, province,
               postal, phone, email, year_of_birth, month_of_birth,
               date_of_birth, sex, hin, hc_type, provider_no,
               patient_status, date_joined, roster_status,
               chart_no, lastUpdateUser, lastUpdateDate,
               country_of_origin, official_lang)
            VALUES
              (%s,%s,%s,%s,%s,'ON',
               %s,%s,%s,%s,%s,
               %s,%s,%s,'ON',%s,
               'AC',CURDATE(),'RO',
               '',%s,NOW(),
               'CAN','ENG')
        """, (last, first, middle, street, city,
              postal, phone, email, yob, mob,
              dob_d, sex, hin, PROVIDER_NO,
              PROVIDER_NO))
        demo_no = cur.lastrowid

        # ── Conditions → dxresearch ───────────────────────────────────────
        cond_ct = 0
        for r in resources['Condition']:
            coding  = (r.get('code',{}).get('coding') or [{}])[0]
            code    = coding.get('code','')[:10]
            system  = coding.get('system','')
            onset   = parse_date(r.get('onsetDateTime',''))
            clin    = (r.get('clinicalStatus',{}).get('coding') or [{}])[0].get('code','active')
            status  = 'A' if clin in ('active','recurrence','relapse') else 'I'
            cs      = 'snomed' if 'snomed' in system.lower() else 'icd10'

            cur.execute("""
                INSERT INTO dxresearch
                  (demographic_no, start_date, update_date, status,
                   dxresearch_code, coding_system, association, providerNo)
                VALUES (%s,%s,NOW(),%s,%s,%s,0,%s)
            """, (demo_no, onset or date.today(), status, code, cs, PROVIDER_NO))
            cond_ct += 1

        # ── MedicationRequests → drugs ────────────────────────────────────
        med_ct = 0
        for r in resources['MedicationRequest']:
            med    = r.get('medicationCodeableConcept',{})
            text   = med.get('text','') or (med.get('coding') or [{}])[0].get('display','Unknown')
            gn     = text.split()[0] if text else 'Unknown'
            rx_dt  = parse_date(r.get('authoredOn','')) or date.today()
            active = r.get('status','active') == 'active'

            cur.execute("""
                INSERT INTO drugs
                  (provider_no, demographic_no, rx_date, end_date, written_date,
                   BN, GN, customName, special, archived, rxStatus, create_date,
                   GCN_SEQNO, takemin, takemax, freqcode, duration, durunit,
                   quantity, `repeat`, nosubs, prn, unit, method, route,
                   hide_cpp, hide_from_drug_profile, custom_note,
                   long_term, short_term, non_authoritative,
                   past_med, patient_compliance, start_date_unknown)
                VALUES
                  (%s,%s,%s,'2099-12-31',%s,
                   %s,%s,%s,%s,%s,%s,NOW(),
                   0,1,1,'od','30','d',
                   '30',0,0,0,'tab','Take','PO',
                   0,0,0,0,0,0,0,0,0)
            """, (PROVIDER_NO, demo_no, rx_dt, rx_dt,
                  gn[:255], gn[:255], text[:60], text,
                  0 if active else 1,
                  'active' if active else 'discontinued'))
            med_ct += 1

        # ── Admit to OSCAR program so eChart is accessible ────────────────
        cur.execute("""
            INSERT INTO admission
              (client_id, program_id, provider_no, admitted_by, admit_date,
               admit_time, discharge_date, discharge_time, temporary_admission_flag,
               automatic_discharge, notes)
            VALUES (%s,%s,%s,%s,CURDATE(),NOW(),NULL,NULL,0,0,'Synthea import')
        """, (demo_no, PROGRAM_ID, PROVIDER_NO, PROVIDER_NO))

        conn.commit()
        imported += 1
        dob_str = pt.get('birthDate','?')
        print(f"  {first} {last} ({dob_str}, {sex}) → demo #{demo_no}"
              f"  [{cond_ct} dx, {med_ct} meds]")

    cur.close()
    conn.close()
    print(f"\n✓ {imported} patient(s) imported into OSCAR.")
    print(f"\n  Open eChart:")
    print(f"  http://localhost:9090/oscar/oscarEncounter/IncomingEncounter.do"
          f"?case_program_id={PROGRAM_ID}&demographicNo=DEMO_NO&status=B")

if __name__ == '__main__':
    main()
