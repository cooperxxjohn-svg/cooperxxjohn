"""
Construction Estimator Module
Generates estimates for drywall, painting, concrete trades
New functionality for xboq.ai
"""

import json
import logging
from utils.pdf_processor import PDFProcessor
from utils.claude_client import ClaudeClient

logger = logging.getLogger(__name__)


class ConstructionEstimator:
    """
    AI-powered construction estimator for multiple trades
    """

    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.claude = ClaudeClient()
        logger.info("Construction Estimator initialized")

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
