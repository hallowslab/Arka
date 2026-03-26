import logging
from typing import Dict, List, Optional, Type
from importlib.metadata import entry_points
from .base import ArkaPlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Singleton registry for ARKA plugins discovered via entry points.
    """

    _instance: Optional["PluginRegistry"] = None
    _plugins: Dict[str, ArkaPlugin] = {}

    def __new__(cls) -> "PluginRegistry":
        if cls._instance is None:
            cls._instance = super(PluginRegistry, cls).__new__(cls)
        return cls._instance

    def discover(self) -> None:
        """
        Scans for plugins registered under the 'arka.plugins' entry point group.
        """
        eps = entry_points(group="arka.plugins")
        for ep in eps:
            try:
                plugin_instance = ep.load()
                if isinstance(plugin_instance, ArkaPlugin):
                    self._plugins[plugin_instance.name] = plugin_instance
                    logger.info(
                        f"Discovered plugin: {plugin_instance.name} (version {plugin_instance.version})"
                    )
                else:
                    logger.warning(
                        f"Entry point {ep.name} did not provide an ArkaPlugin instance."
                    )
            except Exception as e:
                logger.error(f"Failed to load plugin from entry point {ep.name}: {e}")

    def get_plugins(self) -> List[ArkaPlugin]:
        """Returns all discovered plugins."""
        return list(self._plugins.values())

    def get_plugin(self, name: str) -> Optional[ArkaPlugin]:
        """Retrieves a specific plugin by name."""
        return self._plugins.get(name)

    def get_enabled_plugins(self) -> List[ArkaPlugin]:
        """
        Returns plugins that are currently enabled in the database.
        Note: This requires Django app registry to be ready.
        """
        from django.db import connection

        # Check if table exists to avoid errors during initial migrations
        if "arka_moduleconfig" not in connection.introspection.table_names():
            return []

        from .models import ModuleConfig

        enabled_names = ModuleConfig.objects.filter(enabled=True).values_list(
            "name", flat=True
        )
        return [p for name, p in self._plugins.items() if name in enabled_names]


registry = PluginRegistry()
