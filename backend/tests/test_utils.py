"""Tests for core utility helpers."""

from __future__ import annotations

from src.core.utils import generate_slug


def test_generate_slug_transliterates_and_sanitizes() -> None:
    assert generate_slug("Мой крутой товар!") == "moy-krutoy-tovar"
    assert generate_slug("Product @#$% Name") == "product-name"
    assert generate_slug("Café déjà vu") == "cafe-deja-vu"


def test_generate_slug_adds_unique_suffix() -> None:
    assert generate_slug("Existing Name", {"existing-name"}) == "existing-name-1"
    assert generate_slug("", {"untitled"}) == "untitled-1"


def test_generate_slug_respects_max_length_with_suffix() -> None:
    existing = {"a" * 255}

    slug = generate_slug("a" * 300, existing)

    assert slug == f"{'a' * 253}-1"
    assert len(slug) == 255
