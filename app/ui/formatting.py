"""Kelime durumunu (aktif/beklemede/bilinenler) gecerli dilde metne cevirir.

Bu mantik veritabani katmanindan (dilden bagimsiz olmali) ayri tutulur;
UI, kelime nesnesinin ham alanlarina (is_known/is_active/level) bakip
i18n.tr() ile goruntulenecek metni burada olusturur.
"""
from app import srs
from app.database import Word
from app.i18n import tr


def word_status_text(word: Word) -> str:
    """Detay/liste gorunumlerinde kullanilan uzun durum metni."""
    if word.is_known:
        return tr("status_known")
    if not word.is_active:
        return tr("status_pending_full", level=srs.DERIVATION_ACTIVATION_LEVEL)
    return tr("status_level_full", level=word.level, date=word.next_review_date.isoformat())


def word_status_short(word: Word) -> str:
    """Kelime agacindaki baloncuklar gibi dar alanlarda kullanilan kisa metin."""
    if word.is_known:
        return tr("status_known")
    if not word.is_active:
        return tr("status_pending_short")
    return tr("status_level_short", level=word.level)
