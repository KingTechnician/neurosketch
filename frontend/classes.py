from dataclasses import dataclass
from typing import List
import uuid

@dataclass
class Session:
    title: str
    session_id: str
    participants: List[str]

# Sample sessions for testing
SAMPLE_SESSIONS = [
    Session(
        "Team Brainstorm",
        str(uuid.uuid4()),
        ["user123", "user456", "user789"]
    ),
    Session(
        "Project Wireframes",
        str(uuid.uuid4()),
        ["user456", "user234"]
    ),
    Session(
        "UI Design Review",
        str(uuid.uuid4()),
        ["user123", "user567", "user890", "user111"]
    )
]
