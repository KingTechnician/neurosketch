from dataclasses import dataclass
from typing import List,Optional
from datetime import datetime
import uuid

@dataclass
class Session:
    id: str
    title: str
    width: int = 800
    height: int = 600
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    participants: List[str] = None

    def __post_init__(self):
        if self.participants is None:
            self.participants = []


    @classmethod
    def from_db_row(cls, row: tuple) -> 'Session':
        """Create a Session instance from a database row."""
        return cls(
            id=row[0],
            title=row[1],
            width=row[2],
            height=row[3],
            created_at=datetime.fromisoformat(row[4]) if row[4] else None,
            updated_at=datetime.fromisoformat(row[5]) if row[5] else None
        )

@dataclass
class User:
    id: str
    public_key: str
    client_identifier: str
    display_name: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'User':
        """Create a User instance from a database row."""
        return cls(
            id=row[0],
            public_key=row[1],
            client_identifier=row[2],
            display_name=row[3],
            created_at=datetime.fromisoformat(row[4]) if row[4] else None
        )

@dataclass
class SessionParticipant:
    session_id: str
    user_id: str

    @classmethod
    def from_db_row(cls, row: tuple) -> 'SessionParticipant':
        """Create a SessionParticipant instance from a database row."""
        return cls(
            session_id=row[0],
            user_id=row[1]
        )



@dataclass
class CanvasObjectDB:
    id: str
    session_id: str
    object_data: str  # JSON string
    created_by: str
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'CanvasObjectDB':
        """Create a CanvasObject instance from a database row."""
        return cls(
            id=row[0],
            session_id=row[1],
            object_data=row[2],
            created_by=row[3],
            created_at=datetime.fromisoformat(row[4]) if row[4] else None,
            updated_at=datetime.fromisoformat(row[5]) if row[5] else None,
            version=row[6] if row[6] else 1,
            
        )

# Sample sessions for testing
SAMPLE_SESSIONS = [
    Session(
        id=str(uuid.uuid4()),
        title="Team Brainstorm",
        participants=["user123", "user456", "user789"]
    ),
    Session(
        id=str(uuid.uuid4()),
        title="Project Wireframes",
        participants=["user456", "user234"]
    ),
    Session(
        id=str(uuid.uuid4()),
        title="UI Design Review",
        participants=["user123", "user567", "user890", "user111"]
    )
]
