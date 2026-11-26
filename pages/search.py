"""Ranked search over site pages, tickets and comments.

On PostgreSQL: full-text search (weighted, ranked, prefix matching) plus trigram
similarity for typos, accent-insensitive (e matches ë, c matches ç).
On other databases (SQLite) it falls back to a plain icontains search.
"""
import re
import unicodedata

from django.db import connection
from django.db.models import F, Func, Q, TextField, Value
from django.urls import reverse

from tickets.models import Comment, Ticket

MAX_RESULTS = 50
MIN_SIMILARITY = 0.5
MIN_TYPO_LENGTH = 4
CONFIG = "simple"  # PostgreSQL ships no Albanian dictionary

SITE_PAGES = [
    {"title": "Kreu", "url_name": "pages:home", "text": "Njohuri të hapura, teknologji dhe komuniteti digjital."},
    {"title": "Rreth nesh", "url_name": "pages:about", "text": "Misioni, parimet, qasja e hapur, privatësia dhe bashkëpunimi."},
    {"title": "Kontakt", "url_name": "pages:contact", "text": "Na kontakto për pyetje, sugjerime dhe bashkëpunim."},
    {"title": "Statusi i shërbimeve", "url_name": "pages:status", "text": "Statusi dhe monitorimi i shërbimeve të KOD."},
]


class Unaccent(Func):
    function = "UNACCENT"
    output_field = TextField()


def clean(name):
    """Unaccent the column and turn punctuation into spaces, so that
    'CVE-2026-99999' is indexed as the words cve, 2026 and 99999."""
    return Func(
        Unaccent(name), Value("[^[:alnum:]]+"), Value(" "), Value("g"),
        function="REGEXP_REPLACE", output_field=TextField(),
    )


def normalize(text):
    """Lowercase and strip accents so 'Përshëndetje' matches 'pershendetje'."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def search_pages(query):
    terms = normalize(query).split()
    results = []
    for page in SITE_PAGES:
        title, text = normalize(page["title"]), normalize(page["text"])
        score = sum(3 * title.count(t) + text.count(t) for t in terms)
        if score:
            results.append({"title": page["title"], "url": reverse(page["url_name"]), "text": page["text"], "score": score})
    results.sort(key=lambda r: -r["score"])
    return results


def _ranked(qs, fields, terms):
    """fields: list of (field_name, weight). Annotates rank, sim, score and filters.

    Every term must match the beginning of a word ("pri" finds "printer").
    A single longer term also gets typo tolerance through trigram similarity.
    """
    from django.contrib.postgres.search import (
        SearchQuery, SearchRank, SearchVector, TrigramWordSimilarity,
    )

    vector = None
    for name, weight in fields:
        part = SearchVector(clean(name), weight=weight, config=CONFIG)
        vector = part if vector is None else vector + part
    tsquery = SearchQuery(" & ".join(f"{t}:*" for t in terms), config=CONFIG, search_type="raw")

    # "search" is the real full-text match (@@); ts_rank alone is never exactly 0.
    qs = qs.annotate(search=vector, rank=SearchRank(vector, tsquery))
    if len(terms) == 1 and len(terms[0]) >= MIN_TYPO_LENGTH:
        qs = qs.annotate(sim=TrigramWordSimilarity(terms[0], Unaccent(fields[0][0])))
        qs = qs.filter(Q(search=tsquery) | Q(sim__gte=MIN_SIMILARITY))
        qs = qs.annotate(score=F("rank") + F("sim"))
    else:
        qs = qs.filter(search=tsquery).annotate(score=F("rank"))
    return qs.order_by("-score", "-pk")


def _basic(qs, fields, query):
    cond = Q()
    for term in query.lower().split():
        for name in fields:
            cond |= Q(**{f"{name}__icontains": term})
    return qs.filter(cond).order_by("-pk")


def _search_model(qs, fields, terms, use_postgres):
    names = [name for name, _ in fields]
    if use_postgres:
        return list(_ranked(qs, fields, terms)[:MAX_RESULTS])
    return list(_basic(qs, names, " ".join(terms))[:MAX_RESULTS])


def search_all(query, user):
    from accounts.models import Profile
    from events.models import Event
    from knowledge.models import Article
    from resources.models import Resource

    query = query.strip()
    out = {k: [] for k in ("pages", "articles", "events", "resources", "members", "tickets", "comments")}
    if not query or not normalize(query).strip():
        return out

    use_postgres = connection.vendor == "postgresql"
    terms = re.findall(r"\w+", normalize(query))
    if not terms:
        return out

    out["pages"] = search_pages(query)

    # Public content, visible to everyone.
    out["articles"] = _search_model(
        Article.objects.filter(status=Article.Status.PUBLISHED).select_related("category"),
        [("title", "A"), ("summary", "B"), ("body", "C")], terms, use_postgres)
    out["events"] = _search_model(
        Event.objects.filter(is_published=True),
        [("title", "A"), ("description", "B"), ("location", "C")], terms, use_postgres)
    out["resources"] = _search_model(
        Resource.objects.filter(is_published=True).select_related("category"),
        [("title", "A"), ("description", "B")], terms, use_postgres)
    out["members"] = _search_model(
        Profile.objects.filter(is_public=True).select_related("user"),
        [("user__username", "A"), ("display_name", "A"), ("headline", "B"), ("skills", "B"), ("bio", "C")],
        terms, use_postgres)

    # Private content, only for logged-in users and only what they may see.
    if user.is_authenticated:
        tickets = Ticket.objects.select_related("category", "requester")
        comments = Comment.objects.select_related("ticket", "author")
        if not user.is_staff:
            tickets = tickets.filter(requester=user)
            comments = comments.filter(ticket__requester=user)
        out["tickets"] = _search_model(tickets, [("title", "A"), ("description", "B")], terms, use_postgres)
        out["comments"] = _search_model(comments, [("body", "A")], terms, use_postgres)
    return out
