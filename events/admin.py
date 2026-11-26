from django.contrib import admin

from .models import Event, RSVP


class RSVPInline(admin.TabularInline):
    model = RSVP
    extra = 0
    readonly_fields = ["created_at"]


@admin.action(description="Publish selected events")
def publish(modeladmin, request, queryset):
    queryset.update(is_published=True)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "starts_at", "location", "capacity", "is_published"]
    list_filter = ["is_published"]
    search_fields = ["title", "description", "location"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [RSVPInline]
    actions = [publish]

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
