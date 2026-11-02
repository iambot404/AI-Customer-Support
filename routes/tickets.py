import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from config import Config
from database.db import (
    create_ticket,
    get_ticket,
    get_tickets,
    update_ticket,
    update_ticket_classification,
    get_dashboard_metrics
)
from services.gemini_service import classify_ticket
from routes.auth import login_required

logger = logging.getLogger("tickets")
tickets_bp = Blueprint("tickets", __name__)


@tickets_bp.route("/", methods=["GET"])
def index():
    """Public customer portal for submitting support tickets and tracking status."""
    recent_id = request.args.get("submitted_id")
    submitted_ticket = get_ticket(int(recent_id)) if recent_id and recent_id.isdigit() else None
    return render_template(
        "index.html",
        submitted_ticket=submitted_ticket,
        categories=Config.CATEGORIES,
        priorities=Config.PRIORITIES
    )


@tickets_bp.route("/tickets", methods=["POST"])
def submit_ticket():
    """Creates a support ticket, invokes Gemini classification, and records the result."""
    customer_name = request.form.get("customer_name", "").strip() or None
    customer_email = request.form.get("customer_email", "").strip() or None
    subject = request.form.get("subject", "").strip()
    message = request.form.get("message", "").strip()

    errors = []
    if not subject:
        errors.append("Subject is required.")
    elif len(subject) > 200:
        errors.append("Subject cannot exceed 200 characters.")

    if not message:
        errors.append("Ticket message/description is required.")
    elif len(message) < 10:
        errors.append("Message must be at least 10 characters long.")
    elif len(message) > 5000:
        errors.append("Message exceeds maximum allowed length of 5000 characters.")

    if errors:
        for err in errors:
            flash(err, "danger")
        return render_template(
            "index.html",
            customer_name=customer_name,
            customer_email=customer_email,
            subject=subject,
            message=message,
            categories=Config.CATEGORIES,
            priorities=Config.PRIORITIES
        ), 400

    # 1. Save ticket to DB first to ensure customer data is NEVER lost
    try:
        ticket_id = create_ticket(
            subject=subject,
            message=message,
            customer_name=customer_name,
            customer_email=customer_email
        )
    except Exception as db_err:
        logger.error(f"Failed to persist ticket: {db_err}")
        flash("Could not save ticket to database. Please try again.", "danger")
        return redirect(url_for("tickets.index"))

    # 2. Call Gemini for classification
    ai_result = classify_ticket(subject=subject, message=message)

    if ai_result["success"]:
        update_ticket_classification(
            ticket_id=ticket_id,
            category=ai_result["category"],
            priority=ai_result["priority"],
            ai_summary=ai_result["summary"],
            ai_reason=ai_result["reason"],
            confidence=ai_result["confidence"],
            classification_status="Completed"
        )
        flash(f"Ticket #{ticket_id} submitted and categorized as '{ai_result['category']}' with {ai_result['priority']} priority.", "success")
    else:
        # Mark as Pending classification
        update_ticket_classification(
            ticket_id=ticket_id,
            ai_reason=ai_result.get("error", "AI service unreachable."),
            classification_status="Pending"
        )
        flash(f"Ticket #{ticket_id} submitted successfully. AI triage is pending: {ai_result.get('error', 'Service busy')}", "warning")

    return redirect(url_for("tickets.index", submitted_id=ticket_id))


@tickets_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    """Agent dashboard showing real counts, priority queues, and breakdown metrics."""
    metrics = get_dashboard_metrics()
    return render_template(
        "dashboard.html",
        metrics=metrics,
        categories=Config.CATEGORIES,
        priorities=Config.PRIORITIES,
        statuses=Config.STATUSES
    )


@tickets_bp.route("/tickets", methods=["GET"])
@login_required
def ticket_list():
    """Ticket list with search, category/priority/status filters, and pagination."""
    category = request.args.get("category", "").strip() or None
    priority = request.args.get("priority", "").strip() or None
    status = request.args.get("status", "").strip() or None
    search = request.args.get("search", "").strip() or None
    
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    per_page = 12
    tickets, total_count, total_pages = get_tickets(
        category=category,
        priority=priority,
        status=status,
        search=search,
        page=page,
        per_page=per_page
    )

    return render_template(
        "tickets.html",
        tickets=tickets,
        total_count=total_count,
        total_pages=total_pages,
        current_page=page,
        selected_category=category,
        selected_priority=priority,
        selected_status=status,
        search_query=search,
        categories=Config.CATEGORIES,
        priorities=Config.PRIORITIES,
        statuses=Config.STATUSES
    )


@tickets_bp.route("/tickets/<int:ticket_id>", methods=["GET"])
@login_required
def ticket_detail(ticket_id):
    """Ticket details page showing original message, AI triage explanation, and human overrides."""
    ticket = get_ticket(ticket_id)
    if not ticket:
        abort(404)

    return render_template(
        "ticket_detail.html",
        ticket=ticket,
        categories=Config.CATEGORIES,
        priorities=Config.PRIORITIES,
        statuses=Config.STATUSES
    )


@tickets_bp.route("/tickets/<int:ticket_id>/classify", methods=["POST"])
@login_required
def reclassify(ticket_id):
    """Re-attempts or triggers Gemini classification for a ticket."""
    ticket = get_ticket(ticket_id)
    if not ticket:
        abort(404)

    ai_result = classify_ticket(subject=ticket["subject"], message=ticket["message"])

    if ai_result["success"]:
        update_ticket_classification(
            ticket_id=ticket_id,
            category=ai_result["category"],
            priority=ai_result["priority"],
            ai_summary=ai_result["summary"],
            ai_reason=ai_result["reason"],
            confidence=ai_result["confidence"],
            classification_status="Completed"
        )
        flash("Ticket successfully re-classified by Gemini.", "success")
    else:
        update_ticket_classification(
            ticket_id=ticket_id,
            ai_reason=ai_result.get("error"),
            classification_status="Failed"
        )
        flash(f"Reclassification attempt failed: {ai_result.get('error')}", "danger")

    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))


@tickets_bp.route("/tickets/<int:ticket_id>/update", methods=["POST"])
@login_required
def update_ticket_data(ticket_id):
    """Allows support agents to override category, priority, or status."""
    ticket = get_ticket(ticket_id)
    if not ticket:
        abort(404)

    new_category = request.form.get("category", "").strip() or None
    new_priority = request.form.get("priority", "").strip() or None
    new_status = request.form.get("status", "").strip() or None

    if new_category and new_category not in Config.CATEGORIES:
        flash("Invalid category specified.", "danger")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))

    if new_priority and new_priority not in Config.PRIORITIES:
        flash("Invalid priority specified.", "danger")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))

    if new_status and new_status not in Config.STATUSES:
        flash("Invalid status specified.", "danger")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))

    update_ticket(
        ticket_id=ticket_id,
        status=new_status,
        category=new_category,
        priority=new_priority
    )

    flash("Ticket updated successfully with your changes.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))
