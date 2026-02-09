"""Loads regulatory references from JSONL and provides lookup.

The JSONL format is one regulation per line — greppable, diffable,
inspectable with jq, and editable without touching Python code.

Usage:
    registry = RegulatoryRegistry.from_jsonl("regulations/base_policies.jsonl")
    registry.get("MHPAEA")                  # → BasePolicy
    registry.governs("ACA")                 # → ["preventive_care", "oop_max"]
    registry.statutes_for("emergency")      # → ["NSA"]
    registry.base_policies_for("emergency") # → [BasePolicy(id="NSA", ...)]
    registry.all()                          # → [BasePolicy, ...]
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from policy.models import BasePolicy, RegulatoryReference


class RegulatoryRegistry:
    """Loads and indexes regulatory references from a JSONL file."""

    def __init__(self) -> None:
        self._policies: dict[str, BasePolicy] = {}
        self._governs: dict[str, list[str]] = {}

    @classmethod
    def from_jsonl(cls, path: str | Path) -> RegulatoryRegistry:
        reg = cls()
        reg._load(Path(path))
        return reg

    def _load(self, path: Path) -> None:
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("#"):
                continue

            raw = json.loads(line)
            governs = raw.pop("governs", [])

            refs = []
            for r in raw.pop("references", []):
                eff = r.get("effective_date")
                if isinstance(eff, str):
                    r["effective_date"] = date.fromisoformat(eff)
                refs.append(RegulatoryReference(**r))

            bp = BasePolicy(references=refs, **raw)
            self._policies[bp.id] = bp
            self._governs[bp.id] = governs

    # -- lookup --

    def get(self, statute_id: str) -> BasePolicy:
        return self._policies[statute_id]

    def all(self) -> list[BasePolicy]:
        return list(self._policies.values())

    @property
    def ids(self) -> list[str]:
        return list(self._policies.keys())

    # -- graph queries --

    def governs(self, statute_id: str) -> list[str]:
        """Section IDs governed by a statute."""
        return list(self._governs.get(statute_id, []))

    def statutes_for(self, section_id: str) -> list[str]:
        """Statute IDs that govern a section."""
        return [sid for sid, sections in self._governs.items() if section_id in sections]

    def base_policies_for(self, section_id: str) -> list[BasePolicy]:
        """BasePolicy objects that govern a section."""
        return [self._policies[sid] for sid in self.statutes_for(section_id)]

    # -- validation --

    def validate(self) -> list[str]:
        """Return a list of issues found in the regulatory data."""
        issues = []
        for bp_id, bp in self._policies.items():
            if not bp.references:
                issues.append(f"{bp_id}: no regulatory references")
            for ref in bp.references:
                if not ref.statute:
                    issues.append(f"{bp_id}: reference missing statute name")
                if not ref.citation:
                    issues.append(f"{bp_id}: reference missing citation")
        return issues

    def __len__(self) -> int:
        return len(self._policies)

    def __contains__(self, statute_id: str) -> bool:
        return statute_id in self._policies

    def __repr__(self) -> str:
        return f"RegulatoryRegistry({len(self)} statutes)"
