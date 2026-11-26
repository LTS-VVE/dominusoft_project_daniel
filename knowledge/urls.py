from django.urls import path

from . import views

app_name = "knowledge"

urlpatterns = [
    path("", views.article_list, name="list"),
    path("e-re/", views.article_create, name="create"),
    path("<slug:slug>/", views.article_detail, name="detail"),
    path("<slug:slug>/ndrysho/", views.article_edit, name="edit"),
]
