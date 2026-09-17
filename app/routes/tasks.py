from datetime import datetime, timezone

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from app import db
from app.models import Task


tasks_bp = Blueprint(
    "tasks",
    __name__,
    url_prefix="/tasks",
)


def parse_datetime(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def get_task_lists():
    all_tasks = Task.query.order_by(Task.created.desc()).all()

    today = datetime.now(timezone.utc).date()

    today_tasks = []
    upcoming_tasks = []
    overdue_tasks = []
    completed_tasks = []
    skipped_tasks = []

    for task in all_tasks:
        if task.skipped:
            skipped_tasks.append(task)

        elif task.completed:
            completed_tasks.append(task)

        elif task.is_overdue():
            overdue_tasks.append(task)

        elif task.exp_date:
            deadline_date = task.exp_date.date()

            if deadline_date == today:
                today_tasks.append(task)
            elif deadline_date > today:
                upcoming_tasks.append(task)
            else:
                overdue_tasks.append(task)

        else:
            today_tasks.append(task)

    total = len(all_tasks)
    completed = len(completed_tasks)

    progress = (
        round((completed / total) * 100)
        if total
        else 0
    )

    return {
        "today_tasks": today_tasks,
        "upcoming_tasks": upcoming_tasks,
        "overdue_tasks": overdue_tasks,
        "completed_tasks": completed_tasks,
        "skipped_tasks": skipped_tasks,
        "total_tasks": total,
        "completed_count": completed,
        "overdue_count": len(overdue_tasks),
        "progress": progress,
    }


@tasks_bp.route("", methods=["GET", "POST"])
def task_page():

    if request.method == "POST":
        content = request.form.get("task", "").strip()
        description = request.form.get("description", "").strip()

        priority = request.form.get(
            "priority",
            "medium",
        ).lower()

        category = request.form.get(
            "category",
            "General",
        ).strip() or "General"

        exp_date = parse_datetime(
            request.form.get("exp_date", "")
        )

        if not content:
            flash("Task title is required.", "error")
            return redirect(url_for("tasks.task_page"))

        if priority not in {"low", "medium", "high"}:
            priority = "medium"

        task = Task(
            content=content,
            description=description or None,
            priority=priority,
            category=category,
            exp_date=exp_date,
        )

        db.session.add(task)
        db.session.commit()

        flash("Task created successfully.", "success")

        return redirect(url_for("tasks.task_page"))

    task_data = get_task_lists()

    view = request.args.get("view", "today").lower()

    valid_views = {
        "today",
        "upcoming",
        "overdue",
        "completed",
        "skipped",
        "all",
    }

    if view not in valid_views:
        view = "today"

    return render_template(
        "tasks.html",
        **task_data,
        current_view=view,
    )


@tasks_bp.route("/<int:task_id>/edit", methods=["GET", "POST"])
def task_edit(task_id):

    task = Task.query.get_or_404(task_id)

    if request.method == "POST":
        content = request.form.get("task", "").strip()
        description = request.form.get("description", "").strip()

        priority = request.form.get(
            "priority",
            "medium",
        ).lower()

        category = request.form.get(
            "category",
            "General",
        ).strip() or "General"

        exp_date = parse_datetime(
            request.form.get("exp_date", "")
        )

        if not content:
            flash("Task title is required.", "error")
            return redirect(
                url_for(
                    "tasks.task_edit",
                    task_id=task.id,
                )
            )

        if priority not in {"low", "medium", "high"}:
            priority = "medium"

        task.content = content
        task.description = description or None
        task.priority = priority
        task.category = category
        task.exp_date = exp_date

        db.session.commit()

        flash("Task updated successfully.", "success")

        return redirect(url_for("tasks.task_page"))

    return render_template(
        "edit_task.html",
        task=task,
    )


@tasks_bp.post("/<int:task_id>/toggle")
def task_toggle(task_id):

    task = Task.query.get_or_404(task_id)

    task.toggle_complete()

    db.session.commit()

    return redirect(
        request.referrer
        or url_for("tasks.task_page")
    )


@tasks_bp.post("/<int:task_id>/skip")
def task_skip(task_id):

    task = Task.query.get_or_404(task_id)

    task.toggle_skip()

    db.session.commit()

    return redirect(
        request.referrer
        or url_for("tasks.task_page")
    )


@tasks_bp.post("/<int:task_id>/delete")
def task_delete(task_id):

    task = Task.query.get_or_404(task_id)

    db.session.delete(task)
    db.session.commit()

    flash("Task deleted.", "success")

    return redirect(
        request.referrer
        or url_for("tasks.task_page")
    )


@tasks_bp.post("/<int:task_id>/priority")
def task_priority(task_id):

    task = Task.query.get_or_404(task_id)

    priority = request.form.get("priority")

    if priority in {"low", "medium", "high"}:
        task.priority = priority
        db.session.commit()

    return redirect(
        request.referrer
        or url_for("tasks.task_page")
    )