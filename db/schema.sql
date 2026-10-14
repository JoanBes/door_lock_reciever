-- Door lock server database schema.
-- Engine: SQLite3.

PRAGMA foreign_keys = ON;

-- One row per physical lock (matches DEVICE_ID in the firmware).
CREATE TABLE IF NOT EXISTS doors (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id       TEXT NOT NULL UNIQUE,      -- e.g. "ESP32_Door_Lock_01"
    name            TEXT NOT NULL,             -- e.g. "Main door" or room "101"
    location        TEXT NOT NULL DEFAULT 'Ground floor',
    capacity        INTEGER NOT NULL DEFAULT 4,
    rfid_topic      TEXT NOT NULL,             -- e.g. "doorlock/01/rfid"
    command_topic   TEXT NOT NULL,             -- e.g. "doorlock/01/command"
    released_topic  TEXT NOT NULL,             -- e.g. "doorlock/01/released"
    status_topic    TEXT NOT NULL,             -- e.g. "doorlock/01/status"
    state           TEXT NOT NULL DEFAULT 'locked'
                        CHECK (state IN ('locked', 'unlocked', 'offline')),
    last_seen_at    TIMESTAMP
);

-- Authorized cards/users.
CREATE TABLE IF NOT EXISTS cards (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    uid             TEXT NOT NULL UNIQUE,      -- normalized UID (uppercase, no separators)
    owner_name      TEXT,
    student_id      TEXT,                      -- e.g. "STU-2025-1842"
    email           TEXT,
    password_hash   TEXT,                      -- lets the student sign in to the web (view-only)
    active          INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Many-to-many: which card can open which door.
CREATE TABLE IF NOT EXISTS door_cards (
    door_id         INTEGER NOT NULL REFERENCES doors(id) ON DELETE CASCADE,
    card_id         INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    PRIMARY KEY (door_id, card_id)
);

-- Event log.
-- card_id is NULL when the UID read is not registered in `cards`.
-- 'access_granted' / 'access_denied' are only generated when trying to OPEN.
-- 'door_closed' is generated when the `released` topic is received, with no
-- prior validation (closing just requires re-scanning the same card).
CREATE TABLE IF NOT EXISTS events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    door_id         INTEGER REFERENCES doors(id) ON DELETE SET NULL,
    card_id         INTEGER REFERENCES cards(id) ON DELETE SET NULL,
    uid             TEXT NOT NULL,
    event_type      TEXT NOT NULL CHECK (event_type IN (
                        'rfid_read',
                        'access_granted',
                        'access_denied',
                        'door_opened',
                        'door_closed',
                        'status_online',
                        'status_offline'
                    )),
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_door_id ON events(door_id);
CREATE INDEX IF NOT EXISTS idx_events_card_id ON events(card_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_door_cards_card_id ON door_cards(card_id);

-- Administrators allowed to sign in to the web interface.
CREATE TABLE IF NOT EXISTS admin_users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    full_name       TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'Library Administrator',
    password_hash   TEXT NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
