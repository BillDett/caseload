"""Jira data source implementation."""

import logging
import re
from datetime import datetime
from typing import Iterator

from data.sources.base import DataSource, RawTracker
from data.sources.registry import SourceRegistry

logger = logging.getLogger(__name__)


@SourceRegistry.register
class JiraDataSource(DataSource):
    """Jira implementation of DataSource."""

    SOURCE_TYPE = "jira"

    # Regex pattern to extract CVE IDs from text
    CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)

    def __init__(
        self,
        server: str,
        username: str,
        api_token: str,
    ):
        """Initialize Jira data source.

        Args:
            server: Jira server URL.
            username: Jira username/email.
            api_token: Jira API token.
        """
        self.server = server
        self.username = username
        self.api_token = api_token
        self._client = None

    @property
    def source_type(self) -> str:
        return self.SOURCE_TYPE

    @property
    def display_name(self) -> str:
        return "Jira"

    @property
    def client(self):
        """Lazy-load Jira client."""
        if self._client is None:
            from jira import JIRA

            logger.info(f"Connecting to Jira server: {self.server}")
            self._client = JIRA(
                server=self.server,
                token_auth=self.api_token
            )
            logger.info("Jira client initialized successfully")
        return self._client

    def test_connection(self) -> tuple[bool, str]:
        """Test connection to Jira."""
        try:
            logger.info("Testing Jira connection...")
            user = self.client.myself()
            logger.info(f"Connected as: {user.get('displayName', user.get('name', 'unknown'))}")
            return True, "Connected successfully"
        except Exception as e:
            logger.error(f"Jira connection failed: {e}")
            return False, f"Connection failed: {str(e)}"

    def fetch_trackers(
        self,
        project_keys: list[str],
        since: datetime | None = None,
    ) -> Iterator[RawTracker]:
        """Fetch trackers from Jira.

        Args:
            project_keys: List of Jira project keys to fetch (required).
            since: Optional datetime to fetch only recently updated issues.

        Yields:
            RawTracker objects with normalized Jira issue data.

        Raises:
            ValueError: If project_keys is empty.
        """
        if not project_keys:
            raise ValueError("project_keys is required - cannot fetch without specifying projects")

        jql_parts = []

        keys_str = ", ".join(f'"{k}"' for k in project_keys)
        jql_parts.append(f"project IN ({keys_str})")

        if since:
            since_str = since.strftime("%Y-%m-%d %H:%M")
            jql_parts.append(f'updated >= "{since_str}"')

        # Only fetch issues that are likely CVE trackers
        # Adjust this JQL based on how CVE trackers are identified in your Jira
        jql_parts.append('labels in ("Security", "SecurityTracking")')

        jql = " AND ".join(jql_parts)
        logger.info(f"Fetching issues with JQL: {jql}")

        start_at = 0
        max_results = 100
        total_fetched = 0

        while True:
            logger.info(f"Fetching issues {start_at} to {start_at + max_results}...")
            try:
                issues = self.client.search_issues(
                    jql,
                    startAt=start_at,
                    maxResults=max_results,
                    fields="summary,status,resolution,priority,assignee,reporter,"
                    "created,updated,resolutiondate,duedate,project,labels",
                )
            except Exception as e:
                logger.error(f"Jira search failed: {e}")
                raise

            if not issues:
                if total_fetched == 0:
                    logger.warning(f"No issues found matching JQL: {jql}")
                else:
                    logger.info("No more issues to fetch")
                break

            batch_size = len(issues)
            total_fetched += batch_size
            logger.info(f"Fetched {batch_size} issues (total: {total_fetched})")

            for issue in issues:
                logger.debug(f"Processing issue: {issue.key}")
                yield self._convert_issue(issue)

            start_at += batch_size
            if batch_size < max_results:
                logger.info(f"Reached end of results. Total issues fetched: {total_fetched}")
                break

    def _convert_issue(self, issue) -> RawTracker:
        """Convert Jira issue to RawTracker."""
        fields = issue.fields

        # Extract CVE IDs from summary and description
        cve_ids = self._extract_cve_ids(fields.summary or "")

        if cve_ids:
            logger.debug(f"Issue {issue.key}: found CVEs {cve_ids}")

        return RawTracker(
            source_key=issue.key,
            source_type=self.SOURCE_TYPE,
            project_key=fields.project.key,
            summary=fields.summary,
            status=fields.status.name if fields.status else None,
            resolution=fields.resolution.name if fields.resolution else None,
            priority=fields.priority.name if fields.priority else None,
            assignee=fields.assignee.displayName if fields.assignee else None,
            reporter=fields.reporter.displayName if fields.reporter else None,
            created_date=self._parse_date(fields.created),
            updated_date=self._parse_date(fields.updated),
            resolved_date=self._parse_date(fields.resolutiondate),
            due_date=self._parse_date(fields.duedate),
            cve_ids=cve_ids,
            labels=[str(label) for label in (fields.labels or [])],
        )

    def _extract_cve_ids(self, text: str) -> list[str]:
        """Extract CVE IDs from text."""
        matches = self.CVE_PATTERN.findall(text)
        return [cve.upper() for cve in set(matches)]

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse Jira date string to datetime."""
        if not date_str:
            return None
        try:
            # Jira returns ISO format dates
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    def fetch_projects(self) -> list[dict]:
        """Fetch all accessible Jira projects."""
        logger.info("Fetching available Jira projects...")
        projects = self.client.projects()
        logger.info(f"Found {len(projects)} projects")
        return [{"key": p.key, "name": p.name} for p in projects]
