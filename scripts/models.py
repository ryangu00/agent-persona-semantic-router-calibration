"""Small shared records; the library backend converts Route explicitly."""
from dataclasses import dataclass, field


@dataclass
class Route:
    name: str
    utterances: list[str]
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Routed:
    persona: str | None
    score: float | None
    escalate: bool
    runner_up: str | None = None
    runner_up_score: float | None = None
    source: str = "semantic"
