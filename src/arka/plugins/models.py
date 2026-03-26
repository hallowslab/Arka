from django.db import models


class ModuleConfig(models.Model):
    """
    Configuration and enabled status for ARKA plugins.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The plugin name as defined in ArkaPlugin.name",
    )
    enabled = models.BooleanField(default=False)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        status = "Enabled" if self.enabled else "Disabled"
        return f"{self.name} ({status})"

    class Meta:
        verbose_name = "Module Configuration"
        verbose_name_plural = "Module Configurations"
        db_table = "arka_moduleconfig"
