"""Utility model for application state."""

from datetime import datetime
from app.extensions import db


class Util(db.Model):
    """Key-value store for application state like sync timestamps."""

    __tablename__ = "util"

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )

    def __repr__(self) -> str:
        return f"<Util {self.key}={self.value}>"

    @classmethod
    def get(cls, key: str, default: str | None = None) -> str | None:
        """Get a value by key."""
        record = cls.query.filter_by(key=key).first()
        return record.value if record else default

    @classmethod
    def set(cls, key: str, value: str) -> None:
        """Set a value by key."""
        record = cls.query.filter_by(key=key).first()
        if record:
            record.value = value
        else:
            record = cls(key=key, value=value)
            db.session.add(record)
        db.session.commit()

    @classmethod
    def get_last_sync(cls) -> datetime | None:
        """Get the last sync datetime."""
        value = cls.get("last_sync_datetime")
        if value:
            return datetime.fromisoformat(value)
        return None

    @classmethod
    def set_last_sync(cls, dt: datetime) -> None:
        """Set the last sync datetime."""
        cls.set("last_sync_datetime", dt.isoformat())
