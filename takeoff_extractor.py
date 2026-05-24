"""
Takeoff Extractor — VLM-based element extraction from construction drawings.

Uses trade-specific prompts so Claude focuses on the right element classes
for each sheet type. Returns a list of DetectedElement objects ready for
the assembly engine.
"""

from __future__ import annotations
import base64
import io
import json
import logging
from typing import Any, Dict, List, Optional

import anthropic
from PIL import Image

from takeoff_schema import DetectedElement, SheetType, TradeCategory

logger = logging.getLogger(__name__)


# ── Per-trade extraction prompts ─────────────────────────────────────────────

_PREAMBLE = """You are a licensed construction estimator performing a quantity takeoff.
Analyze this {sheet_type} drawing carefully. Scale: {scale_text}.

Extract every quantifiable element and return a JSON object:
{{
  "elements": [
    {{
      "element_type": "<type — see valid types below>",
      "trade": "<trade category>",
      "count": <integer>,
      "length_ft": <number|null>,
      "width_ft": <number|null>,
      "height_ft": <number|null>,
      "area_sf": <number|null>,
      "volume_cf": <number|null>,
      "label": "<raw text from drawing>",
      "location": "<grid ref or room name>",
      "confidence": <0.0-1.0>,
      "notes": "<any special conditions>"
    }}
  ],
  "global_notes": ["<important notes about entire sheet>"],
  "warnings": ["<things that need human review>"]
}}

CONFIDENCE GUIDE: 1.0=clearly legible, 0.8=likely, 0.6=estimated, 0.4=guessed.

IMPORTANT RULES:
- Use null for any dimension you cannot read from the drawing.
- Do NOT invent dimensions — use null and note it.
- If multiple identical elements exist, use count > 1 rather than listing each separately.
- Convert all dimensions to DECIMAL FEET (e.g. 3'-6" = 3.5, 8" = 0.667).
- Return ONLY valid JSON. No markdown, no code fences.
"""

_ARCH_FLOOR_PLAN_TYPES = """
VALID element_type values for architectural floor plans:
  door, door_double, door_overhead, door_sliding
  window
  wall_exterior, wall_interior, wall_masonry, wall_curtain
  room  (use area_sf for floor area)
  stair, ramp, elevator
  opening, corridor
  casework, countertop
  flooring_tile, flooring_vct, flooring_carpet, flooring_hardwood
  partition_toilet
  column_concrete, column_steel (if visible on arch plan)

TRADE categories: doors_windows | framing | masonry | finishes | concrete | misc
"""

_STRUCTURAL_TYPES = """
VALID element_type values for structural drawings:
  concrete_slab, concrete_slab_elevated
  column_concrete, column_steel
  beam_concrete, beam_steel
  wall_concrete, shear_wall
  footing_spread, footing_continuous, footing_pile_cap
  grade_beam, retaining_wall

TRADE categories: concrete | framing
"""

_MEP_MECHANICAL_TYPES = """
VALID element_type values for mechanical drawings:
  ahu, vav_box, diffuser, exhaust_fan, chiller, cooling_tower
  ductwork (use length_ft for linear run)
  piping_mechanical (use length_ft)

TRADE categories: hvac
"""

_MEP_ELECTRICAL_TYPES = """
VALID element_type values for electrical drawings:
  panel_electrical, transformer, generator
  outlet_duplex, outlet_gfci, light_fixture, switch, conduit
  fire_alarm_device

TRADE categories: electrical
"""

_MEP_PLUMBING_TYPES = """
VALID element_type values for plumbing drawings:
  toilet, lavatory, urinal, floor_drain, water_heater
  kitchen_sink, mop_sink
  piping_domestic (use length_ft)

TRADE categories: plumbing
"""

_ELEVATION_TYPES = """
VALID element_type values for elevation drawings:
  wall_exterior, window, door, door_overhead
  painting_exterior, cladding, louver
  signage

TRADE categories: finishes | doors_windows | framing
"""

_GENERIC_TYPES = """
Extract whatever building elements you can identify.
Use descriptive element_type strings and best-guess trade categories from:
  concrete | masonry | doors_windows | framing | roofing | flooring |
  finishes | plumbing | hvac | electrical | sitework | miscellaneous
"""

_SHEET_TYPE_CONTEXT: Dict[SheetType, str] = {
    SheetType.ARCHITECTURAL_FLOOR_PLAN: _ARCH_FLOOR_PLAN_TYPES,
    SheetType.ARCHITECTURAL_ELEVATION:  _ELEVATION_TYPES,
    SheetType.ARCHITECTURAL_SECTION:    _ELEVATION_TYPES,
    SheetType.ARCHITECTURAL_DETAIL:     _GENERIC_TYPES,
    SheetType.STRUCTURAL:               _STRUCTURAL_TYPES,
    SheetType.MEP_MECHANICAL:           _MEP_MECHANICAL_TYPES,
    SheetType.MEP_ELECTRICAL:           _MEP_ELECTRICAL_TYPES,
    SheetType.MEP_PLUMBING:             _MEP_PLUMBING_TYPES,
}

_TRADE_MAP: Dict[str, TradeCategory] = {tc.value: tc for tc in TradeCategory}


class TakeoffExtractor:
    """
    Extracts DetectedElement objects from a single drawing image using Claude Vision.
    """

    def __init__(self, api_key: str, model: str = "claude-opus-4-5"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def extract(
        self,
        image: Image.Image,
        sheet_type: SheetType,
        sheet_ref: str = "page",
        scale_text: Optional[str] = None,
    ) -> tuple[List[DetectedElement], List[str], List[str]]:
        """
        Extract elements from a drawing image.

        Returns:
            (elements, global_notes, warnings)
        """
        if sheet_type in (SheetType.SPECIFICATION, SheetType.SHEET_INDEX):
            logger.info("Skipping non-drawing sheet %s (%s)", sheet_ref, sheet_type.value)
            return [], [], []

        type_context = _SHEET_TYPE_CONTEXT.get(sheet_type, _GENERIC_TYPES)
        scale_display = scale_text or "unknown — assume typical architectural scale"

        prompt = (
            _PREAMBLE.format(
                sheet_type=sheet_type.value.replace("_", " ").title(),
                scale_text=scale_display,
            )
            + "\n"
            + type_context
        )

        image_b64 = _image_to_b64(image)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_b64,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )

            raw = _parse_json(message.content[0].text)
            elements = _parse_elements(raw.get("elements", []), sheet_ref)
            notes    = raw.get("global_notes", [])
            warnings = raw.get("warnings", [])

            logger.info(
                "Extracted %d elements from %s (%s)",
                len(elements), sheet_ref, sheet_type.value,
            )
            return elements, notes, warnings

        except Exception as exc:
            logger.error("Extraction failed for %s: %s", sheet_ref, exc)
            return [], [], [f"Extraction error: {exc}"]


# ── helpers ──────────────────────────────────────────────────────────────────

def _parse_elements(raw_list: List[Dict[str, Any]], sheet_ref: str) -> List[DetectedElement]:
    elements: List[DetectedElement] = []
    for item in raw_list:
        try:
            trade_str = item.get("trade", "miscellaneous").strip().lower()
            trade = _TRADE_MAP.get(trade_str, TradeCategory.MISC)

            el = DetectedElement(
                element_type = item.get("element_type", "unknown").strip().lower(),
                trade        = trade,
                count        = int(item.get("count") or 1),
                length_ft    = _float(item.get("length_ft")),
                width_ft     = _float(item.get("width_ft")),
                height_ft    = _float(item.get("height_ft")),
                area_sf      = _float(item.get("area_sf")),
                volume_cf    = _float(item.get("volume_cf")),
                label        = str(item.get("label") or ""),
                location     = str(item.get("location") or ""),
                sheet_ref    = sheet_ref,
                confidence   = float(item.get("confidence") or 0.8),
                notes        = str(item.get("notes") or ""),
                raw_data     = item,
            )
            elements.append(el)
        except Exception as exc:
            logger.warning("Skipping malformed element: %s — %s", item, exc)

    return elements


def _float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _image_to_b64(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return {}
