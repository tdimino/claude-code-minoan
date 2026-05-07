"""Domain types for Linear A decipherment pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CognateMethod = Literal["gordon_direct", "yashar_mana", "proto_semitic"]


@dataclass(frozen=True)
class SignReading:
    value: str
    consonant: str | None
    vowel: str
    source: str
    confidence: str
    is_primary: bool
    implications: tuple[str, ...] = ()


@dataclass(frozen=True)
class SignEntry:
    ab_number: str
    name: str
    readings: tuple[SignReading, ...]
    unicode: str | None = None
    rendering_tier: str = "unicode_native"
    evolution_id: str | None = None


@dataclass(frozen=True)
class Inscription:
    name: str
    site: str
    support: str
    context: str
    transliterated_words: tuple[str, ...]
    words: tuple[str, ...]
    translated_words: tuple[str, ...]
    parsed_inscription: str
    scribe: str = ""
    findspot: str = ""


@dataclass(frozen=True)
class LexiconEntry:
    gordon_translit: str
    semitic: str
    meaning: str
    category: str
    refs: str
    source: str
    note: str = ""


@dataclass(frozen=True)
class CognateMatch:
    root: str
    language: str
    meaning: str
    distance: float
    method: CognateMethod
