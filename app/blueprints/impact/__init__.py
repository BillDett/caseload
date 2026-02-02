"""Impact blueprint - Vulnerability Impact (per-CVE blast radius)."""

from flask import Blueprint, render_template, request

bp = Blueprint("impact", __name__)


@bp.route("/")
def index():
    """Vulnerability Impact dashboard."""
    from sqlalchemy import func

    from app.extensions import db
    from app.models import CVE, Tracker

    page = request.args.get("page", 1, type=int)
    per_page = 20

    # Get CVEs sorted by most recent tracker created_date (descending)
    # Subquery to get max created_date per CVE
    max_created_subq = (
        db.session.query(
            Tracker.cve_id,
            func.max(Tracker.created_date).label("max_created")
        )
        .group_by(Tracker.cve_id)
        .subquery()
    )

    # Join CVEs with the subquery and order by max created_date
    pagination = (
        db.session.query(CVE)
        .join(max_created_subq, CVE.id == max_created_subq.c.cve_id)
        .order_by(max_created_subq.c.max_created.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return render_template(
        "impact/index.html",
        recent_cves=pagination.items,
        pagination=pagination,
    )


@bp.route("/cve/<cve_id>")
def cve_detail(cve_id: str):
    """Display blast radius for a specific CVE."""
    from analytics.registry import AnalyticsRegistry

    AnalyticsRegistry.discover()
    metric_class = AnalyticsRegistry.get("blast_radius")

    if not metric_class:
        return render_template("errors/404.html", message="Metric not found"), 404

    metric_instance = metric_class()
    result = metric_instance.compute(cve_id=cve_id)

    return render_template(
        "impact/cve_detail.html",
        cve_id=cve_id,
        result=result,
    )


@bp.route("/search")
def search():
    """Search for a CVE by ID."""
    cve_id = request.args.get("q", "").strip().upper()

    if not cve_id:
        return render_template("impact/index.html", error="Please enter a CVE ID")

    from app.models import CVE

    cve = CVE.query.filter_by(cve_id=cve_id).first()

    if cve:
        from flask import redirect, url_for

        return redirect(url_for("impact.cve_detail", cve_id=cve_id))

    return render_template(
        "impact/index.html",
        error=f"CVE {cve_id} not found in the database",
    )
