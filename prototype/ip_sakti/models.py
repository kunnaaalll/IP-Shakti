"""Shared data structures for the IP-SAKTI proof-of-concept pipeline.

These are deliberately plain dataclasses (no ORM, no DB) — the prototype's job
is to prove the *logic* of the pipeline, not to be a persistence layer. See
ARCHITECTURE.md at the project root for the real Postgres schema this stands
in for.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StatutoryChunk:
    chunk_id: str
    act: str
    section: str
    text: str
    applies_to: List[str]
    relevance_score: float = 0.0


@dataclass
class Citation:
    act: str
    section: str
    chunk_id: str


@dataclass
class RoadmapStep:
    step: int
    action: str
    rationale: str
    citations: List[Citation]
    risk_level: str  # low | medium | high | blocker
    timeline_note: Optional[str] = None
    phase: Optional[str] = None
    deliverable: Optional[str] = None
    statutory_hazard: Optional[str] = None
    governing_authority: Optional[str] = None
    operational_guidance: Optional[str] = None


@dataclass
class Analysis:
    classification: str
    roadmap: List[RoadmapStep]
    confidence_score: float
    status: str  # delivered | escalated
    escalation_reason: Optional[str] = None
    retries_used: int = 0
    tkrc_match: Optional[dict] = None
