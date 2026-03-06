"""
Integration tests for Marvel Mosaic views.

Author: Sai Saketh Gooty Kase
"""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from website.models import FavoriteCharacter, Post, Reply

MOCK_CHARACTER = {
    "id": 1009368,
    "name": "Iron Man",
    "description": "Genius billionaire.",
    "thumbnail": {"path": "http://i.annihil.us/ironman", "extension": "jpg"},
    "comics": {"available": 2, "items": [{"name": "Iron Man #1"}]},
    "series": {"available": 0, "items": []},
    "events": {"available": 0, "items": []},
    "stories": {"available": 1, "items": [{"name": "Extremis"}]},
}


class HomeViewTest(TestCase):
    def test_get_renders_home(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_login_valid_credentials(self):
        User.objects.create_user(username="tony", password="pepper99")
        response = self.client.post(
            reverse("home"), {"username": "tony", "password": "pepper99"}
        )
        self.assertRedirects(response, reverse("home"))

    def test_login_invalid_credentials(self):
        response = self.client.post(
            reverse("home"), {"username": "tony", "password": "wrong"}
        )
        self.assertRedirects(response, reverse("home"))


class RegisterViewTest(TestCase):
    def test_get_renders_register_form(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "register.html")

    def test_successful_registration_logs_in_user(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "pepper",
                "email": "pepper@starkindustries.com",
                "password1": "StrongP@ss1",
                "password2": "StrongP@ss1",
                "first_name": "Pepper",
                "last_name": "Potts",
            },
        )
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(User.objects.filter(username="pepper").exists())


class CharactersListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="steve", password="shield99")
        self.client.login(username="steve", password="shield99")

    @patch("website.views.get_marvel_characters", return_value=[MOCK_CHARACTER])
    def test_renders_characters(self, _mock):
        response = self.client.get(reverse("characters_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "characters_list.html")

    @patch("website.views.get_marvel_characters", return_value=[MOCK_CHARACTER])
    def test_ajax_returns_json(self, _mock):
        response = self.client.get(
            reverse("characters_list"),
            {"search": "Iron"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("characters_html", data)

    @patch("website.views.get_marvel_characters", return_value=[MOCK_CHARACTER])
    def test_search_filters_results(self, _mock):
        response = self.client.get(
            reverse("characters_list"),
            {"search": "Thor"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        data = response.json()
        self.assertNotIn("Iron Man", data["characters_html"])

    def test_redirects_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse("characters_list"))
        self.assertEqual(response.status_code, 302)


class CharacterDetailViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="natasha", password="blackwidow")
        self.client.login(username="natasha", password="blackwidow")

    @patch("website.views.get_character_by_id", return_value=MOCK_CHARACTER)
    def test_renders_detail_page(self, _mock):
        response = self.client.get(
            reverse("character_detail", args=[1009368])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "character_detail.html")

    @patch("website.views.get_character_by_id", return_value=None)
    def test_redirects_when_character_not_found(self, _mock):
        response = self.client.get(
            reverse("character_detail", args=[9999999])
        )
        self.assertRedirects(response, reverse("characters_list"))


class AddToFavoritesViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="clint", password="hawkeye1")
        self.client.login(username="clint", password="hawkeye1")

    @patch("website.views.get_character_by_id", return_value=MOCK_CHARACTER)
    def test_adds_character_to_favorites(self, _mock):
        self.client.post(reverse("add_to_favorites", args=[1009368]))
        self.assertTrue(
            FavoriteCharacter.objects.filter(
                user=self.user, character_id=1009368
            ).exists()
        )

    @patch("website.views.get_character_by_id", return_value=MOCK_CHARACTER)
    def test_duplicate_add_does_not_create_second_entry(self, _mock):
        self.client.post(reverse("add_to_favorites", args=[1009368]))
        self.client.post(reverse("add_to_favorites", args=[1009368]))
        self.assertEqual(
            FavoriteCharacter.objects.filter(
                user=self.user, character_id=1009368
            ).count(),
            1,
        )

    def test_unauthenticated_redirects(self):
        self.client.logout()
        response = self.client.post(reverse("add_to_favorites", args=[1009368]))
        self.assertEqual(response.status_code, 302)


class RemoveFromFavoritesViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="wanda", password="scarlet1")
        self.client.login(username="wanda", password="scarlet1")
        self.fav = FavoriteCharacter.objects.create(
            user=self.user, character_id=1009368
        )

    @patch("website.views.get_character_by_id", return_value=MOCK_CHARACTER)
    def test_removes_existing_favorite(self, _mock):
        self.client.post(reverse("remove_from_favorites", args=[1009368]))
        self.assertFalse(
            FavoriteCharacter.objects.filter(
                user=self.user, character_id=1009368
            ).exists()
        )

    @patch("website.views.get_character_by_id", return_value=MOCK_CHARACTER)
    def test_redirects_to_favorites(self, _mock):
        response = self.client.post(
            reverse("remove_from_favorites", args=[1009368])
        )
        self.assertRedirects(response, reverse("view_favorites"))

    @patch("website.views.get_character_by_id", return_value=MOCK_CHARACTER)
    def test_remove_nonexistent_does_not_error(self, _mock):
        response = self.client.post(
            reverse("remove_from_favorites", args=[9999])
        )
        self.assertRedirects(response, reverse("view_favorites"))


class DiscussionViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="sam", password="falcon2024")
        self.client.login(username="sam", password="falcon2024")

    @patch("website.views.get_character_by_id", return_value=MOCK_CHARACTER)
    def test_create_post(self, _mock):
        self.client.post(
            reverse("create_post", args=[1009368]),
            {"content": "Cap would be proud."},
        )
        self.assertTrue(
            Post.objects.filter(
                user=self.user,
                character_id=1009368,
                content="Cap would be proud.",
            ).exists()
        )

    @patch("website.views.get_character_by_id", return_value=MOCK_CHARACTER)
    def test_empty_post_content_not_saved(self, _mock):
        self.client.post(
            reverse("create_post", args=[1009368]),
            {"content": "   "},
        )
        self.assertEqual(Post.objects.filter(character_id=1009368).count(), 0)

    @patch("website.views.get_character_by_id", return_value=MOCK_CHARACTER)
    def test_create_reply(self, _mock):
        post = Post.objects.create(
            user=self.user, character_id=1009368, content="Hello Asgard."
        )
        self.client.post(
            reverse("create_reply", args=[post.id]),
            {"content": "Wakanda Forever."},
        )
        self.assertTrue(
            Reply.objects.filter(post=post, content="Wakanda Forever.").exists()
        )
