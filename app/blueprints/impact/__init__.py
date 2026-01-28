"""Impact blueprint - Vulnerability Impact (per-CVE blast radius)."""

from flask import Blueprint, render_template, request

bp = Blueprint("impact", __name__)


@bp.route("/")
def index():
    """Vulnerability Impact dashboard."""
    from app.models import CVE

    # Get recent CVEs for quick access
    recent_cves = CVE.query.order_by(CVE.created_at.desc()).limit(10).all()

    return render_template("impact/index.html", recent_cves=recent_cves)


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
