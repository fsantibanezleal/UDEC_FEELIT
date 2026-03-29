"""Braille translation and preview layout services."""

from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, Field


def _mask_from_dots(*dots: int) -> int:
    """Build a six-dot Braille mask from one-based dot positions."""
    mask = 0
    for dot in dots:
        mask |= 1 << (dot - 1)
    return mask


BRAILLE_MASKS: dict[str, int] = {
    " ": 0,
    "a": _mask_from_dots(1),
    "b": _mask_from_dots(1, 2),
    "c": _mask_from_dots(1, 4),
    "d": _mask_from_dots(1, 4, 5),
    "e": _mask_from_dots(1, 5),
    "f": _mask_from_dots(1, 2, 4),
    "g": _mask_from_dots(1, 2, 4, 5),
    "h": _mask_from_dots(1, 2, 5),
    "i": _mask_from_dots(2, 4),
    "j": _mask_from_dots(2, 4, 5),
    "k": _mask_from_dots(1, 3),
    "l": _mask_from_dots(1, 2, 3),
    "m": _mask_from_dots(1, 3, 4),
    "n": _mask_from_dots(1, 3, 4, 5),
    "o": _mask_from_dots(1, 3, 5),
    "p": _mask_from_dots(1, 2, 3, 4),
    "q": _mask_from_dots(1, 2, 3, 4, 5),
    "r": _mask_from_dots(1, 2, 3, 5),
    "s": _mask_from_dots(2, 3, 4),
    "t": _mask_from_dots(2, 3, 4, 5),
    "u": _mask_from_dots(1, 3, 6),
    "v": _mask_from_dots(1, 2, 3, 6),
    "w": _mask_from_dots(2, 4, 5, 6),
    "x": _mask_from_dots(1, 3, 4, 6),
    "y": _mask_from_dots(1, 3, 4, 5, 6),
    "z": _mask_from_dots(1, 3, 5, 6),
    ".": _mask_from_dots(2, 5, 6),
    ",": _mask_from_dots(2),
    ";": _mask_from_dots(2, 3),
    ":": _mask_from_dots(2, 5),
    "!": _mask_from_dots(2, 3, 5),
    "?": _mask_from_dots(2, 3, 6),
    "-": _mask_from_dots(3, 6),
    "(": _mask_from_dots(2, 3, 5, 6),
    ")": _mask_from_dots(2, 3, 5, 6),
    "'": _mask_from_dots(3),
    '"': _mask_from_dots(5),
    "/": _mask_from_dots(3, 4),
    "&": _mask_from_dots(1, 2, 3, 4, 6),
}

FALLBACK_MASK = _mask_from_dots(3, 4, 5)


class BrailleCell(BaseModel):
    """Braille cell metadata used by both API and frontend."""

    source: str = Field(..., min_length=1, max_length=1)
    normalized: str = Field(..., min_length=1, max_length=1)
    mask: int = Field(..., ge=0, le=63)
    dots: list[bool] = Field(..., min_length=6, max_length=6)
    unicode_cell: str = Field(..., min_length=1, max_length=1)


class PositionedBrailleCell(BrailleCell):
    """Braille cell plus logical preview position."""

    index: int = Field(..., ge=0)
    column: int = Field(..., ge=0)
    row: int = Field(..., ge=0)


def _normalize_character(char: str) -> str:
    """Normalize a source character into the current translation alphabet."""
    lowered = char.lower()
    replacements = {
        "á": "a",
        "à": "a",
        "ä": "a",
        "â": "a",
        "é": "e",
        "è": "e",
        "ë": "e",
        "ê": "e",
        "í": "i",
        "ì": "i",
        "ï": "i",
        "î": "i",
        "ó": "o",
        "ò": "o",
        "ö": "o",
        "ô": "o",
        "ú": "u",
        "ù": "u",
        "ü": "u",
        "û": "u",
        "\n": " ",
        "\r": " ",
        "\t": " ",
    }
    return replacements.get(lowered, lowered)


def _build_unicode_cell(mask: int) -> str:
    """Return the Unicode Braille pattern for a six-dot mask."""
    return chr(0x2800 + mask)


def translate_character(char: str) -> BrailleCell:
    """Translate a single character into a Braille cell payload."""
    normalized = _normalize_character(char)
    mask = BRAILLE_MASKS.get(normalized, FALLBACK_MASK)
    dots = [(mask & (1 << index)) != 0 for index in range(6)]
    return BrailleCell(
        source=char,
        normalized=normalized,
        mask=mask,
        dots=dots,
        unicode_cell=_build_unicode_cell(mask),
    )


def translate_text_to_cells(text: str) -> list[BrailleCell]:
    """Translate a text string into a list of Braille cells."""
    return [translate_character(char) for char in text]


def layout_braille_cells(
    cells: Iterable[BrailleCell],
    *,
    columns: int = 12,
) -> list[PositionedBrailleCell]:
    """Project Braille cells into a row/column preview grid."""
    positioned: list[PositionedBrailleCell] = []
    for index, cell in enumerate(cells):
        positioned.append(
            PositionedBrailleCell(
                **cell.model_dump(),
                index=index,
                column=index % columns,
                row=index // columns,
            )
        )
    return positioned

