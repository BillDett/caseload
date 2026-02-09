"""Trends blueprint - Vulnerability Trends (org-wide analytics)."""

from urllib.parse import quote

from flask import Blueprint, current_app, render_template, request

from analytics.visualizations.charts import PieChart, ScatterTimeline

bp = Blueprint("trends", __name__)


@bp.route("/")
def index():
    """Vulnerability Trends dashboard."""
    from analytics.registry import AnalyticsRegistry

    AnalyticsRegistry.discover()
    metrics = AnalyticsRegistry.get_by_category("trends")

    return render_template(
        "trends/index.html",
        metrics=[
            {
                "id": m.metric_id.fget(None),
                "title": m.title.fget(None),
                "description": m.description.fget(None),
            }
            for m in metrics
        ],
    )


@bp.route("/metric/<metric_id>")
def metric(metric_id: str):
    """Display a specific trends metric."""
    from analytics.registry import AnalyticsRegistry

    AnalyticsRegistry.discover()
    metric_class = AnalyticsRegistry.get(metric_id)

    if not metric_class:
        return render_template("errors/404.html", message="Metric not found"), 404

    metric_instance = metric_class()

    # Get filter values from query params
    filters = {}
    for key, value in request.args.items():
        if value:
            filters[key] = value

    result = metric_instance.compute(**filters)

    return render_template(
        "trends/metric.html",
        metric=metric_instance,
        result=result,
        filters=metric_instance.get_filter_options(),
    )


@bp.route("/component-history")
def component_history():
    """Component CVE History page."""
    from app.extensions import db
    from app.models import Project, Tracker

    projects = Project.query.order_by(Project.key).all()

    selected_project = request.args.get("project", "")
    selected_component = request.args.get("component", "")

    # Build components list for the selected project
    components = []
    if selected_project:
        project = Project.query.filter_by(key=selected_project).first()
        if project:
            components = [
                row[0]
                for row in db.session.query(Tracker.downstream_component)
                .filter(
                    Tracker.project_id == project.id,
                    Tracker.downstream_component.isnot(None),
                    Tracker.downstream_component != "",
                    Tracker.cve_id.isnot(None),
                )
                .distinct()
                .order_by(Tracker.downstream_component)
                .all()
            ]

    tracker_count = 0
    chart_json = None
    status_chart_json = None
    jira_url = None
    cve_ids = []

    if selected_project and selected_component:
        project = Project.query.filter_by(key=selected_project).first()
        if project:
            trackers = (
                Tracker.query.filter(
                    Tracker.project_id == project.id,
                    Tracker.downstream_component == selected_component,
                    Tracker.cve_id.isnot(None),
                )
                .order_by(Tracker.created_date)
                .all()
            )
            tracker_count = len(trackers)

            # Collect unique CVE IDs across all trackers
            seen = set()
            for t in trackers:
                if t.cve and t.cve.cve_id and t.cve.cve_id not in seen:
                    seen.add(t.cve.cve_id)
                    cve_ids.append(t.cve.cve_id)
            cve_ids.sort()

            # Build status breakdown pie chart
            if trackers:
                status_counts: dict[str, int] = {}
                for t in trackers:
                    status = t.status or "Unknown"
                    status_counts[status] = status_counts.get(status, 0) + 1
                sorted_statuses = sorted(status_counts.items(), key=lambda x: x[1], reverse=True)
                pie = PieChart()
                status_chart_json = pie.render_json(
                    {
                        "labels": [s for s, _ in sorted_statuses],
                        "values": [c for _, c in sorted_statuses],
                    },
                    title="Status Breakdown",
                )

            # Build Jira search URL
            jira_server = current_app.config.get("JIRA_SERVER", "")
            if jira_server:
                jql = (
                    f'project = "{selected_project}" '
                    f'AND "Downstream Component Name" ~ "{selected_component}" '
                    f'AND labels in ("Security", "SecurityTracking")'
                )
                jira_url = f"{jira_server}/issues/?jql={quote(jql)}"

            # Build ScatterTimeline chart
            if trackers:
                points = []
                for t in trackers:
                    if t.created_date:
                        points.append(
                            {
                                "x": t.created_date.strftime("%Y-%m-%d"),
                                "y": selected_component,
                                "label": f"{t.jira_key} ({t.created_date.strftime('%Y-%m-%d')})",
                            }
                        )

                chart_data = {
                    "points": points,
                    "categories": [selected_component],
                }
                chart = ScatterTimeline()
                chart_json = chart.render_json(
                    chart_data,
                    title=f"CVE Tracker Creation Timeline - {selected_component}",
                    x_label="Date",
                    height=250,
                )

    return render_template(
        "trends/component_history.html",
        projects=projects,
        components=components,
        selected_project=selected_project,
        selected_component=selected_component,
        tracker_count=tracker_count,
        jira_url=jira_url,
        chart_json=chart_json,
        status_chart_json=status_chart_json,
        cve_ids=cve_ids,
    )
