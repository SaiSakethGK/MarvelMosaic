"""
Unit tests for the Marvel API client module.

Author: Sai Saketh Gooty Kase
"""

from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase, override_settings

import marvel_api


@override_settings(
    MARVEL_PUBLIC_KEY="pub_test",
    MARVEL_PRIVATE_KEY="priv_test",
)
class AuthParamsTest(TestCase):
    def test_auth_params_keys_present(self):
        params = marvel_api._auth_params()
        self.assertIn("apikey", params)
        self.assertIn("ts", params)
        self.assertIn("hash", params)

    def test_auth_params_uses_public_key(self):
        params = marvel_api._auth_params()
        self.assertEqual(params["apikey"], "pub_test")

    def test_hash_is_32_char_md5(self):
        params = marvel_api._auth_params()
        self.assertEqual(len(params["hash"]), 32)


@override_settings(
    MARVEL_PUBLIC_KEY="pub_test",
    MARVEL_PRIVATE_KEY="priv_test",
)
class GetCharactersTest(TestCase):
    def setUp(self):
        cache.clear()

    def _mock_response(self, results, total=100):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {"results": results, "total": total}
        }
        mock_resp.raise_for_status.return_value = None
        return mock_resp

    @patch("marvel_api.requests.get")
    def test_returns_list_of_characters(self, mock_get):
        mock_get.return_value = self._mock_response(
            [{"id": 1, "name": "Spider-Man"}]
        )
        result = marvel_api.get_marvel_characters(max_characters=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Spider-Man")

    @patch("marvel_api.requests.get")
    def test_result_cached_after_first_call(self, mock_get):
        mock_get.return_value = self._mock_response(
            [{"id": 1, "name": "Spider-Man"}]
        )
        marvel_api.get_marvel_characters(max_characters=1)
        marvel_api.get_marvel_characters(max_characters=1)
        self.assertEqual(mock_get.call_count, 1)

    @patch("marvel_api.requests.get")
    def test_returns_empty_list_on_api_failure(self, mock_get):
        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.RequestException(
            "Network error"
        )
        result = marvel_api.get_marvel_characters(max_characters=5)
        self.assertEqual(result, [])

    @patch("marvel_api.requests.get")
    def test_respects_max_characters_limit(self, mock_get):
        chars = [{"id": i, "name": f"Hero {i}"} for i in range(10)]
        mock_get.return_value = self._mock_response(chars, total=10)
        result = marvel_api.get_marvel_characters(max_characters=3)
        self.assertLessEqual(len(result), 3)


@override_settings(
    MARVEL_PUBLIC_KEY="pub_test",
    MARVEL_PRIVATE_KEY="priv_test",
)
class GetCharacterByIdTest(TestCase):
    def setUp(self):
        cache.clear()

    def _mock_response(self, character):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {"results": [character] if character else []}
        }
        mock_resp.raise_for_status.return_value = None
        return mock_resp

    @patch("marvel_api.requests.get")
    def test_returns_character_dict(self, mock_get):
        mock_get.return_value = self._mock_response(
            {"id": 1009368, "name": "Iron Man"}
        )
        result = marvel_api.get_character_by_id(1009368)
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "Iron Man")

    @patch("marvel_api.requests.get")
    def test_returns_none_when_not_found(self, mock_get):
        mock_get.return_value = self._mock_response(None)
        result = marvel_api.get_character_by_id(9999999)
        self.assertIsNone(result)

    @patch("marvel_api.requests.get")
    def test_result_cached_after_first_call(self, mock_get):
        mock_get.return_value = self._mock_response(
            {"id": 1009368, "name": "Iron Man"}
        )
        marvel_api.get_character_by_id(1009368)
        marvel_api.get_character_by_id(1009368)
        self.assertEqual(mock_get.call_count, 1)

    @patch("marvel_api.requests.get")
    def test_returns_none_on_network_failure(self, mock_get):
        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.RequestException("down")
        result = marvel_api.get_character_by_id(1009368)
        self.assertIsNone(result)
