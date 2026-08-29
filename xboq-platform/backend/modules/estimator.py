"""
Construction Estimator Module
Generates estimates for drywall, painting, concrete trades
New functionality for xboq.ai

Enhanced with Phase 1 precise measurements:
- Scale detection and calibration
- OCR dimension extraction
- Pixel-perfect measurements
- Multi-source validation
- Confidence scoring
"""

import json
import logging
from utils.pdf_processor import PDFProcessor
from utils.claude_client import ClaudeClient

# Phase 1: Precise measurement modules
try:
    from utils.precise_takeoff_pipeline import PreciseTakeoffPipeline
    PRECISION_MODE_AVAILABLE = True
except ImportError:
    PRECISION_MODE_AVAILABLE = False
    logging.warning("Precision modules not available. Install: pip install opencv-python keras-ocr shapely")

logger = logging.getLogger(__name__)


class ConstructionEstimator:
    """
    AI-powered construction estimator for multiple trades

    Features:
    - Claude API for initial room detection
    - Precise measurements with validation (Phase 1)
    - Multi-source cross-validation
    - Confidence scoring
    """

    def __init__(self, use_precision: bool = True):
        self.pdf_processor = PDFProcessor()
        self.claude = ClaudeClient()

        # Initialize precision pipeline if available
        self.use_precision = use_precision and PRECISION_MODE_AVAILABLE
        if self.use_precision:
            try:
                self.precision_pipeline = PreciseTakeoffPipeline()
                logger.info("✓ Construction Estimator initialized with precision mode")
            except Exception as e:
                logger.warning(f"Precision mode failed to initialize: {e}")
                self.use_precision = False
                logger.info("Construction Estimator initialized (standard mode)")
        else:
            logger.info("Construction Estimator initialized (standard mode)")

    def generate_drywall_estimate(self, input_data: dict) -> dict:
        """
        Generate drywall estimate from user input or extracted floor plan

        Args:
            input_data: dict with rooms, finish_level, project_type

        Returns:
            dict with estimate details
        """
        logger.info("Generating drywall estimate...")

        prompt = f"""You are a professional drywall estimator. Generate a detailed drywall estimate.

INPUT DATA:
{json.dumps(input_data, indent=2)}

Analyze the room data and create a comprehensive drywall estimate following industry standards.

Return ONLY valid JSON in this exact format:
{{
    "project_name": "Drywall Estimate",
    "summary": {{
        "total_walls": 0,
        "wall_sqft": 0,
        "ceiling_sqft": 0,
        "total_sqft": 0
    }},
    "materials": {{
        "sheets": 0,
        "compound_lbs": 0,
        "tape_lf": 0,
        "screws": 0,
        "corner_bead_lf": 0
    }},
    "labor": {{
        "hanging_hours": 0,
        "taping_hours": 0,
        "finishing_hours": 0,
        "total_hours": 0
    }},
    "costs": {{
        "material_cost": 0,
        "labor_cost": 0,
        "subtotal": 0,
        "overhead": 0,
        "profit": 0,
        "total_cost": 0,
        "cost_per_sqft": 0
    }},
    "rooms": [
        {{
            "name": "Room name",
            "wall_sqft": 0,
            "ceiling_sqft": 0,
            "total_sqft": 0
        }}
    ]
}}

Use these industry standards:
- ASTM C840 finish levels (Level 4 is standard commercial)
- 15% waste factor for materials
- Standard drywall sheet: 4' × 8' (32 sqft)
- Labor rates: $65/hr commercial, $60/hr residential
- Overhead: 25%, Profit: 25%
- Hanging: ~40 sqft/hr
- Taping: ~150 sqft/hr
- Finishing: ~200 sqft/hr (adjusted by finish level)
- Compound rates by finish level:
  - Level 0: 0 lbs/sqft
  - Level 1: 0.028 lbs/sqft
  - Level 2: 0.04 lbs/sqft
  - Level 3: 0.053 lbs/sqft
  - Level 4: 0.067 lbs/sqft (standard)
  - Level 5: 0.095 lbs/sqft
"""

        try:
            response_text = self.claude.generate(prompt, max_tokens=4000)

            try:
                estimate_json = json.loads(response_text)
                logger.info("Successfully generated drywall estimate")
                return {
                    "status": "success",
                    "trade": "drywall",
                    "estimate": estimate_json,
                    "tool": "estimator"
                }
            except json.JSONDecodeError:
                return {
                    "status": "partial",
                    "trade": "drywall",
                    "estimate": response_text,
                    "tool": "estimator"
                }

        except Exception as e:
            logger.error(f"Error generating drywall estimate: {e}")
            return {
                "status": "error",
                "error": str(e),
                "tool": "estimator"
            }

    def generate_painting_estimate(self, input_data: dict) -> dict:
        """
        Generate painting estimate

        Args:
            input_data: dict with rooms and painting specifications

        Returns:
            dict with estimate details
        """
        logger.info("Generating painting estimate...")

        prompt = f"""You are a professional painting estimator. Generate a detailed painting estimate.

INPUT DATA:
{json.dumps(input_data, indent=2)}

Return ONLY valid JSON:
{{
    "project_name": "Painting Estimate",
    "summary": {{
        "total_area": 0,
        "wall_area": 0,
        "ceiling_area": 0,
        "trim_lf": 0,
        "doors": 0,
        "windows": 0
    }},
    "materials": {{
        "primer_gallons": 0,
        "paint_gallons": 0,
        "supplies_cost": 0,
        "total_material_cost": 0
    }},
    "labor": {{
        "prep_hours": 0,
        "primer_hours": 0,
        "paint_hours": 0,
        "total_hours": 0
    }},
    "costs": {{
        "material_cost": 0,
        "labor_cost": 0,
        "subtotal": 0,
        "overhead": 0,
        "profit": 0,
        "total_cost": 0,
        "cost_per_sqft": 0
    }},
    "rooms": [
        {{
            "name": "Room name",
            "wall_area": 0,
            "ceiling_area": 0,
            "paint_gallons": 0
        }}
    ]
}}

Use these standards:
- Coverage: 350-400 sqft/gallon
- 2 coats standard (primer + paint)
- Labor: $50-60/hr
- Prep work: 30% of total time
- Overhead: 25%, Profit: 25%
"""

        try:
            response_text = self.claude.generate(prompt, max_tokens=4000)

            try:
                estimate_json = json.loads(response_text)
                return {
                    "status": "success",
                    "trade": "painting",
                    "estimate": estimate_json,
                    "tool": "estimator"
                }
            except json.JSONDecodeError:
                return {
                    "status": "partial",
                    "trade": "painting",
                    "estimate": response_text,
                    "tool": "estimator"
                }

        except Exception as e:
            logger.error(f"Error generating painting estimate: {e}")
            return {
                "status": "error",
                "error": str(e),
                "tool": "estimator"
            }

    def process_floor_plan(self, pdf_path: str, trade: str = "drywall") -> dict:
        """
        Process floor plan PDF and generate estimate

        Args:
            pdf_path: Path to floor plan PDF
            trade: Type of estimate (drywall, painting, etc.)

        Returns:
            dict with estimate
        """
        logger.info(f"Processing floor plan for {trade} estimate")

        # Use precision mode if available
        if self.use_precision:
            return self.process_floor_plan_precise(pdf_path, trade)

        # Fallback to standard mode
        # Extract text from PDF
        text = self.pdf_processor.extract_text_hybrid(pdf_path)

        if not text or len(text) < 50:
            return {
                "status": "error",
                "error": "Could not extract meaningful data from floor plan",
                "tool": "estimator"
            }

        # Prepare input data
        input_data = {
            "source": "floor_plan_pdf",
            "extracted_text": text[:3000],
            "trade": trade
        }

        # Generate estimate based on trade
        if trade == "drywall":
            return self.generate_drywall_estimate(input_data)
        elif trade == "painting":
            return self.generate_painting_estimate(input_data)
        else:
            return {
                "status": "error",
                "error": f"Unsupported trade: {trade}",
                "tool": "estimator"
            }

    def process_floor_plan_precise(self, pdf_path: str, trade: str = "drywall") -> dict:
        """
        Process floor plan with Phase 1 precision measurements

        Workflow:
        1. Convert PDF to image
        2. Claude API: Detect rooms (initial)
        3. Precision Pipeline: Scale + OCR + Measurements + Validation
        4. Generate estimate with validated measurements
        5. Return with confidence scores

        Args:
            pdf_path: Path to floor plan PDF
            trade: Type of estimate (drywall, painting, etc.)

        Returns:
            dict with precise estimate + validation info
        """
        logger.info(f"🎯 Processing floor plan with PRECISION mode ({trade})")

        try:
            # Step 1: Convert PDF to image
            logger.info("Step 1/4: Converting PDF to image...")
            images = self.pdf_processor.convert_pdf_to_images(pdf_path)

            if not images or len(images) == 0:
                return {
                    "status": "error",
                    "error": "Could not convert PDF to image",
                    "tool": "estimator_precise"
                }

            # Use first page (floor plan)
            image_path = images[0]
            logger.info(f"  ✓ Converted to image: {image_path}")

            # Step 2: Claude API - Initial room detection
            logger.info("Step 2/4: Claude API room detection...")
            claude_result = self._detect_rooms_with_claude(image_path)

            if claude_result['status'] != 'success':
                return claude_result

            claude_rooms = claude_result.get('rooms', [])
            logger.info(f"  ✓ Claude detected {len(claude_rooms)} rooms")

            # Extract room boundaries for precision measurement
            # (Claude gives approximate boundaries, we'll validate them)
            room_boundaries = []
            for room in claude_rooms:
                if 'boundary' in room:
                    room_boundaries.append(room['boundary'])

            # Step 3: Precision Pipeline - Validate & enhance measurements
            logger.info("Step 3/4: Running precision validation pipeline...")

            precision_result = self.precision_pipeline.process_floor_plan(
                image_path=image_path,
                room_boundaries=room_boundaries if room_boundaries else None,
                llm_output=claude_rooms
            )

            validated_rooms = precision_result['rooms']
            summary = precision_result['summary']

            logger.info(f"  ✓ Validated {summary['total_rooms']} rooms")
            logger.info(f"    High confidence: {summary['high_confidence']}")
            logger.info(f"    Needs review: {summary['needs_review']}")

            # Step 4: Generate estimate with validated measurements
            logger.info("Step 4/4: Generating estimate with validated data...")

            # Prepare input with validated measurements
            input_data = {
                "source": "floor_plan_pdf_precise",
                "trade": trade,
                "rooms": [
                    {
                        "name": room['name'],
                        "sqft": room['final_area_sqft'],
                        "perimeter_ft": room.get('sources', {}).get('pixel', {}).get('perimeter'),
                        "confidence": room['confidence'],
                        "needs_review": room['needs_review']
                    }
                    for room in validated_rooms
                ]
            }

            # Generate estimate
            if trade == "drywall":
                estimate_result = self.generate_drywall_estimate(input_data)
            elif trade == "painting":
                estimate_result = self.generate_painting_estimate(input_data)
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported trade: {trade}",
                    "tool": "estimator_precise"
                }

            # Enhance result with precision data
            if estimate_result['status'] == 'success':
                estimate_result['precision'] = {
                    'scale_info': precision_result['scale_info'],
                    'validation_summary': summary,
                    'processing_time': precision_result['processing_time'],
                    'rooms_with_confidence': [
                        {
                            'name': r['name'],
                            'area_sqft': r['final_area_sqft'],
                            'confidence': r['confidence'],
                            'needs_review': r['needs_review'],
                            'validation_score': r['validation_score']
                        }
                        for r in validated_rooms
                    ],
                    'flagged_for_review': [
                        r['name'] for r in validated_rooms if r['needs_review']
                    ]
                }

                logger.info(f"  ✓ Estimate generated with precision validation")

                if summary['needs_review'] > 0:
                    logger.warning(f"  ⚠️ {summary['needs_review']} room(s) flagged for review")

            return estimate_result

        except Exception as e:
            logger.error(f"Error in precision floor plan processing: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "tool": "estimator_precise"
            }

    def _detect_rooms_with_claude(self, image_path: str) -> dict:
        """
        Use Claude API to detect rooms from floor plan image

        Returns:
            {
                'status': 'success',
                'rooms': [
                    {
                        'name': 'Living Room',
                        'sqft': 240,
                        'length': 17.5,
                        'width': 14,
                        'boundary': [(x1,y1), (x2,y2), ...]  # optional
                    }
                ]
            }
        """
        prompt = """Analyze this floor plan image and detect all rooms.

For each room, provide:
- Name (Living Room, Kitchen, Bedroom 1, etc.)
- Approximate area in square feet
- Length and width if rectangular

Return ONLY valid JSON in this format:
{
    "rooms": [
        {
            "name": "Living Room",
            "sqft": 240,
            "length": 17.5,
            "width": 14
        }
    ]
}"""

        try:
            # Use Claude's vision capability
            response_text = self.claude.analyze_image(image_path, prompt)

            # Parse JSON response
            try:
                result = json.loads(response_text)
                return {
                    'status': 'success',
                    'rooms': result.get('rooms', [])
                }
            except json.JSONDecodeError:
                logger.error(f"Claude returned invalid JSON: {response_text[:200]}")
                return {
                    'status': 'error',
                    'error': 'Failed to parse Claude response'
                }

        except Exception as e:
            logger.error(f"Claude room detection failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
