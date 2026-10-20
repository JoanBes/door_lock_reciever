from flask import Blueprint, redirect, render_template, session, url_for

from app.security import admin_required, current_user, login_required

bp = Blueprint("pages", __name__)


@bp.get("/login")
def login():
    if "user_id" in session:
        return redirect(url_for("pages.overview"))
    return render_template("login.html")


@bp.get("/")
@login_required
def overview():
    return render_template("overview.html", active="overview")


@bp.get("/logs")
@admin_required
def logs():
    return render_template("logs.html", active="logs")


@bp.get("/cards")
@admin_required
def cards():
    return render_template("cards.html", active="cards")


@bp.app_context_processor
def inject_user():
    user = current_user()
    return {"user": user, "is_admin": user["role"] == "admin"}
