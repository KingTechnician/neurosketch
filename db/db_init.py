# This is where you would create the database and 
import sqlite3

# Create the database file and tables
conn = sqlite3.connect("neurosketch.db")
cursor = conn.cursor()

# Create sessions table
cursor.execute('''
CREATE TABLE sessions(
    id TEXT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    canvas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    public_key VARCHAR(255) NOT NULL,
    client_identifier VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

# Commit changes and close connection
conn.commit()
conn.close()

print("Database initialized successfully!")