"""
Agronomy Module for Phase 4: Agronomic Rule Database and Rule Selection Engine.
Provides TNAU/STCR/IPNS verified rule registry and rule selection service.
"""

from .service import select_rule, RuleSelectionService
from .registry import AgronomicRuleRegistry

__all__ = ["select_rule", "RuleSelectionService", "AgronomicRuleRegistry"]
