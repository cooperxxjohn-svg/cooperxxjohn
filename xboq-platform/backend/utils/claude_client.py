"""
Claude API Client
Shared between all modules that need AI generation
"""

import os
import logging
import anthropic

logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Wrapper for Anthropic Claude API
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'

        if not self.api_key and not self.test_mode:
            raise ValueError("ANTHROPIC_API_KEY not found in environment. Set TEST_MODE=true for testing without API key.")

        if self.test_mode:
            self.client = None
            self.model = "test-mode"
            logger.info("🧪 TEST MODE: Claude API calls will return mock data")
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-opus-4-5-20251101"
            logger.info(f"Claude Client initialized with model: {self.model}")

    def generate(self, prompt: str, max_tokens: int = 3000) -> str:
        """
        Generate response from Claude

        Args:
            prompt: The prompt to send to Claude
            max_tokens: Maximum tokens in response

        Returns:
            str: Claude's response text
        """
        if self.test_mode:
            logger.info("🧪 TEST MODE: Returning mock data")
            return self._get_mock_response(prompt)

        logger.info(f"Sending request to Claude (max_tokens={max_tokens})...")

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            response_text = response.content[0].text
            logger.info(f"Received response from Claude ({len(response_text)} characters)")

            return response_text

        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            raise

    def analyze_image(self, image_path: str, prompt: str, max_tokens: int = 3000) -> str:
        """
        Analyze an image with Claude's vision capability

        Args:
            image_path: Path to image file
            prompt: The prompt/question about the image
            max_tokens: Maximum tokens in response

        Returns:
            str: Claude's response text
        """
        if self.test_mode:
            logger.info("🧪 TEST MODE: Returning mock floor plan data")
            return self._get_mock_floor_plan_response()

        logger.info(f"Analyzing image with Claude: {image_path}")

        try:
            import base64

            # Read and encode image
            with open(image_path, 'rb') as image_file:
                image_data = base64.standard_b64encode(image_file.read()).decode('utf-8')

            # Determine image type
            if image_path.lower().endswith('.png'):
                media_type = "image/png"
            elif image_path.lower().endswith(('.jpg', '.jpeg')):
                media_type = "image/jpeg"
            else:
                media_type = "image/png"  # Default

            # Create message with image
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            response_text = response.content[0].text
            logger.info(f"Received image analysis from Claude ({len(response_text)} characters)")

            return response_text

        except Exception as e:
            logger.error(f"Error analyzing image with Claude: {e}")
            raise

    def _get_mock_floor_plan_response(self) -> str:
        """Return mock floor plan detection for testing"""
        import json

        return json.dumps({
            "rooms": [
                {
                    "name": "Living Room",
                    "sqft": 245,
                    "length": 17.5,
                    "width": 14
                },
                {
                    "name": "Kitchen",
                    "sqft": 180,
                    "length": 15,
                    "width": 12
                },
                {
                    "name": "Master Bedroom",
                    "sqft": 200,
                    "length": 16,
                    "width": 12.5
                },
                {
                    "name": "Bedroom 2",
                    "sqft": 150,
                    "length": 12.5,
                    "width": 12
                },
                {
                    "name": "Bathroom 1",
                    "sqft": 65,
                    "length": 8,
                    "width": 8
                },
                {
                    "name": "Bathroom 2",
                    "sqft": 58,
                    "length": 7.5,
                    "width": 7.7
                }
            ]
        })

    def _get_mock_response(self, prompt: str) -> str:
        """
        Return mock data for testing
        """
        import json

        # Detect request type from prompt content
        prompt_lower = prompt.lower()

        if "bill of quantities" in prompt_lower or "boq" in prompt_lower:
            # Mock BOQ response
            return json.dumps({
                "project_name": "Test Construction Project",
                "sections": [
                    {
                        "name": "Earthwork",
                        "items": [
                            {
                                "item": "Excavation in ordinary soil",
                                "description": "Excavation for foundation trenches",
                                "quantity": 150.5,
                                "unit": "cum"
                            },
                            {
                                "item": "Backfilling",
                                "description": "Backfilling with excavated soil",
                                "quantity": 75.25,
                                "unit": "cum"
                            }
                        ]
                    },
                    {
                        "name": "Concrete Work",
                        "items": [
                            {
                                "item": "PCC 1:4:8",
                                "description": "Plain cement concrete for foundation",
                                "quantity": 25.5,
                                "unit": "cum"
                            },
                            {
                                "item": "RCC M25",
                                "description": "Reinforced cement concrete",
                                "quantity": 45.75,
                                "unit": "cum"
                            }
                        ]
                    }
                ],
                "total_items": 4
            })

        elif "drywall" in prompt_lower:
            # Mock drywall estimate
            return json.dumps({
                "rooms": [
                    {
                        "name": "Living Room (Test)",
                        "dimensions": "20ft x 15ft x 9ft",
                        "wall_area": 630,
                        "ceiling_area": 300,
                        "materials": {
                            "drywall_sheets": 58,
                            "joint_compound": 6,
                            "tape": 2,
                            "screws": 3
                        },
                        "labor_hours": 24,
                        "total_cost": 2850
                    }
                ],
                "summary": {
                    "total_sqft": 930,
                    "total_materials_cost": 1245,
                    "total_labor_cost": 1605,
                    "total_cost": 2850
                }
            })

        elif "painting" in prompt_lower:
            # Mock painting estimate
            return json.dumps({
                "rooms": [
                    {
                        "name": "Bedroom (Test)",
                        "dimensions": "12ft x 12ft x 8ft",
                        "wall_area": 384,
                        "ceiling_area": 144,
                        "materials": {
                            "primer_gallons": 2,
                            "paint_gallons": 3,
                            "supplies": 1
                        },
                        "labor_hours": 12,
                        "total_cost": 625
                    }
                ],
                "summary": {
                    "total_sqft": 528,
                    "total_materials_cost": 285,
                    "total_labor_cost": 340,
                    "total_cost": 625
                }
            })

        elif "floor plan" in prompt_lower or "drawing" in prompt_lower:
            # Mock floor plan analysis
            return json.dumps({
                "detected_rooms": [
                    {"name": "Living Room", "length": 20, "width": 15},
                    {"name": "Bedroom 1", "length": 12, "width": 12},
                    {"name": "Kitchen", "length": 10, "width": 12}
                ],
                "confidence": "high"
            })

        else:
            # Generic mock response
            return json.dumps({
                "status": "success",
                "message": "Test mode response",
                "data": "Mock data for testing purposes"
            })
