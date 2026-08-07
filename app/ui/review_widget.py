"""'Bugun Tekrar Edilecekler' akisi.

Once klasorler listelenir; her klasorun yaninda o gun tekrar edilecek
kelime sayisi gosterilir. Bir klasore tiklandiginda, sadece o klasorun
vadesi gelmis kelimeleri icin kart cevirme + Bildim/Bilemedim akisi
baslar. Uygulama acilir acilmaz dogrudan bir kart gosterilmez.
"""
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.database import Database
from app.i18n import tr


class ReviewWidget(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.queue: list[int] = []
        self.total_count = 0
        self.current_word_id: int | None = None
        self.current_folder_id: int | None = None
        self._current_folder_name = ""

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_folder_page())
        self.stack.addWidget(self._build_card_page())

        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.choose_folder_label.setText(tr("review_choose_folder"))
        self.folder_refresh_btn.setText(tr("refresh"))
        self.back_btn.setText(tr("back_to_folders"))
        self.flip_btn.setText(tr("flip"))
        self.know_btn.setText(tr("know"))
        self.dont_know_btn.setText(tr("dont_know"))
        self.show_folder_page()

    # --- Klasor secim sayfasi ---

    def _build_folder_page(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.choose_folder_label = QLabel()
        layout.addWidget(self.choose_folder_label)

        self.folder_due_list = QListWidget()
        self.folder_due_list.itemDoubleClicked.connect(self._on_folder_chosen)
        layout.addWidget(self.folder_due_list)

        self.folder_refresh_btn = QPushButton()
        self.folder_refresh_btn.clicked.connect(self.show_folder_page)
        layout.addWidget(self.folder_refresh_btn)
        return widget

    def show_folder_page(self):
        today = date.today()
        due_words = self.db.get_due_words(today)
        counts: dict[int, int] = {}
        for w in due_words:
            counts[w.folder_id] = counts.get(w.folder_id, 0) + 1

        self.folder_due_list.clear()
        for folder in self.db.get_folders():
            count = counts.get(folder["id"], 0)
            item = QListWidgetItem(tr("folder_due_count", name=folder["name"], count=count))
            item.setData(Qt.UserRole, folder["id"])
            item.setData(Qt.UserRole + 1, folder["name"])
            self.folder_due_list.addItem(item)

        self.stack.setCurrentIndex(0)

    def _on_folder_chosen(self, item: QListWidgetItem):
        folder_id = item.data(Qt.UserRole)
        folder_name = item.data(Qt.UserRole + 1)
        today = date.today()
        due_words = self.db.get_due_words(today, folder_id=folder_id)
        if not due_words:
            QMessageBox.information(self, tr("no_review_title"), tr("no_review_message"))
            return

        self.current_folder_id = folder_id
        self._current_folder_name = folder_name
        self.folder_name_label.setText(folder_name)
        self.queue = [w.id for w in due_words]
        self.total_count = len(self.queue)
        self.stack.setCurrentIndex(1)
        self._show_next()

    # --- Kart tekrar sayfasi ---

    def _build_card_page(self) -> QWidget:
        widget = QWidget()

        self.back_btn = QPushButton()
        self.back_btn.clicked.connect(self.show_folder_page)

        self.folder_name_label = QLabel()
        self.folder_name_label.setAlignment(Qt.AlignCenter)

        self.progress_label = QLabel()
        self.progress_label.setAlignment(Qt.AlignCenter)

        self.card_label = QLabel()
        self.card_label.setAlignment(Qt.AlignCenter)
        font = self.card_label.font()
        font.setPointSize(24)
        self.card_label.setFont(font)
        self.card_label.setWordWrap(True)
        self.card_label.setMinimumHeight(120)

        self.flip_btn = QPushButton()
        self.flip_btn.clicked.connect(self._on_flip)

        self.know_btn = QPushButton()
        self.know_btn.clicked.connect(lambda: self._on_answer(True))
        self.dont_know_btn = QPushButton()
        self.dont_know_btn.clicked.connect(lambda: self._on_answer(False))
        self.know_btn.setVisible(False)
        self.dont_know_btn.setVisible(False)

        answer_row = QHBoxLayout()
        answer_row.addWidget(self.dont_know_btn)
        answer_row.addWidget(self.know_btn)

        layout = QVBoxLayout(widget)
        layout.addWidget(self.back_btn)
        layout.addWidget(self.folder_name_label)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.card_label)
        layout.addWidget(self.flip_btn)
        layout.addLayout(answer_row)
        layout.addStretch()
        return widget

    def _show_next(self):
        self.know_btn.setVisible(False)
        self.dont_know_btn.setVisible(False)

        if not self.queue:
            self.current_word_id = None
            self.card_label.setText(tr("review_done_in_folder"))
            self.flip_btn.setVisible(False)
            self.progress_label.setText("")
            return

        self.flip_btn.setVisible(True)
        self.current_word_id = self.queue[0]
        word = self.db.get_word(self.current_word_id)
        remaining = len(self.queue)
        done = self.total_count - remaining
        self.progress_label.setText(tr("review_progress", done=done, total=self.total_count))
        self.card_label.setText(word.front)

    def _on_flip(self):
        if self.current_word_id is None:
            return
        word = self.db.get_word(self.current_word_id)
        self.card_label.setText(f"{word.front}\n\n{word.back}")
        self.flip_btn.setVisible(False)
        self.know_btn.setVisible(True)
        self.dont_know_btn.setVisible(True)

    def _on_answer(self, correct: bool):
        if self.current_word_id is None:
            return
        self.db.review_word(self.current_word_id, correct, date.today())
        self.queue.pop(0)
        self._show_next()
