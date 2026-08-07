"""SQLite veritabani katmani.

Sema, baglanti yonetimi ve CRUD islemleri burada tutulur. Is mantigi
(seviye gecisleri, tarih hesaplari) app.srs modulunde saf fonksiyonlar
olarak yer alir; bu modul sadece o fonksiyonlari cagirip sonucu
kalicilastirir.

Tureme kelimeler her zaman eklenebilir (kok kelimenin seviyesi ne olursa
olsun), ancak eklendikleri anda ebeveyn kelime henuz 4. seviyeye
ulasmamissa "beklemede" (is_active=0) olarak kaydedilir: goruntulenebilir
ama tekrar dongusune girmez. Ebeveyn kelime 4. seviyeye ulastiginda
(review_word icinde) beklemedeki tum tureme kelimeler otomatik olarak
aktiflesir ve o gunden itibaren Seviye 1 tekrar dongusune girer.
"""
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from app import srs

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "kelimeler.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id INTEGER NOT NULL,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    level INTEGER NOT NULL DEFAULT 1,
    level_start_date TEXT NOT NULL,
    streak5 INTEGER NOT NULL DEFAULT 0,
    is_known INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    parent_id INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (folder_id) REFERENCES folders(id),
    FOREIGN KEY (parent_id) REFERENCES words(id)
);

CREATE INDEX IF NOT EXISTS idx_words_folder ON words(folder_id);
CREATE INDEX IF NOT EXISTS idx_words_parent ON words(parent_id);
"""


def _iso(d: date) -> str:
    return d.isoformat()


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def _backdated_level1_start(today: date) -> date:
    """Seviye 1'in 1 gunluk araligini hemen doldurur; kelime eklendigi/aktiflestigi
    gun tekrar listesine dusun diye level_start_date bir gun geriye yazilir."""
    return today - timedelta(days=srs.interval_days(1))


@dataclass
class Word:
    id: int
    folder_id: int
    folder_name: str
    front: str
    back: str
    level: int
    level_start_date: date
    streak5: int
    is_known: bool
    is_active: bool
    parent_id: Optional[int]
    created_at: str

    @property
    def next_review_date(self) -> date:
        return srs.next_review_date(self.level_start_date, self.level)

    def is_due(self, today: date) -> bool:
        return self.is_active and not self.is_known and srs.is_due(self.level_start_date, self.level, today)

    def to_state(self) -> srs.WordState:
        return srs.WordState(
            level=self.level,
            level_start_date=self.level_start_date,
            streak5=self.streak5,
            is_known=self.is_known,
        )


def _row_to_word(row: sqlite3.Row) -> Word:
    return Word(
        id=row["id"],
        folder_id=row["folder_id"],
        folder_name=row["folder_name"],
        front=row["front"],
        back=row["back"],
        level=row["level"],
        level_start_date=_parse_date(row["level_start_date"]),
        streak5=row["streak5"],
        is_known=bool(row["is_known"]),
        is_active=bool(row["is_active"]),
        parent_id=row["parent_id"],
        created_at=row["created_at"],
    )


_WORD_SELECT = """
    SELECT w.*, f.name AS folder_name
    FROM words w
    JOIN folders f ON f.id = w.folder_id
"""


class Database:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        self._migrate()

    def _migrate(self):
        """Eski veritabani dosyalarina (is_active sutunu olmadan olusturulmus)
        veri kaybi olmadan yeni sutunu ekler."""
        columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(words)")}
        if "is_active" not in columns:
            self.conn.execute("ALTER TABLE words ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
            self.conn.commit()

    def close(self):
        self.conn.close()

    # --- Klasorler ---

    def add_folder(self, name: str) -> int:
        name = name.strip()
        if not name:
            raise ValueError("Klasor adi bos olamaz.")
        cur = self.conn.execute("INSERT INTO folders (name) VALUES (?)", (name,))
        self.conn.commit()
        return cur.lastrowid

    def get_folders(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM folders ORDER BY name").fetchall()

    def folder_exists(self, name: str) -> bool:
        row = self.conn.execute("SELECT 1 FROM folders WHERE name = ?", (name.strip(),)).fetchone()
        return row is not None

    def delete_folder(self, folder_id: int):
        """Klasoru ve icindeki tum kelimeleri siler.

        Silinen kelimelerin baska klasorlerde yasayan turemeleri varsa,
        onlar silinmez; sadece kok baglantilari koparilir (parent_id -> NULL)
        ve bagimsiz kelime olarak kalmaya devam ederler.
        """
        word_ids = [row["id"] for row in self.conn.execute(
            "SELECT id FROM words WHERE folder_id = ?", (folder_id,)
        )]
        if word_ids:
            placeholders = ",".join("?" for _ in word_ids)
            self.conn.execute(
                f"UPDATE words SET parent_id = NULL WHERE parent_id IN ({placeholders})", word_ids
            )
            self.conn.execute(f"DELETE FROM words WHERE id IN ({placeholders})", word_ids)
        self.conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
        self.conn.commit()

    # --- Kelimeler ---

    def add_word(self, folder_id: int, front: str, back: str,
                  parent_id: Optional[int] = None, today: Optional[date] = None) -> int:
        front = front.strip()
        back = back.strip()
        if not front or not back:
            raise ValueError("On yuz ve arka yuz bos olamaz.")
        today = today or date.today()
        now = datetime.now().isoformat(timespec="seconds")

        is_active = True
        if parent_id is not None:
            parent = self.get_word(parent_id)
            if parent is None:
                raise ValueError(f"Ebeveyn kelime bulunamadi: {parent_id}")
            # Ebeveyn henuz esik seviyeye ulasmamissa tureme beklemede baslar.
            is_active = parent.is_known or srs.is_derivation_activation_level(parent.level)

        level_start_date = _backdated_level1_start(today) if is_active else today
        cur = self.conn.execute(
            """INSERT INTO words (folder_id, front, back, level, level_start_date,
                                   streak5, is_known, is_active, parent_id, created_at)
               VALUES (?, ?, ?, 1, ?, 0, 0, ?, ?, ?)""",
            (folder_id, front, back, _iso(level_start_date), int(is_active), parent_id, now),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_word(self, word_id: int) -> Optional[Word]:
        row = self.conn.execute(f"{_WORD_SELECT} WHERE w.id = ?", (word_id,)).fetchone()
        return _row_to_word(row) if row else None

    def get_words_by_folder(self, folder_id: int, include_known: bool = True) -> list[Word]:
        query = f"{_WORD_SELECT} WHERE w.folder_id = ?"
        params: list = [folder_id]
        if not include_known:
            query += " AND w.is_known = 0"
        query += " ORDER BY w.created_at"
        rows = self.conn.execute(query, params).fetchall()
        return [_row_to_word(r) for r in rows]

    def get_due_words(self, today: Optional[date] = None, folder_id: Optional[int] = None) -> list[Word]:
        today = today or date.today()
        query = f"{_WORD_SELECT} WHERE w.is_known = 0 AND w.is_active = 1"
        params: list = []
        if folder_id is not None:
            query += " AND w.folder_id = ?"
            params.append(folder_id)
        rows = self.conn.execute(query, params).fetchall()
        words = [_row_to_word(r) for r in rows]
        return [w for w in words if w.is_due(today)]

    def get_known_words(self) -> list[Word]:
        rows = self.conn.execute(f"{_WORD_SELECT} WHERE w.is_known = 1 ORDER BY w.created_at").fetchall()
        return [_row_to_word(r) for r in rows]

    def get_all_words(self) -> list[Word]:
        """Kok/tureme agacini cizebilmek icin tum kelimeleri (durumdan bagimsiz) dondurur."""
        rows = self.conn.execute(f"{_WORD_SELECT} ORDER BY w.created_at").fetchall()
        return [_row_to_word(r) for r in rows]

    def get_derivations(self, parent_id: int) -> list[Word]:
        rows = self.conn.execute(f"{_WORD_SELECT} WHERE w.parent_id = ? ORDER BY w.created_at", (parent_id,)).fetchall()
        return [_row_to_word(r) for r in rows]

    def delete_word(self, word_id: int):
        """Kelimeyi siler. Bagli turemeleri silmez; sadece kok baglantilarini
        koparir (parent_id -> NULL) ki bagimsiz kelimeler olarak kalabilsinler."""
        self.conn.execute("UPDATE words SET parent_id = NULL WHERE parent_id = ?", (word_id,))
        self.conn.execute("DELETE FROM words WHERE id = ?", (word_id,))
        self.conn.commit()

    def _activate_pending_derivations(self, parent_id: int, today: date):
        """parent_id'ye bagli, henuz beklemede olan tureme kelimeleri aktiflestirir."""
        pending = self.conn.execute(
            "SELECT id FROM words WHERE parent_id = ? AND is_active = 0", (parent_id,)
        ).fetchall()
        if not pending:
            return
        level_start_date = _iso(_backdated_level1_start(today))
        for row in pending:
            self.conn.execute(
                "UPDATE words SET is_active = 1, level_start_date = ? WHERE id = ?",
                (level_start_date, row["id"]),
            )

    def review_word(self, word_id: int, correct: bool, today: Optional[date] = None) -> Word:
        """Bildim/Bilemedim sonucunu uygular ve yeni durumu kaydeder."""
        today = today or date.today()
        word = self.get_word(word_id)
        if word is None:
            raise ValueError(f"Kelime bulunamadi: {word_id}")

        old_state = word.to_state()
        new_state = srs.apply_correct(old_state, today) if correct else srs.apply_incorrect(old_state, today)

        self.conn.execute(
            """UPDATE words
               SET level = ?, level_start_date = ?, streak5 = ?, is_known = ?
               WHERE id = ?""",
            (new_state.level, _iso(new_state.level_start_date), new_state.streak5,
             int(new_state.is_known), word_id),
        )

        if new_state.is_known or srs.is_derivation_activation_level(new_state.level):
            self._activate_pending_derivations(word_id, today)

        self.conn.commit()
        return self.get_word(word_id)
