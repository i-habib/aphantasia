#!/usr/bin/env python3
"""Inventory and optionally download the programme's public research files.

This module deliberately uses only Python's standard library.  It never sends
credentials, never accepts private share tokens, and never extracts archives.
"""

from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable


USER_AGENT = "aphantasia-public-data-audit/1.0 (stdlib urllib; public files only)"
DEFAULT_MAX_BYTES = 250 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    ".csv", ".tsv", ".tab", ".xlsx", ".xls", ".ods", ".sav", ".por",
    ".dta", ".rdata", ".rds", ".json", ".jsonl", ".parquet", ".feather",
    ".txt", ".md", ".pdf", ".doc", ".docx", ".rtf", ".html", ".htm",
    ".r", ".py", ".ipynb", ".do", ".sps", ".syntax", ".zip", ".tar",
    ".tgz", ".gz", ".7z",
}
TABULAR_EXTENSIONS = {
    ".csv", ".tsv", ".tab", ".xlsx", ".xls", ".ods", ".sav", ".por",
    ".dta", ".rdata", ".rds", ".json", ".jsonl", ".parquet", ".feather",
}
SCRIPT_EXTENSIONS = {".r", ".py", ".ipynb", ".do", ".sps", ".syntax"}
ARCHIVE_EXTENSIONS = {".zip", ".tar", ".tgz", ".gz", ".7z"}
SENSITIVE_QUERY_KEYS = {
    "access_token", "auth", "authorization", "key", "password", "signature",
    "token", "view_only", "x-amz-credential", "x-amz-signature", "x-goog-signature",
}

SOURCES: dict[str, dict[str, str]] = {
    "new2026": {
        "title": "New et al. (2026), multisensory imagery",
        "doi": "10.1016/j.cortex.2026.04.019",
        "repository": "OSF",
        "repository_id": "2bdn6",
        "landing_url": "https://osf.io/2bdn6/",
    },
    "mawtus2024": {
        "title": "Mawtus et al. (2024), aphantasia and mental healthcare",
        "doi": "10.1525/collabra.127416",
        "repository": "OSF",
        "repository_id": "v7krh",
        "landing_url": "https://osf.io/v7krh/",
    },
    "arnold2026": {
        "title": "Arnold et al. (2026), Autism and Aphantasia",
        "doi": "10.48610/57f325b",
        "repository": "UQ eSpace",
        "repository_id": "UQ:57f325b",
        "landing_url": "https://espace.library.uq.edu.au/view/UQ:57f325b",
    },
}


class FetchError(RuntimeError):
    pass


def validate_public_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise FetchError(f"refusing non-public URL: {url!r}")
    keys = {key.lower() for key, _ in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)}
    if keys & SENSITIVE_QUERY_KEYS:
        raise FetchError(f"refusing URL containing an authentication/share token: {url!r}")
    return url


def request(url: str) -> urllib.request.Request:
    validate_public_url(url)
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})


def read_url(url: str, opener: Callable[..., Any] = urllib.request.urlopen) -> bytes:
    with opener(request(url), timeout=45) as response:
        return response.read()


def read_json(url: str, opener: Callable[..., Any] = urllib.request.urlopen) -> dict[str, Any]:
    try:
        return json.loads(read_url(url, opener).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FetchError(f"invalid JSON from {url}: {exc}") from exc


def safe_relative_path(source: str, remote_path: str, fallback: str = "file") -> Path:
    decoded = urllib.parse.unquote(remote_path).replace("\\", "/")
    parts = [part for part in PurePosixPath(decoded).parts if part not in ("", "/")]
    if not parts:
        parts = [fallback]
    if any(part in (".", "..") or "\x00" in part for part in parts):
        raise FetchError(f"unsafe remote path: {remote_path!r}")
    cleaned = [re.sub(r"[^\w.()\[\]{} +,@'-]", "_", part, flags=re.UNICODE) for part in parts]
    if any(not part or part in (".", "..") for part in cleaned):
        raise FetchError(f"unsafe remote path after normalization: {remote_path!r}")
    return Path("raw") / source / Path(*cleaned)


def file_kind(name: str) -> str:
    suffix = Path(urllib.parse.urlsplit(name).path).suffix.lower()
    if suffix in TABULAR_EXTENSIONS:
        return "tabular_data"
    if suffix in SCRIPT_EXTENSIONS:
        return "analysis_script"
    if suffix in ARCHIVE_EXTENSIONS:
        return "archive"
    if suffix in {".pdf", ".doc", ".docx", ".rtf", ".md", ".txt", ".html", ".htm"}:
        return "documentation"
    return "other"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _osf_files_url(node_id: str) -> str:
    return f"https://api.osf.io/v2/nodes/{node_id}/files/"


def _get_next(payload: dict[str, Any]) -> str | None:
    next_link = payload.get("links", {}).get("next")
    if isinstance(next_link, dict):
        next_link = next_link.get("href")
    return validate_public_url(next_link) if next_link else None


def _walk_osf_listing(
    url: str,
    source: str,
    provider: str,
    opener: Callable[..., Any],
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    pending = [validate_public_url(url)]
    seen: set[str] = set()
    while pending:
        page_url = pending.pop(0)
        if page_url in seen:
            continue
        seen.add(page_url)
        payload = read_json(page_url, opener)
        for item in payload.get("data", []):
            attrs = item.get("attributes", {})
            links = item.get("links", {})
            name = str(attrs.get("name") or item.get("id") or "file")
            if attrs.get("kind") == "folder":
                child_url = links.get("move") or links.get("new_folder")
                child_url = links.get("files") or item.get("relationships", {}).get("files", {}).get("links", {}).get("related", {}).get("href") or child_url
                if child_url:
                    pending.append(validate_public_url(child_url))
                continue
            if attrs.get("kind") != "file" or not links.get("download"):
                continue
            materialized = str(attrs.get("materialized_path") or name)
            if materialized.endswith("/"):
                materialized += name
            rel = safe_relative_path(source, f"{provider}/{materialized}", name)
            found.append({
                "id": str(item.get("id") or links.get("download")),
                "name": name,
                "relative_path": rel.as_posix(),
                "url": validate_public_url(links["download"]),
                "sha256": None,
                "size": attrs.get("size"),
                "kind": file_kind(name),
                "status": "available",
                "provider": provider,
                "modified": attrs.get("date_modified"),
            })
        nxt = _get_next(payload)
        if nxt:
            pending.append(nxt)
    return found


def inventory_osf(source: str, spec: dict[str, str], opener: Callable[..., Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    node_url = f"https://api.osf.io/v2/nodes/{spec['repository_id']}/"
    node = read_json(node_url, opener).get("data", {})
    attrs = node.get("attributes", {})
    providers = read_json(_osf_files_url(spec["repository_id"]), opener)
    files: list[dict[str, Any]] = []
    for provider in providers.get("data", []):
        provider_name = str(provider.get("attributes", {}).get("name") or provider.get("id") or "storage")
        related = provider.get("relationships", {}).get("files", {}).get("links", {}).get("related", {}).get("href")
        if related:
            files.extend(_walk_osf_listing(related, source, provider_name, opener))
    files.sort(key=lambda item: (item["relative_path"], item["id"]))
    metadata = {
        "api_url": node_url,
        "repository_title": attrs.get("title"),
        "description": attrs.get("description"),
        "license": attrs.get("license") or "not stated in OSF node metadata",
        "public": attrs.get("public"),
        "date_modified": attrs.get("date_modified"),
    }
    return files, metadata


class LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str | None]] = []
        self.meta: dict[str, list[str]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self.links.append((values["href"] or "", values.get("download")))
        if tag == "meta":
            key = values.get("name") or values.get("property")
            value = values.get("content")
            if key and value:
                self.meta.setdefault(key.lower(), []).append(value)


def inventory_uq(source: str, spec: dict[str, str], opener: Callable[..., Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    datacite_url = "https://api.datacite.org/dois/" + urllib.parse.quote(spec["doi"], safe="")
    dc = read_json(datacite_url, opener).get("data", {}).get("attributes", {})
    landing_url = validate_public_url(dc.get("url") or spec["landing_url"])
    page_bytes = read_url(landing_url, opener)
    parser = LinkParser()
    parser.feed(page_bytes.decode("utf-8", errors="replace"))
    candidates: set[str] = set()
    for key in ("citation_pdf_url", "citation_fulltext_html_url", "dc.identifier.uri"):
        candidates.update(parser.meta.get(key, []))
    candidates.update(href for href, download in parser.links if download is not None or Path(urllib.parse.urlsplit(href).path).suffix.lower() in ALLOWED_EXTENSIONS)
    files: list[dict[str, Any]] = []
    for index, href in enumerate(sorted(candidates)):
        absolute = urllib.parse.urljoin(landing_url, href)
        try:
            validate_public_url(absolute)
        except FetchError:
            continue
        name = Path(urllib.parse.unquote(urllib.parse.urlsplit(absolute).path)).name or f"attachment-{index + 1}"
        if Path(name).suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        rel = safe_relative_path(source, name)
        files.append({
            "id": f"uq:{index + 1}:{hashlib.sha256(absolute.encode()).hexdigest()[:12]}",
            "name": name,
            "relative_path": rel.as_posix(),
            "url": absolute,
            "sha256": None,
            "size": None,
            "kind": file_kind(name),
            "status": "available",
        })
    rights = dc.get("rightsList") or []
    metadata = {
        "api_url": datacite_url,
        "repository_title": (dc.get("titles") or [{}])[0].get("title"),
        "description": [item.get("description") for item in dc.get("descriptions", [])],
        "license": rights if rights else "not stated in DataCite metadata",
        "landing_url_resolved": landing_url,
        "publisher": dc.get("publisher"),
    }
    return files, metadata


def inventory_source(source: str, opener: Callable[..., Any] = urllib.request.urlopen) -> dict[str, Any]:
    spec = SOURCES[source]
    base = {
        "source": source,
        "title": spec["title"],
        "doi": spec["doi"],
        "repository": spec["repository"],
        "repository_id": spec["repository_id"],
        "landing_url": spec["landing_url"],
        "status": "inventory_only",
        "error": None,
        "files": [],
    }
    try:
        if spec["repository"] == "OSF":
            files, metadata = inventory_osf(source, spec, opener)
        else:
            files, metadata = inventory_uq(source, spec, opener)
        base["files"] = files
        base["provenance"] = metadata
        if not files:
            base["status"] = "no_downloadable_files_found"
    except (FetchError, urllib.error.URLError, TimeoutError, OSError) as exc:
        base["status"] = "unavailable"
        base["error"] = f"{type(exc).__name__}: {exc}"
    return base


def _previous_files(manifest_path: Path) -> dict[str, dict[str, Any]]:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return {item.get("relative_path", ""): item for item in payload.get("files", [])}


def download_entry(
    entry: dict[str, Any],
    output_root: Path,
    previous: dict[str, Any] | None = None,
    opener: Callable[..., Any] = urllib.request.urlopen,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> dict[str, Any]:
    entry = dict(entry)
    rel = Path(entry["relative_path"])
    if rel.is_absolute() or ".." in rel.parts or not rel.parts or rel.parts[0] != "raw":
        raise FetchError(f"unsafe output relative_path: {entry['relative_path']!r}")
    suffix = Path(entry.get("name", "")).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        entry["status"] = "skipped_kind"
        return entry
    remote_size = entry.get("size")
    if isinstance(remote_size, int) and remote_size > max_bytes:
        entry["status"] = "skipped_size"
        return entry
    destination = output_root / rel
    destination.parent.mkdir(parents=True, exist_ok=True)
    if previous and destination.is_file() and previous.get("url") == entry.get("url"):
        actual_hash = sha256_file(destination)
        if actual_hash == previous.get("sha256"):
            entry.update(sha256=actual_hash, size=destination.stat().st_size, status="skipped_existing")
            return entry
    fd, temporary_name = tempfile.mkstemp(prefix=destination.name + ".", suffix=".part", dir=destination.parent)
    digest = hashlib.sha256()
    size = 0
    try:
        with os.fdopen(fd, "wb") as output, opener(request(entry["url"]), timeout=90) as response:
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > max_bytes:
                raise FetchError(f"file exceeds {max_bytes} byte limit")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise FetchError(f"file exceeds {max_bytes} byte limit")
                digest.update(chunk)
                output.write(chunk)
        os.replace(temporary_name, destination)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    entry.update(sha256=digest.hexdigest(), size=size, status="downloaded")
    return entry


def download_manifest(
    manifest: dict[str, Any],
    output_root: Path,
    previous_files: dict[str, dict[str, Any]],
    opener: Callable[..., Any] = urllib.request.urlopen,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> dict[str, Any]:
    if manifest["status"] == "unavailable":
        return manifest
    downloaded: list[dict[str, Any]] = []
    errors: list[str] = []
    for entry in manifest["files"]:
        try:
            downloaded.append(download_entry(entry, output_root, previous_files.get(entry["relative_path"]), opener, max_bytes))
        except (FetchError, urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            failed = dict(entry)
            failed["status"] = "error"
            failed["error"] = f"{type(exc).__name__}: {exc}"
            downloaded.append(failed)
            errors.append(f"{entry.get('name')}: {exc}")
    manifest["files"] = downloaded
    if errors:
        manifest["status"] = "partial" if any(item["status"] in {"downloaded", "skipped_existing"} for item in downloaded) else "unavailable"
        manifest["error"] = "; ".join(errors)
    elif downloaded:
        manifest["status"] = "downloaded"
    else:
        manifest["status"] = "no_downloadable_files_found"
    return manifest


def write_manifest(manifest: dict[str, Any], output_root: Path) -> Path:
    path = output_root / "manifests" / f"{manifest['source']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != rendered:
        path.write_text(rendered, encoding="utf-8")
    return path


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=(*SOURCES, "all"), default="all")
    parser.add_argument("--output-root", type=Path, default=Path("data"))
    parser.add_argument("--download", action="store_true", help="download selected public files; default is inventory only")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES, help="per-file byte limit")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    if args.max_bytes <= 0:
        raise SystemExit("--max-bytes must be positive")
    sources = list(SOURCES) if args.source == "all" else [args.source]
    exit_code = 0
    for source in sources:
        manifest_path = args.output_root / "manifests" / f"{source}.json"
        previous = _previous_files(manifest_path)
        manifest = inventory_source(source)
        if args.download:
            manifest = download_manifest(manifest, args.output_root, previous, max_bytes=args.max_bytes)
        path = write_manifest(manifest, args.output_root)
        counts: dict[str, int] = {}
        for item in manifest["files"]:
            counts[item["status"]] = counts.get(item["status"], 0) + 1
        print(f"{source}: {manifest['status']}; {len(manifest['files'])} files; {counts}; manifest={path}")
        if manifest["error"]:
            print(f"  error: {manifest['error']}", file=sys.stderr)
        if manifest["status"] == "unavailable":
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
