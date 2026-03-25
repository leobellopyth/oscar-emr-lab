"""
oscar_llm_query.py

OSCAR EMR Natural Language Query Tool
Groq (Llama 3.1 70B) generates the SQL.
MedGemma 4B (local Ollama) interprets the results clinically.
"""

import json
import os
import requests
import pymysql

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")  # export GROQ_API_KEY=gsk_...
GROQ_MODEL     = "llama-3.3-70b-versatile"
GROQ_URL       = "https://api.groq.com/openai/v1/chat/completions"

OLLAMA_URL     = "http://localhost:11434/api/chat"
MEDGEMMA_MODEL = "alibayram/medgemma:4b"

DB_HOST = "192.168.2.38"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "lyn1iIyOSVA="
DB_NAME = "oscar"

# ---------------------------------------------------------------------------
# OSCAR SCHEMA PROMPT
# This is the "map" we hand to Groq so it knows what tables exist in OSCAR.
# ---------------------------------------------------------------------------

OSCAR_SCHEMA = """
You are a SQL expert working with OSCAR EMR (MariaDB).
Generate a single read-only SELECT query. Never use INSERT, UPDATE, DELETE, or DROP.
Return ONLY the raw SQL — no explanation, no markdown fences.

Tables available:

demographic(demographic_no, first_name, last_name, year_of_birth, month_of_birth,
            date_of_birth, sex, city, province, postal, phone, email,
            patient_status, hin, provider_no, roster_status, end_date)
  -- patient_status: 'AC'=active, 'IN'=inactive, 'DE'=deceased
  -- DOB is split across three columns: year_of_birth, month_of_birth, date_of_birth

dxresearch(dxresearch_no, demographic_no, dxresearch_code, coding_system,
           status, start_date, update_date, providerNo)
  -- diagnoses; coding_system = 'icd10' or 'snomed'
  -- status: 'A'=active, 'I'=inactive

drugs(drugid, demographic_no, GN, BN, customName, dosage, unit, route,
      freqcode, start_date, end_date, rx_date, archived, long_term,
      past_med, rxStatus)
  -- GN=generic name, BN=brand name
  -- archived=0 means currently active prescription

casemgmt_note(note_id, demographic_no, note, update_date, observation_date,
              provider_no, signed, archived, encounter_type)
  -- encounter/SOAP notes; archived=0 means current

admission(am_id, client_id, program_id, provider_no, admission_date,
          discharge_date, admission_status)
  -- CAISI program enrollment; client_id = demographic_no

measurements(id, demographicNo, type, dataField, measuringInstruction,
             dateObserved, dateEntered)
  -- vitals and labs; demographicNo links to demographic.demographic_no
  -- type examples: 'A1C' (HbA1c), 'BP' (blood pressure), 'WT' (weight), 'HT' (height)
  -- dataField holds the measurement value as text
"""

# ---------------------------------------------------------------------------
# STEP 1: Send question + schema to Groq → get SQL back
# ---------------------------------------------------------------------------

def generate_sql(question):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": OSCAR_SCHEMA},
            {"role": "user",   "content": question},
        ],
        "temperature": 0,
        "max_tokens": 512,
    }
    response = requests.post(GROQ_URL, json=payload, headers=headers)
    response.raise_for_status()
    sql = response.json()["choices"][0]["message"]["content"].strip()
    if sql.startswith("```"):
        lines = sql.split("\n")
        sql = "\n".join(lines[1:-1])
    return sql

# ---------------------------------------------------------------------------
# STEP 2: Run the SQL against OSCAR MariaDB (read-only connection)
# ---------------------------------------------------------------------------

def run_query(sql):
    connection = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
    )
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

# ---------------------------------------------------------------------------
# STEP 3: Send SQL results to local MedGemma for clinical interpretation
# ---------------------------------------------------------------------------

def interpret(question, sql, rows):
    context = (
        f"Question: {question}\n\n"
        f"SQL used:\n{sql}\n\n"
        f"Results ({len(rows)} rows):\n"
        f"{json.dumps(rows[:20], default=str, indent=2)}"
    )
    payload = {
        "model": MEDGEMMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a clinical informatics assistant. "
                    "Interpret the following OSCAR EMR query results "
                    "in plain clinical language. Be concise and clinically relevant."
                ),
            },
            {"role": "user", "content": context},
        ],
        "stream": False,
    }
    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    return response.json()["message"]["content"]

# ---------------------------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("OSCAR LLM Query")
    print("  SQL generation : Groq (Llama 3.1 70B)")
    print("  Interpretation : MedGemma 4B (local)")
    print("  Database       : OSCAR MariaDB @ 192.168.2.38")
    print("=" * 60)
    print("Type 'quit' to exit\n")

    while True:
        question = input("Question: ").strip()
        if not question:
            continue
        if question.lower() == "quit":
            break

        print("\n[1/3] Groq generating SQL...")
        try:
            sql = generate_sql(question)
        except Exception as e:
            print(f"     Groq error: {e}\n")
            continue

        print(f"\n  SQL: {sql}\n")
        confirm = input("  Run this query? (y/n): ").strip().lower()
        if confirm != "y":
            print("  Skipped.\n")
            continue

        print("\n[2/3] Running against OSCAR MariaDB...")
        try:
            rows = run_query(sql)
            print(f"  {len(rows)} rows returned\n")
        except Exception as e:
            print(f"  Query failed: {e}\n")
            continue

        print("[3/3] MedGemma interpreting results...")
        try:
            interpretation = interpret(question, sql, rows)
        except Exception as e:
            print(f"  MedGemma error: {e}\n")
            continue

        print(f"\n{interpretation}\n")
        print("-" * 60 + "\n")

if __name__ == "__main__":
    main()
