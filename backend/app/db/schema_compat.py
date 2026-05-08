"""Lightweight ALTERs for existing DBs when models gain columns / FK changes (no Alembic in MVP)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import inspect, text

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

_log = logging.getLogger(__name__)


def ensure_schema_compat(engine: Engine) -> None:
    try:
        insp = inspect(engine)
    except Exception as e:  # noqa: BLE001
        _log.warning("schema_compat: inspect failed: %s", e)
        return
    dialect = engine.dialect.name
    if not insp.has_table("drafts"):
        return

    with engine.begin() as conn:
        cols = {c["name"] for c in insp.get_columns("drafts")}
        if "expires_at" not in cols:
            if dialect == "postgresql":
                conn.execute(
                    text(
                        "ALTER TABLE drafts ADD COLUMN IF NOT EXISTS "
                        "expires_at TIMESTAMP WITHOUT TIME ZONE NULL"
                    )
                )
            elif dialect == "sqlite":
                conn.execute(text("ALTER TABLE drafts ADD COLUMN expires_at TIMESTAMP NULL"))
            else:
                conn.execute(text("ALTER TABLE drafts ADD COLUMN expires_at DATETIME NULL"))
            _log.info("schema_compat: added drafts.expires_at")

        if not insp.has_table("send_attempts"):
            return

        sacols = insp.get_columns("send_attempts")
        by_name = {c["name"]: c for c in sacols}
        draft_col = by_name.get("draft_id")
        if draft_col is not None and draft_col.get("nullable") is False:
            if dialect == "postgresql":
                for fk in insp.get_foreign_keys("send_attempts"):
                    if "draft_id" in fk.get("constrained_columns", []):
                        name = fk.get("name")
                        if name:
                            conn.execute(text(f'ALTER TABLE send_attempts DROP CONSTRAINT IF EXISTS "{name}"'))
                conn.execute(text("ALTER TABLE send_attempts ALTER COLUMN draft_id DROP NOT NULL"))
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE send_attempts ADD CONSTRAINT send_attempts_draft_id_fkey "
                            "FOREIGN KEY (draft_id) REFERENCES drafts(id) ON DELETE SET NULL"
                        )
                    )
                except Exception as e:  # noqa: BLE001
                    _log.warning("schema_compat: could not add SET NULL FK (%s)", e)
                else:
                    _log.info("schema_compat: send_attempts.draft_id nullable + ON DELETE SET NULL")
            elif dialect == "sqlite":
                _log.warning(
                    "schema_compat: SQLite cannot ALTER FK in place; use a new DB file or migrate manually."
                )
