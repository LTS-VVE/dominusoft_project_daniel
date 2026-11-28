from django.contrib import admin

from .models import BlockTemplate, DataBlock, SavedView, SchemaSnapshot, Workspace


class DataBlockInline(admin.TabularInline):
    model = DataBlock
    extra = 0
    fields = ["name", "position", "width"]


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "created_at"]
    inlines = [DataBlockInline]


@admin.register(DataBlock)
class DataBlockAdmin(admin.ModelAdmin):
    list_display = ["name", "workspace", "source_key", "updated_at"]


admin.site.register(SavedView)
admin.site.register(BlockTemplate)
admin.site.register(SchemaSnapshot)
