from flask import Blueprint, render_template, redirect, url_for

pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/")
def root():
    return redirect(url_for("tasks.task_page"))

@pages_bp.route("/about")
def about():
    return render_template("about.html")

@pages_bp.route("/contact")
def contact():
    return render_template("contact.html")
