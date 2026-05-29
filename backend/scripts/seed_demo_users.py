
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.database import SessionLocal, init_db
from app.models.user import User
from app.services.auth import AuthService
from app.services.recommendation import RecommendationService


DEMO_USERS: list[dict[str, object]] = [
    {
        "name": "Anna Tech",
        "email": "anna.demo@example.com",
        "categories": ["Science & Technology", "Education", "Gaming", "News & Politics", "How-to & Style"],
    },
    {
        "name": "Mark Gamer",
        "email": "mark.demo@example.com",
        "categories": ["Gaming", "Entertainment", "Comedy", "Film & Animation"],
    },
    {
        "name": "Olena Music",
        "email": "olena.demo@example.com",
        "categories": ["Music", "Entertainment", "People & Blogs"],
    },
    {
        "name": "Dmytro Sport",
        "email": "dmytro.demo@example.com",
        "categories": ["Sports", "News & Politics"],
    },
    {
        "name": "Ira Learn",
        "email": "ira.demo@example.com",
        "categories": ["Education", "How-to & Style", "Science & Technology", "People & Blogs"],
    },
    {
        "name": "Bohdan Dev",
        "email": "bohdan.demo@example.com",
        "categories": ["Science & Technology", "Gaming"],
    },
    {
        "name": "Kateryna Art",
        "email": "kateryna.demo@example.com",
        "categories": ["Film & Animation", "Entertainment", "Music", "Anime/Animation", "People & Blogs"],
    },
    {
        "name": "Serhii News",
        "email": "serhii.demo@example.com",
        "categories": ["News & Politics", "Education"],
    },
    {
        "name": "Yulia Vlog",
        "email": "yulia.demo@example.com",
        "categories": ["People & Blogs", "Travel & Events", "How-to & Style", "Music"],
    },
    {
        "name": "Taras Science",
        "email": "taras.demo@example.com",
        "categories": ["Science & Technology", "Education", "News & Politics", "Film & Animation", "How-to & Style"],
    },
    {
        "name": "Nazar Esports",
        "email": "nazar.demo@example.com",
        "categories": ["Gaming", "Sports", "Entertainment"],
    },
    {
        "name": "Marta DIY",
        "email": "marta.demo@example.com",
        "categories": ["How-to & Style", "Education"],
    },
    {
        "name": "Roman Music",
        "email": "roman.demo@example.com",
        "categories": ["Music", "Comedy", "Entertainment", "People & Blogs"],
    },
    {
        "name": "Alina Anime",
        "email": "alina.demo@example.com",
        "categories": ["Anime/Animation", "Gaming", "Film & Animation", "Entertainment", "Music"],
    },
    {
        "name": "Vlad Travel",
        "email": "vlad.demo@example.com",
        "categories": ["Travel & Events", "People & Blogs"],
    },
    {
        "name": "Oksana Health",
        "email": "oksana.demo@example.com",
        "categories": ["How-to & Style", "Sports", "People & Blogs"],
    },
    {
        "name": "Andrii Startup",
        "email": "andrii.demo@example.com",
        "categories": ["Science & Technology", "News & Politics", "Education", "How-to & Style"],
    },
    {
        "name": "Liza Fun",
        "email": "liza.demo@example.com",
        "categories": ["Comedy", "Entertainment", "People & Blogs", "Music", "Film & Animation"],
    },
    {
        "name": "Mykola Cinema",
        "email": "mykola.demo@example.com",
        "categories": ["Film & Animation", "Music"],
    },
    {
        "name": "Polina Study",
        "email": "polina.demo@example.com",
        "categories": ["Education", "Science & Technology", "How-to & Style", "News & Politics"],
    },
    {
        "name": "Denys Fit",
        "email": "denys.demo@example.com",
        "categories": ["Sports", "How-to & Style"],
    },
    {
        "name": "Sofia Creator",
        "email": "sofia.demo@example.com",
        "categories": ["People & Blogs", "Music", "Education", "Travel & Events", "Comedy"],
    },
    {
        "name": "Artem Auto",
        "email": "artem.demo@example.com",
        "categories": ["Autos & Vehicles", "Science & Technology", "Travel & Events"],
    },
    {
        "name": "Nadiia Space",
        "email": "nadiia.demo@example.com",
        "categories": ["Science & Technology", "Education", "Film & Animation", "News & Politics"],
    },
    {
        "name": "Petro Football",
        "email": "petro.demo@example.com",
        "categories": ["Sports", "News & Politics", "Entertainment", "People & Blogs", "Comedy"],
    },
    {
        "name": "Ihor Retro",
        "email": "ihor.demo@example.com",
        "categories": ["Gaming", "Film & Animation"],
    },
    {
        "name": "Diana Culture",
        "email": "diana.demo@example.com",
        "categories": ["Music", "Education", "Travel & Events", "People & Blogs", "Film & Animation"],
    },
    {
        "name": "Maks Review",
        "email": "maks.demo@example.com",
        "categories": ["Science & Technology", "Entertainment", "People & Blogs"],
    },
    {
        "name": "Veronika Mix",
        "email": "veronika.demo@example.com",
        "categories": ["Education", "Comedy", "Music", "How-to & Style"],
    },
]

# Each set has 1–5 categories (no more than 5)
CATEGORY_SETS: list[list[str]] = [
    ["Science & Technology", "Education", "Gaming", "News & Politics", "How-to & Style"],
    ["Gaming", "Entertainment", "Comedy", "Film & Animation"],
    ["Music", "Entertainment", "People & Blogs"],
    ["Sports", "News & Politics"],
    ["Education", "How-to & Style", "Science & Technology", "People & Blogs"],
    ["Film & Animation", "Entertainment", "Music", "Anime/Animation", "People & Blogs"],
    ["People & Blogs", "Travel & Events"],
    ["News & Politics", "Education", "Science & Technology"],
    ["Comedy", "Entertainment", "People & Blogs", "Music", "Film & Animation"],
    ["Anime/Animation", "Gaming", "Film & Animation"],
    ["How-to & Style", "Sports", "People & Blogs"],
    ["Autos & Vehicles", "Science & Technology", "Travel & Events", "News & Politics"],
]

FIRST_NAMES = [
    "Oleksii", "Mila", "Yevhen", "Tetiana", "Volodymyr", "Anastasiia", "Kyrylo", "Iryna",
    "Ruslan", "Nina", "Pavlo", "Mariya", "Stanislav", "Halyna", "Yaroslav", "Larysa",
    "Maksym", "Inna", "Vitalii", "Lesia", "Rostyslav", "Zlata", "Borys", "Ivanna",
    "Stepan", "Roksolana", "Oleh", "Karina", "Bogdan", "Olha", "Semen", "Kseniia",
]

SUFFIXES = [
    "Tech", "Studio", "Flow", "Lab", "Creator", "Vision", "Pulse", "Stream",
]


def build_generated_users(count: int = 1000) -> list[dict[str, object]]:
    generated: list[dict[str, object]] = []
    for i in range(count):
        first = FIRST_NAMES[i % len(FIRST_NAMES)]
        suffix = SUFFIXES[(i // len(FIRST_NAMES)) % len(SUFFIXES)]
        name = f"{first} {suffix}"
        email = f"seed{i + 1:03d}.demo@example.com"
        categories = CATEGORY_SETS[i % len(CATEGORY_SETS)]
        generated.append({"name": name, "email": email, "categories": categories})
    return generated


def get_or_create_user(db: Session, name: str, email: str) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        return existing

    user = User(
        id=str(uuid.uuid4()),
        email=email,
        name=name,
        password_hash=AuthService.hash_password("demo12345"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def seed_demo_users() -> None:
    init_db()
    db = SessionLocal()
    recommender = RecommendationService()
    created = 0
    updated = 0
    all_users = DEMO_USERS + build_generated_users()

    try:
        for item in all_users:
            name = str(item["name"])
            email = str(item["email"])
            categories = [str(c) for c in item["categories"]]

            # Guard: never exceed 5 interests per user
            categories = categories[:5]

            user_before = db.query(User).filter(User.email == email).first()
            user = get_or_create_user(db, name, email)
            if user_before is None:
                created += 1

            result = recommender.save_manual_interests(db, user.id, categories)
            if result.get("profile_updated"):
                updated += 1
                print(f"OK: {email} -> {categories}")
            else:
                print(f"SKIP: {email} -> profile not updated")

        print(f"\nDone. Created users: {created}, profiles updated: {updated}.")
        print("Demo password for all new users: demo12345")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_users()
