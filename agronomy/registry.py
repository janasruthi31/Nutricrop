"""
Agronomic Rule Registry.
Loads and manages verified TNAU, STCR, and IPNS recommendation rules and source registry.
"""
import csv
import json
import os
from typing import Dict, List, Optional, Set

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_RULES_PATH = os.path.join(_BASE_DIR, "data", "agronomy", "tnau_stcr_rules.json")
_DEFAULT_SOURCES_PATH = os.path.join(_BASE_DIR, "data", "agronomy", "source_registry.csv")


class AgronomicRuleRegistry:
    def __init__(self, rules_path: Optional[str] = None, sources_path: Optional[str] = None):
        self.rules_path = rules_path or _DEFAULT_RULES_PATH
        self.sources_path = sources_path or _DEFAULT_SOURCES_PATH
        self._rules: List[dict] = []
        self._sources: List[dict] = []
        self.reload()

    def reload(self):
        """Load or reload rules from JSON and source registry from CSV."""
        if os.path.exists(self.rules_path):
            with open(self.rules_path, "r", encoding="utf-8") as f:
                self._rules = json.load(f)
        else:
            self._rules = []

        if os.path.exists(self.sources_path):
            with open(self.sources_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self._sources = list(reader)
        else:
            self._sources = []

    def get_all_rules(self) -> List[dict]:
        return list(self._rules)

    def get_verified_rules(self) -> List[dict]:
        return [r for r in self._rules if r.get("verification_status") == "VERIFIED"]

    def get_sources(self) -> List[dict]:
        return list(self._sources)

    def known_crops(self) -> Set[str]:
        crops = set()
        for r in self._rules:
            c = r.get("crop")
            if c:
                crops.add(c.strip().lower())
        return crops

    def get_rules_for_crop(self, crop: str) -> List[dict]:
        c_norm = crop.strip().lower()
        # allow crop alias mapping matching Phase 3 / Phase 2 naming
        matches = []
        for r in self._rules:
            rc = r.get("crop", "").strip().lower()
            if rc == c_norm or rc in c_norm or c_norm in rc:
                matches.append(r)
        return matches
