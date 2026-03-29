"""Tests for FeelIT's bundled public-domain library assets."""

from pathlib import Path

from app.core.library_assets import (
    AUDIO_DIR,
    DOCUMENTS_DIR,
    build_audio_catalog,
    build_document_catalog,
    build_document_payload,
    read_document_text,
)

MAX_BUNDLED_ASSET_BYTES = 60 * 1024 * 1024


def test_txt_document_loader_strips_gutenberg_boilerplate() -> None:
    text = read_document_text("alice_in_wonderland_txt")
    assert "START OF THE PROJECT GUTENBERG EBOOK" not in text
    assert "Alice was beginning to get very tired" in text


def test_html_document_loader_extracts_visible_text() -> None:
    text = read_document_text("the_raven_html")
    assert "Once upon a midnight dreary" in text
    assert "<html" not in text.lower()


def test_epub_document_loader_extracts_spine_text() -> None:
    text = read_document_text("pride_and_prejudice_epub")
    assert "Mr. Bennet" in text
    assert "Netherfield Park" in text
    assert len(text) > 10_000


def test_document_payload_clips_segments_cleanly() -> None:
    payload = build_document_payload("pride_and_prejudice_txt", offset=0, max_chars=800)
    assert payload["loaded_characters"] <= 800
    assert payload["next_offset"] is not None
    assert payload["total_characters"] > payload["loaded_characters"]


def test_catalog_file_urls_exist_on_disk() -> None:
    for document in build_document_catalog():
        assert (DOCUMENTS_DIR / document["filename"]).is_file()
    for audio in build_audio_catalog():
        assert (AUDIO_DIR / audio["filename"]).is_file()


def test_bundled_library_assets_stay_under_per_file_threshold() -> None:
    for asset_dir in (DOCUMENTS_DIR, AUDIO_DIR):
        for path in asset_dir.iterdir():
            if path.is_file():
                assert path.stat().st_size < MAX_BUNDLED_ASSET_BYTES, path.name


def test_demo_model_assets_stay_under_per_file_threshold() -> None:
    models_dir = Path(__file__).resolve().parents[1] / "app" / "static" / "assets" / "models" / "demo"
    for path in models_dir.iterdir():
        if path.is_file():
            assert path.stat().st_size < MAX_BUNDLED_ASSET_BYTES, path.name
