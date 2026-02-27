"""
Base types for transfer pipeline stages.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StageResult:
    stage: str
    passed: bool
    score: float
    finding: str  # "PASS", "CONDITIONAL", "FAIL"
    reasoning: str = ""
    conditions: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    monitoring: List[str] = field(default_factory=list)


ENTITY_TYPES = [
    "farmer", "water_district", "municipality", "water_bank",
    "industrial", "gsa", "developer", "environmental",
]

TRANSFER_TYPES = ["direct", "in_lieu", "banked"]

ALLOWED_TRANSFER_TYPES = {
    "direct": {"farmer", "water_district", "municipality", "water_bank",
               "industrial", "gsa", "developer", "environmental"},
    "in_lieu": {"farmer", "water_district", "municipality", "water_bank",
                "gsa", "industrial"},
    "banked": {"farmer", "water_district", "municipality", "water_bank",
               "industrial", "developer", "environmental"},
}
