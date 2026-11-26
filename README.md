# KOD

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?logo=bootstrap&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

A Django web app I'm building as part of my Full Stack Web Development training at Dominusoft.

It's a training and portfolio project, so things will keep changing.

## Stack

Python, Django, PostgreSQL (SQLite also works), HTML, CSS, JavaScript, Bootstrap.

## Apps

| App | Models |
| --- | --- |
| `accounts` | `User`, `Profile` |
| `events` | `Event`, `RSVP` |
| `knowledge` | `Category`, `Article` |
| `resources` | `Category`, `Resource` |
| `tickets` | `Category`, `Ticket`, `Comment` |
| `pages` | none, just general pages |

The project uses a custom user model in `accounts`, so on a fresh database always run all migrations from the start.

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

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
python manage.py check
python manage.py test
python manage.py collectstatic
python manage.py shell
```

## Notes

* `media/` (uploads) and `.env` aren't in the repo.
* Commit migrations together with the model changes that created them.
* `runserver` is for development only.

## Todo

* [ ] Docker setup
* [ ] Tests and GitHub Actions
* [ ] Search across articles and resources
* [ ] Email notifications
* [ ] REST API
* [ ] Deployment guide

## License

MIT. See [LICENSE](LICENSE).

## Author

Daniel Agalliu
