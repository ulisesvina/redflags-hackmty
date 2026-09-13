"""Detector registry: one module per detector, discovered automatically.

Each module `agent/detectors/<name>.py` defines exactly one public function `detect_<name>(ds) -> list[dict]`.
It must be a pure function of the Dataset (no I/O, no LLM, never reads `hidden/`). Every returned dict is a
*lead*, not an accusation, and carries at least:

    entity_id : str        the supplier/customer/employee the lead points at (S*, C*, E*)
    evidence  : list[str]  record IDs that triggered it (invoice UUIDs, TX*, CP*, GR*)

plus detector-specific fields. Results must be deterministic (sorted).

Adding a detector never requires editing this file or any other detector: drop in the module and it is
registered on import. Tests live in `tests/test_detect_<name>.py`.
"""
from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable

DETECTORS: dict[str, Callable] = {}

for _m in pkgutil.iter_modules(__path__):
    _mod = importlib.import_module(f"{__name__}.{_m.name}")
    for _k, _v in vars(_mod).items():
        if _k.startswith("detect_") and callable(_v):
            DETECTORS[_k] = _v


def run_all(ds) -> dict[str, list[dict]]:
    """Run every registered detector; returns {detector_name: leads}."""
    return {name: fn(ds) for name, fn in sorted(DETECTORS.items())}
