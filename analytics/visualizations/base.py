"""Abstract base class for visualizations."""

from abc import ABC, abstractmethod
from typing import Any


class Visualization(ABC):
    """Abstract base class for chart types.

    Renders data to HTML or JSON for frontend display.
    """

    @property
    @abstractmethod
    def viz_type(self) -> str:
        """Return the visualization type identifier."""
        pass

    @abstractmethod
    def render_json(self, data: Any, **options) -> str:
        """Render data to Plotly JSON.

        Args:
            data: Input data (DataFrame, dict, etc.)
            **options: Visualization-specific options.

        Returns:
            JSON string for Plotly.
        """
        pass

    @abstractmethod
    def render_html(self, data: Any, **options) -> str:
        """Render data to embeddable HTML.

        Args:
            data: Input data (DataFrame, dict, etc.)
            **options: Visualization-specific options.

        Returns:
            HTML string with embedded chart.
        """
        pass
