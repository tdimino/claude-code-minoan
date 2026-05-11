"""Sample Pydantic models for testing the Python extractor."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
from pydantic import BaseModel


class UserInput(BaseModel):
    name: str
    email: str
    age: int | None = None


class UserOutput(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime


@dataclass
class TransformConfig:
    uppercase: bool = False
    strip_whitespace: bool = True
    max_length: int = 255


class AnalyticsEvent(TypedDict):
    event_type: str
    timestamp: str
    payload: dict[str, str]


def validate_email(email: str) -> bool:
    """Check if an email address is valid."""
    return "@" in email and "." in email.split("@")[1]


def create_user(input_data: UserInput) -> UserOutput:
    """Create a new user from validated input."""
    return UserOutput(
        id="generated",
        name=input_data.name,
        email=input_data.email,
        created_at=datetime.now(),
    )


def transform_name(name: str, config: TransformConfig) -> str:
    """Apply transformations to a user name."""
    result = name
    if config.strip_whitespace:
        result = result.strip()
    if config.uppercase:
        result = result.upper()
    return result[:config.max_length]


def fetch_users(limit: int = 10, offset: int = 0) -> list[UserOutput]:
    """Fetch users from the database."""
    return []


def _internal_helper(x: int) -> int:
    """This should NOT be extracted (private)."""
    return x * 2
