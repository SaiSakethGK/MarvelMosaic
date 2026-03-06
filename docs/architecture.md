# Architecture

This document explains how Marvel Mosaic is structured and how its main components interact.

## Project Layout

```
marvel-mosaic/
├── marvel/                 # Django project package
│   ├── settings.py         # All configuration, reads from env vars
│   └── urls.py             # Root URL routing
├── website/                # Main application
│   ├── models.py           # Database models
│   ├── views.py            # Request handlers
│   ├── urls.py             # App-level URL patterns
│   ├── forms.py            # Sign-up form
│   ├── middleware.py       # Request logging with timing
│   ├── templates/          # HTML templates
│   └── tests/              # Automated tests
├── marvel_api.py           # Marvel API client (standalone module)
├── requirements.txt
└── docs/
```

## Data Models

There are four models in `website/models.py`:

**`Profile`** extends Django's built-in `User` with a single extra field: `subscribe_news`. A `Profile` is created automatically for every new user via a `post_save` signal.

**`FavoriteCharacter`** links a user to a Marvel character ID (an integer from the Marvel API). The `unique_together` constraint prevents duplicate favorites. The `rank` field lets users assign their own ordering.

**`Post`** stores a discussion post for a character. Character data isn't saved to the database — only the `character_id` integer. Posts are ordered newest-first by default.

**`Reply`** belongs to a `Post`. Replies are ordered oldest-first so threads read chronologically.

```
User (Django built-in)
 └── Profile          (1-to-1)
 └── FavoriteCharacter (many, unique per user+character_id)
 └── Post             (many)
       └── Reply      (many)
```

## Marvel API Client

`marvel_api.py` is a standalone module (not a Django app) that wraps the Marvel REST API. It has two public functions:

- `get_marvel_characters(max_characters)` — returns a list of character dicts
- `get_character_by_id(character_id)` — returns a single character dict or `None`

Both functions check Django's cache before making a network request. Results are cached for one hour. On a cache miss the client makes up to 3 attempts before giving up and returning `None` or an empty list.

Authentication uses the MD5 signature scheme Marvel requires: `hash = md5(ts + private_key + public_key)`.

## Request Flow

A typical page request goes through these layers:

```
Browser
  → RequestLogMiddleware   (records method, path, status, elapsed ms)
  → Django URL router
  → View function / class-based view
  → marvel_api (cache → Marvel API)
  → Template rendering
  → Response
```

Views never import from `marvel_api` directly — they call `get_marvel_characters` or `get_character_by_id`, which keeps API concerns isolated to one module.

## Configuration

All secrets and environment-specific values are read from environment variables in `marvel/settings.py`. Nothing is hardcoded. The relevant variables are:

| Variable | Used for |
|---|---|
| `DJANGO_SECRET_KEY` | Django session signing |
| `MARVEL_PUBLIC_KEY` | Marvel API auth |
| `MARVEL_PRIVATE_KEY` | Marvel API auth (MD5 hash) |
| `ZAPIER_WEBHOOK_URL` | Email webhook (optional) |

## Frontend

There is no JavaScript framework. The frontend is server-rendered Django templates with Bootstrap 5.3 for layout and a small set of CSS custom properties for theming. The only client-side logic is:

- **Live character search** — a debounced `input` listener fetches `characters_list/?search=...` as an AJAX request and replaces the results grid with the returned HTML partial.
- **Tab switching** on character detail pages — pure DOM manipulation, no library.
- **Confirmation modals** on the favorites page — Bootstrap 5 modal component.

## Email Notifications

When a user registers with the "subscribe" checkbox checked, a POST request is sent to the Zapier webhook with `{"email": "...", "name": "...", "type": "welcome"}`. A separate internal endpoint (`/api/trigger-morning-email/`) sends a `"morning"` event for all subscribed users. Zapier handles the actual email delivery.
