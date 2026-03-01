-- TreasureHunt.Tectrix2026 relational schema (PostgreSQL)

CREATE TYPE department_enum AS ENUM ('IT','CSE','ECE','EE','AIML','BCA','MCA','MTech');
CREATE TYPE year_enum AS ENUM ('1st','2nd','3rd','4th');
CREATE TYPE participant_status_enum AS ENUM ('active','disqualified','withdrawn');
CREATE TYPE group_status_enum AS ENUM ('forming','active','disbanded','disqualified');
CREATE TYPE invitation_status_enum AS ENUM ('pending','accepted','rejected','cancelled');
CREATE TYPE game_status_enum AS ENUM ('draft','running','paused','closed');

CREATE TABLE participants (
  id BIGSERIAL PRIMARY KEY,
  participant_code VARCHAR(32) UNIQUE NOT NULL,
  full_name VARCHAR(120) NOT NULL,
  department department_enum NOT NULL,
  college_email VARCHAR(255) NOT NULL UNIQUE,
  college_roll VARCHAR(64) NOT NULL UNIQUE,
  study_year year_enum NOT NULL,
  status participant_status_enum NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE groups (
  id BIGSERIAL PRIMARY KEY,
  group_name VARCHAR(120) NOT NULL UNIQUE,
  leader_participant_id BIGINT NOT NULL REFERENCES participants(id),
  status group_status_enum NOT NULL DEFAULT 'forming',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
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
  token_hash VARCHAR(255) NOT NULL UNIQUE,
  question_text TEXT NOT NULL,
  is_final BOOLEAN NOT NULL DEFAULT FALSE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
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
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE game_settings (
  id BIGSERIAL PRIMARY KEY,
  status game_status_enum NOT NULL DEFAULT 'draft',
  final_qr_code_id BIGINT REFERENCES qr_codes(id),
  close_submissions BOOLEAN NOT NULL DEFAULT FALSE,
  updated_by_admin_id BIGINT REFERENCES admin_users(id),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT single_settings_row CHECK (id = 1)
);

CREATE TABLE team_completion (
  id BIGSERIAL PRIMARY KEY,
  group_id BIGINT NOT NULL UNIQUE REFERENCES groups(id),
  completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completion_message TEXT NOT NULL
);

CREATE TABLE broadcast_messages (
  id BIGSERIAL PRIMARY KEY,
  channel VARCHAR(32) NOT NULL DEFAULT 'in_app',
  message_text TEXT NOT NULL,
  sent_by_admin_id BIGINT NOT NULL REFERENCES admin_users(id),
  sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE audit_logs (
  id BIGSERIAL PRIMARY KEY,
  actor_type VARCHAR(20) NOT NULL,
  actor_id BIGINT NOT NULL,
  action_name VARCHAR(120) NOT NULL,
  entity_type VARCHAR(120),
  entity_id BIGINT,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- performance indexes
CREATE INDEX idx_submissions_group_submitted_at ON submissions(group_id, submitted_at DESC);
CREATE INDEX idx_submissions_qr_submitted_at ON submissions(qr_code_id, submitted_at DESC);
CREATE INDEX idx_group_members_participant ON group_members(participant_id);
CREATE INDEX idx_group_invitations_invited_status ON group_invitations(invited_participant_id, status);

-- NOTE:
-- Application logic should enforce minimum group size (2) before a group can start gameplay.
-- For PostgreSQL, partial unique indexes are usually preferred for active membership constraints.
CREATE UNIQUE INDEX uniq_active_group_per_participant
  ON group_members(participant_id)
  WHERE left_at IS NULL;

