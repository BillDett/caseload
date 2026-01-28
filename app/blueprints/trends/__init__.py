"""Trends blueprint - Vulnerability Trends (org-wide analytics)."""

from flask import Blueprint, render_template, request

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
