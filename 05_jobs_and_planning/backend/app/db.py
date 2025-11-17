"""データアクセス層。SQLite / JSON の二重化をサポートする。"""

from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings
from .models import (
    ArticleDetail,
    ArticleIndexRecord,
    ArticleMetadata,
    ArticleSummary,
    Base,
    Profile,
    ProfileRecord,
    ProfileResponse,
)

PROFILE_SINGLETON_ID = 1
DEFAULT_PROFILE = Profile(
    name="WAKE Guest",
    years=5,
    current_role="Product Generalist",
    target_role="AI Product Manager",
    skills=["Facilitation", "LLM Prompting", "Career Coaching"],
    interests=["WAKE Articles", "1on1", "RAG"],
    notes="初期状態のサンプルプロフィールです。",
)


class DatabaseNotReadyError(RuntimeError):
    """DB操作前に connect が呼ばれていない際に送出される。"""


class ArticleNotFoundError(RuntimeError):
    pass


class JsonProfileStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path = self.base_dir / "profile.json"

    def load(self) -> Optional[ProfileResponse]:
        if not self.profile_path.exists():
            return None
        payload = json.loads(self.profile_path.read_text(encoding="utf-8"))
        return ProfileResponse(**payload)

    def save(self, profile: ProfileResponse) -> ProfileResponse:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path.write_text(
            json.dumps(profile.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return profile


class JsonArticleStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.base_dir / "article_index.json"

    def load(self) -> list[ArticleMetadata]:
        if not self.index_path.exists():
            return []
        payload = json.loads(self.index_path.read_text(encoding="utf-8"))
        return [ArticleMetadata(**item) for item in payload]

    def save(self, records: list[ArticleMetadata]) -> list[ArticleMetadata]:
        existing = {record.slug: record for record in self.load()}
        for record in records:
            existing[record.slug] = record
        serialized = [item.model_dump() for item in existing.values()]
        self.index_path.write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8")
        return list(existing.values())

    def get(self, slug: str) -> Optional[ArticleMetadata]:
        for item in self.load():
            if item.slug == slug:
                return item
        return None


class Database:
    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._storage_dir = storage_dir
        self._json_profile_store: Optional[JsonProfileStore] = None
        self._json_article_store: Optional[JsonArticleStore] = None

    @property
    def mode(self) -> str:
        return get_settings().db_mode

    @property
    def storage_dir(self) -> Path:
        if self._storage_dir is None:
            self._storage_dir = get_settings().json_db_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        return self._storage_dir

    def connect(self) -> None:
        if self.mode != "sqlite":
            return
        if self._engine is not None:
            return

        settings = get_settings()
        settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(settings.database_url, future=True)
        Base.metadata.create_all(engine)
        self._engine = engine
        self._session_factory = sessionmaker(bind=self._engine, autoflush=False, autocommit=False, future=True)

    def close(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
        self._engine = None
        self._session_factory = None

    @contextmanager
    def session(self) -> Iterator[Session]:
        self.connect()
        if self._session_factory is None:
            raise DatabaseNotReadyError("SQLite セッションが初期化されていません。")
        session: Session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _json_profiles(self) -> JsonProfileStore:
        if self._json_profile_store is None:
            self._json_profile_store = JsonProfileStore(self.storage_dir)
        return self._json_profile_store

    def _json_articles(self) -> JsonArticleStore:
        if self._json_article_store is None:
            self._json_article_store = JsonArticleStore(self.storage_dir)
        return self._json_article_store

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------
    def get_profile(self) -> Optional[ProfileResponse]:
        if self.mode == "sqlite":
            with self.session() as session:
                record = session.get(ProfileRecord, PROFILE_SINGLETON_ID)
                if record is None:
                    return self._create_default_profile()
                return record.to_schema()
        data = self._json_profiles().load()
        if data is None:
            return self._create_default_profile()
        return data

    def save_profile(self, payload: Profile) -> ProfileResponse:
        timestamp = datetime.now(timezone.utc)
        if self.mode == "sqlite":
            with self.session() as session:
                record = session.get(ProfileRecord, PROFILE_SINGLETON_ID)
                if record is None:
                    record = ProfileRecord(id=PROFILE_SINGLETON_ID, updated_at=timestamp)
                    session.add(record)
                record.name = payload.name
                record.years = payload.years
                record.current_role = payload.current_role
                record.target_role = payload.target_role
                record.skills = payload.skills
                record.interests = payload.interests
                record.notes = payload.notes
                record.updated_at = timestamp
                session.flush()
                session.refresh(record)
                return record.to_schema()
        response = ProfileResponse(**payload.model_dump(), updated_at=timestamp.isoformat())
        return self._json_profiles().save(response)

    def ensure_profile(self, default: Profile = DEFAULT_PROFILE) -> None:
        if self.get_profile() is None:
            self.save_profile(default)

    def _create_default_profile(self) -> ProfileResponse:
        return self.save_profile(DEFAULT_PROFILE)

    # ------------------------------------------------------------------
    # Article index
    # ------------------------------------------------------------------
    def save_article_index(self, articles: list[ArticleMetadata]) -> list[ArticleMetadata]:
        if not articles:
            return []
        if self.mode == "sqlite":
            saved: list[ArticleMetadata] = []
            with self.session() as session:
                for article in articles:
                    stmt = select(ArticleIndexRecord).where(ArticleIndexRecord.slug == article.slug)
                    record = session.execute(stmt).scalar_one_or_none()
                    if record is None:
                        record = ArticleIndexRecord(slug=article.slug)
                        session.add(record)
                    record.title = article.title
                    record.source_url = article.source_url
                    record.tags = article.tags
                    record.published_at = _parse_datetime(article.published)
                    record.category = article.category
                    saved.append(article)
                session.flush()
            return saved
        return self._json_articles().save(articles)

    def list_articles(self) -> list[ArticleMetadata]:
        if self.mode == "sqlite":
            with self.session() as session:
                stmt = select(ArticleIndexRecord).order_by(
                    ArticleIndexRecord.published_at.is_(None), ArticleIndexRecord.published_at.desc()
                )
                records = session.scalars(stmt).all()
                return [self._record_to_metadata(record) for record in records]
        return self._json_articles().load()

    def get_article(self, slug: str) -> ArticleDetail:
        metadata = self._get_article_metadata(slug)
        if metadata is None:
            raise ArticleNotFoundError(f"article '{slug}' not found")
        body = self._read_article_body(slug)
        return ArticleDetail(**metadata.model_dump(), body=body)

    def _get_article_metadata(self, slug: str) -> Optional[ArticleMetadata]:
        if self.mode == "sqlite":
            with self.session() as session:
                record = session.scalar(select(ArticleIndexRecord).where(ArticleIndexRecord.slug == slug))
                if record is None:
                    return None
                return self._record_to_metadata(record)
        return self._json_articles().get(slug)

    def _record_to_metadata(self, record: ArticleIndexRecord) -> ArticleMetadata:
        published = record.published_at.isoformat() if record.published_at else None
        return ArticleMetadata(
            slug=record.slug,
            title=record.title,
            source_url=record.source_url,
            tags=record.tags or [],
            category=record.category,
            published=published,
        )

    def _read_article_body(self, slug: str) -> str:
        settings = get_settings()
        articles_dir = settings.articles_dir
        candidates = []
        if slug.endswith(".md"):
            candidates.append(articles_dir / slug)
        else:
            candidates.append(articles_dir / f"{slug}.md")
        candidates.extend(articles_dir.glob(f"{slug}*.md"))
        for path in candidates:
            if path.exists():
                return path.read_text(encoding="utf-8")
        raise ArticleNotFoundError(f"article body for '{slug}' not found under {articles_dir}")

    # テスト向けのダイレクト設定
    def override_storage_dir(self, path: Path) -> None:
        self._storage_dir = path
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._json_profile_store = None
        self._json_article_store = None


database = Database()


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
