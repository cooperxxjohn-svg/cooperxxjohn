"""
Takeoff Schema — trade-agnostic data structures for construction quantity takeoff.
Supports US units (ft/in) and SI. Designed to be used alongside the existing
Indian BOQ system without modifying it.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class SheetType(str, Enum):
    ARCHITECTURAL_FLOOR_PLAN = "architectural_floor_plan"
    ARCHITECTURAL_ELEVATION   = "architectural_elevation"
    ARCHITECTURAL_SECTION     = "architectural_section"
    ARCHITECTURAL_DETAIL      = "architectural_detail"
    STRUCTURAL                = "structural"
    MEP_MECHANICAL            = "mep_mechanical"
    MEP_ELECTRICAL            = "mep_electrical"
    MEP_PLUMBING              = "mep_plumbing"
    CIVIL_SITE                = "civil_site"
    LANDSCAPE                 = "landscape"
    SPECIFICATION             = "specification"
    SHEET_INDEX               = "sheet_index"
    UNKNOWN                   = "unknown"

    @classmethod
    def from_str(cls, s: str) -> "SheetType":
        s = s.lower().strip()
        for member in cls:
            if member.value == s or member.name.lower() == s:
                return member
        return cls.UNKNOWN


class TradeCategory(str, Enum):
    CONCRETE      = "concrete"
    MASONRY       = "masonry"
    DOORS_WINDOWS = "doors_windows"
    FRAMING       = "framing"
    ROOFING       = "roofing"
    FLOORING      = "flooring"
    FINISHES      = "finishes"
    PLUMBING      = "plumbing"
    HVAC          = "hvac"
    ELECTRICAL    = "electrical"
    SITEWORK      = "sitework"
    MISC          = "miscellaneous"


class MeasurementUnit(str, Enum):
    # Imperial area / length / volume
    SF  = "SF"   # square feet
    LF  = "LF"   # linear feet
    CF  = "CF"   # cubic feet
    CY  = "CY"   # cubic yards
    SY  = "SY"   # square yards
    # Count
    EA  = "EA"
    SET = "SET"
    LS  = "LS"   # lump sum
    # Weight
    TON = "TON"
    LB  = "LB"
    # Liquid
    GAL = "GAL"
    # SI equivalents
    SQM = "SQM"
    LM  = "LM"
    CUM = "CUM"


@dataclass
class DetectedElement:
    """A single structural or architectural element detected on a drawing sheet."""
    element_type: str               # e.g. "door", "window", "wall_exterior"
    trade: TradeCategory
    count: int = 1
    # Dimensions in feet (None = unknown / not detected)
    length_ft: Optional[float] = None
    width_ft:  Optional[float] = None
    height_ft: Optional[float] = None
    area_sf:   Optional[float] = None
    volume_cf: Optional[float] = None
    # Context
    label:     str = ""             # raw label text from drawing
    location:  str = ""
    sheet_ref: str = ""
    confidence: float = 1.0
    notes:     str = ""
    raw_data:  Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["trade"] = self.trade.value
        return d


@dataclass
class TakeoffLineItem:
    """One cost/quantity line item in the final takeoff output."""
    item_code:    str
    description:  str
    trade:        TradeCategory
    quantity:     float
    unit:         MeasurementUnit
    unit_cost:    Optional[float] = None
    total_cost:   Optional[float] = None
    confidence:   float = 1.0
    notes:        str = ""
    source_refs:  List[str] = field(default_factory=list)  # sheet_ref values

    @property
    def computed_total(self) -> Optional[float]:
        if self.unit_cost is not None:
            return round(self.quantity * self.unit_cost, 2)
        return None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["trade"] = self.trade.value
        d["unit"] = self.unit.value
        d["computed_total"] = self.computed_total
        return d


@dataclass
class SheetExtractionResult:
    """Everything extracted from a single drawing sheet page."""
    sheet_ref:              str
    sheet_type:             SheetType
    sheet_type_confidence:  float
    scale_text:             Optional[str]    # e.g. '1/4" = 1\'-0"'
    scale_ratio:            Optional[float]  # feet per pixel, if computed
    elements:               List[DetectedElement] = field(default_factory=list)
    raw_extraction:         Dict[str, Any]   = field(default_factory=dict)
    processing_notes:       List[str]        = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "sheet_ref": self.sheet_ref,
            "sheet_type": self.sheet_type.value,
            "sheet_type_confidence": self.sheet_type_confidence,
            "scale_text": self.scale_text,
            "scale_ratio": self.scale_ratio,
            "elements": [e.to_dict() for e in self.elements],
            "processing_notes": self.processing_notes,
        }


@dataclass
class TakeoffResult:
    """Complete takeoff result for an entire drawing set."""
    job_id:               str = field(default_factory=lambda: str(uuid.uuid4()))
    project_name:         str = ""
    created_at:           str = field(default_factory=lambda: datetime.utcnow().isoformat())
    sheets_processed:     int = 0
    sheet_results:        List[SheetExtractionResult] = field(default_factory=list)
    line_items:           List[TakeoffLineItem]       = field(default_factory=list)
    elements_by_type:     Dict[str, int]              = field(default_factory=dict)
    elements_by_trade:    Dict[str, int]              = field(default_factory=dict)
    total_cost_estimate:  Optional[float]             = None
    currency:             str = "USD"
    confidence_avg:       float = 0.0
    warnings:             List[str] = field(default_factory=list)

    def summarize(self):
        """Populate summary fields from sheet_results and line_items."""
        self.sheets_processed = len(self.sheet_results)

        # Element counts
        type_counts: Dict[str, int] = {}
        trade_counts: Dict[str, int] = {}
        confidences = []
        for sr in self.sheet_results:
            for el in sr.elements:
                type_counts[el.element_type] = type_counts.get(el.element_type, 0) + el.count
                trade_key = el.trade.value
                trade_counts[trade_key] = trade_counts.get(trade_key, 0) + el.count
                confidences.append(el.confidence)

        self.elements_by_type  = type_counts
        self.elements_by_trade = trade_counts
        self.confidence_avg = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

        # Cost rollup
        totals = [li.computed_total for li in self.line_items if li.computed_total is not None]
        self.total_cost_estimate = round(sum(totals), 2) if totals else None

    def to_dict(self) -> dict:
        return {
            "job_id":              self.job_id,
            "project_name":        self.project_name,
            "created_at":          self.created_at,
            "sheets_processed":    self.sheets_processed,
            "elements_by_type":    self.elements_by_type,
            "elements_by_trade":   self.elements_by_trade,
            "total_cost_estimate": self.total_cost_estimate,
            "currency":            self.currency,
            "confidence_avg":      self.confidence_avg,
            "warnings":            self.warnings,
            "line_items":          [li.to_dict() for li in self.line_items],
            "sheet_results":       [sr.to_dict() for sr in self.sheet_results],
        }
