import pytest
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage

@pytest.fixture
def mock_flash_response():
    """Generates a mock response for Gemini 2.5 Flash."""
    def _create(content: str, in_tokens: int = 120, out_tokens: int = 60):
        mock_resp = AIMessage(content=content)
        mock_resp.response_metadata = {
            "usage_metadata": {
                "prompt_token_count": in_tokens,
                "candidates_token_count": out_tokens,
            }
        }
        return mock_resp
    return _create

@pytest.fixture
def mock_pro_response():
    """Generates a mock response for Gemini 2.5 Pro."""
    def _create(content: str, in_tokens: int = 350, out_tokens: int = 150):
        mock_resp = AIMessage(content=content)
        mock_resp.response_metadata = {
            "usage_metadata": {
                "prompt_token_count": in_tokens,
                "candidates_token_count": out_tokens,
            }
        }
        return mock_resp
    return _create
