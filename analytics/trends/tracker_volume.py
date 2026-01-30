"""Tracker volume metric."""

from datetime import datetime, timedelta
from typing import Literal

import pandas as pd

from analytics.base import AnalyticsMetric, AnalyticsResult
from analytics.registry import AnalyticsRegistry
from analytics.visualizations import LineChart


@AnalyticsRegistry.register
class TrackerVolumeMetric(AnalyticsMetric):
    """Track the volume of CVE trackers over time."""

    @property
    def metric_id(self) -> str:
        return "tracker_volume"

    @property
    def title(self) -> str:
        return "Tracker Volume"

    @property
    def description(self) -> str:
        return "Number of open and closed CVE trackers over time"

    @property
    def category(self) -> Literal["trends", "impact"]:
        return "trends"

    def _parse_date(self, date_str: str | None, default: datetime) -> datetime:
        """Parse date string to datetime, returning default if invalid."""
        if not date_str:
            return default
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            return default

    def compute(self, **kwargs) -> AnalyticsResult:
        """Compute tracker volume over time.

        Kwargs:
            date_range_start: Start of date range.
            date_range_end: End of date range.
            team_id: Optional team filter.
            project_id: Optional project filter.
        """
        from app.extensions import db
        from app.models import Tracker

        default_start = datetime.utcnow() - timedelta(days=90)
        default_end = datetime.utcnow()

        start_date = self._parse_date(kwargs.get("date_range_start"), default_start)
        end_date = self._parse_date(kwargs.get("date_range_end"), default_end)
        team_id = kwargs.get("team_id")
        project_id = kwargs.get("project_id")

        try:
            query = db.session.query(Tracker)

            if project_id:
                query = query.filter(Tracker.project_id == project_id)
            elif team_id:
                from app.models import Project

                query = query.join(Project).filter(Project.team_id == team_id)

            trackers = query.filter(
                Tracker.created_date >= start_date,
                Tracker.created_date <= end_date,
            ).all()

            # Build time series data
            date_range = pd.date_range(start=start_date, end=end_date, freq="W")
            open_counts = []
            closed_counts = []

            for week_end in date_range:
                week_start = week_end - timedelta(days=7)
                open_count = sum(
                    1
                    for t in trackers
                    if t.created_date
                    and t.created_date <= week_end
                    and (not t.resolved_date or t.resolved_date > week_end)
                )
                closed_count = sum(
                    1
                    for t in trackers
                    if t.resolved_date
                    and t.resolved_date > week_start
                    and t.resolved_date <= week_end
                )
                open_counts.append(open_count)
                closed_counts.append(closed_count)

            data = {
                "x": [d.strftime("%Y-%m-%d") for d in date_range],
                "y": [open_counts, closed_counts],
                "names": ["Open Trackers", "Closed Trackers"],
            }

            chart = LineChart()
            chart_json = chart.render_json(
                data,
                title="CVE Tracker Volume Over Time",
                x_label="Date",
                y_label="Count",
            )

            return AnalyticsResult(
                metric_id=self.metric_id,
                title=self.title,
                data=data,
                chart_json=chart_json,
                summary={
                    "total_trackers": len(trackers),
                    "currently_open": sum(1 for t in trackers if t.is_open),
                    "closed": sum(1 for t in trackers if not t.is_open),
                },
            )

        except Exception as e:
            return AnalyticsResult(
                metric_id=self.metric_id,
                title=self.title,
                error=str(e),
            )

    def get_filter_options(self) -> dict:
        return {
            "date_range": {"type": "daterange", "label": "Date Range"},
            "team_id": {"type": "select", "label": "Team"},
            "project_id": {"type": "select", "label": "Project"},
        }
