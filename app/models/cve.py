"""CVE model."""

from app.extensions import db


class CVE(db.Model):
    """CVE entity - identified by CVE key."""

    __tablename__ = "cves"

    id = db.Column(db.Integer, primary_key=True)
    cve_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    url = db.Column(db.String(512), nullable=True)
    description = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), nullable=True)  # critical, high, medium, low
    cvss_score = db.Column(db.Float, nullable=True)
    published_date = db.Column(db.DateTime, nullable=True)
    is_embargoed = db.Column(db.Boolean, default=False, nullable=False)
    embargo_end_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    trackers = db.relationship("Tracker", back_populates="cve", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<CVE {self.cve_id}>"

    @property
    def affected_teams(self) -> list:
        """Get list of teams affected by this CVE."""
        teams = set()
        for tracker in self.trackers:
            if tracker.project and tracker.project.team:
                teams.add(tracker.project.team)
        return list(teams)

    @property
    def affected_projects(self) -> list:
        """Get list of projects affected by this CVE."""
        projects = set()
        for tracker in self.trackers:
            if tracker.project:
                projects.add(tracker.project)
        return list(projects)
