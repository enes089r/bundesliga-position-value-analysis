"""Klasor olusturma ve klasor icinde kelime ekleme/goruntuleme sekmesi."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.database import Database
from app.i18n import tr
from app.ui.dialogs import AddFolderDialog, AddWordDialog, WordDetailDialog
from app.ui.formatting import word_status_text


class FoldersWidget(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self._current_folder_id = None

        self.folder_list = QListWidget()
        self.folder_list.currentItemChanged.connect(self._on_folder_selected)
        self.add_folder_btn = QPushButton()
        self.add_folder_btn.clicked.connect(self._on_add_folder)
        self.delete_folder_btn = QPushButton()
        self.delete_folder_btn.clicked.connect(self._on_delete_folder)

        folder_btn_row = QHBoxLayout()
        folder_btn_row.addWidget(self.add_folder_btn)
        folder_btn_row.addWidget(self.delete_folder_btn)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        self.folders_header_label = QLabel()
        left_layout.addWidget(self.folders_header_label)
        left_layout.addWidget(self.folder_list)
        left_layout.addLayout(folder_btn_row)

        self.word_list = QListWidget()
        self.word_list.itemDoubleClicked.connect(self._on_word_double_clicked)
        self.add_word_btn = QPushButton()
        self.add_word_btn.clicked.connect(self._on_add_word)
        self.delete_word_btn = QPushButton()
        self.delete_word_btn.clicked.connect(self._on_delete_word)

        word_btn_row = QHBoxLayout()
        word_btn_row.addWidget(self.add_word_btn)
        word_btn_row.addWidget(self.delete_word_btn)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        self.words_header_label = QLabel()
        right_layout.addWidget(self.words_header_label)
        right_layout.addWidget(self.word_list)
        right_layout.addLayout(word_btn_row)

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(1, 2)

        layout = QHBoxLayout(self)
        layout.addWidget(splitter)

        self.retranslate_ui()
        self.refresh_folders()

    def retranslate_ui(self):
        self.folders_header_label.setText(tr("folders_header"))
        self.add_folder_btn.setText(tr("add_folder"))
        self.delete_folder_btn.setText(tr("delete_folder"))
        self.words_header_label.setText(tr("words_header"))
        self.add_word_btn.setText(tr("add_word"))
        self.delete_word_btn.setText(tr("delete_word"))
        self._refresh_words()

    def refresh_folders(self):
        self.folder_list.clear()
        for folder in self.db.get_folders():
            item = QListWidgetItem(folder["name"])
            item.setData(Qt.UserRole, folder["id"])
            self.folder_list.addItem(item)

    def _on_add_folder(self):
        dialog = AddFolderDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name = dialog.folder_name
            if not name:
                QMessageBox.warning(self, tr("missing_info_title"), tr("folder_name_empty"))
                return
            if self.db.folder_exists(name):
                QMessageBox.warning(self, tr("already_exists_title"), tr("folder_already_exists"))
                return
            self.db.add_folder(name)
            self.refresh_folders()

    def _on_folder_selected(self, current, _previous):
        self._current_folder_id = current.data(Qt.UserRole) if current else None
        self._refresh_words()

    def _refresh_words(self):
        self.word_list.clear()
        if self._current_folder_id is None:
            return
        for word in self.db.get_words_by_folder(self._current_folder_id):
            item = QListWidgetItem(f"{word.front} → {word.back}  [{word_status_text(word)}]")
            item.setData(Qt.UserRole, word.id)
            self.word_list.addItem(item)

    def _on_add_word(self):
        if self._current_folder_id is None:
            QMessageBox.warning(self, tr("no_folder_selected_title"), tr("select_folder_first"))
            return
        dialog = AddWordDialog(self)
        if dialog.exec() == QDialog.Accepted:
            if not dialog.front or not dialog.back:
                QMessageBox.warning(self, tr("missing_info_title"), tr("front_back_empty"))
                return
            self.db.add_word(self._current_folder_id, dialog.front, dialog.back)
            self._refresh_words()

    def _on_word_double_clicked(self, item: QListWidgetItem):
        word_id = item.data(Qt.UserRole)
        dialog = WordDetailDialog(self.db, word_id, self)
        dialog.exec()
        self._refresh_words()

    def _on_delete_word(self):
        item = self.word_list.currentItem()
        if item is None:
            QMessageBox.warning(self, tr("no_word_selected_title"), tr("select_word_to_delete"))
            return
        word_id = item.data(Qt.UserRole)
        word = self.db.get_word(word_id)
        if word is None:
            return
        derivations = self.db.get_derivations(word_id)
        message = tr("confirm_delete_word", front=word.front)
        if derivations:
            message += tr("delete_word_derivations_warning", count=len(derivations))
        reply = QMessageBox.question(
            self, tr("delete_word_title"), message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_word(word_id)
            self._refresh_words()

    def _on_delete_folder(self):
        item = self.folder_list.currentItem()
        if item is None:
            QMessageBox.warning(self, tr("no_folder_selected_title"), tr("select_folder_to_delete"))
            return
        folder_id = item.data(Qt.UserRole)
        folder_name = item.text()
        word_count = len(self.db.get_words_by_folder(folder_id))
        message = tr("confirm_delete_folder", name=folder_name)
        if word_count:
            message += tr("delete_folder_words_warning", count=word_count)
        reply = QMessageBox.question(
            self, tr("delete_folder_title"), message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_folder(folder_id)
            self._current_folder_id = None
            self.refresh_folders()
            self.word_list.clear()

    def refresh(self):
        """Sekmeye donuldugunde secili klasorun kelime listesini gunceller."""
        self._refresh_words()
