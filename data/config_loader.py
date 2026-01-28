"""Load teams and projects from JSON configuration."""

import json
from pathlib import Path


def load_teams_config(config_path: str | Path | None = None) -> dict:
    """Load teams and projects configuration from JSON file.

    Args:
        config_path: Path to the JSON config file. Defaults to config/teams.json.

    Returns:
        Dictionary with 'teams' and 'project_dependencies' keys.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "teams.json"

    config_path = Path(config_path)

    if not config_path.exists():
        return {"teams": [], "project_dependencies": {}}

    with open(config_path) as f:
        return json.load(f)


def sync_teams_from_config(config_path: str | Path | None = None) -> dict:
    """Sync teams and projects from config file to database.

    Args:
        config_path: Path to the JSON config file.

    Returns:
        Statistics about the sync operation.
    """
    from app.extensions import db
    from app.models import Team, Project

    config = load_teams_config(config_path)
    stats = {"teams_created": 0, "teams_updated": 0, "projects_created": 0}

    # Create/update teams and their projects
    for team_data in config.get("teams", []):
        team = Team.query.filter_by(name=team_data["name"]).first()
        if not team:
            team = Team(name=team_data["name"], description=team_data.get("description"))
            db.session.add(team)
            stats["teams_created"] += 1
        else:
            team.description = team_data.get("description")
            stats["teams_updated"] += 1

        db.session.flush()

        # Create projects for this team
        for project_key in team_data.get("projects", []):
            project = Project.query.filter_by(key=project_key).first()
            if not project:
                project = Project(key=project_key, name=project_key, team_id=team.id)
                db.session.add(project)
                stats["projects_created"] += 1
            else:
                project.team_id = team.id

    db.session.flush()

    # Set up project dependencies
    for downstream_key, upstream_keys in config.get("project_dependencies", {}).items():
        downstream = Project.query.filter_by(key=downstream_key).first()
        if downstream:
            for upstream_key in upstream_keys:
                upstream = Project.query.filter_by(key=upstream_key).first()
                if upstream and upstream not in downstream.upstream_dependencies:
                    downstream.upstream_dependencies.append(upstream)

    db.session.commit()
    return stats
