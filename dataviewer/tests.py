import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse

from tickets.models import Category, Ticket

from . import codegen, schema
from .models import DataBlock, Workspace
from .query import ConfigError, build_queryset, clean_config
from .registry import get_source

User = get_user_model()


class Fixtures(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("admin", "a@example.com", "pass")
        cls.viewer = User.objects.create_user("viewer", password="pass")
        cls.viewer.user_permissions.add(Permission.objects.get(codename="view_ticket"))
        cls.nobody = User.objects.create_user("nobody", password="pass")
        cat = Category.objects.create(name="Hardware")
        for i in range(30):
            Ticket.objects.create(title=f"Ticket {i}", status="open" if i % 2 else "closed",
                                  category=cat, created_by=cls.admin)


class RegistryTests(TestCase):
    def test_password_never_exposed(self):
        source = get_source("accounts.User")
        self.assertNotIn("password", source.fields)

    def test_unregistered_model_rejected(self):
        with self.assertRaises(LookupError):
            get_source("auth.Permission")


class ConfigTests(Fixtures):
    def setUp(self):
        self.source = get_source("tickets.Ticket")

    def test_unknown_field(self):
        with self.assertRaises(ConfigError):
            clean_config({"fields": ["title", "nope"]}, self.source)

    def test_relation_traversal_blocked(self):
        with self.assertRaises(ConfigError):
            clean_config({"filters": {"created_by__password": "x"}}, self.source)

    def test_bad_lookup(self):
        with self.assertRaises(ConfigError):
            clean_config({"filters": {"title__regex": ".*"}}, self.source)

    def test_page_size_clamped(self):
        self.assertEqual(clean_config({"pagination": 9999}, self.source)["pagination"], 100)

    def test_board_needs_group_by(self):
        with self.assertRaises(ConfigError):
            clean_config({"display": "board"}, self.source)

    def test_filter_and_order(self):
        _, _, qs = build_queryset(self.admin, {"source": "tickets.Ticket", "filters": {"status": "open"},
                                               "ordering": "title"})
        self.assertEqual(qs.count(), 15)

    def test_bad_filter_value(self):
        with self.assertRaises(ConfigError):
            build_queryset(self.admin, {"source": "tickets.Ticket", "filters": {"id": "abc"}})

    def test_permission_checked(self):
        with self.assertRaises(PermissionDenied):
            build_queryset(self.nobody, {"source": "tickets.Ticket"})


class ExplorerViewTests(Fixtures):
    def test_login_required(self):
        response = self.client.get(reverse("dataviewer:explorer"))
        self.assertEqual(response.status_code, 302)

    def test_viewer_sees_only_allowed_sources(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("dataviewer:explorer"))
        self.assertContains(response, "tickets.Ticket")
        self.assertNotContains(response, "events.Event")

    def test_records_search_sort_page(self):
        self.client.force_login(self.admin)
        url = reverse("dataviewer:records", args=["tickets.Ticket"])
        response = self.client.get(url, {"q": "Ticket 1", "sort": "title", "page": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total"], 11)  # Ticket 1, 10..19

    def test_forbidden_source(self):
        self.client.force_login(self.nobody)
        response = self.client.get(reverse("dataviewer:records", args=["tickets.Ticket"]))
        self.assertEqual(response.status_code, 403)

    def test_record_inspector(self):
        self.client.force_login(self.admin)
        ticket = Ticket.objects.first()
        response = self.client.get(reverse("dataviewer:record_detail", args=["tickets.Ticket", ticket.pk]))
        self.assertContains(response, ticket.title)

    def test_model_detail(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dataviewer:model_detail", args=["tickets.Ticket"]))
        self.assertContains(response, "ForeignKey")


class BlockTests(Fixtures):
    def setUp(self):
        self.workspace = Workspace.objects.create(owner=self.admin, name="Main")
        self.block = self.workspace.blocks.create(name="Open Tickets", config={
            "source": "tickets.Ticket", "fields": ["id", "title", "status"],
            "filters": {"status": "open"}, "ordering": "-id", "display": "table", "pagination": 10,
        })

    def test_workspace_renders_all_displays(self):
        self.workspace.blocks.create(name="Board", config={"source": "tickets.Ticket", "display": "board",
                                                            "group_by": "status"})
        self.workspace.blocks.create(name="Chart", config={"source": "tickets.Ticket", "display": "chart",
                                                            "group_by": "category"})
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dataviewer:workspace", args=[self.workspace.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hardware")

    def test_other_users_cannot_open_block(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("dataviewer:block_detail", args=[self.block.pk]))
        self.assertEqual(response.status_code, 404)

    def test_edit_block(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("dataviewer:block_edit", args=[self.block.pk]), {
            "name": "Closed", "columns": ["id", "title"], "ordering": "title", "display": "table",
            "pagination": 5, "filters": '{"status": "closed"}',
        })
        self.assertEqual(response.status_code, 302)
        self.block.refresh_from_db()
        self.assertEqual(self.block.config["filters"], {"status__exact": "closed"})

    def test_edit_rejects_bad_filter(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("dataviewer:block_edit", args=[self.block.pk]), {
            "name": "X", "columns": ["id"], "display": "table", "pagination": 5,
            "filters": '{"created_by__password": "x"}',
        })
        self.assertEqual(response.status_code, 200)
        self.block.refresh_from_db()
        self.assertEqual(self.block.name, "Open Tickets")

    def test_saved_view(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("dataviewer:view_save", args=[self.block.pk]),
                         {"name": "No status", "hide": ["status"], "sort": "title"})
        view = self.block.views.get()
        response = self.client.get(reverse("dataviewer:block_detail", args=[self.block.pk]), {"view": view.pk})
        self.assertEqual(response.context["cfg"]["fields"], ["id", "title"])

    def test_layout_endpoint(self):
        other = self.workspace.blocks.create(name="B", config={"source": "tickets.Ticket"})
        self.client.force_login(self.admin)
        url = reverse("dataviewer:workspace_layout", args=[self.workspace.pk])
        response = self.client.post(url, json.dumps({"order": [other.pk, self.block.pk], "widths": {other.pk: 6}}),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)
        other.refresh_from_db()
        self.assertEqual((other.position, other.width), (0, 6))

    def test_export_csv_and_json(self):
        self.client.force_login(self.admin)
        csv_resp = self.client.get(reverse("dataviewer:export_data", args=[self.block.pk, "csv"]))
        body = b"".join(csv_resp.streaming_content).decode()
        self.assertEqual(len(body.strip().splitlines()), 16)  # header + 15 open tickets
        json_resp = self.client.get(reverse("dataviewer:export_data", args=[self.block.pk, "json"]))
        self.assertEqual(len(json_resp.json()), 15)

    def test_config_roundtrip(self):
        self.client.force_login(self.admin)
        exported = self.client.get(reverse("dataviewer:export_config", args=[self.block.pk])).content
        from django.core.files.uploadedfile import SimpleUploadedFile
        upload = SimpleUploadedFile("block.json", exported, content_type="application/json")
        response = self.client.post(reverse("dataviewer:import_config", args=[self.workspace.pk]), {"file": upload})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.workspace.blocks.count(), 2)

    def test_api(self):
        self.client.force_login(self.admin)
        data = self.client.get(reverse("dataviewer:api_block_data", args=[self.block.pk])).json()
        self.assertEqual(data["total"], 15)
        self.assertEqual(len(data["results"]), 10)


class CodegenTests(Fixtures):
    def test_generated_python_compiles(self):
        workspace = Workspace.objects.create(owner=self.admin, name="W")
        block = DataBlock.objects.create(workspace=workspace, name="Open tickets!", config=clean_config(
            {"fields": ["id", "title", "category"], "filters": {"status": "open"}}, get_source("tickets.Ticket")))
        files = codegen.generate_files(block, get_source("tickets.Ticket"))
        compile(files["views.py"], "views.py", "exec")
        compile(files["urls.py"], "urls.py", "exec")
        self.assertIn("{% extends", files["templates/tickets/open_tickets.html"])
        self.assertIn("OpenTicketsListView", files["views.py"])


class SchemaTests(TestCase):
    def test_compare_detects_changes(self):
        old = schema.describe_all()
        new = json.loads(json.dumps(old))
        new["tickets.Ticket"]["fields"].append({"name": "priority", "type": "IntegerField"})
        del new["events.RSVP"]
        diff = schema.compare(old, new)
        self.assertEqual(diff["models_removed"], ["events.RSVP"])
        self.assertEqual(diff["models_changed"]["tickets.Ticket"]["added"], ["priority"])
