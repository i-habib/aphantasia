import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "fetch_public.py"
SPEC = importlib.util.spec_from_file_location("fetch_public", MODULE_PATH)
fetch_public = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(fetch_public)


class FakeResponse:
    def __init__(self, body: bytes):
        self.body = body
        self.offset = 0
        self.headers = {"Content-Length": str(len(body))}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size=-1):
        if size < 0:
            size = len(self.body) - self.offset
        chunk = self.body[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk


class CountingOpener:
    def __init__(self, body: bytes):
        self.body = body
        self.calls = []

    def __call__(self, req, timeout=None):
        self.calls.append((req, timeout))
        return FakeResponse(self.body)


class FetchPublicTests(unittest.TestCase):
    def test_download_hash_and_idempotency(self):
        body = b"participant,value\n1,5\n"
        opener = CountingOpener(body)
        entry = {
            "name": "data.csv",
            "relative_path": "raw/new2026/data.csv",
            "url": "https://example.test/data.csv",
            "sha256": None,
            "size": len(body),
            "kind": "tabular_data",
            "status": "available",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = fetch_public.download_entry(entry, root, opener=opener)
            self.assertEqual(first["sha256"], hashlib.sha256(body).hexdigest())
            self.assertEqual(first["status"], "downloaded")
            second = fetch_public.download_entry(entry, root, previous=first, opener=opener)
            self.assertEqual(second["status"], "skipped_existing")
            self.assertEqual(len(opener.calls), 1)

    def test_safe_paths_reject_traversal(self):
        for value in ("../secret.csv", "folder/../../secret.csv", "folder\\..\\secret.csv"):
            with self.subTest(value=value), self.assertRaises(fetch_public.FetchError):
                fetch_public.safe_relative_path("new2026", value)

    def test_download_rejects_absolute_and_escaping_paths(self):
        base = {"name": "x.csv", "url": "https://example.test/x.csv", "size": 1}
        with tempfile.TemporaryDirectory() as directory:
            for relative in ("/tmp/x.csv", "raw/new2026/../../x.csv", "other/x.csv"):
                with self.subTest(relative=relative), self.assertRaises(fetch_public.FetchError):
                    fetch_public.download_entry({**base, "relative_path": relative}, Path(directory))

    def test_refuses_tokens_and_never_sends_authorization(self):
        for key in ("view_only", "token", "access_token", "X-Amz-Signature"):
            with self.subTest(key=key), self.assertRaises(fetch_public.FetchError):
                fetch_public.validate_public_url(f"https://example.test/data.csv?{key}=secret")
        req = fetch_public.request("https://example.test/data.csv?page=2")
        headers = {key.lower() for key, _ in req.header_items()}
        self.assertNotIn("authorization", headers)
        self.assertNotIn("cookie", headers)

    def test_manifest_is_stable_when_unchanged(self):
        manifest = {"source": "new2026", "status": "inventory_only", "error": None, "files": []}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = fetch_public.write_manifest(manifest, root)
            before = path.read_bytes()
            fetch_public.write_manifest(json.loads(before), root)
            self.assertEqual(before, path.read_bytes())

    def test_size_limit_leaves_no_partial_file(self):
        opener = CountingOpener(b"123456")
        entry = {
            "name": "data.csv", "relative_path": "raw/new2026/data.csv",
            "url": "https://example.test/data.csv", "size": None,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(fetch_public.FetchError):
                fetch_public.download_entry(entry, root, opener=opener, max_bytes=5)
            self.assertFalse((root / "raw/new2026/data.csv").exists())
            self.assertEqual(list((root / "raw/new2026").glob("*.part")), [])


if __name__ == "__main__":
    unittest.main()
