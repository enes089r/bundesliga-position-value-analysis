"""'Bilinenler' listesini gosteren sekme."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from app.database import Database
from app.i18n import tr
from app.ui.dialogs import WordDetailDialog


class KnownWidget(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db

        self.header_label = QLabel()
        self.known_list = QListWidget()
        self.known_list.itemDoubleClicked.connect(self._on_word_double_clicked)
        self.refresh_btn = QPushButton()
        self.refresh_btn.clicked.connect(self.refresh)

        layout = QVBoxLayout(self)
        layout.addWidget(self.header_label)
        layout.addWidget(self.known_list)
        layout.addWidget(self.refresh_btn)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.header_label.setText(tr("known_header"))
        self.refresh_btn.setText(tr("refresh"))
        self.refresh()

    def refresh(self):
        self.known_list.clear()
        for word in self.db.get_known_words():
            item = QListWidgetItem(f"{word.front} → {word.back}  [{word.folder_name}]")
            item.setData(Qt.UserRole, word.id)
            self.known_list.addItem(item)

    def _on_word_double_clicked(self, item: QListWidgetItem):
        word_id = item.data(Qt.UserRole)
        dialog = WordDetailDialog(self.db, word_id, self)
        dialog.exec()
        self.refresh()
