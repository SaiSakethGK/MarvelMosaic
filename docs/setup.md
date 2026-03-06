# Local Development Setup

This guide walks you through running Marvel Mosaic on your machine for the first time.

## Prerequisites

- Python 3.10 or higher
- A Marvel developer account — register free at [developer.marvel.com](https://developer.marvel.com/)
- Git

## 1. Clone the Repository

```bash
git clone https://github.com/SaiSakethGK/marvel-mosaic.git
cd marvel-mosaic
```

## 2. Create a Virtual Environment

```bash
python -m venv env
source env/bin/activate    # Windows: env\Scripts\activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure Environment Variables

Copy the example file and edit it:

```bash
cp .env.example .env
```

Open `.env` and set the following values:

**`DJANGO_SECRET_KEY`**
Generate a new key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**`MARVEL_PUBLIC_KEY` and `MARVEL_PRIVATE_KEY`**
Log in to [developer.marvel.com](https://developer.marvel.com/), go to your account, and copy your public and private API keys.

You also need to add `http://localhost` to the authorized referrers list in the Marvel portal, otherwise API requests will return a 401.

**`ZAPIER_WEBHOOK_URL`** *(optional)*
If you want email notifications to work, create a Zap in Zapier with a Webhooks trigger and paste the URL here. Leave this blank to skip email features.

## 5. Apply Database Migrations

```bash
python manage.py migrate
```

This creates the SQLite database and all required tables.

## 6. Create a Superuser *(optional)*

```bash
python manage.py createsuperuser
```

Gives you access to the Django admin at `/admin/`.

## 7. Run the Development Server

```bash
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Running Tests

```bash
python manage.py test website.tests
```

To run a specific test module:

```bash
python manage.py test website.tests.test_views
python manage.py test website.tests.test_models
python manage.py test website.tests.test_api_client
```

## Common Issues

**Characters page is empty**
The most likely cause is a missing or incorrect Marvel API key. Check that `MARVEL_PUBLIC_KEY` and `MARVEL_PRIVATE_KEY` are set in `.env` and that `http://localhost` is in your Marvel portal referrer list.

**`ModuleNotFoundError` on startup**
Your virtual environment is probably not active. Run `source env/bin/activate` (or `env\Scripts\activate` on Windows) before starting the server.

**Migrations fail**
Delete `db.sqlite3` and run `python manage.py migrate` again. This is safe in local development since it only removes local test data.
