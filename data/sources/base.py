"""Abstract base class for data sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator


@dataclass
class RawTracker:
    """Normalized tracker data from any source."""

    source_key: str  # Unique identifier from the source (e.g., Jira key)
    source_type: str  # Type of source (e.g., 'jira')
    project_key: str
    summary: str | None = None
    status: str | None = None
    resolution: str | None = None
    priority: str | None = None
    severity: str | None = None  # Critical, Important, Moderate
    assignee: str | None = None
    reporter: str | None = None
    created_date: datetime | None = None
    updated_date: datetime | None = None
    resolved_date: datetime | None = None
    due_date: datetime | None = None
    sla_date: datetime | None = None  # SLA target date
    cve_ids: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    custom_fields: dict = field(default_factory=dict)


class DataSource(ABC):
    """Abstract base class for all data sources.

    Implement this class to add new data sources (e.g., build systems,
    vulnerability databases).
    """

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return the unique identifier for this source type.

        Examples: 'jira', 'github', 'nvd'
        """
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Return human-readable name for this source."""
        pass

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """Test the connection to the data source.

        Returns:
            Tuple of (success, message).
        """
        pass

    @abstractmethod
    def fetch_trackers(
        self,
        project_keys: list[str],
        since: datetime | None = None,
    ) -> Iterator[RawTracker]:
        """Fetch trackers from the data source.

        Args:
            project_keys: List of project keys to fetch (required to avoid unbounded queries).
            since: Optional datetime to fetch only updated trackers.

        Yields:
            RawTracker objects with normalized data.

        Raises:
            ValueError: If project_keys is empty.
        """
        pass

    def fetch_projects(self) -> list[dict]:
        """Fetch available projects from the data source.

        Returns:
            List of project dictionaries with 'key' and 'name' fields.
        """
        return []
