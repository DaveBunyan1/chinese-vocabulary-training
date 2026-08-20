"""
Domain model representing a user account.

Authentication details (password hash, tokens, etc.) live outside
the pure domain in the infrastructure / auth layer.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class UserId:
    value: str


@dataclass(frozen=True, slots=True)
class User:
    id: UserId
    email: str
    display_name: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.email.strip():
            raise ValueError("email cannot be empty")
        if not self.display_name.strip():
            raise ValueError("display_name cannot be empty")
