# API Reference

This document covers the Marvel API client module and the internal HTTP endpoints exposed by the app.

---

## Marvel API Client (`marvel_api.py`)

### `get_marvel_characters(max_characters=80)`

Returns a list of Marvel character dicts, fetching from the Marvel API on a cache miss.

**Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `max_characters` | `int` | `80` | Maximum number of characters to return |

**Returns** `list[dict]` — each dict is the raw Marvel API character object. An empty list is returned if the API is unreachable.

**Caching** Results are stored under the key `marvel:characters:{max_characters}` for 1 hour.

**Example**

```python
from marvel_api import get_marvel_characters

characters = get_marvel_characters()
for c in characters:
    print(c["name"], c["id"])
```

---

### `get_character_by_id(character_id)`

Returns a single character dict by Marvel character ID.

**Parameters**

| Name | Type | Description |
|---|---|---|
| `character_id` | `int` | The Marvel character ID (e.g. `1009368` for Iron Man) |

**Returns** `dict | None` — the Marvel API character object, or `None` if not found or the API is unreachable.

**Caching** Result is stored under the key `marvel:character:{character_id}` for 1 hour.

**Example**

```python
from marvel_api import get_character_by_id

iron_man = get_character_by_id(1009368)
if iron_man:
    print(iron_man["name"])
```

---

### Character dict structure

Both functions return the raw Marvel API response shape. The fields used by the app are:

| Field | Type | Description |
|---|---|---|
| `id` | `int` | Marvel character ID |
| `name` | `str` | Character name |
| `description` | `str` | Short bio (may be empty) |
| `thumbnail.path` | `str` | Image URL without extension |
| `thumbnail.extension` | `str` | Image file extension (e.g. `jpg`) |
| `comics.available` | `int` | Total comic count |
| `comics.items` | `list` | Up to 20 comic name/url objects |
| `series.available` | `int` | Total series count |
| `series.items` | `list` | Up to 20 series name/url objects |
| `events.available` | `int` | Total event count |
| `events.items` | `list` | Up to 20 event name/url objects |
| `stories.available` | `int` | Total story count |
| `stories.items` | `list` | Up to 20 story name/url objects |

Full field documentation: [Marvel API interactive docs](https://developer.marvel.com/docs)

---

## Internal Endpoints

These endpoints are part of the app and are not part of a public API. They are used for internal tooling and Zapier integrations.

### `GET /api/subscribed-emails/`

Returns a list of email addresses for users who have subscribed to news.

**Authentication** None required.

**Response**

```json
{
  "emails": ["user@example.com", "another@example.com"]
}
```

---

### `GET /api/subscribed-users/`

Returns name and email for all subscribed users.

**Authentication** None required.

**Response**

```json
{
  "users": [
    { "email": "user@example.com", "name": "Tony Stark" }
  ]
}
```

---

### `GET /api/trigger-morning-email/`

Sends a `morning` Zapier webhook event for every subscribed user.

**Authentication** Login required.

**Response**

```json
{ "status": "ok", "recipients": 4 }
```

---

## URL Patterns

| Method | URL | View | Name |
|---|---|---|---|
| GET/POST | `/` | `home` | `home` |
| GET | `/logout/` | `logout_user` | `logout` |
| GET/POST | `/register/` | `register_user` | `register` |
| GET | `/characters_list/` | `characters_list` | `characters_list` |
| GET | `/character/<id>/` | `character_detail` | `character_detail` |
| POST | `/character/<id>/post` | `create_post` | `create_post` |
| POST | `/post/<id>/reply` | `create_reply` | `create_reply` |
| POST | `/character/<id>/add_to_favorites/` | `add_to_favorites` | `add_to_favorites` |
| GET | `/view_favorites/` | `view_favorites` | `view_favorites` |
| POST | `/character/<id>/update_rank/` | `update_rank` | `update_rank` |
| POST | `/character/<id>/remove_from_favorites/` | `RemoveFromFavoritesView` | `remove_from_favorites` |
| GET | `/character/<id>/confirm_remove_from_favorites/` | `confirm_remove_from_favorites` | `confirm_remove_from_favorites` |
| GET | `/api/subscribed-emails/` | `subscribed_emails` | `subscribed_emails` |
| GET | `/api/subscribed-users/` | `get_subscribed_users` | `subscribed_users` |
