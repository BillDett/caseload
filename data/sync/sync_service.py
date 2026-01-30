"""Synchronization service for data sources."""

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from data.sources.base import DataSource, RawTracker

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)


class SyncService:
    """Service for synchronizing data from external sources to the database."""

    def __init__(self, app: "Flask | None" = None):
        """Initialize sync service.

        Args:
            app: Optional Flask application for context.
        """
        self.app = app

    def sync_from_source(
        self,
        source: DataSource,
        project_keys: list[str],
        since: datetime | None = None,
    ) -> dict:
        """Synchronize trackers from a data source.

        Args:
            source: DataSource instance to sync from.
            project_keys: List of project keys to sync (required to avoid querying all projects).
            since: Optional datetime for incremental sync.

        Returns:
            Dictionary with sync statistics.

        Raises:
            ValueError: If project_keys is empty.
        """
        if not project_keys:
            raise ValueError("project_keys is required - cannot sync without specifying projects")

        from app.extensions import db
        from app.models import CVE, Project, Tracker

        if since:
            logger.info(f"Starting incremental sync from {source.display_name} for projects: {project_keys} (since {since})")
        else:
            logger.info(f"Starting full sync from {source.display_name} for projects: {project_keys}")

        stats = {
            "trackers_created": 0,
            "trackers_updated": 0,
            "cves_created": 0,
            "projects_created": 0,
            "errors": [],
        }

        processed = 0
        for raw_tracker in source.fetch_trackers(project_keys, since):
            try:
                self._process_tracker(raw_tracker, stats, db, CVE, Project, Tracker)
                processed += 1
                if processed % 50 == 0:
                    logger.info(f"Processed {processed} trackers...")
            except Exception as e:
                logger.warning(f"Error processing {raw_tracker.source_key}: {e}")
                stats["errors"].append(f"{raw_tracker.source_key}: {str(e)}")

        logger.info(f"Committing {processed} trackers to database...")
        db.session.commit()

        logger.info(
            f"Sync complete: {stats['trackers_created']} created, "
            f"{stats['trackers_updated']} updated, "
            f"{stats['cves_created']} CVEs, "
            f"{len(stats['errors'])} errors"
        )

        return stats

    def _process_tracker(
        self,
        raw: RawTracker,
        stats: dict,
        db,
        CVE,
        Project,
        Tracker,
    ) -> None:
        """Process a single raw tracker into database records."""
        # Get or create project
        project = Project.query.filter_by(key=raw.project_key).first()
        if not project:
            project = Project(key=raw.project_key, name=raw.project_key)
            db.session.add(project)
            db.session.flush()
            stats["projects_created"] += 1
            logger.debug(f"Created project: {raw.project_key}")

        # Get or create CVEs
        cve = None
        for cve_id in raw.cve_ids:
            existing_cve = CVE.query.filter_by(cve_id=cve_id).first()
            if not existing_cve:
                existing_cve = CVE(cve_id=cve_id)
                db.session.add(existing_cve)
                db.session.flush()
                stats["cves_created"] += 1
                logger.debug(f"Created CVE: {cve_id}")
            cve = existing_cve  # Link to the first/primary CVE

        # Get or create tracker
        tracker = Tracker.query.filter_by(jira_key=raw.source_key).first()
        if tracker:
            stats["trackers_updated"] += 1
        else:
            tracker = Tracker(jira_key=raw.source_key)
            db.session.add(tracker)
            stats["trackers_created"] += 1
            logger.debug(f"Created tracker: {raw.source_key}")

        # Update tracker fields
        tracker.project_id = project.id
        tracker.cve_id = cve.id if cve else None
        tracker.summary = raw.summary
        tracker.status = raw.status
        tracker.resolution = raw.resolution
        tracker.priority = raw.priority
        tracker.severity = raw.severity
        tracker.assignee = raw.assignee
        tracker.reporter = raw.reporter
        tracker.created_date = raw.created_date
        tracker.updated_date = raw.updated_date
        tracker.resolved_date = raw.resolved_date
        tracker.due_date = raw.due_date
        tracker.sla_date = raw.sla_date
        tracker.last_synced_at = datetime.utcnow()
