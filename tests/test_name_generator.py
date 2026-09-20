"""Tests for character name generator."""

from ecrit.screenplay.name_generator import (
    generate_name, generate_names, generate_character_name, generate_character_names,
    FIRST_NAMES, LAST_NAMES,
)


class TestNameGenerator:
    def test_generate_name_with_last(self):
        name = generate_name(include_last=True)
        parts = name.split()
        assert len(parts) == 2
        assert parts[0] in FIRST_NAMES
        assert parts[1] in LAST_NAMES

    def test_generate_name_first_only(self):
        name = generate_name(include_last=False)
        assert " " not in name
        assert name in FIRST_NAMES

    def test_generate_names_count(self):
        names = generate_names(count=3, include_last=True)
        assert len(names) == 3

    def test_generate_names_unique(self):
        names = generate_names(count=10, include_last=True)
        assert len(names) == len(set(names))

    def test_generate_names_zero(self):
        names = generate_names(count=0)
        assert names == []

    def test_generate_character_name_uppercase(self):
        name = generate_character_name()
        assert name == name.upper()
        assert " " in name

    def test_generate_character_names_count(self):
        names = generate_character_names(count=5)
        assert len(names) == 5
        for name in names:
            assert name == name.upper()

    def test_names_lists_not_empty(self):
        assert len(FIRST_NAMES) > 10
        assert len(LAST_NAMES) > 10
