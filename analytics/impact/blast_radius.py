"""Blast radius metric for individual CVEs."""

import urllib.parse
from collections import defaultdict
from typing import Literal

from analytics.base import AnalyticsMetric, AnalyticsResult
from analytics.registry import AnalyticsRegistry
from analytics.visualizations import SankeyDiagram


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

    def _format_date(self, dt) -> str:
        """Format date for display, handling None."""
        if dt is None:
            return "No Date"
        return dt.strftime("%Y-%m-%d")

    def _get_project_from_jira_key(self, jira_key: str) -> str:
        """Extract project key from Jira key (e.g., 'OCPBUGS-12345' -> 'OCPBUGS')."""
        return jira_key.split("-")[0] if "-" in jira_key else jira_key

    def _get_highest_severity(self, trackers: list) -> str | None:
        """Get the highest severity from trackers.

        Severity order: Critical > Important > Moderate > Low
        """
        severity_order = {"critical": 4, "important": 3, "moderate": 2, "low": 1}
        highest = None
        highest_rank = 0

        for t in trackers:
            if t.severity:
                rank = severity_order.get(t.severity.lower(), 0)
                if rank > highest_rank:
                    highest_rank = rank
                    highest = t.severity

        return highest

    def _build_sankey_data(self, trackers: list, cve_id: str) -> dict:
        """Build Sankey diagram data from trackers.

        Flow: Project -> Created Date -> Due Date -> SLA Date

        Args:
            trackers: List of tracker objects.
            cve_id: CVE identifier for building Jira search URLs.
        """
        # Collect unique values for each column
        projects = set()
        created_dates = set()
        due_dates = set()
        sla_dates = set()

        # Track due dates that are past SLA (due_date > sla_date)
        due_dates_past_sla = set()

        # Build tracker data with all fields
        tracker_data = []
        for t in trackers:
            project = self._get_project_from_jira_key(t.jira_key)
            created = self._format_date(t.created_date)
            due = self._format_date(t.due_date)
            sla = self._format_date(t.sla_date)

            projects.add(project)
            created_dates.add(created)
            due_dates.add(due)
            sla_dates.add(sla)

            # Check if due date is after SLA date
            if t.due_date and t.sla_date and t.due_date > t.sla_date:
                due_dates_past_sla.add(due)

            tracker_data.append({
                "project": project,
                "created": created,
                "due": due,
                "sla": sla,
            })

        # Create node labels (order: projects, created dates, due dates, sla dates)
        projects = sorted(projects)
        created_dates = sorted(created_dates)
        due_dates = sorted(due_dates)
        sla_dates = sorted(sla_dates)

        labels = []
        labels.extend([f"Proj: {p}" for p in projects])
        labels.extend([f"Created: {d}" for d in created_dates])
        labels.extend([f"Due: {d}" for d in due_dates])
        labels.extend([f"SLA: {d}" for d in sla_dates])

        # Create index mappings
        node_index = {label: i for i, label in enumerate(labels)}

        # Count connections
        proj_to_created = defaultdict(int)
        created_to_due = defaultdict(int)
        due_to_sla = defaultdict(int)

        for t in tracker_data:
            proj_label = f"Proj: {t['project']}"
            created_label = f"Created: {t['created']}"
            due_label = f"Due: {t['due']}"
            sla_label = f"SLA: {t['sla']}"

            proj_to_created[(proj_label, created_label)] += 1
            created_to_due[(created_label, due_label)] += 1
            due_to_sla[(due_label, sla_label)] += 1

        # Build links
        sources = []
        targets = []
        values = []

        for (src, tgt), count in proj_to_created.items():
            sources.append(node_index[src])
            targets.append(node_index[tgt])
            values.append(count)

        for (src, tgt), count in created_to_due.items():
            sources.append(node_index[src])
            targets.append(node_index[tgt])
            values.append(count)

        for (src, tgt), count in due_to_sla.items():
            sources.append(node_index[src])
            targets.append(node_index[tgt])
            values.append(count)

        # Define colors for each node
        colors = []

        for label in labels:
            if label.startswith("Proj:"):
                colors.append("rgba(31, 119, 180, 0.8)")  # Blue
            elif label.startswith("Created:"):
                colors.append("rgba(255, 127, 14, 0.8)")  # Orange
            elif label.startswith("Due:"):
                # Extract the date from the label and check if it's past SLA
                due_date_str = label.replace("Due: ", "")
                if due_date_str in due_dates_past_sla:
                    colors.append("rgba(214, 39, 40, 0.8)")   # Red - past SLA
                else:
                    colors.append("rgba(44, 160, 44, 0.8)")   # Green - within SLA
            else:  # SLA
                colors.append("rgba(214, 39, 40, 0.8)")   # Red

        return {
            "labels": labels,
            "sources": sources,
            "targets": targets,
            "values": values,
            "colors": colors,
        }

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

            # Build Sankey diagram data
            sankey_data = self._build_sankey_data(trackers, cve_id)

            sankey = SankeyDiagram()
            chart_json = sankey.render_json(
                sankey_data,
                title=f"Tracker Timeline: {cve_id}",
                height=500,
            )

            # Team impact summary
            team_tracker_counts = {}
            team_projects = {}  # Track projects per team for URL generation
            for tracker in trackers:
                if tracker.project and tracker.project.team:
                    team_name = tracker.project.team.name
                    team_tracker_counts[team_name] = (
                        team_tracker_counts.get(team_name, 0) + 1
                    )
                    # Track projects for this team
                    if team_name not in team_projects:
                        team_projects[team_name] = set()
                    team_projects[team_name].add(tracker.project.key)

            # Sort by count descending
            team_tracker_counts = dict(
                sorted(team_tracker_counts.items(), key=lambda x: x[1], reverse=True)
            )

            # Build team URLs for Jira search
            jira_base_url = "https://issues.redhat.com"
            team_urls = {}
            for team_name, projects in team_projects.items():
                projects_str = ", ".join(f'"{p}"' for p in projects)
                jql = f'project IN ({projects_str}) AND type=Vulnerability AND labels="{cve_id}"'
                team_urls[team_name] = f"{jira_base_url}/issues/?jql={urllib.parse.quote(jql)}"

            # Date skew analysis
            created_dates = [t.created_date for t in trackers if t.created_date]
            date_skew = None
            if len(created_dates) > 1:
                earliest = min(created_dates)
                latest = max(created_dates)
                date_skew = (latest - earliest).days

            # Get highest severity from trackers
            severity = self._get_highest_severity(trackers)

            return AnalyticsResult(
                metric_id=self.metric_id,
                title=f"{self.title}: {cve_id}",
                data={
                    "sankey": sankey_data,
                    "team_impact": team_tracker_counts,
                    "team_urls": team_urls,
                },
                chart_json=chart_json,
                summary={
                    "cve_id": cve_id,
                    "severity": severity,
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
