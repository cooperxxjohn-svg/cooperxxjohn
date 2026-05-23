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

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

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
