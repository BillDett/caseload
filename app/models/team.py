"""Team model."""

from app.extensions import db


class Team(db.Model):
    """Team entity - owns one or more Jira projects."""

    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    projects = db.relationship("Project", back_populates="team", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Team {self.name}>"
