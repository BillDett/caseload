"""SLA compliance metric."""

from datetime import datetime, timedelta
from typing import Literal

from analytics.base import AnalyticsMetric, AnalyticsResult
from analytics.registry import AnalyticsRegistry
from analytics.visualizations import PieChart, BarChart


@AnalyticsRegistry.register
class SLAComplianceMetric(AnalyticsMetric):
    """Track SLA compliance for CVE trackers."""

    @property
    def metric_id(self) -> str:
        return "sla_compliance"

    @property
    def title(self) -> str:
        return "SLA Compliance"

    @property
    def description(self) -> str:
        return "Percentage of trackers resolved within SLA timeframe"

    @property
    def category(self) -> Literal["trends", "impact"]:
        return "trends"

    def compute(self, **kwargs) -> AnalyticsResult:
        """Compute SLA compliance metrics.

        Kwargs:
            sla_days: Number of days for SLA (default from config).
            start_date: Start of date range.
            end_date: End of date range.
            team_id: Optional team filter.
        """
        from flask import current_app
        from app.extensions import db
        from app.models import Tracker, Project

        sla_days = kwargs.get(
            "sla_days", current_app.config.get("DEFAULT_SLA_DAYS", 30)
        )
        start_date = kwargs.get("start_date", datetime.utcnow() - timedelta(days=90))
        end_date = kwargs.get("end_date", datetime.utcnow())
        team_id = kwargs.get("team_id")

        try:
            query = db.session.query(Tracker).filter(
                Tracker.resolved_date.isnot(None),
                Tracker.resolved_date >= start_date,
                Tracker.resolved_date <= end_date,
            )

            if team_id:
                query = query.join(Project).filter(Project.team_id == team_id)

            resolved_trackers = query.all()

            # Calculate SLA compliance
            within_sla = 0
            breached = 0

            for tracker in resolved_trackers:
                if tracker.created_date and tracker.resolved_date:
                    days_to_resolve = (
                        tracker.resolved_date - tracker.created_date
                    ).days
                    if days_to_resolve <= sla_days:
                        within_sla += 1
                    else:
                        breached += 1

            total = within_sla + breached
            compliance_rate = (within_sla / total * 100) if total > 0 else 0

            # Pie chart data
            pie_data = {
                "labels": ["Within SLA", "SLA Breached"],
                "values": [within_sla, breached],
            }

            pie_chart = PieChart()
            chart_json = pie_chart.render_json(
                pie_data,
                title=f"SLA Compliance ({sla_days} day target)",
            )

            # By-team breakdown if we have team data
            team_data = self._compute_by_team(resolved_trackers, sla_days)

            return AnalyticsResult(
                metric_id=self.metric_id,
                title=self.title,
                data={
                    "pie": pie_data,
                    "by_team": team_data,
                },
                chart_json=chart_json,
                summary={
                    "total_resolved": total,
                    "within_sla": within_sla,
                    "breached": breached,
                    "compliance_rate": round(compliance_rate, 1),
                    "sla_days": sla_days,
                },
            )

        except Exception as e:
            return AnalyticsResult(
                metric_id=self.metric_id,
                title=self.title,
                error=str(e),
            )

    def _compute_by_team(self, trackers: list, sla_days: int) -> dict:
        """Compute SLA compliance breakdown by team."""
        teams = {}

        for tracker in trackers:
            if not tracker.project or not tracker.project.team:
                continue

            team_name = tracker.project.team.name
            if team_name not in teams:
                teams[team_name] = {"within": 0, "breached": 0}

            if tracker.created_date and tracker.resolved_date:
                days = (tracker.resolved_date - tracker.created_date).days
                if days <= sla_days:
                    teams[team_name]["within"] += 1
                else:
                    teams[team_name]["breached"] += 1

        return {
            "labels": list(teams.keys()),
            "within_sla": [t["within"] for t in teams.values()],
            "breached": [t["breached"] for t in teams.values()],
        }

    def get_filter_options(self) -> dict:
        return {
            "date_range": {"type": "daterange", "label": "Date Range"},
            "team_id": {"type": "select", "label": "Team"},
            "sla_days": {
                "type": "number",
                "label": "SLA Days",
                "default": 30,
            },
        }
