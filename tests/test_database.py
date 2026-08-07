import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import Database
from app import srs


def make_db(tmp_path):
    return Database(tmp_path / "test.db")


def test_add_folder_and_word(tmp_path):
    db = make_db(tmp_path)
    folder_id = db.add_folder("Ingilizce")
    word_id = db.add_word(folder_id, "apple", "elma", today=date(2026, 1, 1))
    word = db.get_word(word_id)
    assert word.front == "apple"
    assert word.level == 1
    # Yeni eklenen kelime, eklendigi gun tekrar edilebilir olmalidir.
    assert word.next_review_date == date(2026, 1, 1)


def test_new_word_is_due_same_day_it_is_added(tmp_path):
    db = make_db(tmp_path)
    folder_id = db.add_folder("Ingilizce")
    word_id = db.add_word(folder_id, "apple", "elma", today=date(2026, 1, 1))

    due = db.get_due_words(date(2026, 1, 1))
    assert len(due) == 1
    assert due[0].id == word_id


def test_review_word_moves_level_and_persists(tmp_path):
    db = make_db(tmp_path)
    folder_id = db.add_folder("Ingilizce")
    word_id = db.add_word(folder_id, "apple", "elma", today=date(2026, 1, 1))

    updated = db.review_word(word_id, correct=True, today=date(2026, 1, 2))
    assert updated.level == 2
    assert updated.level_start_date == date(2026, 1, 2)

    reloaded = db.get_word(word_id)
    assert reloaded.level == 2


def test_derivation_added_early_starts_pending_until_root_reaches_level4(tmp_path):
    db = make_db(tmp_path)
    en_folder = db.add_folder("Ingilizce")
    de_folder = db.add_folder("Almanca Karsiliklari")

    root_id = db.add_word(en_folder, "grow", "buyumek", today=date(2026, 1, 1))
    root = db.get_word(root_id)
    assert root.level == 1

    # Kok kelime henuz seviye 1'deyken tureme eklenebilir, ama beklemede baslar.
    deriv_id = db.add_word(de_folder, "grow up", "olgunlasmak", parent_id=root_id, today=date(2026, 1, 1))
    deriv = db.get_word(deriv_id)
    assert deriv.is_active is False
    assert deriv.parent_id == root_id

    # Beklemedeki kelime, cok ileri bir tarihte bile tekrar kuyruguna girmez.
    assert all(w.id != deriv_id for w in db.get_due_words(date(2026, 6, 1)))

    # Kok kelime 4. seviyeye cikana kadar ilerler (1 -> 2 -> 3 -> 4).
    day = date(2026, 1, 1)
    for _ in range(3):
        result = db.review_word(root_id, correct=True, today=day)
        day = result.next_review_date
    root_after = db.get_word(root_id)
    assert root_after.level == 4
    assert srs.is_derivation_activation_level(root_after.level)

    # Tureme otomatik olarak aktiflesmis ve o gun tekrar edilebilir olmali.
    deriv_activated = db.get_word(deriv_id)
    assert deriv_activated.is_active is True
    assert deriv_activated.level == 1
    due = db.get_due_words(day)
    assert any(w.id == deriv_id for w in due)

    # Kok kelime dusse bile artik aktif olan tureme etkilenmez.
    db.review_word(root_id, correct=False, today=day)
    root_dropped = db.get_word(root_id)
    assert root_dropped.level == 3
    deriv_still_active = db.get_word(deriv_id)
    assert deriv_still_active.is_active is True
    assert deriv_still_active.level == 1

    derivations = db.get_derivations(root_id)
    assert len(derivations) == 1
    assert derivations[0].id == deriv_id


def test_derivation_added_after_root_already_at_level4_is_active_immediately(tmp_path):
    db = make_db(tmp_path)
    en_folder = db.add_folder("Ingilizce")
    de_folder = db.add_folder("Almanca Karsiliklari")

    root_id = db.add_word(en_folder, "appear", "gorunmek", today=date(2026, 1, 1))
    day = date(2026, 1, 1)
    for _ in range(3):  # 1 -> 2 -> 3 -> 4
        result = db.review_word(root_id, correct=True, today=day)
        day = result.next_review_date
    root = db.get_word(root_id)
    assert root.level == 4

    deriv_id = db.add_word(de_folder, "auftauchen", "gorunmek", parent_id=root_id, today=day)
    deriv = db.get_word(deriv_id)
    assert deriv.is_active is True
    assert deriv.level == 1
    assert any(w.id == deriv_id for w in db.get_due_words(day))


def test_known_word_moves_out_of_due_queue(tmp_path):
    db = make_db(tmp_path)
    folder_id = db.add_folder("Ingilizce")
    word_id = db.add_word(folder_id, "apple", "elma", today=date(2026, 1, 1))

    day = date(2026, 1, 1)
    # 1->2->3->4->5(streak1)->5(streak2)->5(streak3=Bilinenler): 6 dogru cevap gerekir.
    for _ in range(6):
        result = db.review_word(word_id, correct=True, today=day)
        day = result.next_review_date

    word = db.get_word(word_id)
    assert word.level == 5
    assert word.streak5 == 3
    assert word.is_known is True
    assert db.get_due_words(day) == []
    known = db.get_known_words()
    assert len(known) == 1
    assert known[0].id == word_id


def test_delete_word_orphans_its_derivations_instead_of_deleting_them(tmp_path):
    db = make_db(tmp_path)
    en_folder = db.add_folder("Ingilizce")
    de_folder = db.add_folder("Almanca Karsiliklari")

    root_id = db.add_word(en_folder, "grow", "buyumek", today=date(2026, 1, 1))
    deriv_id = db.add_word(de_folder, "grow up", "olgunlasmak", parent_id=root_id, today=date(2026, 1, 1))

    db.delete_word(root_id)

    assert db.get_word(root_id) is None
    deriv = db.get_word(deriv_id)
    assert deriv is not None, "Tureme kelime silinmemeli"
    assert deriv.parent_id is None, "Kok silinince baglanti kopmali"


def test_delete_folder_removes_its_words_and_orphans_cross_folder_derivations(tmp_path):
    db = make_db(tmp_path)
    en_folder = db.add_folder("Ingilizce")
    de_folder = db.add_folder("Almanca Karsiliklari")

    root_id = db.add_word(en_folder, "grow", "buyumek", today=date(2026, 1, 1))
    deriv_id = db.add_word(de_folder, "grow up", "olgunlasmak", parent_id=root_id, today=date(2026, 1, 1))
    other_word_id = db.add_word(en_folder, "book", "kitap", today=date(2026, 1, 1))

    db.delete_folder(en_folder)

    assert db.get_word(root_id) is None
    assert db.get_word(other_word_id) is None
    assert db.folder_exists("Ingilizce") is False

    deriv = db.get_word(deriv_id)
    assert deriv is not None, "Baska klasordeki tureme silinmemeli"
    assert deriv.parent_id is None
    assert db.folder_exists("Almanca Karsiliklari") is True


def test_get_all_words_includes_pending_derivations_for_graph_view(tmp_path):
    db = make_db(tmp_path)
    en_folder = db.add_folder("Ingilizce")

    root_id = db.add_word(en_folder, "grow", "buyumek", today=date(2026, 1, 1))
    deriv_id = db.add_word(en_folder, "grow up", "olgunlasmak", parent_id=root_id, today=date(2026, 1, 1))
    # tureme de kendi tureme kelimesine sahip olabilir (sonsuz derinlik).
    sub_deriv_id = db.add_word(en_folder, "grown-up", "yetiskin", parent_id=deriv_id, today=date(2026, 1, 1))

    all_words = db.get_all_words()
    ids = {w.id for w in all_words}
    assert {root_id, deriv_id, sub_deriv_id} <= ids

    by_id = {w.id: w for w in all_words}
    assert by_id[root_id].parent_id is None
    assert by_id[deriv_id].parent_id == root_id
    assert by_id[deriv_id].is_active is False  # root henuz seviye 4'te degil
    assert by_id[sub_deriv_id].parent_id == deriv_id
