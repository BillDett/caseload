"""Project model."""

from app.extensions import db

# Association table for project dependencies
project_dependencies = db.Table(
    "project_dependencies",
    db.Column(
        "upstream_id", db.Integer, db.ForeignKey("projects.id"), primary_key=True
    ),
    db.Column(
        "downstream_id", db.Integer, db.ForeignKey("projects.id"), primary_key=True
    ),
)


class Project(db.Model):
    """Jira Project entity - associated with a Team, has dependencies."""

    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)
    jira_id = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    team = db.relationship("Team", back_populates="projects")
    trackers = db.relationship("Tracker", back_populates="project", lazy="dynamic")

    # Project dependencies (fix ordering)
    # upstream_dependencies: projects that must deliver before this one
    upstream_dependencies = db.relationship(
        "Project",
        secondary=project_dependencies,
        primaryjoin=id == project_dependencies.c.downstream_id,
        secondaryjoin=id == project_dependencies.c.upstream_id,
        backref="downstream_dependencies",
    )

    def __repr__(self) -> str:
        return f"<Project {self.key}>"
