"""Registry for data sources."""

from typing import Type
from data.sources.base import DataSource


class SourceRegistry:
    """Registry for data source implementations."""

    _sources: dict[str, Type[DataSource]] = {}

    @classmethod
    def register(cls, source_class: Type[DataSource]) -> Type[DataSource]:
        """Register a data source class.

        Can be used as a decorator:
            @SourceRegistry.register
            class MyDataSource(DataSource):
                ...

        Args:
            source_class: DataSource subclass to register.

        Returns:
            The registered class (for decorator use).
        """
        # Create a temporary instance to get the source_type
        # This requires the class to be instantiable without args
        # or we need to use a class attribute instead
        source_type = getattr(source_class, "SOURCE_TYPE", None)
        if source_type is None:
            raise ValueError(
                f"{source_class.__name__} must define SOURCE_TYPE class attribute"
            )
        cls._sources[source_type] = source_class
        return source_class

    @classmethod
    def get(cls, source_type: str) -> Type[DataSource] | None:
        """Get a registered data source class by type.

        Args:
            source_type: The source type identifier.

        Returns:
            The DataSource subclass or None if not found.
        """
        return cls._sources.get(source_type)

    @classmethod
    def get_all(cls) -> dict[str, Type[DataSource]]:
        """Get all registered data sources.

        Returns:
            Dictionary mapping source types to classes.
        """
        return cls._sources.copy()

    @classmethod
    def list_types(cls) -> list[str]:
        """List all registered source types.

        Returns:
            List of registered source type identifiers.
        """
        return list(cls._sources.keys())
