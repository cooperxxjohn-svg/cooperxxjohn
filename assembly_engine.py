"""
Assembly Engine — expands detected elements into takeoff line items.

Reads YAML rule files from the rules/ directory. Each rule maps an
element_type to a list of cost items with quantity formulas.

Formula expressions are evaluated in a sandboxed namespace containing
the element's numeric attributes and safe math functions.
"""

from __future__ import annotations
import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from takeoff_schema import DetectedElement, MeasurementUnit, TakeoffLineItem, TradeCategory

logger = logging.getLogger(__name__)

_UNIT_MAP: Dict[str, MeasurementUnit] = {u.value: u for u in MeasurementUnit}

# Safe builtins for formula evaluation
_SAFE_BUILTINS: Dict[str, Any] = {
    "abs": abs, "round": round, "min": min, "max": max,
    "sqrt": math.sqrt, "ceil": math.ceil, "floor": math.floor,
}


class AssemblyEngine:
    """
    Loads YAML assembly rules and converts DetectedElement lists into
    TakeoffLineItem lists.
    """

    def __init__(self, rules_dir: Optional[str] = None):
        if rules_dir is None:
            rules_dir = Path(__file__).parent / "rules"
        self.rules_dir = Path(rules_dir)
        self._rules: Dict[str, Any] = {}
        self._load_all_rules()

    # ── public API ────────────────────────────────────────────────────────────

    def expand(self, elements: List[DetectedElement]) -> List[TakeoffLineItem]:
        """
        Expand a list of DetectedElement objects into TakeoffLineItem objects.
        Elements with unknown element_type are passed through as a generic item.
        """
        line_items: List[TakeoffLineItem] = []
        for el in elements:
            items = self._expand_element(el)
            line_items.extend(items)
        return _aggregate(line_items)

    def known_types(self) -> List[str]:
        return sorted(self._rules.keys())

    # ── rule loading ──────────────────────────────────────────────────────────

    def _load_all_rules(self):
        if not self.rules_dir.exists():
            logger.warning("Rules directory not found: %s", self.rules_dir)
            return

        for yaml_file in sorted(self.rules_dir.glob("*.yaml")):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                if isinstance(data, dict):
                    for element_type, rule in data.items():
                        self._rules[element_type.lower()] = rule
                logger.debug("Loaded rules from %s (%d types)", yaml_file.name, len(data or {}))
            except Exception as exc:
                logger.error("Failed to load %s: %s", yaml_file, exc)

        logger.info("Assembly engine loaded %d element type rules", len(self._rules))

    # ── element expansion ─────────────────────────────────────────────────────

    def _expand_element(self, el: DetectedElement) -> List[TakeoffLineItem]:
        rule = self._rules.get(el.element_type.lower())

        if rule is None:
            # Unmapped type — emit a generic placeholder so nothing is lost
            return [_generic_item(el)]

        trade_str = rule.get("trade", el.trade.value)
        trade = TradeCategory(trade_str) if trade_str in TradeCategory._value2member_map_ else el.trade

        items: List[TakeoffLineItem] = []
        for item_def in rule.get("items", []):
            try:
                qty = _evaluate_formula(item_def["formula"], el, item_def)
                if qty is None or qty < 0:
                    qty = 0.0

                unit_str = item_def.get("unit", "EA")
                unit = _UNIT_MAP.get(unit_str, MeasurementUnit.EA)

                li = TakeoffLineItem(
                    item_code   = item_def["code"],
                    description = item_def["description"],
                    trade       = trade,
                    quantity    = round(qty, 3),
                    unit        = unit,
                    confidence  = el.confidence,
                    notes       = _build_notes(el, item_def),
                    source_refs = [el.sheet_ref],
                )
                items.append(li)

            except Exception as exc:
                logger.warning(
                    "Formula error for %s / %s: %s",
                    el.element_type, item_def.get("code", "?"), exc,
                )

        return items


# ── formula evaluation ────────────────────────────────────────────────────────

def _evaluate_formula(
    formula: str,
    el: DetectedElement,
    item_def: Dict[str, Any],
) -> Optional[float]:
    """
    Evaluate a formula string in a namespace containing the element's
    numeric attributes plus any default_* overrides from the rule.
    """
    ns: Dict[str, Any] = {
        "count":     float(el.count),
        "length_ft": _resolve(el.length_ft, item_def.get("default_length")),
        "width_ft":  _resolve(el.width_ft,  item_def.get("default_width")),
        "height_ft": _resolve(el.height_ft, item_def.get("default_height")),
        "area_sf":   _resolve(el.area_sf,   item_def.get("default_area")),
        "volume_cf": _resolve(el.volume_cf, item_def.get("default_volume")),
        **_SAFE_BUILTINS,
    }
    # Derived helpers
    if ns["length_ft"] and ns["width_ft"] and not ns["area_sf"]:
        ns["area_sf"] = ns["length_ft"] * ns["width_ft"]

    result = eval(formula, {"__builtins__": {}}, ns)  # noqa: S307
    return float(result) if result is not None else None


def _resolve(value: Optional[float], default: Any) -> Optional[float]:
    """Return value if set, else cast default to float if provided."""
    if value is not None:
        return float(value)
    if default is not None:
        return float(default)
    return None


# ── aggregation ──────────────────────────────────────────────────────────────

def _aggregate(items: List[TakeoffLineItem]) -> List[TakeoffLineItem]:
    """
    Merge line items that share the same item_code by summing quantities
    and combining source_refs.
    """
    merged: Dict[str, TakeoffLineItem] = {}
    for li in items:
        if li.item_code in merged:
            existing = merged[li.item_code]
            existing.quantity = round(existing.quantity + li.quantity, 3)
            existing.source_refs = list(set(existing.source_refs + li.source_refs))
            # Conservative: use minimum confidence
            existing.confidence = min(existing.confidence, li.confidence)
        else:
            merged[li.item_code] = li

    return list(merged.values())


# ── generic fallback ──────────────────────────────────────────────────────────

def _generic_item(el: DetectedElement) -> TakeoffLineItem:
    """Create a placeholder line item for an unmapped element type."""
    qty = float(el.count)
    unit = MeasurementUnit.EA

    if el.area_sf is not None:
        qty = el.area_sf
        unit = MeasurementUnit.SF
    elif el.length_ft is not None:
        qty = el.length_ft * el.count
        unit = MeasurementUnit.LF

    return TakeoffLineItem(
        item_code   = f"UNMAPPED-{el.element_type.upper()}",
        description = f"{el.element_type.replace('_', ' ').title()} — VERIFY",
        trade       = el.trade,
        quantity    = round(qty, 3),
        unit        = unit,
        confidence  = el.confidence * 0.5,  # penalise unmapped items
        notes       = f"No assembly rule defined. Location: {el.location}. {el.notes}".strip(),
        source_refs = [el.sheet_ref],
    )


def _build_notes(el: DetectedElement, item_def: Dict[str, Any]) -> str:
    parts = []
    if el.label:
        parts.append(f"Label: {el.label}")
    if el.location:
        parts.append(f"Loc: {el.location}")
    if item_def.get("notes"):
        parts.append(item_def["notes"])
    return " | ".join(parts)
