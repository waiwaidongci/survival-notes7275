-- 002: 随访更正修订体系。已存在表需手工审查后应用；新库由ORM metadata直接建表。
ALTER TABLE followup_events ADD COLUMN revision_no INT NOT NULL DEFAULT 1;
ALTER TABLE survival_runs ADD COLUMN target_revision INT NOT NULL DEFAULT 0;
ALTER TABLE survival_runs ADD COLUMN result_revision INT NULL;
ALTER TABLE maintenance_notes ADD COLUMN run_revision_no INT NULL;
ALTER TABLE maintenance_notes ADD COLUMN superseded_at VARCHAR(64) NOT NULL DEFAULT '';
ALTER TABLE maintenance_notes ADD COLUMN supersede_reason TEXT NULL;
CREATE TABLE followup_corrections (
  id INT AUTO_INCREMENT PRIMARY KEY,
  reason TEXT NOT NULL,
  status VARCHAR(24) NOT NULL DEFAULT 'applied',
  items JSON NOT NULL,
  affected_run_ids JSON NOT NULL,
  applied_revision INT NULL,
  reject_reason TEXT NOT NULL DEFAULT '',
  owner VARCHAR(160) NOT NULL,
  created_at VARCHAR(64) NOT NULL
);
CREATE TABLE followup_revisions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  specimen_id INT NOT NULL,
  revision_no INT NOT NULL,
  duration_hours DOUBLE NOT NULL,
  event_observed BOOLEAN NOT NULL,
  note TEXT NOT NULL,
  source VARCHAR(24) NOT NULL DEFAULT 'seed',
  correction_id INT NULL,
  owner VARCHAR(160) NOT NULL DEFAULT '',
  created_at VARCHAR(64) NOT NULL,
  UNIQUE KEY uq_followup_revision (specimen_id, revision_no),
  CONSTRAINT fk_revision_correction FOREIGN KEY (correction_id) REFERENCES followup_corrections (id)
);
-- 既有终态随访补登修订号1的不可变留痕
INSERT INTO followup_revisions (specimen_id, revision_no, duration_hours, event_observed, note, source, owner, created_at)
SELECT specimen_id, 1, duration_hours, event_observed, note, 'seed', 'system', NOW(3) FROM followup_events;
CREATE INDEX followup_revision_specimen_idx ON followup_revisions (specimen_id);
CREATE INDEX followup_correction_status_idx ON followup_corrections (status, id);
CREATE INDEX survival_run_revision_idx ON survival_runs (target_revision, result_revision);
