"""Auto-discovery registry for analytics metrics."""

from typing import Type
from analytics.base import AnalyticsMetric


class AnalyticsRegistry:
    """Registry for analytics metric implementations."""

    _metrics: dict[str, Type[AnalyticsMetric]] = {}

    @classmethod
    def register(cls, metric_class: Type[AnalyticsMetric]) -> Type[AnalyticsMetric]:
        """Register an analytics metric class.

        Use as a decorator:
            @AnalyticsRegistry.register
            class MyMetric(AnalyticsMetric):
                ...

        Args:
            metric_class: AnalyticsMetric subclass to register.

        Returns:
            The registered class (for decorator use).
        """
        metric_id = metric_class.metric_id.fget(None)  # type: ignore
        if metric_id is None:
            raise ValueError(
                f"{metric_class.__name__} must define metric_id property"
            )
        cls._metrics[metric_id] = metric_class
        return metric_class

    @classmethod
    def get(cls, metric_id: str) -> Type[AnalyticsMetric] | None:
        """Get a registered metric class by ID.

        Args:
            metric_id: The metric identifier.

        Returns:
            The AnalyticsMetric subclass or None if not found.
        """
        return cls._metrics.get(metric_id)

    @classmethod
    def get_by_category(cls, category: str) -> list[Type[AnalyticsMetric]]:
        """Get all metrics in a category.

        Args:
            category: Category name ('trends' or 'impact').

        Returns:
            List of AnalyticsMetric subclasses in the category.
        """
        result = []
        for metric_class in cls._metrics.values():
            cat = metric_class.category.fget(None)  # type: ignore
            if cat == category:
                result.append(metric_class)
        return result

    @classmethod
    def get_all(cls) -> dict[str, Type[AnalyticsMetric]]:
        """Get all registered metrics.

        Returns:
            Dictionary mapping metric IDs to classes.
        """
        return cls._metrics.copy()

    @classmethod
    def list_ids(cls) -> list[str]:
        """List all registered metric IDs.

        Returns:
            List of registered metric identifiers.
        """
        return list(cls._metrics.keys())

    @classmethod
    def discover(cls) -> None:
        """Import all metric modules to trigger registration.

        Call this during application startup to ensure all metrics
        are registered.
        """
        # Import metric modules to trigger @register decorators
        try:
            import analytics.trends  # noqa: F401
        except ImportError:
            pass
        try:
            import analytics.impact  # noqa: F401
        except ImportError:
            pass
