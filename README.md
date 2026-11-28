# KOD
> [!CAUTION]
> This branch is for testing. Features and data may change or be removed.

**Komuniteti Open Digjital** is a Django web app for running a small tech community. It brings events, a knowledge base, shared resources, and support tickets together in one place.

<p align="center">
  <img src="https://rc3yoc3okr.ufs.sh/f/DI2tWmZ5VtZTiPvEo2YDhpLyjJmvQZPsgFB1He85S4lo306K" alt="KOD demo" width="350">
</p>

## Features

- **Accounts:** sign-up, login, and user profiles
- **Events:** publish events and manage RSVPs
- **Knowledge base:** organize articles into categories
- **Resources:** share useful links, tools, and files
- **Support tickets:** create tickets, comment, and track status
- **KOD Data Viewer:** explore app data in the browser using configurable views

The Data Viewer is being developed in its own Django app, `dataviewer`. It is intended to provide a visual way to inspect registered models and browse records, with saved view settings and export options.

## Apps

| App | Models | Purpose |
| --- | --- | --- |
| `accounts` | `User`, `Profile` | User accounts and profiles |
| `events` | `Event`, `RSVP` | Community events and attendance |
| `knowledge` | `Category`, `Article` | Articles and guides |
| `resources` | `Category`, `Resource` | Shared links, tools, and files |
| `tickets` | `Category`, `Ticket`, `Comment` | Support tickets and comments |
| `pages` | — | Home, about, contact, and other pages |

> [!IMPORTANT] 
> TO BE ADDED

| App | Models | Purpose |
| --- | --- | --- |
| `dataviewer` | `Workspace`, `DataBlock`, `SavedView`, `BlockTemplate`, `SchemaSnapshot` | Data exploration and saved view configurations |

The project uses a custom user model in `accounts`. On a fresh database, run all migrations from the beginning.

## KOD Data Viewer

The Data Viewer lets users configure ways to explore existing Django models. A data block stores a model source and view settings; it does not create a new model.

A block can be configured with fields, filters, ordering, search, and pagination. Supported display ideas include tables, lists or cards, boards, charts, and record inspection.

Example configuration:

```json
{
  "name": "Open Tickets",
  "source": "tickets.Ticket",
  "display": "table",
  "fields": ["id", "title", "status", "created\_at"],
  "filters": {
    "status": "open"
  },
  "ordering": "-created\_at",
  "pagination": 25
}
```

## Setup

```bash
git clone <REPOSITORY_URL>
cd dominusoft_project_daniel
python -m venv venv
source venv/bin/activate          # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env              # then fill it in
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
 
Open http://127.0.0.1:8000/
 
## Configuration
 
Settings come from `.env`. You'll need at least:
 
* `SECRET_KEY`
* `DEBUG`
* `ALLOWED_HOSTS`
* database settings (name, user, password, host, port)
Generate a secret key with:
 
```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```
 
Don't commit `.env` or real credentials.
 
### PostgreSQL
 
```sql
CREATE USER kod_user WITH PASSWORD 'change-me';
CREATE DATABASE kod_db OWNER kod_user;
```
 
Then put the details in `.env`.
 
### SQLite
 
Works for quick local testing, no server needed. Keep `db.sqlite3` out of Git.
 
Switching databases doesn't move your data. Use `dumpdata` / `loaddata` if you need to.
 
## Useful commands
 

```Bash
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
python manage.py check
python manage.py test
python manage.py collectstatic
python manage.py shell
```
 
## Project rules
 
* `media/` (uploads) and `.env` aren't in the repo
* Commit migrations together with the model changes that created them
* `runserver` is for development only
* New Data Viewer sources must be registered, not discovered automatically
## Todo
 
* [ ] Docker setup
* [ ] Tests and GitHub Actions
* [ ] Search across articles and resources
* [ ] Email notifications
* [ ] REST API
* [ ] Deployment guide
* [ ] Data Viewer Development
## License
 
MIT. See [LICENSE](LICENSE).
 
## Author
 
Daniel Agalliu
