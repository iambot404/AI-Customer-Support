import pytest
from unittest.mock import patch, MagicMock
from services.gemini_service import classify_ticket, validate_classification_result, clean_json_text


def test_clean_json_text():
    raw_markdown = """```json
    {
        "category": "Technical Issue",
        "priority": "High"
    }
    ```"""
    cleaned = clean_json_text(raw_markdown)
    assert cleaned.startswith("{")
    assert cleaned.endswith("}")


def test_validate_classification_result_valid():
    sample = {
        "category": "Technical Issue",
        "priority": "Urgent",
        "summary": "Database connection timeout during peak hours.",
        "reason": "Production database is unreachable causing widespread outage.",
        "confidence": 0.95
    }
    is_valid, sanitized, err = validate_classification_result(sample)
    assert is_valid is True
    assert sanitized["category"] == "Technical Issue"
    assert sanitized["priority"] == "Urgent"
    assert sanitized["confidence"] == 0.95
    assert err == ""


def test_validate_classification_result_invalid_category():
    sample = {
        "category": "NonExistentCategory",
        "priority": "Medium",
        "summary": "Something broke.",
        "reason": "Not sure.",
        "confidence": 0.8
    }
    is_valid, sanitized, err = validate_classification_result(sample)
    assert is_valid is False
    assert "Invalid category" in err


def test_validate_classification_result_invalid_priority():
    sample = {
        "category": "Billing & Payments",
        "priority": "Catastrophic",
        "summary": "Incorrect billing amount.",
        "reason": "Invoice error.",
        "confidence": 0.8
    }
    is_valid, sanitized, err = validate_classification_result(sample)
    assert is_valid is False
    assert "Invalid priority" in err


def test_validate_classification_result_confidence_clamping():
    sample = {
        "category": "Feature Request",
        "priority": "Low",
        "summary": "Add dark mode.",
        "reason": "Requested by users.",
        "confidence": 1.5  # Greater than 1.0
    }
    is_valid, sanitized, err = validate_classification_result(sample)
    assert is_valid is True
    assert sanitized["confidence"] == 1.0


def test_classify_ticket_without_api_key():
    result = classify_ticket(subject="Test", message="Test message body", api_key="")
    assert result["success"] is False
    assert "not configured" in result["error"].lower()
    assert result["category"] is None


@patch("google.genai.Client")
def test_classify_ticket_success_mock(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = """{
        "category": "Billing & Payments",
        "priority": "High",
        "summary": "Customer charged twice for enterprise tier.",
        "reason": "Financial discrepancy with concrete invoice impact.",
        "confidence": 0.92
    }"""
    mock_client.models.generate_content.return_value = mock_response

    result = classify_ticket(
        subject="Duplicate subscription charge",
        message="I was billed twice on invoice #4921.",
        api_key="fake-test-key"
    )

    assert result["success"] is True
    assert result["category"] == "Billing & Payments"
    assert result["priority"] == "High"
    assert result["confidence"] == 0.92


@patch("google.genai.Client")
def test_classify_ticket_api_exception(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded")

    result = classify_ticket(
        subject="Any subject",
        message="Any message content that is valid.",
        api_key="fake-test-key"
    )

    assert result["success"] is False
    assert "quota" in result["error"].lower() or "rate limit" in result["error"].lower()
