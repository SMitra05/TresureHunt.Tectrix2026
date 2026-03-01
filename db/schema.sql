-- TreasureHunt.Tectrix2026 relational schema (PostgreSQL reference)

CREATE TYPE department_enum AS ENUM ('IT','CSE','ECE','EE','AIML','BCA','MCA','MTech');
CREATE TYPE year_enum AS ENUM ('1st','2nd','3rd','4th');
CREATE TYPE participant_status_enum AS ENUM ('active','disqualified','withdrawn');
CREATE TYPE group_status_enum AS ENUM ('forming','active','disbanded','disqualified');
CREATE TYPE invitation_status_enum AS ENUM ('pending','accepted','rejected','cancelled');
CREATE TYPE game_status_enum AS ENUM ('running','paused','closed');

CREATE TABLE participants (
  id BIGSERIAL PRIMARY KEY,
  participant_code VARCHAR(32) UNIQUE NOT NULL,
  full_name VARCHAR(120) NOT NULL,
  department department_enum NOT NULL,
  college_email VARCHAR(255) NOT NULL UNIQUE,
  college_roll VARCHAR(64) NOT NULL UNIQUE,
  study_year year_enum NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  password_salt VARCHAR(255) NOT NULL,
  status participant_status_enum NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE groups (
  id BIGSERIAL PRIMARY KEY,
  group_name VARCHAR(120) NOT NULL UNIQUE,
  leader_participant_id BIGINT NOT NULL REFERENCES participants(id),
  status group_status_enum NOT NULL DEFAULT 'forming',
  disqualified_reason TEXT,
  disqualified_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE group_members (
  id BIGSERIAL PRIMARY KEY,
  group_id BIGINT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  participant_id BIGINT NOT NULL REFERENCES participants(id),
  joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  left_at TIMESTAMPTZ,
  UNIQUE (group_id, participant_id)
);

CREATE TABLE group_invitations (
  id BIGSERIAL PRIMARY KEY,
  group_id BIGINT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  invited_participant_id BIGINT NOT NULL REFERENCES participants(id),
  invited_by_participant_id BIGINT NOT NULL REFERENCES participants(id),
  status invitation_status_enum NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  responded_at TIMESTAMPTZ,
  UNIQUE (group_id, invited_participant_id)
);

CREATE TABLE qr_codes (
  id BIGSERIAL PRIMARY KEY,
  qr_number VARCHAR(32) NOT NULL UNIQUE,
  token VARCHAR(255) NOT NULL UNIQUE,
  question_text TEXT NOT NULL,
  is_final BOOLEAN NOT NULL DEFAULT FALSE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE submissions (
  id BIGSERIAL PRIMARY KEY,
  group_id BIGINT NOT NULL REFERENCES groups(id),
  qr_code_id BIGINT NOT NULL REFERENCES qr_codes(id),
  submitted_by_participant_id BIGINT NOT NULL REFERENCES participants(id),
  answer_text TEXT NOT NULL,
  explanation_text TEXT NOT NULL,
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (group_id, qr_code_id)
);

CREATE TABLE admin_users (
  id BIGSERIAL PRIMARY KEY,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  password_salt VARCHAR(255) NOT NULL
);

CREATE TABLE participant_sessions (
  id BIGSERIAL PRIMARY KEY,
  participant_id BIGINT NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
  token VARCHAR(255) NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE admin_sessions (
  id BIGSERIAL PRIMARY KEY,
  admin_id BIGINT NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,
  token VARCHAR(255) NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE game_settings (
  id BIGSERIAL PRIMARY KEY,
  status game_status_enum NOT NULL DEFAULT 'running',
  final_qr_code_id BIGINT REFERENCES qr_codes(id),
  close_submissions BOOLEAN NOT NULL DEFAULT FALSE,
  broadcast_message TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT single_settings_row CHECK (id = 1)
);

CREATE UNIQUE INDEX uniq_active_group_per_participant
  ON group_members(participant_id)
  WHERE left_at IS NULL;

CREATE TABLE audit_logs (
  id BIGSERIAL PRIMARY KEY,
  actor_type VARCHAR(32) NOT NULL,
  actor_id BIGINT NOT NULL,
  action_name VARCHAR(128) NOT NULL,
  details TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
