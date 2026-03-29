"""Tests for Braille translation and layout."""

from app.core.braille import layout_braille_cells, translate_character, translate_text_to_cells


def test_translate_character_a_uses_first_dot() -> None:
    cell = translate_character("A")
    assert cell.normalized == "a"
    assert cell.mask == 1
    assert cell.dots == [True, False, False, False, False, False]


def test_translate_character_accented_letter_is_normalized() -> None:
    cell = translate_character("á")
    assert cell.normalized == "a"
    assert cell.mask == 1


def test_unknown_character_uses_fallback_mask() -> None:
    cell = translate_character("@")
    assert cell.mask == 28


def test_layout_wraps_to_second_row() -> None:
    cells = translate_text_to_cells("abcdef")
    positioned = layout_braille_cells(cells, columns=4)
    assert positioned[0].row == 0
    assert positioned[3].row == 0
    assert positioned[4].row == 1
    assert positioned[4].column == 0

