from django.urls import path

from . import views

app_name = "members"

urlpatterns = [
    path("", views.member_list, name="list"),
    path("<str:username>/", views.member_detail, name="detail"),
    path("<str:username>/ndrysho/", views.member_edit, name="edit"),
]
