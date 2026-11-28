"""Register the models the Data Viewer is allowed to show.

fields=None means "every normal column except sensitive ones".
If a field name below doesn't exist on your model, Django refuses to start
and tells you which one. Fix the name and restart.
"""
from django.contrib.auth import get_user_model

from events.models import RSVP, Event
from knowledge.models import Article
from knowledge.models import Category as KnowledgeCategory
from resources.models import Category as ResourceCategory
from resources.models import Resource
from tickets.models import Category as TicketCategory
from tickets.models import Comment, Ticket

from .registry import register

register(Ticket, search_fields=["title", "description"])
register(TicketCategory, search_fields=["name"], label="Ticket categories")
register(Comment, search_fields=["body"])

register(Event, search_fields=["title", "location"])
register(RSVP)

register(Article, search_fields=["title", "body"])
register(KnowledgeCategory, search_fields=["name"], label="Knowledge categories")

register(Resource, search_fields=["title"])
register(ResourceCategory, search_fields=["name"], label="Resource categories")

# Users: list fields explicitly so nothing private slips through.
register(
    get_user_model(),
    fields=["id", "username", "email", "is_active", "is_staff", "date_joined"],
    search_fields=["username", "email"],
)
