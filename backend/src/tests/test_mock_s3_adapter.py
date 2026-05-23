import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, unquote_plus, urlparse

from app.adapters.s3.adapters.mock import MockAdapter


class MockAdapterTestCase(unittest.TestCase):
    def test_creates_bucket_and_reads_nested_object(self) -> None:
        with tempfile.TemporaryDirectory() as storage_dir:
            adapter = MockAdapter(storage_dir=storage_dir)

            adapter.create_bucket("avatars")
            adapter.put_object("avatars", "users/alice.png", b"image-bytes")

            self.assertTrue(Path(storage_dir, "avatars").is_dir())
            self.assertTrue(adapter.is_exists("avatars", "users/alice.png"))
            self.assertEqual(
                adapter.get_object("avatars", "users/alice.png"),
                b"image-bytes",
            )

    def test_reports_missing_object(self) -> None:
        with tempfile.TemporaryDirectory() as storage_dir:
            adapter = MockAdapter(storage_dir=storage_dir)

            self.assertFalse(adapter.is_exists("avatars", "missing.png"))

    def test_presigned_url_encodes_names_and_expiration(self) -> None:
        with tempfile.TemporaryDirectory() as storage_dir:
            adapter = MockAdapter(
                endpoint="http://storage.local:9000",
                storage_dir=storage_dir,
            )
            before_expiration = datetime.now(UTC) + timedelta(minutes=5)

            url = adapter.get_presigned_url(
                "team avatars",
                "users/alice profile.png",
                timedelta(minutes=5),
            )

            parsed_url = urlparse(url)
            query = parse_qs(parsed_url.query)
            expires_at = datetime.fromtimestamp(int(query["expires"][0]), UTC)

            self.assertEqual(parsed_url.scheme, "http")
            self.assertEqual(parsed_url.netloc, "storage.local:9000")
            self.assertEqual(
                unquote_plus(parsed_url.path),
                "/mock/team avatars/users/alice profile.png",
            )
            self.assertEqual(query["mock"], ["true"])
            self.assertGreaterEqual(expires_at, before_expiration - timedelta(seconds=1))
            self.assertLessEqual(
                expires_at,
                datetime.now(UTC) + timedelta(minutes=5, seconds=1),
            )

    def test_minio_style_methods_are_not_supported(self) -> None:
        with tempfile.TemporaryDirectory() as storage_dir:
            adapter = MockAdapter(storage_dir=storage_dir)

            with self.assertRaises(NotImplementedError):
                adapter.get("avatars", "alice.png")

