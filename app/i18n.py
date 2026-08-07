"""Basit sozluk tabanli cok dilli metin sistemi.

Qt Linguist (.ts/.qm) araclarina ihtiyac duymaz: her metin bir anahtarla
tanimlanir, o anahtarin uc dildeki karsiligi STRINGS sozlugunde tutulur.
Dinamik icerik icin str.format placeholder'lari kullanilir (ör. "{count}").

Kalici (init'te bir kez kurulan) widget'lar dil degisince guncellenebilmek
icin bir `retranslate_ui()` metodu tanimlar; diyaloglar ise her acildiklarinda
yeniden olusturuldugu icin ekstra bir seye gerek duymadan o anki dili kullanir.
"""

DEFAULT_LANGUAGE = "tr"

LANGUAGES = [
    ("tr", "Türkçe"),
    ("en", "English"),
    ("de", "Deutsch"),
]

_current_language = DEFAULT_LANGUAGE

STRINGS: dict[str, dict[str, str]] = {
    "tr": {
        # Ana pencere
        "app_title": "Kelime Öğrenme - Leitner Sistemi",
        "tab_review": "Bugün Tekrar",
        "tab_folders": "Klasörler",
        "tab_known": "Bilinenler",
        "tab_graph": "Kelime Ağacı",
        "language_label": "Dil:",
        "search_placeholder": "Kelime ara...",
        "search_no_results": "Sonuç bulunamadı.",

        # Genel
        "refresh": "Yenile",
        "close": "Kapat",

        # Bugun Tekrar
        "review_choose_folder": "Bugün tekrar etmek için bir klasör seçin:",
        "folder_due_count": "{name}  —  {count} kelime",
        "no_review_title": "Tekrar yok",
        "no_review_message": "Bu klasörde bugün için tekrar edilecek kelime yok.",
        "back_to_folders": "← Klasörlere Dön",
        "flip": "Çevir",
        "know": "Bildim",
        "dont_know": "Bilemedim",
        "review_progress": "{done}/{total} tamamlandı",
        "review_done_in_folder": "Bu klasörde bugün için tekrar kalmadı.",

        # Klasorler
        "folders_header": "Klasörler",
        "add_folder": "Klasör Ekle",
        "delete_folder": "Klasör Sil",
        "words_header": "Kelimeler (detay için çift tıkla)",
        "add_word": "Kelime Ekle",
        "delete_word": "Kelime Sil",
        "missing_info_title": "Eksik bilgi",
        "folder_name_empty": "Klasör adı boş olamaz.",
        "already_exists_title": "Zaten var",
        "folder_already_exists": "Bu isimde bir klasör zaten var.",
        "no_folder_selected_title": "Klasör seçilmedi",
        "select_folder_first": "Önce soldan bir klasör seçin.",
        "front_back_empty": "Ön yüz ve arka yüz boş olamaz.",
        "no_word_selected_title": "Kelime seçilmedi",
        "select_word_to_delete": "Önce silinecek kelimeyi seçin.",
        "delete_word_title": "Kelimeyi Sil",
        "confirm_delete_word": '"{front}" kelimesini silmek istediğinize emin misiniz?',
        "delete_word_derivations_warning": (
            "\n\nBu kelimeye bağlı {count} türeme kelime var. Onlar silinmeyecek, "
            "sadece bu kök kelimeyle olan bağlantıları kopacak."
        ),
        "select_folder_to_delete": "Önce silinecek klasörü seçin.",
        "delete_folder_title": "Klasörü Sil",
        "confirm_delete_folder": '"{name}" klasörünü silmek istediğinize emin misiniz?',
        "delete_folder_words_warning": (
            "\n\nBu klasördeki {count} kelime de silinecek. Bu kelimelere bağlı, "
            "başka klasörlerdeki türemeler silinmeyecek; sadece kök bağlantıları kopacak."
        ),

        # Bilinenler
        "known_header": "Bilinenler (detay/silme için çift tıkla)",

        # Kelime Agaci
        "graph_legend": (
            "🔵 Aktif   🟢 Bilinenler   ⚪ Beklemede (kök kelime eşik seviyeye ulaşınca aktifleşir)"
            "   ·   Fare tekerleği: yakınlaştır, sürükle: kaydır, çift tıkla: detay"
        ),
        "graph_empty": "Henüz kelime yok.",

        # Kelime durumu
        "status_known": "Bilinenler",
        "status_pending_full": "Beklemede (kök kelime Seviye {level}'e çıkınca aktifleşir)",
        "status_pending_short": "Beklemede",
        "status_level_full": "Seviye {level} · {date}",
        "status_level_short": "Seviye {level}",

        # Diyaloglar
        "dlg_add_folder_title": "Klasör Ekle",
        "folder_name_label": "Klasör adı:",
        "dlg_add_word_title": "Kelime Ekle",
        "front_label": "Ön yüz (kelime):",
        "back_label": "Arka yüz (karşılığı):",
        "dlg_add_derivation_title": "Türeme Kelime Ekle",
        "target_folder_label": "Hedef klasör:",
        "derivation_pending_hint": (
            'Not: "{front}" şu an Seviye {level}. Bu türeme, kök kelime Seviye {threshold}\'e '
            "çıkana kadar beklemede kalacak (seçilen klasörde görünür ama tekrar listesine girmez)."
        ),
        "derivation_active_hint": "Kök kelime eşik seviyede olduğu için bu türeme hemen aktif olacak.",
        "dlg_word_detail_title": "Kelime Detayı",
        "word_not_found": "Kelime bulunamadı.",
        "folder_label": "Klasör: {name}",
        "status_label": "Durum: {status}",
        "level_label": "Seviye: {level}",
        "next_review_label": "Sonraki tekrar: {date}",
        "streak_label": "5. seviye doğru sayacı: {streak}/{target}",
        "root_word_label": "Kök kelime: {front} ({folder})",
        "derivations_header": "Bağlı türeme kelimeler (detay/silme için çift tıkla):",
        "add_derivation_btn": "Türeme Kelime Ekle",
        "delete_word_btn": "Kelimeyi Sil",
        "no_folders_title": "Klasör yok",
        "create_folder_first": "Önce en az bir klasör oluşturmalısınız.",
        "confirm_delete_word_with_derivs": (
            '"{front}" kelimesini silmek istediğinize emin misiniz?'
            "\n\nBu kelimeye bağlı {count} türeme kelime var. Onlar silinmeyecek, sadece bu kök "
            "kelimeyle olan bağlantıları kopacak ve bağımsız kelimeler olarak kalacaklar."
        ),
    },
    "en": {
        "app_title": "Vocabulary Trainer - Leitner System",
        "tab_review": "Today's Review",
        "tab_folders": "Folders",
        "tab_known": "Known Words",
        "tab_graph": "Word Map",
        "language_label": "Language:",
        "search_placeholder": "Search words...",
        "search_no_results": "No results found.",

        "refresh": "Refresh",
        "close": "Close",

        "review_choose_folder": "Choose a folder to review today:",
        "folder_due_count": "{name}  —  {count} words",
        "no_review_title": "No review",
        "no_review_message": "There are no words due for review in this folder today.",
        "back_to_folders": "← Back to Folders",
        "flip": "Flip",
        "know": "I knew it",
        "dont_know": "I didn't know",
        "review_progress": "{done}/{total} completed",
        "review_done_in_folder": "No more reviews left in this folder for today.",

        "folders_header": "Folders",
        "add_folder": "Add Folder",
        "delete_folder": "Delete Folder",
        "words_header": "Words (double-click for details)",
        "add_word": "Add Word",
        "delete_word": "Delete Word",
        "missing_info_title": "Missing information",
        "folder_name_empty": "Folder name cannot be empty.",
        "already_exists_title": "Already exists",
        "folder_already_exists": "A folder with this name already exists.",
        "no_folder_selected_title": "No folder selected",
        "select_folder_first": "Please select a folder on the left first.",
        "front_back_empty": "Front and back cannot be empty.",
        "no_word_selected_title": "No word selected",
        "select_word_to_delete": "Please select a word to delete first.",
        "delete_word_title": "Delete Word",
        "confirm_delete_word": 'Are you sure you want to delete "{front}"?',
        "delete_word_derivations_warning": (
            "\n\nThis word has {count} linked derivation word(s). They won't be deleted, "
            "only their link to this root word will be removed."
        ),
        "select_folder_to_delete": "Please select a folder to delete first.",
        "delete_folder_title": "Delete Folder",
        "confirm_delete_folder": 'Are you sure you want to delete the folder "{name}"?',
        "delete_folder_words_warning": (
            "\n\nThe {count} word(s) in this folder will also be deleted. Derivations of these "
            "words living in other folders won't be deleted; only their root link will be removed."
        ),

        "known_header": "Known Words (double-click for details/delete)",

        "graph_legend": (
            "🔵 Active   🟢 Known   ⚪ Pending (activates once the root word reaches the threshold level)"
            "   ·   Scroll: zoom, drag: pan, double-click: details"
        ),
        "graph_empty": "No words yet.",

        "status_known": "Known",
        "status_pending_full": "Pending (activates once the root word reaches Level {level})",
        "status_pending_short": "Pending",
        "status_level_full": "Level {level} · {date}",
        "status_level_short": "Level {level}",

        "dlg_add_folder_title": "Add Folder",
        "folder_name_label": "Folder name:",
        "dlg_add_word_title": "Add Word",
        "front_label": "Front (word):",
        "back_label": "Back (translation):",
        "dlg_add_derivation_title": "Add Derivation Word",
        "target_folder_label": "Target folder:",
        "derivation_pending_hint": (
            'Note: "{front}" is currently at Level {level}. This derivation will stay pending '
            "until the root word reaches Level {threshold} (it will be visible in the selected "
            "folder but won't enter the review queue)."
        ),
        "derivation_active_hint": (
            "This derivation will be active immediately since the root word is already at the "
            "threshold level."
        ),
        "dlg_word_detail_title": "Word Details",
        "word_not_found": "Word not found.",
        "folder_label": "Folder: {name}",
        "status_label": "Status: {status}",
        "level_label": "Level: {level}",
        "next_review_label": "Next review: {date}",
        "streak_label": "Level 5 correct streak: {streak}/{target}",
        "root_word_label": "Root word: {front} ({folder})",
        "derivations_header": "Linked derivation words (double-click for details/delete):",
        "add_derivation_btn": "Add Derivation",
        "delete_word_btn": "Delete Word",
        "no_folders_title": "No folders",
        "create_folder_first": "You need to create at least one folder first.",
        "confirm_delete_word_with_derivs": (
            'Are you sure you want to delete "{front}"?'
            "\n\nThis word has {count} linked derivation word(s). They won't be deleted, only "
            "their link to this root word will be removed and they'll remain as independent words."
        ),
    },
    "de": {
        "app_title": "Vokabeltrainer - Leitner-System",
        "tab_review": "Heute wiederholen",
        "tab_folders": "Ordner",
        "tab_known": "Gelernte Wörter",
        "tab_graph": "Wortnetz",
        "language_label": "Sprache:",
        "search_placeholder": "Wörter suchen...",
        "search_no_results": "Keine Ergebnisse gefunden.",

        "refresh": "Aktualisieren",
        "close": "Schließen",

        "review_choose_folder": "Wähle einen Ordner für die heutige Wiederholung:",
        "folder_due_count": "{name}  —  {count} Wörter",
        "no_review_title": "Keine Wiederholung",
        "no_review_message": "In diesem Ordner gibt es heute keine fälligen Wörter.",
        "back_to_folders": "← Zurück zu den Ordnern",
        "flip": "Umdrehen",
        "know": "Ich wusste es",
        "dont_know": "Ich wusste es nicht",
        "review_progress": "{done}/{total} abgeschlossen",
        "review_done_in_folder": "Keine weiteren Wiederholungen in diesem Ordner für heute.",

        "folders_header": "Ordner",
        "add_folder": "Ordner hinzufügen",
        "delete_folder": "Ordner löschen",
        "words_header": "Wörter (Doppelklick für Details)",
        "add_word": "Wort hinzufügen",
        "delete_word": "Wort löschen",
        "missing_info_title": "Fehlende Angabe",
        "folder_name_empty": "Der Ordnername darf nicht leer sein.",
        "already_exists_title": "Bereits vorhanden",
        "folder_already_exists": "Ein Ordner mit diesem Namen existiert bereits.",
        "no_folder_selected_title": "Kein Ordner ausgewählt",
        "select_folder_first": "Bitte wähle zuerst links einen Ordner aus.",
        "front_back_empty": "Vorder- und Rückseite dürfen nicht leer sein.",
        "no_word_selected_title": "Kein Wort ausgewählt",
        "select_word_to_delete": "Bitte wähle zuerst das zu löschende Wort aus.",
        "delete_word_title": "Wort löschen",
        "confirm_delete_word": 'Möchtest du "{front}" wirklich löschen?',
        "delete_word_derivations_warning": (
            "\n\nDieses Wort hat {count} verknüpfte Ableitung(en). Sie werden nicht gelöscht, "
            "nur die Verknüpfung zu diesem Wurzelwort wird entfernt."
        ),
        "select_folder_to_delete": "Bitte wähle zuerst den zu löschenden Ordner aus.",
        "delete_folder_title": "Ordner löschen",
        "confirm_delete_folder": 'Möchtest du den Ordner "{name}" wirklich löschen?',
        "delete_folder_words_warning": (
            "\n\nDie {count} Wörter in diesem Ordner werden ebenfalls gelöscht. Ableitungen dieser "
            "Wörter in anderen Ordnern werden nicht gelöscht; nur ihre Wurzel-Verknüpfung wird entfernt."
        ),

        "known_header": "Gelernte Wörter (Doppelklick für Details/Löschen)",

        "graph_legend": (
            "🔵 Aktiv   🟢 Gelernt   ⚪ Wartend (aktiviert sich, sobald das Wurzelwort die Schwellenstufe erreicht)"
            "   ·   Scrollen: zoomen, Ziehen: verschieben, Doppelklick: Details"
        ),
        "graph_empty": "Noch keine Wörter.",

        "status_known": "Gelernt",
        "status_pending_full": "Wartend (aktiviert sich, sobald das Wurzelwort Stufe {level} erreicht)",
        "status_pending_short": "Wartend",
        "status_level_full": "Stufe {level} · {date}",
        "status_level_short": "Stufe {level}",

        "dlg_add_folder_title": "Ordner hinzufügen",
        "folder_name_label": "Ordnername:",
        "dlg_add_word_title": "Wort hinzufügen",
        "front_label": "Vorderseite (Wort):",
        "back_label": "Rückseite (Übersetzung):",
        "dlg_add_derivation_title": "Ableitung hinzufügen",
        "target_folder_label": "Zielordner:",
        "derivation_pending_hint": (
            'Hinweis: "{front}" ist derzeit auf Stufe {level}. Diese Ableitung bleibt wartend, bis '
            "das Wurzelwort Stufe {threshold} erreicht (sie ist im gewählten Ordner sichtbar, kommt "
            "aber nicht in die Wiederholungs-Warteschlange)."
        ),
        "derivation_active_hint": (
            "Diese Ableitung wird sofort aktiv, da das Wurzelwort bereits die Schwellenstufe erreicht hat."
        ),
        "dlg_word_detail_title": "Wortdetails",
        "word_not_found": "Wort nicht gefunden.",
        "folder_label": "Ordner: {name}",
        "status_label": "Status: {status}",
        "level_label": "Stufe: {level}",
        "next_review_label": "Nächste Wiederholung: {date}",
        "streak_label": "Stufe-5-Richtig-Serie: {streak}/{target}",
        "root_word_label": "Wurzelwort: {front} ({folder})",
        "derivations_header": "Verknüpfte Ableitungen (Doppelklick für Details/Löschen):",
        "add_derivation_btn": "Ableitung hinzufügen",
        "delete_word_btn": "Wort löschen",
        "no_folders_title": "Keine Ordner",
        "create_folder_first": "Du musst zuerst mindestens einen Ordner erstellen.",
        "confirm_delete_word_with_derivs": (
            'Möchtest du "{front}" wirklich löschen?'
            "\n\nDieses Wort hat {count} verknüpfte Ableitung(en). Sie werden nicht gelöscht, nur "
            "die Verknüpfung zu diesem Wurzelwort wird entfernt, und sie bleiben als eigenständige "
            "Wörter bestehen."
        ),
    },
}


def set_language(lang: str):
    global _current_language
    if lang in STRINGS:
        _current_language = lang


def get_language() -> str:
    return _current_language


def tr(key: str, **kwargs) -> str:
    """Gecerli dildeki metni dondurur; eksikse Turkce'ye, o da yoksa anahtarin
    kendisine duser (gelistirme sirasinda eksik ceviriyi fark etmeyi kolaylastirir)."""
    text = STRINGS.get(_current_language, {}).get(key)
    if text is None:
        text = STRINGS[DEFAULT_LANGUAGE].get(key, key)
    return text.format(**kwargs) if kwargs else text
