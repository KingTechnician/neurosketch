import os
import sqlite3
from typing import List, Optional
from contextlib import contextmanager
from datetime import datetime
import time

from .classes import Session, User, SessionParticipant

class DatabaseManager:
    def __init__(self):
        self.db_path = os.getenv('PATH_TO_DB')
        if not self.db_path:
            raise ValueError("Database path not found in environment variables")
        
        # Enable WAL mode for better concurrent access
        with self._get_connection() as conn:
            conn.execute('PRAGMA journal_mode=WAL')

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections with automatic closing."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            if conn:
                conn.close()

    def _execute_with_retry(self, query: str, params: tuple = None, max_retries: int = 3) -> sqlite3.Cursor:
        """Execute a query with retry logic for handling concurrent access."""
        retry_count = 0
        while retry_count < max_retries:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    conn.commit()
                    return cursor
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and retry_count < max_retries - 1:
                    retry_count += 1
                    time.sleep(0.1 * retry_count)  # Exponential backoff
                    continue
                raise
            except Exception as e:
                raise

    # Session Operations
    def create_session(self, session: Session) -> bool:
        """Create a new session in the database."""
        query = """
        INSERT INTO sessions (id, title, canvas)
        VALUES (?, ?, ?)
        """
        cursor = self._execute_with_retry(query, (session.id, session.title, session.canvas))
        return cursor.rowcount > 0

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by its ID."""
        query = "SELECT * FROM sessions WHERE id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (session_id,))
            row = cursor.fetchone()
            return Session.from_db_row(tuple(row)) if row else None

    def update_session(self, session: Session) -> bool:
        """Update an existing session."""
        query = """
        UPDATE sessions 
        SET title = ?, canvas = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        cursor = self._execute_with_retry(query, (session.title, session.canvas, session.id))
        return cursor.rowcount > 0

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its participants."""
        query = "DELETE FROM sessions WHERE id = ?"
        cursor = self._execute_with_retry(query, (session_id,))
        return cursor.rowcount > 0

    # User Operations
    def create_user(self, user: User) -> bool:
        """Create a new user in the database."""
        query = """
        INSERT INTO users (id, public_key, client_identifier, display_name)
        VALUES (?, ?, ?, ?)
        """
        cursor = self._execute_with_retry(
            query, 
            (user.id, user.public_key, user.client_identifier, user.display_name)
        )
        return cursor.rowcount > 0

    def get_user(self, user_id: str) -> Optional[User]:
        """Retrieve a user by their ID."""
        query = "SELECT * FROM users WHERE id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            row = cursor.fetchone()
            return User.from_db_row(tuple(row)) if row else None

    def get_user_by_client_id(self, client_id: str) -> Optional[User]:
        """Retrieve a user by their client identifier."""
        query = "SELECT * FROM users WHERE client_identifier = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (client_id,))
            row = cursor.fetchone()
            return User.from_db_row(tuple(row)) if row else None

    # Participant Operations
    def add_participant(self, participant: SessionParticipant) -> bool:
        """Add a participant to a session."""
        query = """
        INSERT INTO session_participants (id, user_id)
        VALUES (?, ?)
        """
        cursor = self._execute_with_retry(
            query, 
            (participant.session_id, participant.user_id)
        )
        return cursor.rowcount > 0

    def remove_participant(self, participant: SessionParticipant) -> bool:
        """Remove a participant from a session."""
        query = """
        DELETE FROM session_participants 
        WHERE id = ? AND user_id = ?
        """
        cursor = self._execute_with_retry(
            query, 
            (participant.session_id, participant.user_id)
        )
        return cursor.rowcount > 0

    def get_session_participants(self, session_id: str) -> List[User]:
        """Get all participants in a session."""
        query = """
        SELECT u.* FROM users u
        JOIN session_participants sp ON u.id = sp.user_id
        WHERE sp.id = ?
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (session_id,))
            return [User.from_db_row(tuple(row)) for row in cursor.fetchall()]

    def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all sessions a user is participating in."""
        query = """
        SELECT s.* FROM sessions s
        JOIN session_participants sp ON s.id = sp.id
        WHERE sp.user_id = ?
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            return [Session.from_db_row(tuple(row)) for row in cursor.fetchall()]
