CREATE TABLE IF NOT EXISTS participants (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  participant_code TEXT NOT NULL UNIQUE,
  full_name TEXT NOT NULL,
  department TEXT NOT NULL,
  college_email TEXT NOT NULL UNIQUE,
  college_roll TEXT NOT NULL UNIQUE,
  study_year TEXT NOT NULL,
  password_hash TEXT,
  password_salt TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS groups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  group_name TEXT NOT NULL UNIQUE,
  leader_participant_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'forming',
  disqualified_reason TEXT,
  disqualified_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (leader_participant_id) REFERENCES participants(id)
);

CREATE TABLE IF NOT EXISTS group_members (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  group_id INTEGER NOT NULL,
  participant_id INTEGER NOT NULL,
  joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  left_at TEXT,
  UNIQUE (group_id, participant_id),
  FOREIGN KEY (group_id) REFERENCES groups(id),
  FOREIGN KEY (participant_id) REFERENCES participants(id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_active_group_per_participant
  ON group_members(participant_id)
  WHERE left_at IS NULL;

CREATE TABLE IF NOT EXISTS group_invitations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  group_id INTEGER NOT NULL,
  invited_participant_id INTEGER NOT NULL,
  invited_by_participant_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  responded_at TEXT,
  UNIQUE (group_id, invited_participant_id),
  FOREIGN KEY (group_id) REFERENCES groups(id),
  FOREIGN KEY (invited_participant_id) REFERENCES participants(id),
  FOREIGN KEY (invited_by_participant_id) REFERENCES participants(id)
);

CREATE TABLE IF NOT EXISTS qr_codes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  qr_number TEXT NOT NULL UNIQUE,
  token TEXT NOT NULL UNIQUE,
  question_text TEXT NOT NULL,
  is_final INTEGER NOT NULL DEFAULT 0,
  is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS submissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  group_id INTEGER NOT NULL,
  qr_code_id INTEGER NOT NULL,
  submitted_by_participant_id INTEGER NOT NULL,
  answer_text TEXT NOT NULL,
  explanation_text TEXT NOT NULL,
  submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (group_id, qr_code_id),
  FOREIGN KEY (group_id) REFERENCES groups(id),
  FOREIGN KEY (qr_code_id) REFERENCES qr_codes(id),
  FOREIGN KEY (submitted_by_participant_id) REFERENCES participants(id)
);

CREATE TABLE IF NOT EXISTS admin_users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT,
  password_salt TEXT
);

CREATE TABLE IF NOT EXISTS game_settings (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  status TEXT NOT NULL DEFAULT 'running',
  final_qr_code_id INTEGER,
  close_submissions INTEGER NOT NULL DEFAULT 0,
  broadcast_message TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (final_qr_code_id) REFERENCES qr_codes(id)
);

INSERT OR IGNORE INTO game_settings(id,status,close_submissions) VALUES (1,'running',0);
INSERT OR IGNORE INTO admin_users(id,full_name,email,password_hash,password_salt) VALUES (1,'Admin','admin@tectrix.edu',NULL,NULL);
INSERT OR IGNORE INTO qr_codes(qr_number,token,question_text,is_final,is_active) VALUES
('QR1','token-qr-1','Clue at library gate?',0,1),
('QR2','token-qr-2','Find the red building name?',0,1),
('QR3','token-qr-3','Who is the murderer?',1,1);
