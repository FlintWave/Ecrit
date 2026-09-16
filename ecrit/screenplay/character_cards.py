"""Enhanced character cards with photos, bios, and relationship mapping."""

import json
import os
import re
import uuid
from dataclasses import dataclass, field
from typing import Optional


RELATIONSHIP_TYPES = [
    "ally", "rival", "mentor", "mentee", "love_interest",
    "family", "colleague", "enemy", "friend", "subordinate", "superior",
]


@dataclass
class CharacterPhoto:
    path: str
    caption: str = ""
    is_primary: bool = False


@dataclass
class CharacterRelationship:
    target_name: str
    relationship_type: str
    description: str = ""
    bidirectional: bool = True


@dataclass
class CharacterBio:
    full_name: str = ""
    nickname: str = ""
    age: str = ""
    gender: str = ""
    ethnicity: str = ""
    occupation: str = ""
    physical_description: str = ""
    personality_traits: list[str] = field(default_factory=list)
    backstory: str = ""
    motivation: str = ""
    internal_conflict: str = ""
    external_conflict: str = ""
    speech_pattern: str = ""
    wardrobe: str = ""
    props: list[str] = field(default_factory=list)


@dataclass
class CharacterCard:
    id: str
    name: str
    bio: CharacterBio
    photos: list[CharacterPhoto] = field(default_factory=list)
    relationships: list[CharacterRelationship] = field(default_factory=list)
    arc_summary: str = ""
    wants: str = ""
    needs: str = ""
    flaw: str = ""
    notes: str = ""
    color: str = "#4FC3F7"
    tags: list[str] = field(default_factory=list)

    def get_primary_photo(self) -> Optional[CharacterPhoto]:
        for photo in self.photos:
            if photo.is_primary:
                return photo
        return self.photos[0] if self.photos else None

    def add_photo(self, path: str, caption: str = "", is_primary: bool = False) -> CharacterPhoto:
        if is_primary:
            for photo in self.photos:
                photo.is_primary = False
        photo = CharacterPhoto(path=path, caption=caption, is_primary=is_primary)
        self.photos.append(photo)
        return photo

    def remove_photo(self, path: str) -> bool:
        for i, photo in enumerate(self.photos):
            if photo.path == path:
                self.photos.pop(i)
                return True
        return False

    def add_relationship(self, target: str, rel_type: str, description: str = "") -> CharacterRelationship:
        rel = CharacterRelationship(
            target_name=target,
            relationship_type=rel_type,
            description=description,
        )
        self.relationships.append(rel)
        return rel

    def remove_relationship(self, target: str) -> bool:
        for i, rel in enumerate(self.relationships):
            if rel.target_name == target:
                self.relationships.pop(i)
                return True
        return False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "bio": {
                "full_name": self.bio.full_name,
                "nickname": self.bio.nickname,
                "age": self.bio.age,
                "gender": self.bio.gender,
                "ethnicity": self.bio.ethnicity,
                "occupation": self.bio.occupation,
                "physical_description": self.bio.physical_description,
                "personality_traits": self.bio.personality_traits,
                "backstory": self.bio.backstory,
                "motivation": self.bio.motivation,
                "internal_conflict": self.bio.internal_conflict,
                "external_conflict": self.bio.external_conflict,
                "speech_pattern": self.bio.speech_pattern,
                "wardrobe": self.bio.wardrobe,
                "props": self.bio.props,
            },
            "photos": [
                {"path": p.path, "caption": p.caption, "is_primary": p.is_primary}
                for p in self.photos
            ],
            "relationships": [
                {
                    "target_name": r.target_name,
                    "relationship_type": r.relationship_type,
                    "description": r.description,
                    "bidirectional": r.bidirectional,
                }
                for r in self.relationships
            ],
            "arc_summary": self.arc_summary,
            "wants": self.wants,
            "needs": self.needs,
            "flaw": self.flaw,
            "notes": self.notes,
            "color": self.color,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CharacterCard":
        bio_data = data.get("bio", {})
        bio = CharacterBio(
            full_name=bio_data.get("full_name", ""),
            nickname=bio_data.get("nickname", ""),
            age=bio_data.get("age", ""),
            gender=bio_data.get("gender", ""),
            ethnicity=bio_data.get("ethnicity", ""),
            occupation=bio_data.get("occupation", ""),
            physical_description=bio_data.get("physical_description", ""),
            personality_traits=bio_data.get("personality_traits", []),
            backstory=bio_data.get("backstory", ""),
            motivation=bio_data.get("motivation", ""),
            internal_conflict=bio_data.get("internal_conflict", ""),
            external_conflict=bio_data.get("external_conflict", ""),
            speech_pattern=bio_data.get("speech_pattern", ""),
            wardrobe=bio_data.get("wardrobe", ""),
            props=bio_data.get("props", []),
        )
        photos = [
            CharacterPhoto(
                path=p["path"],
                caption=p.get("caption", ""),
                is_primary=p.get("is_primary", False),
            )
            for p in data.get("photos", [])
        ]
        relationships = [
            CharacterRelationship(
                target_name=r["target_name"],
                relationship_type=r["relationship_type"],
                description=r.get("description", ""),
                bidirectional=r.get("bidirectional", True),
            )
            for r in data.get("relationships", [])
        ]
        return cls(
            id=data.get("id", uuid.uuid4().hex[:8]),
            name=data.get("name", ""),
            bio=bio,
            photos=photos,
            relationships=relationships,
            arc_summary=data.get("arc_summary", ""),
            wants=data.get("wants", ""),
            needs=data.get("needs", ""),
            flaw=data.get("flaw", ""),
            notes=data.get("notes", ""),
            color=data.get("color", "#4FC3F7"),
            tags=data.get("tags", []),
        )


class CharacterCardManager:
    def __init__(self):
        self._cards: dict[str, CharacterCard] = {}

    def add_card(self, name: str) -> CharacterCard:
        key = name.upper()
        card = CharacterCard(
            id=uuid.uuid4().hex[:8],
            name=key,
            bio=CharacterBio(),
        )
        self._cards[key] = card
        return card

    def get_card(self, name: str) -> Optional[CharacterCard]:
        return self._cards.get(name.upper())

    def get_all_cards(self) -> list[CharacterCard]:
        return sorted(self._cards.values(), key=lambda c: c.name)

    def remove_card(self, name: str) -> bool:
        return self._cards.pop(name.upper(), None) is not None

    def update_card(self, card: CharacterCard) -> None:
        self._cards[card.name.upper()] = card

    def get_relationship_map(self) -> dict[str, list[CharacterRelationship]]:
        result: dict[str, list[CharacterRelationship]] = {}
        for card in self._cards.values():
            if card.relationships:
                result[card.name] = list(card.relationships)
        return result

    def auto_populate_from_script(self, content: str) -> list[CharacterCard]:
        # Fountain: character names are lines in ALL CAPS (optionally preceded by @)
        # that appear before dialogue, not scene headings
        names: set[str] = set()
        lines = content.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            # Skip scene headings
            if re.match(r"^(INT\.|EXT\.|INT/EXT\.|I/E\.)", stripped, re.IGNORECASE):
                continue
            # @ prefix forces character name
            if stripped.startswith("@"):
                name = stripped[1:].split("(")[0].strip().upper()
                if name:
                    names.add(name)
                continue
            # All caps line followed by non-empty line (dialogue)
            if stripped.isupper() and stripped.isalpha() or re.match(r"^[A-Z][A-Z\s\.\'-]+$", stripped):
                candidate = stripped.split("(")[0].strip()
                if candidate and len(candidate) > 1 and i + 1 < len(lines) and lines[i + 1].strip():
                    names.add(candidate)

        created = []
        for name in sorted(names):
            if name not in self._cards:
                created.append(self.add_card(name))
        return created

    def save(self, project_path: str) -> None:
        ecrit_dir = os.path.join(project_path, ".ecrit")
        os.makedirs(ecrit_dir, exist_ok=True)
        filepath = os.path.join(ecrit_dir, "characters.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def load(self, project_path: str) -> None:
        filepath = os.path.join(project_path, ".ecrit", "characters.json")
        if not os.path.exists(filepath):
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.from_dict(data)

    def to_dict(self) -> dict:
        return {
            "cards": [card.to_dict() for card in self.get_all_cards()],
        }

    def from_dict(self, data: dict) -> None:
        self._cards.clear()
        for card_data in data.get("cards", []):
            card = CharacterCard.from_dict(card_data)
            self._cards[card.name.upper()] = card
