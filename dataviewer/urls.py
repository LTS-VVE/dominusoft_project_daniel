from django.urls import path

from . import views

app_name = "dataviewer"

urlpatterns = [
    path("explore/", views.explorer_home, name="explorer"),
    path("explore/<str:source_key>/", views.model_detail, name="model_detail"),
    path("explore/<str:source_key>/records/", views.records, name="records"),
    path("explore/<str:source_key>/records/<int:pk>/", views.record_detail, name="record_detail"),
    
    path("", views.workspace_detail, name="home"),
    path("workspace/<int:pk>/", views.workspace_detail, name="workspace"),
    path("workspace/<int:workspace_pk>/blocks/new/", views.block_create, name="block_create"),
    path("workspace/<int:workspace_pk>/templates/<int:template_pk>/use/",
         views.block_from_template, name="block_from_template"),
    path("blocks/<int:pk>/", views.block_detail, name="block_detail"),
    path("blocks/<int:pk>/edit/", views.block_edit, name="block_edit"),
    path("blocks/<int:pk>/duplicate/", views.block_duplicate, name="block_duplicate"),
    path("blocks/<int:pk>/delete/", views.block_delete, name="block_delete"),
    
    path("blocks/<int:pk>/views/save/", views.view_save, name="view_save"),
    path("views/<int:pk>/delete/", views.view_delete, name="view_delete"),
    path("workspace/<int:pk>/layout/", views.workspace_layout, name="workspace_layout"),
    
    path("blocks/<int:pk>/export/config/", views.export_config, name="export_config"),
    path("blocks/<int:pk>/export/<str:fmt>/", views.export_data, name="export_data"),
    path("blocks/<int:pk>/export-code/", views.export_code, name="export_code"),
    path("workspace/<int:workspace_pk>/import/", views.import_config, name="import_config"),
    
    path("api/blocks/<int:pk>/data/", views.api_block_data, name="api_block_data"),
    path("schema/snapshots/", views.snapshot_list, name="snapshots"),
    path("external/<str:alias>/", views.external_db, name="external_db"),
]
