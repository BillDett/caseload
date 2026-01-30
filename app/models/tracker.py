"""Tracker model."""

from app.extensions import db


class Tracker(db.Model):
    """Tracker entity - Jira issue linked to a CVE."""

    __tablename__ = "trackers"

    id = db.Column(db.Integer, primary_key=True)
    jira_key = db.Column(db.String(50), unique=True, nullable=False, index=True)
    summary = db.Column(db.String(512), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    resolution = db.Column(db.String(50), nullable=True)
    priority = db.Column(db.String(50), nullable=True)
    severity = db.Column(db.String(50), nullable=True)  # Critical, Important, Moderate
    assignee = db.Column(db.String(255), nullable=True)
    reporter = db.Column(db.String(255), nullable=True)
    created_date = db.Column(db.DateTime, nullable=True)
    updated_date = db.Column(db.DateTime, nullable=True)
    resolved_date = db.Column(db.DateTime, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    sla_date = db.Column(db.DateTime, nullable=True)  # SLA target date from Jira
    sla_breach = db.Column(db.Boolean, default=False, nullable=False)
    closure_reason = db.Column(db.String(100), nullable=True)

    # Foreign keys
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=True)
    cve_id = db.Column(db.Integer, db.ForeignKey("cves.id"), nullable=True)

    # Sync metadata
    last_synced_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    project = db.relationship("Project", back_populates="trackers")
    cve = db.relationship("CVE", back_populates="trackers")

    def __repr__(self) -> str:
        return f"<Tracker {self.jira_key}>"

    @property
    def is_open(self) -> bool:
        """Check if tracker is still open."""
        closed_statuses = {"done", "closed", "resolved", "cancelled"}
        return self.status.lower() not in closed_statuses if self.status else True

    @property
    def days_open(self) -> int | None:
        """Calculate days the tracker has been open."""
        if not self.created_date:
            return None
        from datetime import datetime

        end_date = self.resolved_date or datetime.utcnow()
        return (end_date - self.created_date).days
