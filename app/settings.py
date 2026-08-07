"""Kucuk kalicilik: kullanicinin sectigi dili yeniden baslatmalar arasinda hatirlar.

Veritabani semasina dokunmamak icin ayri, basit bir JSON dosyasi kullanilir.
"""
import json
from pathlib import Path

from app.i18n import DEFAULT_LANGUAGE, STRINGS

SETTINGS_PATH = Path(__file__).resolve().parent.parent / "settings.json"


def load_language(path: Path | None = None) -> str:
    """path verilmezse cagri anindaki module-level SETTINGS_PATH kullanilir
    (testlerin settings.SETTINGS_PATH'i degistirerek izole calisabilmesi icin
    bu bilerek bir varsayilan parametre degeri olarak sabitlenmez)."""
    if path is None:
        path = SETTINGS_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        lang = data.get("language")
        if lang in STRINGS:
            return lang
    except (OSError, ValueError):
        pass
    return DEFAULT_LANGUAGE


def save_language(lang: str, path: Path | None = None):
    if path is None:
        path = SETTINGS_PATH
    path.write_text(json.dumps({"language": lang}), encoding="utf-8")
