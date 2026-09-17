from datetime import datetime

from flask import Blueprint, jsonify, request

from app import db
from app.models import Task


api_bp = Blueprint("api", __name__, url_prefix="/api")


def parse_datetime(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def task_to_dict(task):
    return {
        "id": task.id,
        "content": task.content,
        "description": task.description,
        "completed": task.completed,
        "skipped": task.skipped,
        "priority": task.priority,
        "category": task.category,
        "created": (
            task.created.isoformat()
            if task.created
            else None
        ),
        "updated": (
            task.updated.isoformat()
            if task.updated
            else None
        ),
        "exp_date": (
            task.exp_date.isoformat()
            if task.exp_date
            else None
        ),
        "overdue": task.is_overdue(),
    }


@api_bp.get("/tasks")
def get_tasks():
    tasks = Task.query.order_by(
        Task.created.desc()
    ).all()

    return jsonify({
        "success": True,
        "count": len(tasks),
        "tasks": [
            task_to_dict(task)
            for task in tasks
        ],
    })


@api_bp.get("/tasks/<int:task_id>")
def get_task(task_id):
    task = Task.query.get_or_404(task_id)

    return jsonify({
        "success": True,
        "task": task_to_dict(task),
    })


@api_bp.post("/tasks")
def create_task():
    data = request.get_json(silent=True) or {}

    content = str(
        data.get("content", "")
    ).strip()

    if not content:
        return jsonify({
            "success": False,
            "error": "Task title is required.",
        }), 400

    priority = str(
        data.get("priority", "medium")
    ).lower()

    if priority not in {
        "low",
        "medium",
        "high",
    }:
        return jsonify({
            "success": False,
            "error": "Invalid priority.",
        }), 400

    category = (
        str(data.get("category", "General")).strip()
        or "General"
    )

    exp_date = parse_datetime(
        data.get("exp_date")
    )

    if data.get("exp_date") and exp_date is None:
        return jsonify({
            "success": False,
            "error": "Invalid deadline.",
        }), 400

    task = Task(
        content=content,
        description=(
            str(data.get("description", "")).strip()
            or None
        ),
        priority=priority,
        category=category,
        exp_date=exp_date,
    )

    db.session.add(task)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Task created successfully.",
        "task": task_to_dict(task),
    }), 201


@api_bp.patch("/tasks/<int:task_id>")
def update_task(task_id):
    task = Task.query.get_or_404(task_id)

    data = request.get_json(silent=True) or {}

    if "content" in data:
        content = str(
            data["content"]
        ).strip()

        if not content:
            return jsonify({
                "success": False,
                "error": "Task title cannot be empty.",
            }), 400

        task.content = content

    if "description" in data:
        task.description = (
            str(data["description"]).strip()
            or None
        )

    if "priority" in data:
        priority = str(
            data["priority"]
        ).lower()

        if priority not in {
            "low",
            "medium",
            "high",
        }:
            return jsonify({
                "success": False,
                "error": "Invalid priority.",
            }), 400

        task.priority = priority

    if "category" in data:
        task.category = (
            str(data["category"]).strip()
            or "General"
        )

    if "exp_date" in data:
        exp_date = parse_datetime(
            data["exp_date"]
        )

        if data["exp_date"] and exp_date is None:
            return jsonify({
                "success": False,
                "error": "Invalid deadline.",
            }), 400

        task.exp_date = exp_date

    if "completed" in data:
        task.completed = bool(
            data["completed"]
        )

        if task.completed:
            task.skipped = False

    if "skipped" in data:
        task.skipped = bool(
            data["skipped"]
        )

        if task.skipped:
            task.completed = False

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Task updated successfully.",
        "task": task_to_dict(task),
    })


@api_bp.delete("/tasks/<int:task_id>")
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    db.session.delete(task)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Task deleted successfully.",
        "task_id": task_id,
    })