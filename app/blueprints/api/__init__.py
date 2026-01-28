"""API blueprint - REST API for AJAX requests."""

from flask import Blueprint, jsonify, request

bp = Blueprint("api", __name__)


@bp.route("/teams")
def list_teams():
    """List all teams."""
    from app.models import Team

    teams = Team.query.all()
    return jsonify(
        [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "project_count": t.projects.count(),
            }
            for t in teams
        ]
    )


@bp.route("/projects")
def list_projects():
    """List all projects."""
    from app.models import Project

    team_id = request.args.get("team_id", type=int)

    query = Project.query
    if team_id:
        query = query.filter_by(team_id=team_id)

    projects = query.all()
    return jsonify(
        [
            {
                "id": p.id,
                "key": p.key,
                "name": p.name,
                "team_id": p.team_id,
                "team_name": p.team.name if p.team else None,
                "tracker_count": p.trackers.count(),
            }
            for p in projects
        ]
    )


@bp.route("/cves")
def list_cves():
    """List CVEs with optional filters."""
    from app.models import CVE

    severity = request.args.get("severity")
    embargoed = request.args.get("embargoed", type=bool)
    limit = request.args.get("limit", 50, type=int)

    query = CVE.query

    if severity:
        query = query.filter_by(severity=severity)
    if embargoed is not None:
        query = query.filter_by(is_embargoed=embargoed)

    cves = query.order_by(CVE.created_at.desc()).limit(limit).all()

    return jsonify(
        [
            {
                "id": c.id,
                "cve_id": c.cve_id,
                "severity": c.severity,
                "cvss_score": c.cvss_score,
                "is_embargoed": c.is_embargoed,
                "published_date": c.published_date.isoformat() if c.published_date else None,
                "tracker_count": c.trackers.count(),
                "affected_teams": len(c.affected_teams),
            }
            for c in cves
        ]
    )


@bp.route("/cves/<cve_id>")
def get_cve(cve_id: str):
    """Get details for a specific CVE."""
    from app.models import CVE

    cve = CVE.query.filter_by(cve_id=cve_id).first()
    if not cve:
        return jsonify({"error": "CVE not found"}), 404

    trackers = list(cve.trackers)
    return jsonify(
        {
            "id": cve.id,
            "cve_id": cve.cve_id,
            "url": cve.url,
            "description": cve.description,
            "severity": cve.severity,
            "cvss_score": cve.cvss_score,
            "is_embargoed": cve.is_embargoed,
            "embargo_end_date": (
                cve.embargo_end_date.isoformat() if cve.embargo_end_date else None
            ),
            "published_date": (
                cve.published_date.isoformat() if cve.published_date else None
            ),
            "trackers": [
                {
                    "jira_key": t.jira_key,
                    "summary": t.summary,
                    "status": t.status,
                    "project_key": t.project.key if t.project else None,
                    "team_name": (
                        t.project.team.name if t.project and t.project.team else None
                    ),
                }
                for t in trackers
            ],
            "affected_teams": [team.name for team in cve.affected_teams],
            "affected_projects": [
                {"key": p.key, "name": p.name} for p in cve.affected_projects
            ],
        }
    )


@bp.route("/trackers")
def list_trackers():
    """List trackers with optional filters."""
    from app.models import Tracker

    project_id = request.args.get("project_id", type=int)
    cve_id = request.args.get("cve_id", type=int)
    status = request.args.get("status")
    open_only = request.args.get("open_only", type=bool)
    limit = request.args.get("limit", 100, type=int)

    query = Tracker.query

    if project_id:
        query = query.filter_by(project_id=project_id)
    if cve_id:
        query = query.filter_by(cve_id=cve_id)
    if status:
        query = query.filter_by(status=status)
    if open_only:
        query = query.filter(Tracker.resolved_date.is_(None))

    trackers = query.order_by(Tracker.created_date.desc()).limit(limit).all()

    return jsonify(
        [
            {
                "id": t.id,
                "jira_key": t.jira_key,
                "summary": t.summary,
                "status": t.status,
                "priority": t.priority,
                "assignee": t.assignee,
                "created_date": (
                    t.created_date.isoformat() if t.created_date else None
                ),
                "resolved_date": (
                    t.resolved_date.isoformat() if t.resolved_date else None
                ),
                "days_open": t.days_open,
                "project_key": t.project.key if t.project else None,
                "cve_id": t.cve.cve_id if t.cve else None,
            }
            for t in trackers
        ]
    )


@bp.route("/metrics/<metric_id>")
def compute_metric(metric_id: str):
    """Compute and return a metric result as JSON."""
    from analytics.registry import AnalyticsRegistry

    AnalyticsRegistry.discover()
    metric_class = AnalyticsRegistry.get(metric_id)

    if not metric_class:
        return jsonify({"error": "Metric not found"}), 404

    metric_instance = metric_class()

    # Get filter values from query params
    filters = {}
    for key, value in request.args.items():
        if value:
            filters[key] = value

    result = metric_instance.compute(**filters)

    return jsonify(
        {
            "metric_id": result.metric_id,
            "title": result.title,
            "computed_at": result.computed_at.isoformat(),
            "summary": result.summary,
            "chart_json": result.chart_json,
            "error": result.error,
        }
    )
