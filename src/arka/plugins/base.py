from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any


class ArkaPlugin(ABC):
    """
    Base class for ARKA plugins.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The machine-readable name of the plugin."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """The version of the plugin."""
        ...

    @property
    @abstractmethod
    def django_app(self) -> str:
        """The full path to the Django AppConfig (e.g., 'pymap.apps.PymapConfig')."""
        ...

    def get_urls(self) -> Optional[Tuple[str, str]]:
        """
        Returns a tuple of (url_module, namespace) if the plugin provides URLs.
        Example: ('pymap.urls', 'pymap')
        """
        return None

    def on_enable(self) -> None:
        """
        Logic to execute when the plugin is enabled.
        """
        pass

    def on_disable(self) -> None:
        """
        Logic to execute when the plugin is disabled.
        """
        pass

    def health_check(self) -> Dict[str, Any]:
        """
        Optional health check for the plugin.
        """
        return {"status": "ok"}
