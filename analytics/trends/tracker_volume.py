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
            show_severity: Whether to show severity breakdown lines.
        """
        from app.extensions import db
        from app.models import Tracker

        default_start = datetime.utcnow() - timedelta(days=90)
        default_end = datetime.utcnow()

        start_date = self._parse_date(kwargs.get("date_range_start"), default_start)
        end_date = self._parse_date(kwargs.get("date_range_end"), default_end)
        show_severity = kwargs.get("show_severity") == "on"

        try:
            trackers = db.session.query(Tracker).filter(
                Tracker.created_date >= start_date,
                Tracker.created_date <= end_date,
            ).all()

            # Build time series data
            date_range = pd.date_range(start=start_date, end=end_date, freq="W")
            open_counts = []
            closed_counts = []

            # Severity breakdown counts
            critical_counts = []
            important_counts = []
            moderate_counts = []

            for week_end in date_range:
                week_start = week_end - timedelta(days=7)

                # Count open trackers at this point in time
                open_at_week = [
                    t for t in trackers
                    if t.created_date
                    and t.created_date <= week_end
                    and (not t.resolved_date or t.resolved_date > week_end)
                ]
                open_counts.append(len(open_at_week))

                closed_count = sum(
                    1
                    for t in trackers
                    if t.resolved_date
                    and t.resolved_date > week_start
                    and t.resolved_date <= week_end
                )
                closed_counts.append(closed_count)

                # Count by severity (open trackers at this point)
                critical_counts.append(sum(
                    1 for t in open_at_week
                    if t.severity and t.severity.lower() == 'critical'
                ))
                important_counts.append(sum(
                    1 for t in open_at_week
                    if t.severity and t.severity.lower() == 'important'
                ))
                moderate_counts.append(sum(
                    1 for t in open_at_week
                    if t.severity and t.severity.lower() == 'moderate'
                ))

            # Build chart data
            y_series = [open_counts, closed_counts]
            names = ["Open Trackers", "Closed Trackers"]
            line_dashes = ["solid", "solid"]

            if show_severity:
                y_series.extend([critical_counts, important_counts, moderate_counts])
                names.extend(["Critical", "Important", "Moderate"])
                line_dashes.extend(["dash", "dash", "dash"])

            data = {
                "x": [d.strftime("%Y-%m-%d") for d in date_range],
                "y": y_series,
                "names": names,
            }

            chart = LineChart()
            chart_json = chart.render_json(
                data,
                title="CVE Tracker Volume Over Time",
                x_label="Date",
                y_label="Count",
                line_dashes=line_dashes,
            )

            # Count trackers closed with inaccurate resolutions
            inaccurate_resolutions = {'obsolete', "won't do", 'not a bug', 'duplicate'}
            inaccurate_count = sum(
                1 for t in trackers
                if t.resolution and t.resolution.lower() in inaccurate_resolutions
            )

            total_closed = sum(1 for t in trackers if not t.is_open)
            accuracy_rate = round(
                ((total_closed - inaccurate_count) / total_closed * 100) if total_closed > 0 else 100,
                1
            )

            return AnalyticsResult(
                metric_id=self.metric_id,
                title=self.title,
                data=data,
                chart_json=chart_json,
                summary={
                    "total_trackers": len(trackers),
                    "currently_open": sum(1 for t in trackers if t.is_open),
                    "closed": total_closed,
                    "inaccurate": inaccurate_count,
                    "accuracy_rate": accuracy_rate,
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
            "time_range": {
                "type": "select",
                "label": "Quick Select",
                "options": [
                    {"value": "", "label": "Custom"},
                    {"value": "last_week", "label": "Last Week"},
                    {"value": "last_month", "label": "Last Month"},
                    {"value": "last_quarter", "label": "Last Quarter"},
                    {"value": "last_year", "label": "Last Year"},
                ],
            },
            "date_range": {"type": "daterange", "label": "Date Range"},
            "show_severity": {
                "type": "checkbox",
                "label": "Show Severity Breakdown",
            },
        }
