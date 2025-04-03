import os
import sqlite3
import uuid
import rsa
import threading
from typing import List, Optional
from contextlib import contextmanager
from datetime import datetime
import time
from dotenv import load_dotenv

from classes import Session, User, SessionParticipant


class DatabaseManager:
    def __init__(self):
        load_dotenv()
        self.db_path = os.getenv('PATH_TO_DB')
        if not self.db_path:
            raise ValueError("Database path not found in environment variables")
        
        # Enable WAL mode for better concurrent access
        with self._get_connection() as conn:
            conn.execute('PRAGMA journal_mode=WAL')
        
        # Initialize the reader-writer lock
        self.rw_lock = threading.RLock()  # Reentrant lock for write operations
        self.reader_count = 0  # Counter for active readers
        self.reader_count_lock = threading.Lock()  # Lock to protect reader count

    @contextmanager
    def read_lock(self):
        """Acquire a shared read lock."""
        try:
            # Increment reader count safely
            with self.reader_count_lock:
                self.reader_count += 1
                if self.reader_count == 1:
                    # First reader acquires the lock
                    self.rw_lock.acquire()
            yield
        finally:
            # Decrement reader count safely
            with self.reader_count_lock:
                self.reader_count -= 1
                if self.reader_count == 0:
                    # Last reader releases the lock
                    self.rw_lock.release()

    @contextmanager
    def write_lock(self):
        """Acquire an exclusive write lock."""
        try:
            # Acquire the lock for exclusive access
            self.rw_lock.acquire()
            yield
        finally:
            # Release the lock
            self.rw_lock.release()

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

    def _execute_with_retry(self, query: str, params: tuple = None, max_retries: int = 3, is_write: bool = True) -> sqlite3.Cursor:
        """Execute a query with retry logic for handling concurrent access."""
        # Choose the appropriate lock based on whether this is a read or write operation
        lock_ctx = self.write_lock() if is_write else self.read_lock()
        
        retry_count = 0
        while retry_count < max_retries:
            try:
                with lock_ctx:
                    with self._get_connection() as conn:
                        cursor = conn.cursor()
                        if params:
                            cursor.execute(query, params)
                        else:
                            cursor.execute(query)
                        if is_write:
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
        cursor = self._execute_with_retry(query, (session.id, session.title, session.canvas), is_write=True)
        return cursor.rowcount > 0

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by its ID."""
        query = "SELECT * FROM sessions WHERE id = ?"
        with self.read_lock():
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
        cursor = self._execute_with_retry(query, (session.title, session.canvas, session.id), is_write=True)
        return cursor.rowcount > 0

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its participants."""
        query = "DELETE FROM sessions WHERE id = ?"
        cursor = self._execute_with_retry(query, (session_id,), is_write=True)
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
            (user.id, user.public_key, user.client_identifier, user.display_name),
            is_write=True
        )
        return cursor.rowcount > 0

    def get_user(self, user_id: str) -> Optional[User]:
        """Retrieve a user by their ID."""
        query = "SELECT * FROM users WHERE id = ?"
        with self.read_lock():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (user_id,))
                row = cursor.fetchone()
                return User.from_db_row(tuple(row)) if row else None

    def get_user_by_client_id(self, client_id: str) -> Optional[User]:
        """Retrieve a user by their client identifier."""
        query = "SELECT * FROM users WHERE client_identifier = ?"
        with self.read_lock():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (client_id,))
                row = cursor.fetchone()
                return User.from_db_row(tuple(row)) if row else None

    def create_anonymous_user(self, display_name: str) -> User:
        """Create an anonymous user with a random UUID and RSA key pair."""
        # Generate UUIDs for both id and client_identifier
        user_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        
        # Generate RSA key pair
        (pubkey, _) = rsa.newkeys(2048)
        public_key = pubkey.save_pkcs1().decode()
        
        # Create and store user
        user = User(
            id=user_id,
            public_key=public_key,
            client_identifier=client_id,
            display_name=display_name
        )
        self.create_user(user)
        return user

    def verify_user_identity(self, client_id: str, challenge_response: bytes, private_key: rsa.PrivateKey) -> bool:
        """
        Verify user identity using RSA challenge-response.
        Returns True if verification succeeds, False otherwise.
        """
        user = self.get_user_by_client_id(client_id)
        if not user:
            return False
            
        try:
            # Create a challenge using stored public key
            public_key = rsa.PublicKey.load_pkcs1(user.public_key.encode())
            # Decrypt response with private key and verify it matches
            decrypted = rsa.decrypt(challenge_response, private_key)
            # Encrypt with public key and compare
            encrypted = rsa.encrypt(decrypted, public_key)
            return encrypted == challenge_response
        except:
            return False

    # Participant Operations
    def add_participant(self, participant: SessionParticipant) -> bool:
        """Add a participant to a session."""
        query = """
        INSERT INTO session_participants (id, user_id)
        VALUES (?, ?)
        """
        cursor = self._execute_with_retry(
            query, 
            (participant.session_id, participant.user_id),
            is_write=True
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
            (participant.session_id, participant.user_id),
            is_write=True
        )
        return cursor.rowcount > 0

    def get_session_participants(self, session_id: str) -> List[User]:
        """Get all participants in a session."""
        query = """
        SELECT u.* FROM users u
        JOIN session_participants sp ON u.id = sp.user_id
        WHERE sp.id = ?
        """
        with self.read_lock():
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
        with self.read_lock():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (user_id,))
                return [Session.from_db_row(tuple(row)) for row in cursor.fetchall()]