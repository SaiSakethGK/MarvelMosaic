# Marvel Mosaic

A Django web app for exploring Marvel characters, building a personal favorites list, and discussing characters with other fans.

Built with the [Marvel Comics API](https://developer.marvel.com/).

---

## Features

- **Character browser** — search across 80+ Marvel characters with live filtering
- **Character detail pages** — view comics, series, events, and stories per character
- **Favorites list** — save characters and assign custom rank order
- **Discussion board** — post and reply per character
- **News subscription** — opt in to receive Marvel update emails via Zapier
- **Dark theme** — Marvel-red design system built with CSS custom properties

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.2, Python 3.11 |
| API | Marvel Comics REST API (MD5 auth) |
| Caching | Django `LocMemCache` (1 h TTL) |
| Frontend | Bootstrap 5.3, vanilla JS |
| Static files | WhiteNoise |
| Deployment | Render (gunicorn) |

## Quick Start

**1. Clone and create a virtual environment**

```bash
git clone https://github.com/SaiSakethGK/marvel-mosaic.git
cd marvel-mosaic
python -m venv env
source env/bin/activate        # Windows: env\Scripts\activate
pip install -r requirements.txt
```

**2. Set environment variables**

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

| Variable | Where to get it |
|---|---|
| `DJANGO_SECRET_KEY` | Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `MARVEL_PUBLIC_KEY` | [developer.marvel.com](https://developer.marvel.com/) |
| `MARVEL_PRIVATE_KEY` | Same Marvel developer portal |
| `ZAPIER_WEBHOOK_URL` | Optional — Zapier webhook for email notifications |

**3. Apply migrations and run**

```bash
python manage.py migrate
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000).

## Documentation

| Document | Purpose |
|---|---|
| [Local setup](docs/setup.md) | Full environment setup walkthrough |
| [Architecture](docs/architecture.md) | How the app is structured |
| [API reference](docs/api-reference.md) | Marvel API client and internal endpoints |
| [Deployment](docs/deployment.md) | Deploying to Render |

## Running Tests

```bash
python manage.py test website.tests
```

46 tests covering models, views, and the Marvel API client.

## Author

**Sai Saketh Gooty Kase** and **Jaydeep**
