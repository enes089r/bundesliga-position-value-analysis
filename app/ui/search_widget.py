"""Global kelime arama cubugu.

Klasor/turevlik farki gozetmeksizin TUM kelimelerin on ve arka yuzunde
harf-buyuklugu ve Turkce/Almanca ozel karakterlerden bagimsiz alt-metin
eslesmesi arar (str.casefold ile) ve eslesenleri anlik olarak listeler.
Bir sonuca cift tiklamak/Enter'a basmak o kelimenin detay penceresini acar.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from app.database import Database
from app.i18n import tr
from app.ui.dialogs import WordDetailDialog
from app.ui.formatting import word_status_text

MAX_RESULTS = 20


class SearchWidget(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db

        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self._on_text_changed)
        self.search_edit.returnPressed.connect(self._on_return_pressed)

        self.results_list = QListWidget()
        self.results_list.setMaximumHeight(170)
        self.results_list.itemActivated.connect(self._on_result_chosen)
        self.results_list.setVisible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.search_edit)
        layout.addWidget(self.results_list)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.search_edit.setPlaceholderText(tr("search_placeholder"))
        self._refresh_results()

    def _on_text_changed(self, _text: str):
        self._refresh_results()

    def _refresh_results(self):
        query = self.search_edit.text().strip().casefold()
        self.results_list.clear()
        if not query:
            self.results_list.setVisible(False)
            return

        matches = [
            w for w in self.db.get_all_words()
            if query in w.front.casefold() or query in w.back.casefold()
        ]
        matches.sort(key=lambda w: w.front.casefold())

        if not matches:
            placeholder = QListWidgetItem(tr("search_no_results"))
            placeholder.setFlags(Qt.NoItemFlags)
            self.results_list.addItem(placeholder)
            self.results_list.setVisible(True)
            return

        for w in matches[:MAX_RESULTS]:
            item = QListWidgetItem(f"{w.front} → {w.back}  [{w.folder_name} · {word_status_text(w)}]")
            item.setData(Qt.UserRole, w.id)
            self.results_list.addItem(item)
        self.results_list.setVisible(True)

    def _on_return_pressed(self):
        first = self.results_list.item(0)
        if first is not None and first.data(Qt.UserRole) is not None:
            self._on_result_chosen(first)

    def _on_result_chosen(self, item: QListWidgetItem):
        word_id = item.data(Qt.UserRole)
        if word_id is None:
            return
        dialog = WordDetailDialog(self.db, word_id, self)
        dialog.exec()
        self._refresh_results()
