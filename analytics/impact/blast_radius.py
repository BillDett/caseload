"""Blast radius metric for individual CVEs."""

from typing import Literal

from analytics.base import AnalyticsMetric, AnalyticsResult
from analytics.registry import AnalyticsRegistry
from analytics.visualizations import NetworkGraph, BarChart


@AnalyticsRegistry.register
class BlastRadiusMetric(AnalyticsMetric):
    """Analyze the blast radius of a specific CVE."""

    @property
    def metric_id(self) -> str:
        return "blast_radius"

    @property
    def title(self) -> str:
        return "CVE Blast Radius"

    @property
    def description(self) -> str:
        return "Affected teams, projects, and dependencies for a CVE"

    @property
    def category(self) -> Literal["trends", "impact"]:
        return "impact"

    def compute(self, **kwargs) -> AnalyticsResult:
        """Compute blast radius for a specific CVE.

        Kwargs:
            cve_id: CVE identifier (required).
        """
        from app.extensions import db
        from app.models import CVE, Tracker, Project, Team

        cve_id = kwargs.get("cve_id")
        if not cve_id:
            return AnalyticsResult(
                metric_id=self.metric_id,
                title=self.title,
                error="cve_id is required",
            )

        try:
            cve = CVE.query.filter_by(cve_id=cve_id).first()
            if not cve:
                return AnalyticsResult(
                    metric_id=self.metric_id,
                    title=self.title,
                    error=f"CVE {cve_id} not found",
                )

            trackers = list(cve.trackers)
            affected_projects = cve.affected_projects
            affected_teams = cve.affected_teams

            # Build dependency graph
            nodes = [{"id": cve.cve_id, "label": cve.cve_id}]
            edges = []

            for project in affected_projects:
                nodes.append({"id": f"proj_{project.id}", "label": project.key})
                edges.append({"source": cve.cve_id, "target": f"proj_{project.id}"})

                # Add project dependencies
                for upstream in project.upstream_dependencies:
                    if upstream not in affected_projects:
                        nodes.append(
                            {"id": f"proj_{upstream.id}", "label": f"{upstream.key} (dep)"}
                        )
                    edges.append(
                        {"source": f"proj_{upstream.id}", "target": f"proj_{project.id}"}
                    )

            graph_data = {"nodes": nodes, "edges": edges}

            network = NetworkGraph()
            chart_json = network.render_json(
                graph_data,
                title=f"Blast Radius: {cve_id}",
            )

            # Team impact summary
            team_tracker_counts = {}
            for tracker in trackers:
                if tracker.project and tracker.project.team:
                    team_name = tracker.project.team.name
                    team_tracker_counts[team_name] = (
                        team_tracker_counts.get(team_name, 0) + 1
                    )

            # Date skew analysis
            created_dates = [t.created_date for t in trackers if t.created_date]
            date_skew = None
            if len(created_dates) > 1:
                earliest = min(created_dates)
                latest = max(created_dates)
                date_skew = (latest - earliest).days

            return AnalyticsResult(
                metric_id=self.metric_id,
                title=f"{self.title}: {cve_id}",
                data={
                    "graph": graph_data,
                    "team_impact": team_tracker_counts,
                },
                chart_json=chart_json,
                summary={
                    "cve_id": cve_id,
                    "severity": cve.severity,
                    "is_embargoed": cve.is_embargoed,
                    "affected_teams": len(affected_teams),
                    "affected_projects": len(affected_projects),
                    "total_trackers": len(trackers),
                    "open_trackers": sum(1 for t in trackers if t.is_open),
                    "date_skew_days": date_skew,
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
            "cve_id": {
                "type": "text",
                "label": "CVE ID",
                "placeholder": "CVE-2024-XXXXX",
                "required": True,
            },
        }
