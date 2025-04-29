import os
import psycopg2
from psycopg2.extras import DictCursor
import uuid
import rsa
from typing import List, Optional, Dict, Any, Tuple
from contextlib import contextmanager
from datetime import datetime
import time
from threading import Lock
from .classes import CanvasObjectDB
from dotenv import load_dotenv

from .classes import Session, User, SessionParticipant





class DatabaseManager:
    _instance = None
    _lock = Lock()  # Thread safety for singleton creation
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        # Skip initialization if already initialized
        if getattr(self, '_initialized', False):
            return
            
        load_dotenv()
        
        # PostgreSQL connection parameters
        self.db_params = {
            'dbname': os.getenv('DB_NAME', 'neurosketch'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'Ach13v3m3nt1!'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432')
        }
        
        # Mark as initialized
        self._initialized = True
    
    def cleanup(self):
        """Cleanup resources when the application is shutting down."""
        # Nothing to clean up since connections are closed by the context manager
        pass

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections with automatic closing."""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_params)
            yield conn
        finally:
            if conn:
                conn.close()
    
    def _adapt_query(self, query: str) -> str:
        """Convert SQLite parameter style to PostgreSQL style."""
        return query.replace('?', '%s')
    
    def _row_to_tuple(self, row: Dict[str, Any], columns: List[str]) -> Tuple:
        """Convert a dictionary row to a tuple with specified column order."""
        result = []
        for col in columns:
            value = row.get(col)
            # Convert datetime objects to ISO format strings
            if isinstance(value, datetime):
                value = value.isoformat()
            result.append(value)
        return tuple(result)

    def _execute_with_retry(self, query: str, params: tuple = None, max_retries: int = 3, is_write: bool = True):
        """Execute a query with retry logic for handling concurrent access."""
        # Convert SQLite style parameters to PostgreSQL style
        query = self._adapt_query(query)
        
        retry_count = 0
        while retry_count < max_retries:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor(cursor_factory=DictCursor)
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    if is_write:
                        conn.commit()
                    return cursor
            except psycopg2.OperationalError as e:
                if retry_count < max_retries - 1:
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
        INSERT INTO sessions (id,title,height,width)
        VALUES (?, ?,?,?)
        """
        cursor = self._execute_with_retry(query, (session.id, session.title, session.height,session.width), is_write=True)

        participant_query = """
        INSERT INTO session_participants (id, user_id)
        VALUES (?, ?)
        """
        for user_id in session.participants:
            self._execute_with_retry(participant_query, (session.id, user_id), is_write=True)
        return cursor.rowcount > 0

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by its ID."""
        query = "SELECT * FROM sessions WHERE id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(self._adapt_query(query), (session_id,))
            row = cursor.fetchone()
            if row:
                # Convert to tuple with expected column order
                columns = ['id', 'title', 'height', 'width', 'created_at', 'updated_at']
                row_tuple = self._row_to_tuple(row, columns)
                return Session.from_db_row(row_tuple)
            return None

    def update_session(self, session: Session) -> bool:
        """Update an existing session."""
        # PostgreSQL uses NOW() instead of CURRENT_TIMESTAMP
        query = """
        UPDATE sessions 
        SET title = ?, canvas = ?, updated_at = NOW()
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
        with self._get_connection() as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(self._adapt_query(query), (user_id,))
            row = cursor.fetchone()
            if row:
                # Convert to tuple with expected column order
                columns = ['id', 'public_key', 'client_identifier', 'display_name', 'created_at']
                row_tuple = self._row_to_tuple(row, columns)
                return User.from_db_row(row_tuple)
            return None
        
    def get_all_users(self) -> List[User]:
        query = "SELECT * FROM users"
        with self._get_connection() as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(self._adapt_query(query))
            users = []
            for row in cursor.fetchall():
                # Convert to tuple with expected column order
                columns = ['id', 'public_key', 'client_identifier', 'display_name', 'created_at']
                row_tuple = self._row_to_tuple(row, columns)
                users.append(User.from_db_row(row_tuple))
            return users


    def add_new_participants(self,session_id:str, user_ids:List[str]) -> bool:
        """Add new participants to a session."""
        query = """
        INSERT INTO session_participants (id, user_id)
        VALUES (?, ?)
        """
        for user_id in user_ids:
            self._execute_with_retry(query, (session_id, user_id), is_write=True)
        return True

    def get_user_by_client_id(self, client_id: str) -> Optional[User]:
        """Retrieve a user by their client identifier."""
        query = "SELECT * FROM users WHERE client_identifier = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(self._adapt_query(query), (client_id,))
            row = cursor.fetchone()
            if row:
                # Convert to tuple with expected column order
                columns = ['id', 'public_key', 'client_identifier', 'display_name', 'created_at']
                row_tuple = self._row_to_tuple(row, columns)
                return User.from_db_row(row_tuple)
            return None

    def create_anonymous_user(self, user_id:str,public_key:str, display_name: str) -> User:
        """Create an anonymous user with a random UUID and RSA key pair."""
        # Generate UUIDs for both id and client_identifier
        client_id = str(uuid.uuid4())
        
        # Create and store user
        user = User(
            id=user_id,
            public_key=public_key,
            client_identifier=client_id,
            display_name=display_name
        )
        self.create_user(user)
        return user

    def verify_user_identity(self, user_id: str, private_key: rsa.PrivateKey) -> bool:
        """
        Verify user identity using RSA challenge-response.
        Generates a challenge internally and verifies it using the stored public key.
        Returns True if verification succeeds, False otherwise.
        """
        user = self.get_user(user_id)
        if not user:
            return False
            
        try:
            # Create a challenge message
            challenge = os.urandom(32)  # 256-bit random challenge
            
            # Load the stored public key
            public_key = rsa.PublicKey.load_pkcs1(user.public_key.encode())
            
            # Create challenge response by encrypting with public key
            challenge_response = rsa.encrypt(challenge, public_key)
            
            # Verify by decrypting with private key
            try:
                decrypted = rsa.decrypt(challenge_response, private_key)
                return decrypted == challenge
            except rsa.pkcs1.DecryptionError as e:
                print("Decryption failed:", str(e))
                return False
                
        except Exception as e:
            print(f"Error in verify_user_identity: {str(e)}")
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
        with self._get_connection() as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(self._adapt_query(query), (session_id,))
            users = []
            for row in cursor.fetchall():
                # Convert to tuple with expected column order
                columns = ['id', 'public_key', 'client_identifier', 'display_name', 'created_at']
                row_tuple = self._row_to_tuple(row, columns)
                users.append(User.from_db_row(row_tuple))
            return users

    def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all sessions a user is participating in."""
        query = """
        SELECT s.* FROM sessions s
        JOIN session_participants sp ON s.id = sp.id
        WHERE sp.user_id = ?
        """
        with self._get_connection() as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(self._adapt_query(query), (user_id,))
            sessions = []
            for row in cursor.fetchall():
                # Convert to tuple with expected column order
                columns = ['id', 'title', 'height', 'width', 'created_at', 'updated_at']
                row_tuple = self._row_to_tuple(row, columns)
                sessions.append(Session.from_db_row(row_tuple))
            return sessions
        
    def clear_canvas(self,session_id:str) -> bool:
        """Clear all canvas objects from a session."""
        query = "DELETE FROM canvas_objects WHERE session_id = ?"
        cursor = self._execute_with_retry(query, (session_id,), is_write=True)
        return cursor.rowcount > 0

    def add_canvas_object(self, canvas_object: dict) -> bool:
        """
        Add a new canvas object to a session.
        Always allowed as they're new objects.
        
        Args:
            canvas_object (dict): Dictionary containing:
                - id: Unique identifier for the object
                - session_id: ID of the session this object belongs to
                - object_data: JSON string of the object data
                - created_by: ID of the user creating the object
        
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        INSERT INTO canvas_objects (id, session_id, object_data, created_by)
        VALUES (?, ?, ?, ?)
        """
        cursor = self._execute_with_retry(
            query,
            (canvas_object['id'], canvas_object['session_id'], 
             canvas_object['object_data'], canvas_object['created_by']),
            is_write=True
        )
        return cursor.rowcount > 0

    def edit_canvas_object(self, object_id: str, object_data: str, new_version: int) -> bool:
        """
        Edit an existing canvas object.
        Only proceeds if the new version is greater than the current version.
        
        Args:
            object_id (str): ID of the object to edit
            object_data (str): New JSON string of object data
            new_version (int): New version number
            
        Returns:
            bool: True if edit was successful, False if version check failed or object not found
        """
        # First get current version
        version_query = "SELECT version FROM canvas_objects WHERE id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(self._adapt_query(version_query), (object_id,))
            result = cursor.fetchone()
            if not result:
                return False
            current_version = result['version']
            
            # Only proceed if new version is greater
            if new_version <= current_version:
                return False
        
        # Update the object
        update_query = """
        UPDATE canvas_objects 
        SET object_data = ?, version = ?, updated_at = NOW()
        WHERE id = ?
        """
        cursor = self._execute_with_retry(
            update_query,
            (object_data, new_version, object_id),
            is_write=True
        )
        return cursor.rowcount > 0

    def delete_canvas_object(self, object_id: str, version: int) -> bool:
        """
        Delete a canvas object.
        Only proceeds if the provided version is greater than the current version.
        
        Args:
            object_id (str): ID of the object to delete
            version (int): Version number for verification
            
        Returns:
            bool: True if deletion was successful, False if version check failed or object not found
        """
        # First get current version
        version_query = "SELECT version FROM canvas_objects WHERE id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(self._adapt_query(version_query), (object_id,))
            result = cursor.fetchone()
            if not result:
                return False
            current_version = result['version']
            
            # Only proceed if provided version is greater
            if version <= current_version:
                return False
        
        # Delete the object
        delete_query = "DELETE FROM canvas_objects WHERE id = ?"
        cursor = self._execute_with_retry(
            delete_query,
            (object_id,),
            is_write=True
        )
        return cursor.rowcount > 0

    def get_session_canvas_objects(self, session_id: str) -> List[CanvasObjectDB]:
        """
        Get all canvas objects for a specific session.
        
        Args:
            session_id (str): ID of the session to get objects for
            
        Returns:
            List[CanvasObjectDB]: List of canvas objects in the session
        """
        query = "SELECT * FROM canvas_objects WHERE session_id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(self._adapt_query(query), (session_id,))
            objects = []
            for row in cursor.fetchall():
                # Convert to tuple with expected column order
                columns = ['id', 'session_id', 'object_data', 'created_by', 'created_at', 'updated_at', 'version']
                row_tuple = self._row_to_tuple(row, columns)
                objects.append(CanvasObjectDB.from_db_row(row_tuple))
            return objects
