-- seed.sql
-- Run once after OSCAR initialises its schema.
-- Seeds the provider account and CAISI program required by the Synthea importer.
-- Usage: docker exec -i oscar-emr-lab-db-1 mysql -uroot -p"$MYSQL_ROOT_PASSWORD" oscar < setup/seed.sql

-- ── Provider: oscardoc (provider_no 999998) ───────────────────────────────
-- This is the "system" provider used by automated imports.
-- Password hash below is for 'mac2002' (bcrypt). Change before production use.
INSERT IGNORE INTO provider (
    provider_no, last_name, first_name, provider_type,
    status, ohip_no, billing_no, practitionerNo,
    lastUpdateUser, lastUpdateDate
) VALUES (
    '999998', 'oscardoc', 'doctor', 'doctor',
    '1', '', '', '',
    'admin', NOW()
);

-- ── Security role for oscardoc ────────────────────────────────────────────
INSERT IGNORE INTO secUserRole (provider_no, role_name)
VALUES ('999998', 'admin');

-- ── Login credentials for oscardoc / mac2002 ─────────────────────────────
-- The open-osp image creates this user automatically on first boot via its
-- entrypoint script. This INSERT is a safety net if it was skipped.
INSERT IGNORE INTO security (
    provider_no, user_name, password, pin,
    forcePasswordReset, accountLocked, dateExpired
) VALUES (
    '999998', 'oscardoc',
    '7e3a9d0f56de2eff2e49a8c6a2afec7b',  -- MD5('mac2002') — change before production
    '1234', 0, 0, '2099-12-31'
);

-- ── CAISI program 10034 (default eChart program) ─────────────────────────
-- The admission INSERT in synthea_oscar_import.py references program id 10034.
-- If this program does not exist, all admissions will fail with a FK error.
INSERT IGNORE INTO program (
    id, facilityId, name, type, programStatus,
    intakeProgram, holdingTank, allowBatchAdmission, allowBatchDischarge,
    lastUpdateUser, lastUpdateDate
) VALUES (
    10034, 1, 'OSCAR', 'Bed', 'active',
    0, 0, 0, 0,
    'admin', NOW()
);
