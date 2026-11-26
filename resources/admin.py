from django.contrib import admin

from .models import Category, Resource


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.action(description="Publish selected resources")
def publish(modeladmin, request, queryset):
    queryset.update(is_published=True)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "kind", "language", "is_free", "is_published", "added_by", "created_at"]
    list_filter = ["is_published", "category", "kind", "language", "is_free"]
    search_fields = ["title", "description", "url"]
    actions = [publish]

    def save_model(self, request, obj, form, change):
        if not obj.added_by_id:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)
