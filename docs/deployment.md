# Deploying to Render

This guide covers deploying Marvel Mosaic to [Render](https://render.com/) using the included `render.yaml` configuration.

## Prerequisites

- A Render account
- The repository pushed to GitHub
- Your Marvel API keys (public and private)

## Steps

### 1. Connect your repository

In the Render dashboard, click **New → Web Service** and connect your GitHub account. Select the `marvel-mosaic` repository.

### 2. Configure the service

Render will detect `render.yaml` automatically. Verify the settings:

| Setting | Value |
|---|---|
| Environment | Python |
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn marvel.wsgi:application` |

### 3. Set environment variables

In the Render dashboard under **Environment**, add the following:

| Key | Value |
|---|---|
| `DJANGO_SECRET_KEY` | A long random string — generate one locally with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `MARVEL_PUBLIC_KEY` | Your Marvel public key |
| `MARVEL_PRIVATE_KEY` | Your Marvel private key |
| `ZAPIER_WEBHOOK_URL` | Your Zapier webhook URL (leave empty to disable) |
| `DEBUG` | `False` |

Render auto-generates `DJANGO_SECRET_KEY` if you use `generateValue: true` in `render.yaml`, so you can also leave that to Render.

### 4. Add your Render domain to Marvel's referrer list

The Marvel API blocks requests from unauthorized origins. Log in to [developer.marvel.com](https://developer.marvel.com/), go to your account, and add your Render domain (e.g. `https://marvel-django.onrender.com`) to the authorized referrers.

### 5. Deploy

Click **Create Web Service**. Render will install dependencies and start the server. The first deploy takes a few minutes.

### 6. Run migrations

Open the Render **Shell** tab for your service and run:

```bash
python manage.py migrate
```

This only needs to be done once (or after any new migration).

## Updating the Deployment

Every push to the `main` branch triggers an automatic redeploy on Render.

## Notes on the Free Tier

Render's free tier spins down the service after 15 minutes of inactivity. The first request after a spin-down takes 30–60 seconds while the container restarts. Upgrade to a paid tier to keep the service always on.

## Static Files

WhiteNoise serves static files directly from gunicorn — no separate static file hosting needed. `STATICFILES_STORAGE` is configured to use `whitenoise.storage.CompressedManifestStaticFilesStorage` in production.

If you ever need to pre-collect static files manually:

```bash
python manage.py collectstatic --noinput
```
