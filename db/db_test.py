import psycopg2

conn = psycopg2.connect(
    dbname="neurosketch",  # Your database name (visible in screenshot)
    user="postgres",       # Default username (visible as owner in screenshot)
    password="Ach13v3m3nt1!",  # The password you set during installation
    host="localhost",      # For local connections
    port="5432"            # Default PostgreSQL port
)
"""CREATE TABLE sessions(
    id TEXT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    height INTEGER NOT NULL,
    width INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)"""

# Test the connection
cursor = conn.cursor()

#Add fake session data



cursor.execute("SELECT * FROM sessions")
tables = cursor.fetchall()
print("Available tables:", tables)