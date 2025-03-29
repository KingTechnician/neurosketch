CREATE TABLE sessions(
    id TEXT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    canvas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

CREATE TABLE session_participants(
    id TEXT,
    user_id TEXT NOT NULL,
    PRIMARY KEY (id, user_id),
    FOREIGN KEY (id) REFERENCES sessions(id) ON DELETE CASCADE
)

CREATE TABLE users(
    id TEXT PRIMARY KEY,
    public_key TEXT NOT NULL,
    client_identifier VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

---Ignore this, but don't delete below: Useful for later
---CREATE INDEX idx_users_client_identifier ON user(client_identifier)