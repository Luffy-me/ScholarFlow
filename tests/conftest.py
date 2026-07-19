"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from models.fake import FakeProvider
from shared.knowledge import clear_knowledge_cache, load_bad_posts, load_good_posts, load_user_memory


@pytest.fixture(autouse=True)
def _clear_caches() -> None:
    clear_knowledge_cache()
    yield
    clear_knowledge_cache()


@pytest.fixture
def provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def user_memory() -> dict:
    return load_user_memory()


@pytest.fixture
def good_post() -> str:
    return load_good_posts()["posts"][0]["text"]


@pytest.fixture
def bad_generic_post() -> str:
    return load_bad_posts()["posts"][0]["text"]


@pytest.fixture
def bad_fake_experience_post() -> str:
    return load_bad_posts()["posts"][1]["text"]
