# CaseLoad

CaseLoad is a web application that provides analytics on CVE (Common Vulnerabilities and Exposures) tracker data from multiple Jira projects. It helps leadership understand macro trends around CVE work affecting engineering teams.

## Requirements

- Python 3.10 or higher
- Access to a Jira instance with CVE tracker data

## Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd caseload
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -e .
   ```

   Or using requirements.txt:

   ```bash
   pip install -r requirements.txt
   ```

4. **Install development dependencies (optional)**

   ```bash
   pip install -e ".[dev]"
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root or export these environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FLASK_ENV` | No | `development` | Environment mode (`development`, `production`, `testing`) |
| `SECRET_KEY` | Yes (prod) | `dev-secret-key...` | Flask secret key for session security |
| `DATABASE_URL` | No | `sqlite:///instance/caseload.db` | Database connection URL |
| `JIRA_SERVER` | Yes | - | Jira server URL (e.g., `https://issues.redhat.com`) |
| `JIRA_API_TOKEN` | Yes | - | Jira Personal Access Token |

### Example .env file

```bash
FLASK_ENV=development
SECRET_KEY=your-secure-secret-key-here

# Jira Configuration
JIRA_SERVER=https://issues.redhat.com
JIRA_API_TOKEN=your-jira-personal-access-token
```

### Generating a Jira Personal Access Token

1. Log into your Jira instance
2. Go to Profile > Personal Access Tokens
3. Create a new token with appropriate permissions
4. Copy the token to your `.env` file

## Running the Application

### Development Mode

```bash
# Using Flask development server
flask run

# Or using the entry point
python run.py

# Or using the installed command
caseload
```

The application will be available at `http://localhost:5000`

### Production Mode

```bash
# Set production environment
export FLASK_ENV=production
export SECRET_KEY=your-secure-production-key

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

## Database

CaseLoad uses SQLite by default. The database file is automatically created at `instance/caseload.db` when the application starts.

To use a different database (PostgreSQL, MySQL, etc.), set the `DATABASE_URL` environment variable:

```bash
# PostgreSQL example
DATABASE_URL=postgresql://user:password@localhost/caseload

# MySQL example
DATABASE_URL=mysql://user:password@localhost/caseload
```

## Syncing Data from Jira

Data is synced from Jira using the sync service. You can trigger a sync programmatically:

```python
from flask import Flask
from app import create_app
from data.sources.jira_source import JiraDataSource
from data.sync.sync_service import SyncService

app = create_app()

with app.app_context():
    # Create Jira data source
    source = JiraDataSource(
        server="https://issues.redhat.com",
        api_token="your-api-token",
    )

    # Test connection
    success, message = source.test_connection()
    print(f"Connection: {message}")

    # Sync specific projects
    sync_service = SyncService(app)
    stats = sync_service.sync_from_source(
        source=source,
        project_keys=["OCPBUGS", "RHEL"],  # Your project keys
    )

    print(f"Created: {stats['trackers_created']}")
    print(f"Updated: {stats['trackers_updated']}")
    print(f"CVEs: {stats['cves_created']}")
```

### Sync Script Example

Create a `sync.py` script:

```python
#!/usr/bin/env python3
"""Sync data from Jira."""

import os
from app import create_app
from data.sources.jira_source import JiraDataSource
from data.sync.sync_service import SyncService

# Projects to sync
PROJECT_KEYS = ["OCPBUGS", "RHEL", "RHOSP"]

app = create_app()

with app.app_context():
    source = JiraDataSource(
        server=os.environ["JIRA_SERVER"],
        api_token=os.environ["JIRA_API_TOKEN"],
    )

    sync_service = SyncService(app)
    stats = sync_service.sync_from_source(
        source=source,
        project_keys=PROJECT_KEYS,
    )

    print(f"Sync complete: {stats}")
```

Run with:

```bash
python sync.py
```

## Application Routes

| Route | Description |
|-------|-------------|
| `/` | Home dashboard with summary statistics |
| `/trends` | Vulnerability Trends - org-wide analytics |
| `/trends/<metric_id>` | Specific trend metric (e.g., `/trends/tracker_volume`) |
| `/impact` | Vulnerability Impact - CVE listing with pagination |
| `/impact/cve/<cve_id>` | Per-CVE blast radius analysis |
| `/impact/search?q=<cve_id>` | Search for a CVE |
| `/api/teams` | REST API - List teams |
| `/api/projects` | REST API - List projects |
| `/api/cves` | REST API - List CVEs |
| `/api/trackers` | REST API - List trackers |
| `/api/metrics/<metric_id>` | REST API - Compute metric |

## Available Metrics

### Trends (Org-wide)

- **Tracker Volume** (`tracker_volume`) - Open/closed tracker counts over time with severity breakdown
- **SLA Compliance** (`sla_compliance`) - Percentage of trackers meeting SLA targets

### Impact (Per-CVE)

- **Blast Radius** (`blast_radius`) - Affected teams, projects, and timeline visualization for a specific CVE

## Project Structure

```
caseload/
├── app/                      # Flask application
│   ├── __init__.py           # Application factory
│   ├── config.py             # Configuration classes
│   ├── extensions.py         # Flask extensions
│   ├── blueprints/           # Route handlers
│   │   ├── main/             # Home dashboard
│   │   ├── trends/           # Vulnerability Trends
│   │   ├── impact/           # Vulnerability Impact
│   │   └── api/              # REST API
│   ├── models/               # SQLAlchemy ORM models
│   ├── templates/            # Jinja2 templates
│   └── static/               # CSS, JS, images
│
├── analytics/                # Analytics layer
│   ├── base.py               # AnalyticsMetric base class
│   ├── registry.py           # Metric auto-discovery
│   ├── trends/               # Trend metrics
│   ├── impact/               # Impact metrics
│   └── visualizations/       # Chart generators (Plotly)
│
├── data/                     # Data layer
│   ├── sources/              # Data source adapters
│   │   ├── base.py           # DataSource base class
│   │   ├── jira_source.py    # Jira implementation
│   │   └── registry.py       # Source registry
│   └── sync/                 # Synchronization logic
│
├── instance/                 # SQLite database (gitignored)
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Project metadata
└── run.py                    # Entry point
```

## Adding New Metrics

Create a new metric by implementing the `AnalyticsMetric` base class:

```python
from analytics.base import AnalyticsMetric, AnalyticsResult
from analytics.registry import AnalyticsRegistry

@AnalyticsRegistry.register
class MyNewMetric(AnalyticsMetric):
    @property
    def metric_id(self) -> str:
        return "my_new_metric"

    @property
    def title(self) -> str:
        return "My New Metric"

    @property
    def description(self) -> str:
        return "Description of what this metric shows"

    @property
    def category(self) -> str:
        return "trends"  # or "impact"

    def compute(self, **kwargs) -> AnalyticsResult:
        # Your metric computation logic
        return AnalyticsResult(
            metric_id=self.metric_id,
            title=self.title,
            data={},
            summary={"key": "value"},
        )
```

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov=analytics --cov=data
```

## License

MIT
