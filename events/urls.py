from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.event_list, name="list"),
    path("e-re/", views.event_create, name="create"),
    path("<slug:slug>/", views.event_detail, name="detail"),
    path("<slug:slug>/ndrysho/", views.event_edit, name="edit"),
    path("<slug:slug>/rsvp/", views.event_rsvp, name="rsvp"),
]
