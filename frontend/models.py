from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Session:
    id: str
    title: str
    canvas: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'Session':
        """Create a Session instance from a database row."""
        return cls(
            id=row[0],
            title=row[1],
            canvas=row[2],
            created_at=datetime.fromisoformat(row[3]) if row[3] else None,
            updated_at=datetime.fromisoformat(row[4]) if row[4] else None
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
