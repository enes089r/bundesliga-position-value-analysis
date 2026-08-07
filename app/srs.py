"""Leitner seviye kurallari ve tarih hesaplamalari.

Bu modul veritabanindan bagimsizdir; sadece saf fonksiyonlar icerir.
Boylece is mantigi UI/DB katmanlarindan ayri test edilebilir.
"""
from dataclasses import dataclass
from datetime import date, timedelta

MIN_LEVEL = 1
MAX_LEVEL = 5
KNOWN_STREAK_TARGET = 3

# Seviye -> tekrar araligi (gun)
INTERVALS = {
    1: 1,
    2: 2,
    3: 4,
    4: 9,
    5: 14,
}


def interval_days(level: int) -> int:
    if level not in INTERVALS:
        raise ValueError(f"Gecersiz seviye: {level}")
    return INTERVALS[level]


def next_review_date(level_start_date: date, level: int) -> date:
    """Kelimenin bu seviyeye girdigi tarihten itibaren bir sonraki tekrar tarihi."""
    return level_start_date + timedelta(days=interval_days(level))


def is_due(level_start_date: date, level: int, today: date) -> bool:
    return today >= next_review_date(level_start_date, level)


@dataclass(frozen=True)
class WordState:
    """Bir kelimenin Leitner durumu (DB satirinin ilgili alt kumesi)."""
    level: int
    level_start_date: date
    streak5: int
    is_known: bool


def apply_correct(state: WordState, today: date) -> WordState:
    """"Bildim" basildiginda kelimenin yeni durumunu hesaplar."""
    if state.is_known:
        return state

    if state.level < MAX_LEVEL:
        new_level = state.level + 1
        # 5. seviyeye ilk cikis ayni zamanda 1. dogru sayilir.
        new_streak = 1 if new_level == MAX_LEVEL else 0
        return WordState(level=new_level, level_start_date=today, streak5=new_streak, is_known=False)

    # Kelime zaten 5. seviyede.
    new_streak = state.streak5 + 1
    if new_streak >= KNOWN_STREAK_TARGET:
        return WordState(level=MAX_LEVEL, level_start_date=today, streak5=new_streak, is_known=True)
    return WordState(level=MAX_LEVEL, level_start_date=today, streak5=new_streak, is_known=False)


def apply_incorrect(state: WordState, today: date) -> WordState:
    """"Bilemedim" basildiginda kelimenin yeni durumunu hesaplar."""
    if state.is_known:
        return state

    if state.level == MAX_LEVEL:
        # 5. seviyede basarisizlik: 4. seviyeye dus, sayac sifirlanir.
        return WordState(level=MAX_LEVEL - 1, level_start_date=today, streak5=0, is_known=False)

    new_level = max(MIN_LEVEL, state.level - 1)
    return WordState(level=new_level, level_start_date=today, streak5=0, is_known=False)


DERIVATION_ACTIVATION_LEVEL = 4


def is_derivation_activation_level(level: int) -> bool:
    """Bir kelime bu seviyeye (veya ustune) ciktiginda, ona bagli 'beklemede'
    tureme kelimeler otomatik olarak aktiflesir (tekrar dongusune girer).

    Tureme kelimeler her zaman eklenebilir; sadece eklendikleri anda ebeveyn
    kelime bu esigin altindaysa "beklemede" (pasif) baslarlar.
    """
    return level >= DERIVATION_ACTIVATION_LEVEL
