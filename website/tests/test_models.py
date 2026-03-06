"""
Unit tests for Marvel Mosaic models.

Author: Sai Saketh Gooty Kase
"""

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from website.models import FavoriteCharacter, Post, Profile, Reply


class ProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="herouser", password="pass1234"
        )

    def test_profile_auto_created_on_user_save(self):
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_profile_subscribe_news_defaults_false(self):
        self.assertFalse(self.user.profile.subscribe_news)

    def test_profile_str(self):
        self.assertEqual(str(self.user.profile), "herouser")


class FavoriteCharacterModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ironman", password="pepper99"
        )

    def test_create_favorite(self):
        fav = FavoriteCharacter.objects.create(
            user=self.user, character_id=1009368
        )
        self.assertEqual(fav.rank, 0)

    def test_unique_together_constraint(self):
        FavoriteCharacter.objects.create(user=self.user, character_id=1009368)
        with self.assertRaises(IntegrityError):
            FavoriteCharacter.objects.create(user=self.user, character_id=1009368)

    def test_str_representation(self):
        fav = FavoriteCharacter.objects.create(
            user=self.user, character_id=1009368
        )
        self.assertIn("ironman", str(fav))
        self.assertIn("1009368", str(fav))

    def test_default_ordering_by_rank_then_id(self):
        FavoriteCharacter.objects.create(user=self.user, character_id=100, rank=3)
        FavoriteCharacter.objects.create(user=self.user, character_id=200, rank=1)
        FavoriteCharacter.objects.create(user=self.user, character_id=300, rank=2)
        ids = list(
            FavoriteCharacter.objects.filter(user=self.user).values_list(
                "character_id", flat=True
            )
        )
        self.assertEqual(ids, [200, 300, 100])


class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="thor", password="mjolnir")

    def test_create_post(self):
        post = Post.objects.create(
            user=self.user, character_id=1009664, content="Worthy!"
        )
        self.assertEqual(post.content, "Worthy!")
        self.assertIsNotNone(post.created_at)

    def test_str_truncates_long_content(self):
        long_content = "A" * 100
        post = Post.objects.create(
            user=self.user, character_id=1009664, content=long_content
        )
        self.assertLessEqual(len(str(post)), len("thor: ") + 60)

    def test_posts_ordered_newest_first(self):
        from datetime import timedelta
        from django.utils import timezone

        now = timezone.now()
        p1 = Post.objects.create(
            user=self.user, character_id=1, content="first"
        )
        Post.objects.filter(pk=p1.pk).update(
            created_at=now - timedelta(seconds=10)
        )
        p2 = Post.objects.create(
            user=self.user, character_id=1, content="second"
        )
        Post.objects.filter(pk=p2.pk).update(created_at=now)

        posts = list(Post.objects.filter(character_id=1))
        self.assertEqual(posts[0].content, "second")
        self.assertEqual(posts[1].content, "first")


class ReplyModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="banner", password="hulk2024")
        self.post = Post.objects.create(
            user=self.user, character_id=1009351, content="Puny god."
        )

    def test_create_reply(self):
        reply = Reply.objects.create(
            user=self.user, post=self.post, content="Indeed."
        )
        self.assertEqual(reply.post, self.post)

    def test_reply_str(self):
        reply = Reply.objects.create(
            user=self.user, post=self.post, content="Indeed."
        )
        self.assertIn("banner", str(reply))

    def test_cascade_delete_on_post_remove(self):
        Reply.objects.create(user=self.user, post=self.post, content="Gone soon.")
        self.post.delete()
        self.assertEqual(Reply.objects.count(), 0)
