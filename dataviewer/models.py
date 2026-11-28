from django.conf import settings
from django.db import models


class Workspace(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workspaces")
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["owner", "name"], name="unique_workspace_per_owner")]

    def __str__(self):
        return self.name


class DataBlock(models.Model):
    WIDTHS = [(3, "Quarter"), (4, "Third"), (6, "Half"), (8, "Two thirds"), (12, "Full")]

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="blocks")
    name = models.CharField(max_length=100)
    config = models.JSONField(default=dict)
    position = models.PositiveIntegerField(default=0)
    width = models.PositiveSmallIntegerField(choices=WIDTHS, default=12)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return self.name

    @property
    def source_key(self):
        return self.config.get("source", "")


class SavedView(models.Model):
    """Named overrides on top of a block: other filters, sorting, columns or display."""

    block = models.ForeignKey(DataBlock, on_delete=models.CASCADE, related_name="views")
    name = models.CharField(max_length=100)
    overrides = models.JSONField(default=dict)
    search = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def merged_config(self):
        return {**self.block.config, **self.overrides}


class BlockTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    config = models.JSONField(default=dict)
    is_builtin = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SchemaSnapshot(models.Model):
    label = models.CharField(max_length=100, blank=True)
    data = models.JSONField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.label or f"Snapshot {self.created_at:%Y-%m-%d %H:%M}"
