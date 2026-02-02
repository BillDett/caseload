"""Main blueprint - home dashboard."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    """Home dashboard."""
    from app.models import Team, Project, CVE, Tracker

    stats = {
        "teams": Team.query.count(),
        "projects": Project.query.count(),
        "cves": CVE.query.count(),
        "trackers": Tracker.query.count(),
        "open_trackers": Tracker.query.filter(
            Tracker.resolved_date.is_(None)
        ).count(),
    }

    # Check if Jira is configured
    jira_configured = bool(
        current_app.config.get("JIRA_SERVER")
        and current_app.config.get("JIRA_API_TOKEN")
    )

    return render_template("main/index.html", stats=stats, jira_configured=jira_configured)


@bp.route("/sync", methods=["POST"])
def sync():
    """Trigger data synchronization."""
    from data.config_loader import sync_teams_from_config, load_teams_config
    from data.sources.jira_source import JiraDataSource
    from data.sync import SyncService

    # First sync teams/projects from config
    config_stats = sync_teams_from_config()
    flash(
        f"Config sync: {config_stats['teams_created']} teams created, "
        f"{config_stats['projects_created']} projects created",
        "info",
    )

    # Get project keys from config
    teams_config = load_teams_config()
    project_keys = []
    for team in teams_config.get("teams", []):
        project_keys.extend(team.get("projects", []))

    if not project_keys:
        flash("No projects defined in config/teams.json. Cannot sync from Jira.", "warning")
        return redirect(url_for("main.index"))

    # Then sync from Jira if configured
    jira_server = current_app.config.get("JIRA_SERVER")
    jira_token = current_app.config.get("JIRA_API_TOKEN")

    if jira_server and jira_token:
        try:
            from datetime import datetime
            from app.models import Util

            jira = JiraDataSource(
                server=jira_server,
                api_token=jira_token,
            )

            success, message = jira.test_connection()
            if not success:
                # Truncate error message to avoid session cookie overflow
                error_msg = message[:200] + "..." if len(message) > 200 else message
                flash(f"Jira connection failed: {error_msg}", "error")
                return redirect(url_for("main.index"))

            # Get last sync datetime for incremental sync
            last_sync = Util.get_last_sync()
            sync_start_time = datetime.utcnow()

            sync_service = SyncService(current_app)
            stats = sync_service.sync_from_source(
                jira,
                project_keys=project_keys,
                since=last_sync,
            )

            # Update last sync datetime on success
            Util.set_last_sync(sync_start_time)

            flash(
                f"Jira sync: {stats['trackers_created']} trackers created, "
                f"{stats['trackers_updated']} updated, "
                f"{stats['cves_created']} CVEs found",
                "success",
            )

            if stats["errors"]:
                flash(f"Sync errors: {len(stats['errors'])}", "warning")

        except Exception as e:
            error_msg = str(e)[:200] + "..." if len(str(e)) > 200 else str(e)
            flash(f"Jira sync failed: {error_msg}", "error")
    else:
        flash("Jira not configured. Only synced teams/projects from config.", "warning")

    return redirect(url_for("main.index"))


@bp.route("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
