# Database schema

SQLite database for the door lock server (`data/door_lock.db`, created by
`init_db.py` from `schema.sql`). It has five tables.

## `doors`

One row per physical lock (one per ESP32 device running the `door_lock`
firmware).

**Why it exists:** the firmware supports multiple independently addressable
locks (each with its own `DEVICE_ID` and MQTT topics). This table is the
server's registry of which locks exist, which MQTT topics belong to each one,
and its last known state (`locked` / `unlocked` / `offline`). Without it the
server would have no way to know which topics to subscribe to, or to tell one
door apart from another when an event comes in.

## `cards`

Authorized RFID cards/users, identified by their normalized UID.

**Why it exists:** the firmware's `AccessPolicy::deriveAccessCode()` computes
a code from *any* UID — it does not check whether that UID is allowed in.
Real access control has to happen on the server: it looks up the UID here,
and only if a matching, active card exists does it compute and publish the
unlock code. This table is what makes "access control" actually control
access, instead of unlocking for anyone who scans a card.

## `door_cards`

Many-to-many link between `doors` and `cards`.

**Why it exists:** a card should be allowed on some doors and not others once
there is more than one lock. A join table lets the same card be granted
access to multiple doors, and the same door accept multiple cards, without
duplicating card data.

## `events`

Append-only log of everything that happens: RFID reads, access
granted/denied, doors opening/closing, and online/offline status.

**Why it exists:** this is the audit trail — who opened which door and when,
including failed attempts with unrecognized cards (`card_id` is `NULL` in
that case, but the raw `uid` is still kept). It's also the only place that
records `door_closed` events, since closing the door only requires
re-scanning the same card and does not go through the access-granted/denied
check that opening does.

## `admin_users`

Administrators who can sign in to the web interface (passwords are stored
hashed).

`cards` also has `password_hash`: when set, the student can sign in to the
web interface with their student ID or email (view-only access to room
occupancy). Removing a student deletes the card, its door permissions and its
web login.

The schema is created directly from `schema.sql`; older database versions are
not migrated.
