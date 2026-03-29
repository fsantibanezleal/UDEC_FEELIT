"""Bundled public-domain document and audio library services for FeelIT."""

from __future__ import annotations

import hashlib
import posixpath
import re
import zipfile
from dataclasses import asdict, dataclass
from functools import lru_cache
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
DOCUMENTS_DIR = STATIC_DIR / "assets" / "library" / "documents"
AUDIO_DIR = STATIC_DIR / "assets" / "library" / "audio"


@dataclass(frozen=True)
class LibraryDocument:
    """Describe a bundled public-domain document asset."""

    slug: str
    title: str
    author: str
    format: str
    filename: str
    file_url: str
    source_name: str
    source_url: str
    summary: str
    recommended_excerpt_chars: int
    companion_audio_slugs: tuple[str, ...]


@dataclass(frozen=True)
class LibraryAudio:
    """Describe a bundled public-domain audio asset."""

    slug: str
    title: str
    creator: str
    filename: str
    file_url: str
    format: str
    source_name: str
    source_url: str
    summary: str
    related_document_slugs: tuple[str, ...]


DOCUMENT_LIBRARY: tuple[LibraryDocument, ...] = (
    LibraryDocument(
        slug="alice_in_wonderland_txt",
        title="Alice's Adventures in Wonderland",
        author="Lewis Carroll",
        format="txt",
        filename="alice_in_wonderland.txt",
        file_url="/static/assets/library/documents/alice_in_wonderland.txt",
        source_name="Project Gutenberg",
        source_url="https://www.gutenberg.org/ebooks/928",
        summary="Classic fantasy novel with dialogue-heavy scenes useful for tactile reading trials.",
        recommended_excerpt_chars=1200,
        companion_audio_slugs=("alice_chapter_01", "alice_chapter_02"),
    ),
    LibraryDocument(
        slug="pride_and_prejudice_txt",
        title="Pride and Prejudice",
        author="Jane Austen",
        format="txt",
        filename="pride_and_prejudice.txt",
        file_url="/static/assets/library/documents/pride_and_prejudice.txt",
        source_name="Project Gutenberg",
        source_url="https://www.gutenberg.org/ebooks/1342",
        summary="Long-form prose with dialogue and narrative paragraphs suitable for segmented loading.",
        recommended_excerpt_chars=1200,
        companion_audio_slugs=(),
    ),
    LibraryDocument(
        slug="pride_and_prejudice_epub",
        title="Pride and Prejudice (EPUB)",
        author="Jane Austen",
        format="epub",
        filename="pride_and_prejudice.epub",
        file_url="/static/assets/library/documents/pride_and_prejudice.epub",
        source_name="Project Gutenberg",
        source_url="https://www.gutenberg.org/ebooks/1342.epub.noimages",
        summary="EPUB edition used to validate packaged ebook extraction and normalization.",
        recommended_excerpt_chars=1200,
        companion_audio_slugs=(),
    ),
    LibraryDocument(
        slug="the_raven_html",
        title="The Raven",
        author="Edgar Allan Poe",
        format="html",
        filename="the_raven.html",
        file_url="/static/assets/library/documents/the_raven.html",
        source_name="Project Gutenberg",
        source_url="https://www.gutenberg.org/ebooks/1065",
        summary="Short poem in HTML form for markup-aware text extraction tests.",
        recommended_excerpt_chars=900,
        companion_audio_slugs=("the_raven_librivox",),
    ),
    LibraryDocument(
        slug="feeding_the_mind_txt",
        title="Feeding the Mind",
        author="Lewis Carroll",
        format="txt",
        filename="feeding_the_mind.txt",
        file_url="/static/assets/library/documents/feeding_the_mind.txt",
        source_name="Project Gutenberg",
        source_url="https://www.gutenberg.org/ebooks/35535",
        summary="Compact essay-sized text for quick scene loading and short reading sessions.",
        recommended_excerpt_chars=950,
        companion_audio_slugs=(),
    ),
)

AUDIOLIBRARY: tuple[LibraryAudio, ...] = (
    LibraryAudio(
        slug="alice_chapter_01",
        title="Alice's Adventures in Wonderland, Chapter 1",
        creator="LibriVox volunteers",
        filename="alice_chapter_01.mp3",
        file_url="/static/assets/library/audio/alice_chapter_01.mp3",
        format="mp3",
        source_name="Project Gutenberg Audio",
        source_url="https://www.gutenberg.org/files/23716/mp3/23716-01.mp3",
        summary="Opening chapter companion audio for optional parallel listening.",
        related_document_slugs=("alice_in_wonderland_txt",),
    ),
    LibraryAudio(
        slug="alice_chapter_02",
        title="Alice's Adventures in Wonderland, Chapter 2",
        creator="LibriVox volunteers",
        filename="alice_chapter_02.mp3",
        file_url="/static/assets/library/audio/alice_chapter_02.mp3",
        format="mp3",
        source_name="Project Gutenberg Audio",
        source_url="https://www.gutenberg.org/files/23716/mp3/23716-02.mp3",
        summary="Second chapter continuation to test multi-track companion audio.",
        related_document_slugs=("alice_in_wonderland_txt",),
    ),
    LibraryAudio(
        slug="the_raven_librivox",
        title="The Raven",
        creator="LibriVox volunteers",
        filename="the_raven_librivox.mp3",
        file_url="/static/assets/library/audio/the_raven_librivox.mp3",
        format="mp3",
        source_name="Internet Archive / LibriVox",
        source_url="https://archive.org/details/raven",
        summary="Short poem recording useful for audio-assist workflow validation.",
        related_document_slugs=("the_raven_html",),
    ),
    LibraryAudio(
        slug="visit_from_saint_nicholas_v1",
        title="A Visit from St. Nicholas",
        creator="LibriVox volunteers",
        filename="visit_from_saint_nicholas_v1.mp3",
        file_url="/static/assets/library/audio/visit_from_saint_nicholas_v1.mp3",
        format="mp3",
        source_name="Internet Archive / LibriVox",
        source_url="https://archive.org/details/visitfrom_saint_nicholas_0912_librivox",
        summary="Additional public-domain narration sample to validate the internal audio library.",
        related_document_slugs=(),
    ),
)

BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "div",
    "figcaption",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "p",
    "section",
    "table",
    "td",
    "th",
    "tr",
}
SKIP_TAGS = {"head", "script", "style", "title"}


class VisibleTextHTMLParser(HTMLParser):
    """Extract visible text while ignoring scripts, styles, and head content."""

    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth == 0 and tag in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth == 0 and tag in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and data.strip():
            self._chunks.append(data)

    def get_text(self) -> str:
        """Return the extracted text."""
        return "".join(self._chunks)


def _document_by_slug(slug: str) -> LibraryDocument | None:
    return next((document for document in DOCUMENT_LIBRARY if document.slug == slug), None)


def _audio_by_slug(slug: str) -> LibraryAudio | None:
    return next((audio for audio in AUDIOLIBRARY if audio.slug == slug), None)


def _asset_file_size(path: Path) -> int:
    """Return the file size for a bundled asset."""
    return path.stat().st_size


def _normalize_text(text: str) -> str:
    """Normalize extracted text into a predictable reading payload."""
    cleaned = unescape(text).replace("\ufeff", "")
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t\f\v]+", " ", cleaned)
    cleaned = re.sub(r" *\n *", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _strip_gutenberg_boilerplate(text: str) -> str:
    """Remove common Project Gutenberg header and footer blocks when present."""
    lines = text.splitlines()
    start_index = 0
    end_index = len(lines)

    for index, line in enumerate(lines):
        normalized = line.upper()
        if "START OF THE PROJECT GUTENBERG EBOOK" in normalized or "START OF THIS PROJECT GUTENBERG EBOOK" in normalized:
            start_index = index + 1
            break

    for index, line in enumerate(lines[start_index:], start=start_index):
        normalized = line.upper()
        if "END OF THE PROJECT GUTENBERG EBOOK" in normalized or "END OF THIS PROJECT GUTENBERG EBOOK" in normalized:
            end_index = index
            break

    return "\n".join(lines[start_index:end_index])


def _extract_html_text(raw_html: str) -> str:
    """Return visible text from an HTML or XHTML payload."""
    parser = VisibleTextHTMLParser()
    parser.feed(raw_html)
    parser.close()
    return _normalize_text(parser.get_text())


def _extract_txt_text(path: Path) -> str:
    """Load and clean a plain-text public-domain document."""
    raw_text = path.read_text(encoding="utf-8", errors="ignore")
    return _normalize_text(_strip_gutenberg_boilerplate(raw_text))


def _extract_html_file_text(path: Path) -> str:
    """Load and clean an HTML document."""
    raw_html = path.read_text(encoding="utf-8", errors="ignore")
    return _extract_html_text(raw_html)


def _extract_epub_text(path: Path) -> str:
    """Extract readable text from a simple EPUB package without external dependencies."""
    with zipfile.ZipFile(path) as archive:
        container_xml = archive.read("META-INF/container.xml")
        container_root = ET.fromstring(container_xml)
        rootfile_path = ""
        for element in container_root.iter():
            if element.tag.endswith("rootfile"):
                rootfile_path = element.attrib["full-path"]
                break

        if not rootfile_path:
            raise ValueError(f"Unable to locate rootfile in EPUB: {path.name}")

        opf_root = ET.fromstring(archive.read(rootfile_path))
        manifest: dict[str, tuple[str, str]] = {}
        spine_ids: list[str] = []

        for element in opf_root.iter():
            if element.tag.endswith("item"):
                manifest[element.attrib["id"]] = (
                    element.attrib["href"],
                    element.attrib.get("media-type", ""),
                )
            elif element.tag.endswith("itemref"):
                spine_ids.append(element.attrib["idref"])

        opf_dir = posixpath.dirname(rootfile_path)
        parts: list[str] = []

        for spine_id in spine_ids:
            href, media_type = manifest.get(spine_id, ("", ""))
            if not href:
                continue
            if "html" not in media_type and not href.lower().endswith((".html", ".htm", ".xhtml")):
                continue
            member_path = posixpath.normpath(posixpath.join(opf_dir, href))
            raw_html = archive.read(member_path).decode("utf-8", errors="ignore")
            extracted = _extract_html_text(raw_html)
            if extracted:
                parts.append(extracted)

    return _normalize_text(_strip_gutenberg_boilerplate("\n\n".join(parts)))


def extract_document_text_from_path(path: Path) -> str:
    """Extract readable text from a supported document path."""
    suffix = path.suffix.lower()
    if suffix == ".txt" or suffix == ".md":
        return _extract_txt_text(path)
    if suffix in {".html", ".htm"}:
        return _extract_html_file_text(path)
    if suffix == ".epub":
        return _extract_epub_text(path)
    raise ValueError(f"Unsupported document format: {path.suffix}")


@lru_cache(maxsize=None)
def read_document_text(slug: str) -> str:
    """Return the fully extracted text for a known bundled document."""
    document = _document_by_slug(slug)
    if document is None:
        raise KeyError(slug)

    path = DOCUMENTS_DIR / document.filename
    return extract_document_text_from_path(path)


def _clip_excerpt(text: str, offset: int, max_chars: int) -> tuple[str, int, int]:
    """Return a word-aware excerpt slice."""
    if not text:
        return "", 0, 0

    start = min(max(offset, 0), len(text))
    end = min(len(text), start + max_chars)
    excerpt = text[start:end]
    if end < len(text):
        last_break = max(excerpt.rfind(" "), excerpt.rfind("\n"))
        if last_break > int(len(excerpt) * 0.65):
            excerpt = excerpt[:last_break]
            end = start + last_break
    return excerpt.strip(), start, end


def build_document_catalog() -> list[dict[str, object]]:
    """Return metadata for the bundled document library."""
    catalog: list[dict[str, object]] = []
    for document in DOCUMENT_LIBRARY:
        payload = asdict(document)
        payload["file_size_bytes"] = _asset_file_size(DOCUMENTS_DIR / document.filename)
        catalog.append(payload)
    return catalog


def build_audio_catalog() -> list[dict[str, object]]:
    """Return metadata for the bundled audio library."""
    catalog: list[dict[str, object]] = []
    for audio in AUDIOLIBRARY:
        payload = asdict(audio)
        payload["file_size_bytes"] = _asset_file_size(AUDIO_DIR / audio.filename)
        catalog.append(payload)
    return catalog


def build_text_payload_from_path(
    path: Path,
    *,
    title: str,
    source_name: str,
    source_url: str,
    slug_seed: str | None = None,
    offset: int = 0,
    max_chars: int = 1200,
) -> dict[str, object]:
    """Return a clipped text payload for a supported arbitrary document path."""
    text = extract_document_text_from_path(path)
    excerpt, start, end = _clip_excerpt(text, offset, max_chars)
    return {
        "slug": _slugify_path(path, slug_seed=slug_seed),
        "title": title,
        "author": "Unknown",
        "format": path.suffix.lower().lstrip("."),
        "filename": path.name,
        "file_url": "",
        "source_name": source_name,
        "source_url": source_url,
        "summary": f"Text content loaded from {path.name}.",
        "recommended_excerpt_chars": max_chars,
        "companion_audio_slugs": (),
        "file_size_bytes": _asset_file_size(path),
        "text": excerpt,
        "offset": start,
        "next_offset": end if end < len(text) else None,
        "previous_offset": max(0, start - max_chars) if start > 0 else None,
        "loaded_characters": len(excerpt),
        "total_characters": len(text),
        "has_more": end < len(text),
    }


def _slugify_path(path: Path, *, slug_seed: str | None = None) -> str:
    """Convert a filesystem path into a stable collision-resistant slug."""
    seed = slug_seed or path.as_posix()
    base = re.sub(r"[^a-z0-9]+", "_", path.stem.lower()).strip("_") or "document"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
    return f"{base}_{digest}"


def build_document_payload(slug: str, *, offset: int = 0, max_chars: int | None = None) -> dict[str, object]:
    """Return a clipped document segment plus metadata for the Braille Reader."""
    document = _document_by_slug(slug)
    if document is None:
        raise KeyError(slug)

    resolved_max_chars = max_chars or document.recommended_excerpt_chars
    full_text = read_document_text(slug)
    excerpt, start, end = _clip_excerpt(full_text, offset, resolved_max_chars)

    payload = asdict(document)
    payload["file_size_bytes"] = _asset_file_size(DOCUMENTS_DIR / document.filename)
    payload["text"] = excerpt
    payload["offset"] = start
    payload["next_offset"] = end if end < len(full_text) else None
    payload["previous_offset"] = max(0, start - resolved_max_chars) if start > 0 else None
    payload["loaded_characters"] = len(excerpt)
    payload["total_characters"] = len(full_text)
    payload["has_more"] = end < len(full_text)
    return payload


def get_audio_payload(slug: str) -> dict[str, object]:
    """Return metadata for a single known audio asset."""
    audio = _audio_by_slug(slug)
    if audio is None:
        raise KeyError(slug)

    payload = asdict(audio)
    payload["file_size_bytes"] = _asset_file_size(AUDIO_DIR / audio.filename)
    return payload
