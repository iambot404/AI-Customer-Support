import os
import pytest
from unittest.mock import patch
from app import create_app
from config import Config
from database.db import init_db, create_ticket, get_ticket, get_tickets, update_ticket


class TestConfig(Config):
    TESTING = True
    DATABASE_URL = ""
    SQLITE_PATH = ":memory:"  # In-memory database for isolated tests
    SECRET_KEY = "test-secret"
    GEMINI_API_KEY = "mock-key"


@pytest.fixture
def app(tmp_path):
    test_db = tmp_path / "test.db"
    
    class LocalTestConfig(Config):
        TESTING = True
        DATABASE_URL = ""
        SQLITE_PATH = str(test_db)
        SECRET_KEY = "test-secret"
        GEMINI_API_KEY = "mock-key"

    app = create_app(LocalTestConfig)
    with app.app_context():
        init_db()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client, app):
    """Client with an active agent session."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "testagent"
        sess["role"] = "agent"
    return client


def test_home_page_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Instant Support Request Triage" in response.data


def test_submit_ticket_validation_error(client):
    # Missing subject and message
    response = client.post("/tickets", data={"subject": "", "message": ""}, follow_redirects=True)
    assert response.status_code == 400
    assert b"Subject is required." in response.data


def test_submit_ticket_short_message(client):
    response = client.post("/tickets", data={"subject": "Short", "message": "1234"}, follow_redirects=True)
    assert response.status_code == 400
    assert b"Message must be at least 10 characters long." in response.data


@patch("routes.tickets.classify_ticket")
def test_submit_ticket_success_with_classification(mock_classify, client):
    mock_classify.return_value = {
        "success": True,
        "category": "Technical Issue",
        "priority": "Urgent",
        "summary": "Full API outage detected.",
        "reason": "Customer reports all endpoints returning 500 errors.",
        "confidence": 0.98,
        "error": None
    }

    response = client.post("/tickets", data={
        "customer_name": "Alice Developer",
        "customer_email": "alice@company.com",
        "subject": "Production API servers down",
        "message": "All our customer requests are returning 500 Internal Server Error."
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Technical Issue" in response.data
    assert b"Urgent" in response.data


@patch("routes.tickets.classify_ticket")
def test_submit_ticket_gemini_failure_fallback(mock_classify, client):
    # Simulate Gemini failure (ticket must still be saved in Pending state)
    mock_classify.return_value = {
        "success": False,
        "category": None,
        "priority": None,
        "summary": None,
        "reason": None,
        "confidence": None,
        "error": "Gemini API rate limit exceeded."
    }

    response = client.post("/tickets", data={
        "customer_name": "Bob",
        "customer_email": "bob@example.com",
        "subject": "Cannot export monthly transactions",
        "message": "The CSV export button spins indefinitely without downloading."
    }, follow_redirects=True)

    assert response.status_code == 200
    # Ticket should be saved and marked Pending
    assert b"AI triage is pending" in response.data


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_dashboard_authenticated(auth_client):
    response = auth_client.get("/dashboard")
    assert response.status_code == 200
    assert b"Operations &amp; Triage Dashboard" in response.data or b"Operations & Triage Dashboard" in response.data


def test_ticket_detail_and_override(app, auth_client):
    with app.app_context():
        ticket_id = create_ticket(
            subject="Test Override Subject",
            message="This is a test ticket message that has enough characters.",
            customer_name="Override Tester"
        )

    # View details
    response = auth_client.get(f"/tickets/{ticket_id}")
    assert response.status_code == 200
    assert b"Test Override Subject" in response.data

    # Perform human override
    update_resp = auth_client.post(f"/tickets/{ticket_id}/update", data={
        "status": "In Progress",
        "category": "Feature Request",
        "priority": "Low"
    }, follow_redirects=True)

    assert update_resp.status_code == 200
    assert b"Ticket updated successfully" in update_resp.data

    # Verify updated record
    with app.app_context():
        updated = get_ticket(ticket_id)
        assert updated["status"] == "In Progress"
        assert updated["category"] == "Feature Request"
        assert updated["priority"] == "Low"


def test_missing_ticket_id_returns_404(auth_client):
    response = auth_client.get("/tickets/999999")
    assert response.status_code == 404
    assert b"Ticket or Page Not Found" in response.data


def test_ticket_filtering(app, auth_client):
    with app.app_context():
        tid1 = create_ticket(subject="Bug in checkout", message="Payment error occurred during cart checkout.")
        update_ticket(tid1, category="Billing & Payments", priority="Urgent", status="Open")

        tid2 = create_ticket(subject="Documentation typo", message="Page 4 has a spelling mistake.")
        update_ticket(tid2, category="General Inquiry", priority="Low", status="Resolved")

    # Filter by Urgent priority
    resp = auth_client.get("/tickets?priority=Urgent")
    assert resp.status_code == 200
    assert b"Bug in checkout" in resp.data
    assert b"Documentation typo" not in resp.data

    # Filter by search
    resp_search = auth_client.get("/tickets?search=checkout")
    assert resp_search.status_code == 200
    assert b"Bug in checkout" in resp_search.data
