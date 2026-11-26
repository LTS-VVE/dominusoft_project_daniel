from django.urls import path
from . import views

app_name = "tickets"

urlpatterns = [
    path("tickets/", views.ticket_list, name="ticket_list"),
    path("tickets/create/", views.ticket_create, name="ticket_create"),
    path("tickets/<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("tickets/<int:pk>/edit/", views.ticket_update, name="ticket_update"),
    path("tickets/<int:pk>/comments/", views.comment_create, name="comment_create"),
]
