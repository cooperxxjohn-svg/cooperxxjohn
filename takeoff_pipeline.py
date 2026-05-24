"""
Takeoff Pipeline — full end-to-end orchestrator.

Flow per sheet:
  1. Render PDF page (or load image)
  2. Classify sheet type (SheetClassifier)
  3. Detect scale (ScaleDetector)
  4. Extract elements (TakeoffExtractor)
  5. Expand to line items (AssemblyEngine)

Returns a TakeoffResult with all sheet results, aggregated line items,
and summary statistics.
"""

from __future__ import annotations
import json
import logging
import os
from pathlib import Path
from typing import List, Optional, Union

from PIL import Image

from assembly_engine import AssemblyEngine
from scale_detector import ScaleDetector
from sheet_classifier import SheetClassifier
from takeoff_extractor import TakeoffExtractor
from takeoff_schema import (
    SheetExtractionResult,
    SheetType,
    TakeoffLineItem,
    TakeoffResult,
)

logger = logging.getLogger(__name__)


class TakeoffPipeline:
    """
    Main pipeline for construction drawing takeoff.

    Args:
        api_key:     Anthropic API key.
        rules_dir:   Path to YAML assembly rules directory.
        model:       Claude model to use for all VLM calls.
        dpi:         DPI for PDF-to-image conversion (300 recommended).
        skip_types:  Sheet types to skip (default: specification, sheet_index).
    """

    DEFAULT_SKIP = {SheetType.SPECIFICATION, SheetType.SHEET_INDEX}

    def __init__(
        self,
        api_key: str,
        rules_dir: Optional[str] = None,
        model: str = "claude-opus-4-5",
        dpi: int = 200,
        skip_types: Optional[set] = None,
    ):
        self.api_key   = api_key
        self.dpi       = dpi
        self.skip_types = skip_types if skip_types is not None else self.DEFAULT_SKIP

        self.classifier = SheetClassifier(api_key=api_key, model=model)
        self.scale_det  = ScaleDetector(api_key=api_key,  model=model)
        self.extractor  = TakeoffExtractor(api_key=api_key, model=model)
        self.assembler  = AssemblyEngine(rules_dir=rules_dir)

        logger.info(
            "TakeoffPipeline ready — model=%s dpi=%d rules=%d types",
            model, dpi, len(self.assembler.known_types()),
        )

    # ── public entry points ───────────────────────────────────────────────────

    def process_pdf(
        self,
        pdf_path: Union[str, Path],
        project_name: str = "",
        page_limit: Optional[int] = None,
    ) -> TakeoffResult:
        """Process all pages of a PDF drawing set."""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        images = _render_pdf(pdf_path, dpi=self.dpi)
        if page_limit:
            images = images[:page_limit]

        logger.info("Processing PDF: %s (%d pages)", pdf_path.name, len(images))
        return self._process_images(images, project_name or pdf_path.stem)

    def process_images(
        self,
        image_paths: List[Union[str, Path]],
        project_name: str = "",
    ) -> TakeoffResult:
        """Process a list of image files."""
        images = [Image.open(p) for p in image_paths]
        return self._process_images(images, project_name)

    def process_single_image(
        self,
        image: Image.Image,
        project_name: str = "",
        sheet_ref: str = "page_1",
    ) -> TakeoffResult:
        """Process a single PIL Image (useful for testing)."""
        return self._process_images([image], project_name, base_sheet_ref=sheet_ref)

    # ── core loop ─────────────────────────────────────────────────────────────

    def _process_images(
        self,
        images: List[Image.Image],
        project_name: str,
        base_sheet_ref: str = "page",
    ) -> TakeoffResult:
        result = TakeoffResult(project_name=project_name)
        all_line_items: List[TakeoffLineItem] = []

        for idx, image in enumerate(images, start=1):
            sheet_ref = f"{base_sheet_ref}_{idx}"
            logger.info("--- Processing %s (%d/%d) ---", sheet_ref, idx, len(images))

            sr = self._process_sheet(image, sheet_ref)
            result.sheet_results.append(sr)

            if sr.sheet_type in self.skip_types:
                logger.info("Skipping %s — sheet type %s", sheet_ref, sr.sheet_type.value)
                continue

            # Assemble elements → line items
            sheet_items = self.assembler.expand(sr.elements)
            for li in sheet_items:
                if sheet_ref not in li.source_refs:
                    li.source_refs.append(sheet_ref)
            all_line_items.extend(sheet_items)

        # Final aggregation across all sheets
        result.line_items = _aggregate_all(all_line_items)
        result.summarize()

        logger.info(
            "Pipeline complete: %d sheets, %d line items, %d elements",
            result.sheets_processed,
            len(result.line_items),
            sum(result.elements_by_type.values()),
        )
        return result

    def _process_sheet(self, image: Image.Image, sheet_ref: str) -> SheetExtractionResult:
        notes: List[str] = []
        warnings: List[str] = []

        # Step 1 — classify
        sheet_type, type_conf, raw_cls = self.classifier.classify(image, sheet_ref)
        if raw_cls.get("sheet_title"):
            notes.append(f"Title: {raw_cls['sheet_title']}")
        if raw_cls.get("sheet_number"):
            notes.append(f"Number: {raw_cls['sheet_number']}")

        # Step 2 — scale detection
        scale_text, scale_ratio = None, None
        if sheet_type not in self.skip_types:
            scale_text, scale_ratio = self.scale_det.detect(image)
            if scale_text:
                notes.append(f"Scale: {scale_text}")
            else:
                warnings.append("Scale not detected — dimensions may be inaccurate")

        # Step 3 — element extraction
        elements, ext_notes, ext_warnings = self.extractor.extract(
            image, sheet_type, sheet_ref, scale_text
        )
        notes.extend(ext_notes)
        warnings.extend(ext_warnings)

        return SheetExtractionResult(
            sheet_ref             = sheet_ref,
            sheet_type            = sheet_type,
            sheet_type_confidence = type_conf,
            scale_text            = scale_text,
            scale_ratio           = scale_ratio,
            elements              = elements,
            raw_extraction        = {"classifier": raw_cls},
            processing_notes      = notes + [f"WARN: {w}" for w in warnings],
        )

    # ── output helpers ────────────────────────────────────────────────────────

    def save_result(
        self,
        result: TakeoffResult,
        output_dir: Union[str, Path],
        filename: str = "takeoff_result.json",
    ) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / filename
        with open(out_path, "w") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        logger.info("Result saved to %s", out_path)
        return out_path

    def print_summary(self, result: TakeoffResult):
        print("\n" + "=" * 70)
        print(f"  TAKEOFF SUMMARY — {result.project_name}")
        print("=" * 70)
        print(f"  Sheets processed : {result.sheets_processed}")
        print(f"  Line items       : {len(result.line_items)}")
        print(f"  Avg confidence   : {result.confidence_avg:.0%}")
        if result.total_cost_estimate:
            print(f"  Cost estimate    : ${result.total_cost_estimate:,.2f} {result.currency}")
        print()

        if result.elements_by_type:
            print("  ELEMENTS DETECTED:")
            for etype, cnt in sorted(result.elements_by_type.items()):
                print(f"    {etype:<30} {cnt:>5}")
            print()

        print("  TOP LINE ITEMS (by quantity):")
        for li in sorted(result.line_items, key=lambda x: x.quantity, reverse=True)[:15]:
            cost_str = f"  unit_cost TBD" if li.unit_cost is None else f"  ${li.computed_total:,.0f}"
            print(f"    [{li.item_code}] {li.description[:45]:<46}"
                  f"  {li.quantity:>9.2f} {li.unit.value:<5}{cost_str}")

        print("=" * 70 + "\n")


# ── helpers ───────────────────────────────────────────────────────────────────

def _render_pdf(pdf_path: Path, dpi: int) -> List[Image.Image]:
    """Convert PDF pages to PIL Images using pdf2image."""
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(str(pdf_path), dpi=dpi)
        logger.info("Rendered %d pages from %s at %d dpi", len(images), pdf_path.name, dpi)
        return images
    except ImportError:
        raise RuntimeError(
            "pdf2image not installed. Run: pip install pdf2image "
            "and install poppler-utils (apt-get install poppler-utils)."
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to render PDF: {exc}") from exc


def _aggregate_all(items: List[TakeoffLineItem]) -> List[TakeoffLineItem]:
    """Final cross-sheet aggregation by item_code."""
    merged: dict = {}
    for li in items:
        if li.item_code in merged:
            ex = merged[li.item_code]
            ex.quantity = round(ex.quantity + li.quantity, 3)
            ex.source_refs = list(set(ex.source_refs + li.source_refs))
            ex.confidence = min(ex.confidence, li.confidence)
        else:
            merged[li.item_code] = li
    return list(merged.values())
