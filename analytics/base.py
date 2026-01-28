"""Abstract base class for analytics metrics."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass
class AnalyticsResult:
    """Result of computing an analytics metric."""

    metric_id: str
    title: str
    computed_at: datetime = field(default_factory=datetime.utcnow)
    data: Any = None  # Raw data (DataFrame, dict, list, etc.)
    chart_json: str | None = None  # Plotly JSON for visualization
    table_html: str | None = None  # HTML table representation
    summary: dict = field(default_factory=dict)  # Key stats for display
    error: str | None = None


class AnalyticsMetric(ABC):
    """Abstract base class for analytics metrics.

    Implement this class to add new metrics. Use the
    @AnalyticsRegistry.register decorator for auto-discovery.

    Example:
        @AnalyticsRegistry.register
        class TrackerVolume(AnalyticsMetric):
            metric_id = "tracker_volume"
            title = "Tracker Volume"
            description = "Total number of trackers over time"
            category = "trends"

            def compute(self, **kwargs) -> AnalyticsResult:
                # ... compute the metric
                return AnalyticsResult(...)
    """

    @property
    @abstractmethod
    def metric_id(self) -> str:
        """Unique identifier for this metric."""
        pass

    @property
    @abstractmethod
    def title(self) -> str:
        """Human-readable title for display."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this metric shows."""
        pass

    @property
    @abstractmethod
    def category(self) -> Literal["trends", "impact"]:
        """Category this metric belongs to.

        - 'trends': Organization-wide CVE impact (Vulnerability Trends)
        - 'impact': Per-CVE blast radius (Vulnerability Impact)
        """
        pass

    @abstractmethod
    def compute(self, **kwargs) -> AnalyticsResult:
        """Compute the metric.

        Args:
            **kwargs: Metric-specific parameters (date range, filters, etc.)

        Returns:
            AnalyticsResult with computed data and visualizations.
        """
        pass

    def get_filter_options(self) -> dict:
        """Return available filter options for this metric.

        Override to provide UI filter controls.

        Returns:
            Dictionary of filter definitions:
            {
                'date_range': {'type': 'daterange', 'label': 'Date Range'},
                'team': {'type': 'select', 'label': 'Team', 'options': [...]},
            }
        """
        return {}
