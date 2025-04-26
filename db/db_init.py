import sqlite3

# Create the database file and tables
conn = sqlite3.connect("neurosketch.db")
cursor = conn.cursor()

# Create sessions table
cursor.execute('''
CREATE TABLE sessions(
    id TEXT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    height INTEGER NOT NULL,
    width INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

cursor.execute('''
CREATE TABLE canvas_objects(
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    object_data TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id)
)''')

# Create session_participants table
cursor.execute('''
CREATE TABLE session_participants(
    id TEXT,
    user_id TEXT NOT NULL,
    PRIMARY KEY (id, user_id),
    FOREIGN KEY (id) REFERENCES sessions(id) ON DELETE CASCADE
)''')

# Create users table
cursor.execute('''
CREATE TABLE users(
    id TEXT PRIMARY KEY,
    public_key TEXT NOT NULL,
    client_identifier VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

# Commit changes and close connection
conn.commit()
conn.close()

print("Database initialized successfully!")