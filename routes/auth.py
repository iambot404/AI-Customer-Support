from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import create_user, get_user_by_username, get_user_by_email, get_user_by_id

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view_func):
    """Decorator to enforce login on protected agent routes."""
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to access the agent portal.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view_func(*args, **kwargs)
    return decorated_view


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("tickets.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters long.")
        if not email or "@" not in email:
            errors.append("A valid email address is required.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if not errors:
            if get_user_by_username(username):
                errors.append("That username is already taken.")
            elif get_user_by_email(email):
                errors.append("That email address is already registered.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("register.html", username=username, email=email)

        # Hash and store
        pw_hash = generate_password_hash(password, method="pbkdf2:sha256")
        user_id = create_user(username=username, email=email, password_hash=pw_hash, role="agent")

        # Establish session
        session["user_id"] = user_id
        session["username"] = username
        session["email"] = email
        session["role"] = "agent"

        flash(f"Welcome aboard, {username}! Your agent account has been created.", "success")
        return redirect(url_for("tickets.dashboard"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("tickets.dashboard"))

    next_url = request.args.get("next") or request.form.get("next") or url_for("tickets.dashboard")

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        if not identifier or not password:
            flash("Please enter both username/email and password.", "danger")
            return render_template("login.html", identifier=identifier, next=next_url)

        # Find user by username or email
        user = get_user_by_username(identifier)
        if not user:
            user = get_user_by_email(identifier)

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid username or password.", "danger")
            return render_template("login.html", identifier=identifier, next=next_url)

        # Set session
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["email"] = user["email"]
        session["role"] = user.get("role", "agent")

        flash(f"Welcome back, {user['username']}!", "success")
        return redirect(next_url)

    return render_template("login.html", next=next_url)


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("auth.login"))
