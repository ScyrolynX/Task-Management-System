from datetime import datetime, timezone
from app import db


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.String(200), nullable=False)

    description = db.Column(db.Text, nullable=True)

    completed = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    skipped = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    priority = db.Column(
        db.String(20),
        default="medium",
        nullable=False
    )

    category = db.Column(
        db.String(50),
        default="General",
        nullable=False
    )

    created = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    exp_date = db.Column(
        db.DateTime,
        nullable=True
    )

    def is_overdue(self):
        if not self.exp_date or self.completed or self.skipped:
            return False

        deadline = self.exp_date

        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        return deadline < datetime.now(timezone.utc)

    def toggle_complete(self):
        self.completed = not self.completed

        if self.completed:
            self.skipped = False

    def toggle_skip(self):
        self.skipped = not self.skipped

        if self.skipped:
            self.completed = False

    def __repr__(self):
        return f"<Task {self.id}: {self.content}>"