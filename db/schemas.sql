CREATE TABLE sessions(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    canvas jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)

CREATE TABLE session_participants(
    id uuid REFERENCES sessions(session_id) ON DELETE CASCADE,
    user_id UUID NOT NULL, --References users table TODO
    PRIMARY KEY (id, user_id)
)

CREATE TABLE users(
    id UUID PRIMARY KEY,
    client_identifier CARCHAR (255) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
)

---Ignore this, but don't delete below: Useful for later
---CREATE INDEX idx_users_client_identifier ON user(client_identifier)