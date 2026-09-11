"""Random character name generator for placeholder names during drafting."""

import random

FIRST_NAMES = [
    "Alex", "Jordan", "Casey", "Riley", "Morgan", "Taylor", "Quinn", "Avery",
    "Blake", "Cameron", "Dakota", "Drew", "Ellis", "Finley", "Gray", "Harper",
    "James", "Sarah", "Michael", "Emily", "David", "Maria", "Robert", "Anna",
    "William", "Sofia", "Daniel", "Claire", "Thomas", "Olivia", "Henry", "Grace",
    "Samuel", "Lily", "Benjamin", "Ella", "Lucas", "Nora", "Jack", "Chloe",
    "Max", "Zoe", "Leo", "Mia", "Kai", "Luna", "Ezra", "Nova", "Felix", "Iris",
    "Omar", "Fatima", "Wei", "Mei", "Raj", "Priya", "Kenji", "Yuki", "Marco", "Lucia",
    "Nikolai", "Natasha", "Amir", "Layla", "Diego", "Carmen", "Pavel", "Ingrid",
    "Kwame", "Amara", "Sven", "Freya", "Ravi", "Ananya", "Hassan", "Leila",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Anderson", "Taylor", "Thomas", "Moore", "Jackson",
    "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Clark", "Lewis",
    "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Hill",
    "Green", "Adams", "Baker", "Nelson", "Carter", "Mitchell", "Roberts", "Turner",
    "Chen", "Kim", "Park", "Singh", "Patel", "Nakamura", "Sato", "Mueller",
    "Petrov", "Fernandez", "Santos", "Andersen", "Berg", "Fischer", "Dubois",
    "Moreau", "Laurent", "Novak", "Bergman", "Costa", "Silva", "Okafor", "Diallo",
]


def generate_name(include_last: bool = True) -> str:
    first = random.choice(FIRST_NAMES)
    if include_last:
        last = random.choice(LAST_NAMES)
        return f"{first} {last}"
    return first


def generate_names(count: int = 5, include_last: bool = True) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    attempts = 0
    while len(result) < count and attempts < count * 10:
        name = generate_name(include_last)
        if name not in seen:
            seen.add(name)
            result.append(name)
        attempts += 1
    return result


def generate_character_name() -> str:
    return generate_name(include_last=True).upper()


def generate_character_names(count: int = 5) -> list[str]:
    return [n.upper() for n in generate_names(count, include_last=True)]
