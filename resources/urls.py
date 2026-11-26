from django.urls import path

from . import views

app_name = "resources"

urlpatterns = [
    path("", views.resource_list, name="list"),
    path("sugjero/", views.resource_suggest, name="suggest"),
    path("e-re/", views.resource_create, name="create"),
    path("<int:pk>/ndrysho/", views.resource_edit, name="edit"),
]
