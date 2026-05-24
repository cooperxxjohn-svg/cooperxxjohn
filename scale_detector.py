"""
Scale Detector -- reads the scale annotation from a construction drawing.

Architectural drawings carry either:
  - A text annotation like 1/4 inch = 1 foot, 1:100, or NTS (not to scale)
  - A graphical scale bar with labeled lengths

This module extracts the text and, where possible, derives a real-feet-per-
paper-inch ratio so pixel measurements can be converted to real-world dims.
Phase 2 will augment this with OpenCV-based scale bar pixel detection.
"""

from __future__ import annotations
import base64
import io
import json
import logging
import re
from typing import Optional, Tuple

import anthropic
from PIL import Image

logger = logging.getLogger(__name__)

_SCALE_PROMPT = (
    "You are analyzing a construction drawing for scale information.\n"
    "\n"
    "Look for:\n"
    "1. Text scale annotations like '1/4\" = 1\\'-0\"', 'SCALE: 1:100', 'NTS' (not to scale)\n"
    "2. A graphical scale bar (horizontal bar with labeled lengths)\n"
    "3. Scale noted in the title block\n"
    "\n"
    "Return JSON:\n"
    "{\n"
    '  "scale_found": true/false,\n'
    '  "scale_text": "<raw text or null>",\n'
    '  "scale_type": "architectural | engineering | metric | nts | unknown",\n'
    '  "confidence": 0.0-1.0\n'
    "}\n"
    "\n"
    "Common architectural scales (paper inches to real feet):\n"
    "  1/8\" = 1'-0\"  -> 1 paper inch = 8 real feet\n"
    "  1/4\" = 1'-0\"  -> 1 paper inch = 4 real feet\n"
    "  3/8\" = 1'-0\"  -> 1 paper inch = 2.667 real feet\n"
    "  1/2\" = 1'-0\"  -> 1 paper inch = 2 real feet\n"
    "  3/4\" = 1'-0\"  -> 1 paper inch = 1.333 real feet\n"
    "  1\" = 1'-0\"    -> full scale\n"
    "\n"
    "IMPORTANT: Return ONLY valid JSON. No markdown."
)


class ScaleDetector:
    """Detects drawing scale using Claude Vision."""

    def __init__(self, api_key: str, model: str = "claude-opus-4-5"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def detect(self, image: Image.Image) -> Tuple[Optional[str], Optional[float]]:
        """
        Detect scale from a drawing image.

        Returns:
            (scale_text, paper_inches_to_real_feet_ratio)
            ratio is None when scale cannot be determined.
        """
        image_b64 = _image_to_b64(image)
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=256,
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
                            {"type": "text", "text": _SCALE_PROMPT},
                        ],
                    }
                ],
            )
            raw = _parse_json(message.content[0].text)
            scale_text = raw.get("scale_text") or None
            ratio = _extract_ratio(scale_text) if scale_text else None
            logger.info("Scale detected: %s  ratio=%s", scale_text, ratio)
            return scale_text, ratio
        except Exception as exc:
            logger.error("Scale detection failed: %s", exc)
            return None, None


# ---------------------------------------------------------------------------
# Ratio parsing
# ---------------------------------------------------------------------------

# Lookup table: simplified key -> real feet per paper inch
# Keys use only ASCII quote chars (" and ')
_ARCH_SCALE_TABLE = {
    '1"=10\'':  10.0,
    '1"=20\'':  20.0,
    '1/8"=1\'': 8.0,
    '1/4"=1\'': 4.0,
    '3/8"=1\'': 2.6667,
    '1/2"=1\'': 2.0,
    '3/4"=1\'': 1.3333,
    '1"=1\'':   1.0,
    '1.5"=1\'': 0.6667,
    '3"=1\'':   0.3333,
}

# Map of non-ASCII quote characters to ASCII equivalents (by code point)
_FANCY_QUOTE_MAP = {
    chr(0x201C): '"',   # LEFT DOUBLE QUOTATION MARK
    chr(0x201D): '"',   # RIGHT DOUBLE QUOTATION MARK
    chr(0x2018): "'",   # LEFT SINGLE QUOTATION MARK
    chr(0x2019): "'",   # RIGHT SINGLE QUOTATION MARK
    chr(0x0060): "'",   # GRAVE ACCENT
    chr(0x00B4): "'",   # ACUTE ACCENT
}


def _normalise(text: str) -> str:
    """Lowercase, strip whitespace, normalise quotes to ASCII."""
    s = text.strip().lower()
    s = re.sub(r"\s+", "", s)
    s = s.replace(chr(0x2212), "-").replace(chr(0x2013), "-")  # minus/en-dash
    for fancy, plain in _FANCY_QUOTE_MAP.items():
        s = s.replace(fancy, plain)
    return s


def _extract_ratio(scale_text: str) -> Optional[float]:
    """
    Convert a scale text string to real-feet-per-paper-inch.
    Returns None if the scale cannot be parsed.
    """
    s = _normalise(scale_text)

    # Quick table lookup
    for key, ratio in _ARCH_SCALE_TABLE.items():
        if re.sub(r"\s+", "", key.lower()) in s:
            return ratio

    # Pattern: N/D" = M'-0"  e.g. 1/4"=1'-0"
    m = re.search(r"(\d+)/(\d+)\"=(\d+)'", s)
    if m:
        paper_frac = int(m.group(1)) / int(m.group(2))
        real_ft = int(m.group(3))
        return real_ft / paper_frac

    # Pattern: N" = M'  e.g. 1"=20'
    m = re.search(r"(\d+)\"=(\d+)'", s)
    if m:
        return int(m.group(2)) / int(m.group(1))

    # Pattern: 1:N  e.g. 1:100
    m = re.search(r"1:(\d+)", s)
    if m:
        # 1:N where units are both inches -> convert to feet
        return int(m.group(1)) / 12.0

    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
