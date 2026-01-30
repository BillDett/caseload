#!/usr/bin/env python3
"""
Prototype: Sankey diagram for CVE tracker relationships.

Visualizes the flow of trackers from Project -> Created Date -> Due Date -> SLA Date
for a specific CVE.
"""

import sys
from collections import defaultdict

import plotly.graph_objects as go

# Add parent directory to path for imports
sys.path.insert(0, "/Users/bdettelb/dev/caseload")

from app import create_app
from app.models import CVE, Tracker, Project


def get_project_from_jira_key(jira_key: str) -> str:
    """Extract project key from Jira key (e.g., 'OCPBUGS-12345' -> 'OCPBUGS')."""
    return jira_key.split("-")[0] if "-" in jira_key else jira_key


def format_date(dt) -> str:
    """Format date for display, handling None."""
    if dt is None:
        return "No Date"
    return dt.strftime("%Y-%m-%d")




def build_sankey_data(cve_id: str):
    """
    Build Sankey diagram data for a CVE's trackers.

    Returns nodes (labels) and links (source, target, value).
    """
    # Get the CVE and its trackers
    cve = CVE.query.filter_by(cve_id=cve_id).first()
    if not cve:
        print(f"CVE {cve_id} not found")
        return None

    trackers = list(cve.trackers)
    if not trackers:
        print(f"No trackers found for {cve_id}")
        return None

    print(f"Found {len(trackers)} trackers for {cve_id}")

    # Collect unique values for each column
    projects = set()
    created_dates = set()
    due_dates = set()
    sla_dates = set()

    # Build tracker data with all fields
    tracker_data = []
    for t in trackers:
        project = get_project_from_jira_key(t.jira_key)
        created = format_date(t.created_date)
        due = format_date(t.due_date)
        sla = format_date(t.sla_date)

        projects.add(project)
        created_dates.add(created)
        due_dates.add(due)
        sla_dates.add(sla)

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
    # Project -> Created Date
    proj_to_created = defaultdict(int)
    # Created Date -> Due Date
    created_to_due = defaultdict(int)
    # Due Date -> SLA Date
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

    return {
        "labels": labels,
        "sources": sources,
        "targets": targets,
        "values": values,
        "tracker_count": len(trackers),
    }


def create_sankey_diagram(cve_id: str):
    """Create and display a Sankey diagram for the CVE."""

    app = create_app()

    with app.app_context():
        data = build_sankey_data(cve_id)

        if data is None:
            return

        # Define colors for each column
        colors = []
        for label in data["labels"]:
            if label.startswith("Proj:"):
                colors.append("rgba(31, 119, 180, 0.8)")  # Blue
            elif label.startswith("Created:"):
                colors.append("rgba(255, 127, 14, 0.8)")  # Orange
            elif label.startswith("Due:"):
                colors.append("rgba(44, 160, 44, 0.8)")   # Green
            else:  # SLA
                colors.append("rgba(214, 39, 40, 0.8)")   # Red

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=data["labels"],
                color=colors,
            ),
            link=dict(
                source=data["sources"],
                target=data["targets"],
                value=data["values"],
                color="rgba(150, 150, 150, 0.4)",
            )
        )])

        fig.update_layout(
            title=dict(
                text=f"CVE Tracker Flow: {cve_id}<br><sub>{data['tracker_count']} trackers</sub>",
                font=dict(size=16),
            ),
            font=dict(size=12),
            height=600,
        )

        # Save to HTML file
        output_file = f"/Users/bdettelb/dev/caseload/prototypes/sankey_{cve_id.replace('-', '_')}.html"
        fig.write_html(output_file)
        print(f"Sankey diagram saved to: {output_file}")

        # Also show in browser
        fig.show()


if __name__ == "__main__":
    cve_id = "CVE-2025-61729"

    if len(sys.argv) > 1:
        cve_id = sys.argv[1]

    print(f"Generating Sankey diagram for {cve_id}...")
    create_sankey_diagram(cve_id)
