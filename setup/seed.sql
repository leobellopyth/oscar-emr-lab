-- OSCAR Lab Seed SQL
-- Run once after initial startup.
-- Idempotent: safe to run multiple times.
-- Sets up the OSCAR program, provider enrollment, and default program
-- so that eChart access works out of the box.

USE oscar;

-- 1. Create the OSCAR program (id=10034)
--    This is the CAISI program that controls eChart access.
INSERT INTO program
  (id, facilityId, name, type, maxAllowed, programStatus,
   transgender, firstNation, bedProgramAffiliated, alcohol,
   physicalHealth, mentalHealth, housing, exclusiveView,
   defaultServiceRestrictionDays, ageMin, ageMax, userDefined,
   lastUpdateDate, enableEncounterTime, enableEncounterTransportationTime,
   enableOCAN)
VALUES
  (10034, 1, 'OSCAR', 'Bed', 99999, 'active',
   0, 0, 0, 0,
   0, 0, 0, 'no',
   30, 1, 200, 1,
   NOW(), 0, 0,
   0)
ON DUPLICATE KEY UPDATE programStatus='active';

-- 2. Enroll provider oscardoc (999998) in the OSCAR program
INSERT INTO program_provider
  (program_id, provider_no, role_id, status, provider_type)
VALUES
  (10034, '999998', 1, 'active', 'doctor')
ON DUPLICATE KEY UPDATE status='active';

-- 3. Set the default program for oscardoc so eChart session is pre-populated
INSERT INTO provider_default_program
  (provider_no, program_id, signnote)
VALUES
  ('999998', 10034, 0)
ON DUPLICATE KEY UPDATE program_id=10034;
