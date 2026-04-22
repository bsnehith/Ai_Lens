from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, List


class ReportStorage:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save_report(self, report: Dict) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO reports (id, title, generated_at, payload_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    report["id"],
                    report["title"],
                    report["generated_at"],
                    json.dumps(report),
                ),
            )
            conn.commit()

    def history(self, limit: int = 20) -> List[Dict[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, title, generated_at
                FROM reports
                ORDER BY generated_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "title": row[1],
                "date": row[2].split("T")[0],
            }
            for row in rows
        ]
