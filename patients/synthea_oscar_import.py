#!/usr/bin/env python3
"""
Synthea FHIR R4 → OSCAR EMR importer
Reads FHIR bundles from /synthea_out/fhir and inserts:
  - Patient          → demographic
  - Condition        → dxresearch
  - MedicationRequest→ drugs
"""
import json, os, re, random, string, sys
from datetime import datetime, date
import pymysql

# ── Config ────────────────────────────────────────────────────────────────
DB_HOST     = '192.168.2.38'
DB_PORT     = 3306
DB_USER     = 'root'
DB_PASS     = 'lyn1iIyOSVA='
DB_NAME     = 'oscar'
FHIR_DIR    = sys.argv[1] if len(sys.argv) > 1 else '/synthea_out/fhir'
PROVIDER_NO = '999998'   # oscardoc

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
    p = random.choice(ON_PREFIXES)
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
    conn = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER,
                           password=DB_PASS, database=DB_NAME,
                           cursorclass=pymysql.cursors.Cursor,
                           autocommit=False)
    cur = conn.cursor()

    files = sorted([
        f for f in os.listdir(FHIR_DIR)
        if f.endswith('.json')
        and 'hospitalInformation' not in f
        and 'practitionerInformation' not in f
    ])

    imported = 0
    for fname in files:
        with open(os.path.join(FHIR_DIR, fname), encoding='utf-8') as f:
            bundle = json.load(f)

        entries = bundle.get('entry', [])
        resources = {rt: [] for rt in ['Patient','Condition','MedicationRequest','Observation','Encounter']}
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

        dob = parse_date(pt.get('birthDate',''))
        yob = str(dob.year)  if dob else ''
        mob = str(dob.month) if dob else ''
        dob_d = str(dob.day) if dob else ''

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
            display = (r.get('code',{}).get('text') or coding.get('display',''))[:100]
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

        # Admit to default OSCAR program so eChart is accessible
        cur.execute("""
            INSERT INTO admission
              (client_id, program_id, provider_no, admission_date, discharge_date,
               temporary_admission_flag, automatic_discharge, admission_notes, lastUpdateDate)
            VALUES (%s, 10034, %s, NOW(), NULL, 0, 0, 'Auto-admitted by Synthea import', NOW())
        """, (demo_no, PROVIDER_NO))

        # ── Observations → measurements ───────────────────────────────────
        LOINC_MAP = {
            '4548-4':  'A1C',
            '29463-7': 'WT',
            '8302-2':  'HT',
            '39156-5': 'BMI',
            '2093-3':  'CHOL',
            '18262-6': 'LDL',
            '2085-9':  'HDL',
            '2571-8':  'TRIG',
            '33914-3': 'eGFR',
        }
        BP_PANEL   = '85354-9'
        SYS_LOINC  = '8480-6'
        DIA_LOINC  = '8462-4'

        meas_ct = 0
        for r in resources['Observation']:
            coding  = (r.get('code', {}).get('coding') or [{}])[0]
            loinc   = coding.get('code', '')
            obs_dt  = r.get('effectiveDateTime') or r.get('issued', '')
            obs_date = parse_date(obs_dt)

            if loinc == BP_PANEL:
                # Panel — extract systolic and diastolic components
                sys_val = dia_val = None
                for comp in r.get('component', []):
                    c_code = (comp.get('code', {}).get('coding') or [{}])[0].get('code', '')
                    val = comp.get('valueQuantity', {}).get('value')
                    if c_code == SYS_LOINC and val is not None:
                        sys_val = val
                    elif c_code == DIA_LOINC and val is not None:
                        dia_val = val
                if sys_val is not None and dia_val is not None:
                    data_field = f"{int(sys_val)}/{int(dia_val)}"
                    cur.execute("""
                        INSERT INTO measurements
                          (demographicNo, type, dataField, dateObserved, dateEntered, providerNo)
                        VALUES (%s, 'BP', %s, %s, NOW(), %s)
                    """, (demo_no, data_field, obs_date or date.today(), PROVIDER_NO))
                    meas_ct += 1
            elif loinc in LOINC_MAP:
                val = r.get('valueQuantity', {}).get('value')
                if val is not None:
                    cur.execute("""
                        INSERT INTO measurements
                          (demographicNo, type, dataField, dateObserved, dateEntered, providerNo)
                        VALUES (%s, %s, %s, %s, NOW(), %s)
                    """, (demo_no, LOINC_MAP[loinc], str(val), obs_date or date.today(), PROVIDER_NO))
                    meas_ct += 1

        # ── Encounters → casemgmt_note ────────────────────────────────────
        enc_ct = 0
        for r in resources['Encounter']:
            enc_type = (r.get('type') or [{}])[0].get('text', 'Encounter')
            period   = r.get('period', {})
            enc_date = parse_date(period.get('start', ''))
            cur.execute("""
                INSERT INTO casemgmt_note
                  (demographic_no, note, observation_date, update_date,
                   provider_no, signing_provider_no, signed, archived, encounter_type)
                VALUES (%s, %s, %s, NOW(), %s, %s, 1, 0, %s)
            """, (demo_no, enc_type, enc_date or date.today(),
                  PROVIDER_NO, PROVIDER_NO, enc_type[:100]))
            enc_ct += 1

        conn.commit()
        imported += 1
        dob_str = pt.get('birthDate','?')
        print(f"  {first} {last} ({dob_str}, {sex}) -> demo #{demo_no}"
              f"  [{cond_ct} dx, {med_ct} meds, {meas_ct} meas, {enc_ct} enc]")

    cur.close()
    conn.close()
    print(f"\n✓ {imported} patients imported into OSCAR.")

if __name__ == '__main__':
    main()
