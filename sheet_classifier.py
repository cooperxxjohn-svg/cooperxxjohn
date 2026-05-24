"""
Sheet Classifier — identifies the type of a construction drawing sheet.

Uses Claude Vision to classify each page of a drawing set before running
trade-specific extraction, so the extractor uses the right prompt.
"""

from __future__ import annotations
import base64
import io
import json
import logging
from typing import Tuple

import anthropic
from PIL import Image

from takeoff_schema import SheetType

logger = logging.getLogger(__name__)

_CLASSIFY_PROMPT = """You are an expert construction document controller.
Look at this drawing and identify what type of sheet it is.

Return a JSON object with exactly these keys:
{
  "sheet_type": "<type>",
  "confidence": <0.0-1.0>,
  "sheet_number": "<e.g. A-101 or null>",
  "sheet_title": "<e.g. FIRST FLOOR PLAN or null>",
  "reasoning": "<one sentence>"
}

sheet_type must be one of:
  architectural_floor_plan  - floor plan / room layout
  architectural_elevation   - exterior or interior elevation view
  architectural_section     - building or wall cross-section
  architectural_detail      - detail or enlarged view (typ. one element)
  structural                - structural framing, foundation, or rebar plans
  mep_mechanical            - HVAC, ductwork, mechanical equipment
  mep_electrical            - electrical, power, lighting plans
  mep_plumbing              - plumbing, piping, drainage
  civil_site                - site plan, grading, utilities
  landscape                 - landscaping plan
  specification             - text specifications (no drawing)
  sheet_index               - title sheet, drawing index, or general notes
  unknown                   - cannot determine

Confidence guide: 0.95+ = obvious, 0.80 = likely, 0.60 = uncertain.

IMPORTANT: Return ONLY the JSON object. No markdown, no code fences."""


class SheetClassifier:
    """Classifies construction drawing sheets using Claude Vision."""

    def __init__(self, api_key: str, model: str = "claude-opus-4-5"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def classify(
        self,
        image: Image.Image,
        sheet_ref: str = "page",
    ) -> Tuple[SheetType, float, dict]:
        """
        Classify a single drawing image.

        Returns:
            (sheet_type, confidence, raw_response_dict)
        """
        image_b64 = _image_to_b64(image)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=512,
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
                            {"type": "text", "text": _CLASSIFY_PROMPT},
                        ],
                    }
                ],
            )

            raw = _parse_json(message.content[0].text)
            sheet_type = SheetType.from_str(raw.get("sheet_type", "unknown"))
            confidence = float(raw.get("confidence", 0.5))
            logger.info(
                "Sheet %s classified as %s (conf=%.2f)",
                sheet_ref, sheet_type.value, confidence,
            )
            return sheet_type, confidence, raw

        except Exception as exc:
            logger.error("Sheet classification failed for %s: %s", sheet_ref, exc)
            return SheetType.UNKNOWN, 0.0, {"error": str(exc)}


# ── helpers ──────────────────────────────────────────────────────────────────

def _image_to_b64(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _parse_json(text: str) -> dict:
    text = text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Last-resort: find the first { ... } block
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return {}
