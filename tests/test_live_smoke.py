import pytest
from app.config import GEMINI_API_KEY
from app.seeder import seed_database_from_file
from app.classifier import classify_enquiry
from app.drafter import draft_response_for_enquiry

@pytest.mark.live_llm
def test_live_gemini_api_handshake(tmp_path):
    """
    Isolated live smoke test verifying real Google Gemini 3.8 Flash API calls.
    Only runs when GEMINI_API_KEY is populated.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("test_") or len(GEMINI_API_KEY) < 10:
        pytest.skip("GEMINI_API_KEY not configured or is a placeholder. Skipping live smoke test.")

    db_file = str(tmp_path / "test_live.db")
    seed_database_from_file("data/data.md", db_path=db_file)

    # 1. Live Gemini 3.8 Flash Classification
    result = classify_enquiry("E001", db_path=db_file, use_fixtures=False)
    if "error" in result:
        pytest.skip(f"Live Gemini API call error (e.g. quota limit): {result['error']}")
    assert result["category"] == "sales_lead"
    assert "Matt Cooper" in result["assigned_owner"]
    assert result["confidence"] > 0.5

    # 2. Live Gemini 3.8 Flash Grounded Drafting
    draft = draft_response_for_enquiry("E001", db_path=db_file, use_fixtures=False)
    assert draft is not None
    assert len(draft) > 50
    assert "Amelia" in draft or "Hume" in draft

