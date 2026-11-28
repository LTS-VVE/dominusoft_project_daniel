from django.core.management.base import BaseCommand

from dataviewer.models import BlockTemplate
from dataviewer.query import ConfigError, clean_config
from dataviewer.registry import UnknownSource, get_source

BUILTINS = [
    {
        "name": "Ticket Explorer",
        "description": "All tickets, newest first.",
        "config": {"source": "tickets.Ticket", "display": "table", "ordering": "-created_at", "pagination": 25,
                   "fields": ["id", "title", "status", "category", "created_by", "created_at"]},
    },
    {
        "name": "Ticket Board",
        "description": "Tickets grouped by status.",
        "config": {"source": "tickets.Ticket", "display": "board", "group_by": "status",
                   "fields": ["id", "title", "category", "created_by"]},
    },
    {
        "name": "Tickets per Category",
        "description": "Bar chart of ticket counts per category.",
        "config": {"source": "tickets.Ticket", "display": "chart", "group_by": "category", "fields": ["category"]},
    },
    {
        "name": "Event Explorer",
        "description": "Upcoming and past events.",
        "config": {"source": "events.Event", "display": "table", "ordering": "-starts_at",
                   "fields": ["id", "title", "starts_at", "location"]},
    },
    {
        "name": "Knowledge Explorer",
        "description": "Articles by category.",
        "config": {"source": "knowledge.Article", "display": "table", "fields": ["id", "title", "category"]},
    },
    {
        "name": "Resource Explorer",
        "description": "Shared links and tools.",
        "config": {"source": "resources.Resource", "display": "cards", "fields": ["id", "title", "category"]},
    },
    {
        "name": "RSVPs",
        "description": "Who is going where.",
        "config": {"source": "events.RSVP", "display": "table", "fields": ["id", "event", "user", "going"]},
    },
]


class Command(BaseCommand):
    help = "Create or update the built-in block templates."

    def handle(self, *args, **options):
        ready = 0
        for item in BUILTINS:
            # Validate first, so a field name that doesn't match your models is reported, not saved.
            try:
                config = clean_config(item["config"], get_source(item["config"]["source"]))
            except (ConfigError, UnknownSource) as exc:
                self.stderr.write(f"Skipped {item['name']}: {exc}")
                continue
            BlockTemplate.objects.update_or_create(
                name=item["name"],
                defaults={"description": item["description"], "config": config, "is_builtin": True},
            )
            ready += 1
        self.stdout.write(self.style.SUCCESS(f"{ready} built-in templates ready."))
