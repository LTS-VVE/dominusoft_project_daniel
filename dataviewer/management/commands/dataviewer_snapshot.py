from django.core.management.base import BaseCommand

from dataviewer.schema import take_snapshot


class Command(BaseCommand):
    help = "Store a snapshot of all registered Data Viewer models."

    def add_arguments(self, parser):
        parser.add_argument("--label", default="")

    def handle(self, *args, **options):
        snap = take_snapshot(label=options["label"])
        self.stdout.write(self.style.SUCCESS(f"Saved snapshot #{snap.pk} with {len(snap.data)} models."))
