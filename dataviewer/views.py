from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from .introspect import describe_source
from .query import ConfigError, board_columns, build_queryset, build_rows, chart_data, paginate
from .registry import UnknownSource, get_source, sources_for
import json
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from .forms import BlockConfigForm, BlockCreateForm, SavedViewForm
from .models import BlockTemplate, DataBlock, SavedView, Workspace
from .query import clean_config
import csv
from django.http import HttpResponse, StreamingHttpResponse
from django.utils.text import slugify
from . import codegen
from .forms import ImportConfigForm
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connections
from . import schema
from .models import SchemaSnapshot


# Helpers

def get_source_or_404(user, key):
    try:
        source = get_source(key)
    except UnknownSource:
        raise Http404("Unknown data source")
    if not user.has_perm(source.view_perm):
        raise PermissionDenied
    return source


def block_context(user, config, params):
    """Everything a block template needs, for any display type."""
    search = params.get("q", "").strip()
    sort = params.get("sort", "")
    source, cfg, qs = build_queryset(user, config, search=search, sort=sort)
    ctx = {"source": source, "cfg": cfg, "search": search, "sort": sort or cfg["ordering"], "total": qs.count()}

    if cfg["display"] == "board":
        ctx["columns"] = board_columns(source, cfg, qs)
    elif cfg["display"] == "chart":
        ctx["chart"] = chart_data(source, cfg, qs)
    else:
        page = paginate(qs, cfg["pagination"], params.get("page"))
        ctx["page"] = page
        ctx["rows"] = build_rows(page.object_list, cfg["fields"])
    return ctx


def own_block(request, pk):
    return get_object_or_404(DataBlock, pk=pk, workspace__owner=request.user)


def default_workspace(user):
    workspace, _ = Workspace.objects.get_or_create(owner=user, name="My workspace")
    return workspace


# Model Explorer

@login_required
def explorer_home(request):
    sources = [{"source": s, "count": s.model._default_manager.count()} for s in sources_for(request.user)]
    return render(request, "dataviewer/explorer_home.html", {"sources": sources})


@login_required
def model_detail(request, source_key):
    source = get_source_or_404(request.user, source_key)
    return render(request, "dataviewer/model_detail.html", {"source": source, "info": describe_source(source)})


@login_required
def records(request, source_key):
    source = get_source_or_404(request.user, source_key)
    ctx = block_context(request.user, {"source": source.key, "pagination": 25}, request.GET)
    return render(request, "dataviewer/records.html", ctx)


@login_required
def record_detail(request, source_key, pk):
    """Record Inspector: all registered fields plus related records (Phase 5)."""
    source = get_source_or_404(request.user, source_key)
    obj = get_object_or_404(source.model._default_manager, pk=pk)
    cells = build_rows([obj], list(source.fields))[0]["cells"]
    fields = list(zip(source.fields, cells))

    related = []
    for rel in source.model._meta.related_objects:
        target_key = rel.related_model._meta.label
        try:
            target = get_source(target_key)
        except UnknownSource:
            continue
        if not request.user.has_perm(target.view_perm):
            continue
        if rel.one_to_one:
            continue
        qs = getattr(obj, rel.get_accessor_name()).all()
        related.append({"source": target, "via": rel.field.name, "total": qs.count(), "items": qs[:20]})

    return render(request, "dataviewer/record_detail.html",
                  {"source": source, "obj": obj, "fields": fields, "related": related})


# Blocks

@login_required
def workspace_detail(request, pk=None):
    if pk is None:
        workspace = default_workspace(request.user)
    else:
        workspace = get_object_or_404(Workspace, pk=pk, owner=request.user)

    blocks = []
    for block in workspace.blocks.all():
        try:
            ctx = block_context(request.user, block.config, {})
            blocks.append({"block": block, **ctx})
        except (ConfigError, PermissionDenied, UnknownSource) as exc:
            blocks.append({"block": block, "error": str(exc) or "No access to this source."})

    return render(request, "dataviewer/workspace.html", {
        "workspace": workspace,
        "workspaces": request.user.workspaces.all(),
        "blocks": blocks,
        "templates": BlockTemplate.objects.all(),
        "widths": DataBlock.WIDTHS,
    })


@login_required
def block_create(request, workspace_pk):
    workspace = get_object_or_404(Workspace, pk=workspace_pk, owner=request.user)
    form = BlockCreateForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        source = get_source_or_404(request.user, form.cleaned_data["source"])
        block = workspace.blocks.create(
            name=form.cleaned_data["name"],
            config={"source": source.key, "fields": list(source.fields), "display": "table", "pagination": 25},
            position=workspace.blocks.count(),
        )
        return redirect("dataviewer:block_edit", pk=block.pk)
    return render(request, "dataviewer/block_create.html", {"form": form, "workspace": workspace})


@login_required
def block_edit(request, pk):
    block = own_block(request, pk)
    source = get_source_or_404(request.user, block.source_key)
    initial = BlockConfigForm.initial_from_config(block.name, block.config)
    form = BlockConfigForm(request.POST or None, source=source, initial=initial)
    if request.method == "POST" and form.is_valid():
        block.name = form.cleaned_data["name"]
        block.config = {**form.config, "column_widths": block.config.get("column_widths", {})}
        block.save()
        messages.success(request, "Block saved.")
        return redirect("dataviewer:block_detail", pk=block.pk)
    return render(request, "dataviewer/block_edit.html", {"form": form, "data_block": block, "source": source})


@login_required
def block_detail(request, pk):
    block = own_block(request, pk)
    config = block.config
    params = request.GET.copy()
    active_view = None
    if params.get("view"):
        active_view = get_object_or_404(SavedView, pk=params["view"], block=block)
        config = active_view.merged_config()
        params.setdefault("q", active_view.search)
    try:
        ctx = block_context(request.user, config, params)
    except ConfigError as exc:
        messages.error(request, f"This block's config is broken: {exc}")
        return redirect("dataviewer:block_edit", pk=block.pk)
    ctx.update({"data_block": block, "views": block.views.all(), "active_view": active_view,
                "view_form": SavedViewForm()})
    return render(request, "dataviewer/block_detail.html", ctx)


@login_required
@require_POST
def block_duplicate(request, pk):
    block = own_block(request, pk)
    copy = DataBlock.objects.create(
        workspace=block.workspace, name=f"{block.name} (copy)"[:100],
        config=block.config, width=block.width, position=block.workspace.blocks.count(),
    )
    return redirect("dataviewer:block_edit", pk=copy.pk)


@login_required
@require_POST
def block_delete(request, pk):
    block = own_block(request, pk)
    workspace_pk = block.workspace_id
    block.delete()
    messages.success(request, "Block deleted.")
    return redirect("dataviewer:workspace", pk=workspace_pk)


@login_required
@require_POST
def block_from_template(request, workspace_pk, template_pk):
    workspace = get_object_or_404(Workspace, pk=workspace_pk, owner=request.user)
    template = get_object_or_404(BlockTemplate, pk=template_pk)
    source = get_source_or_404(request.user, template.config.get("source", ""))
    try:
        config = clean_config(template.config, source)
    except ConfigError as exc:
        messages.error(request, f"Template is broken: {exc}")
        return redirect("dataviewer:workspace", pk=workspace.pk)
    workspace.blocks.create(name=template.name, config=config, position=workspace.blocks.count())
    return redirect("dataviewer:workspace", pk=workspace.pk)


# Saved views & Layout

@login_required
@require_POST
def view_save(request, pk):
    block = own_block(request, pk)
    form = SavedViewForm(request.POST)
    if form.is_valid():
        overrides = {}
        sort = request.POST.get("sort", "")
        if sort:
            overrides["ordering"] = sort
        hidden = request.POST.getlist("hide")
        if hidden:
            overrides["fields"] = [f for f in block.config.get("fields", []) if f not in hidden]
        SavedView.objects.create(block=block, name=form.cleaned_data["name"],
                                 overrides=overrides, search=request.POST.get("q", "")[:200])
        messages.success(request, "View saved.")
    return redirect("dataviewer:block_detail", pk=block.pk)


@login_required
@require_POST
def view_delete(request, pk):
    view = get_object_or_404(SavedView, pk=pk, block__workspace__owner=request.user)
    block_pk = view.block_id
    view.delete()
    return redirect("dataviewer:block_detail", pk=block_pk)


@login_required
@require_POST
def workspace_layout(request, pk):
    """Receives {"order": [ids...]} and/or {"widths": {"id": 6}} from the drag-and-drop JS."""
    workspace = get_object_or_404(Workspace, pk=pk, owner=request.user)
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "bad json"}, status=400)

    blocks = {b.pk: b for b in workspace.blocks.all()}
    valid_widths = {w for w, _ in DataBlock.WIDTHS}

    for position, block_id in enumerate(payload.get("order", [])):
        block = blocks.get(int(block_id))
        if block:
            block.position = position
    for block_id, width in (payload.get("widths") or {}).items():
        block = blocks.get(int(block_id))
        if block and int(width) in valid_widths:
            block.width = int(width)
    DataBlock.objects.bulk_update(blocks.values(), ["position", "width"])
    return JsonResponse({"ok": True})


# Exportation and importation

@login_required
def export_config(request, pk):
    block = own_block(request, pk)
    payload = {"kod_dataviewer": 1, "block": {"name": block.name, "config": block.config}}
    response = HttpResponse(json.dumps(payload, indent=2), content_type="application/json")
    response["Content-Disposition"] = f'attachment; filename="{slugify(block.name) or "block"}.json"'
    return response


@login_required
def import_config(request, workspace_pk):
    workspace = get_object_or_404(Workspace, pk=workspace_pk, owner=request.user)
    form = ImportConfigForm(request.POST or None, request.FILES or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        block = workspace.blocks.create(name=form.block_name, config=form.config,
                                        position=workspace.blocks.count())
        messages.success(request, "Block imported.")
        return redirect("dataviewer:block_detail", pk=block.pk)
    return render(request, "dataviewer/import.html", {"form": form, "workspace": workspace})


class Echo:
    def write(self, value):
        return value


@login_required
def export_data(request, pk, fmt):
    block = own_block(request, pk)
    source, cfg, qs = build_queryset(request.user, block.config,
                                     search=request.GET.get("q", ""), sort=request.GET.get("sort", ""))
    filename = slugify(block.name) or "export"

    def plain(value):
        return value if isinstance(value, (int, float, bool)) or value is None else str(value)

    if fmt == "csv":
        writer = csv.writer(Echo())

        def stream():
            yield writer.writerow(cfg["fields"])
            for row in build_rows(qs.iterator(chunk_size=500), cfg["fields"]):
                yield writer.writerow([c["value"] for c in row["cells"]])

        response = StreamingHttpResponse(stream(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
        return response

    if fmt == "json":
        data = [
            {f: plain(c["value"]) for f, c in zip(cfg["fields"], row["cells"])}
            for row in build_rows(qs[:10_000], cfg["fields"])
        ]
        response = JsonResponse(data, safe=False, json_dumps_params={"indent": 2})
        response["Content-Disposition"] = f'attachment; filename="{filename}.json"'
        return response
    raise Http404


@login_required
def export_code(request, pk):
    block = own_block(request, pk)
    source = get_source_or_404(request.user, block.source_key)
    data = codegen.build_zip(block, source)
    response = HttpResponse(data, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{slugify(block.name) or "block"}_django.zip"'
    return response


# External DB, Schema & API

@login_required
def api_block_data(request, pk):
    block = own_block(request, pk)
    try:
        source, cfg, qs = build_queryset(request.user, block.config,
                                         search=request.GET.get("q", ""), sort=request.GET.get("sort", ""))
    except ConfigError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    page = paginate(qs, cfg["pagination"], request.GET.get("page"))

    def plain(value):
        return value if isinstance(value, (int, float, bool)) or value is None else str(value)

    return JsonResponse({
        "block": block.name,
        "source": source.key,
        "fields": cfg["fields"],
        "page": page.number,
        "pages": page.paginator.num_pages,
        "total": page.paginator.count,
        "results": [
            {f: plain(c["value"]) for f, c in zip(cfg["fields"], row["cells"])}
            for row in build_rows(page.object_list, cfg["fields"])
        ],
    })


@staff_member_required
def snapshot_list(request):
    if request.method == "POST":
        schema.take_snapshot(user=request.user, label=request.POST.get("label", "")[:100])
        messages.success(request, "Snapshot saved.")
        return redirect("dataviewer:snapshots")
    snapshots = SchemaSnapshot.objects.all()[:50]
    diff = None
    a, b = request.GET.get("a"), request.GET.get("b")
    if a and b:
        diff = schema.compare(get_object_or_404(SchemaSnapshot, pk=a).data,
                              get_object_or_404(SchemaSnapshot, pk=b).data)
    return render(request, "dataviewer/snapshots.html", {"snapshots": snapshots, "diff": diff})


@staff_member_required
def external_db(request, alias="external"):
    """Read-only table listing of another database configured in settings.DATABASES."""
    if alias not in connections.databases:
        raise Http404("No such database alias configured.")
    connection = connections[alias]
    with connection.cursor() as cursor:
        tables = []
        for table in connection.introspection.get_table_list(cursor):
            columns = connection.introspection.get_table_description(cursor, table.name)
            tables.append({"name": table.name, "type": table.type,
                           "columns": [{"name": c.name, "null": c.null_ok} for c in columns]})
    return render(request, "dataviewer/external_db.html", {"alias": alias, "tables": tables})
