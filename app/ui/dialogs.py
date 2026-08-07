"""Klasor/kelime ekleme ve kelime detayi icin diyalog pencereleri.

Diyaloglar her acildiklarinda yeniden olusturuldugu icin (modal, kisa omurlu)
o anki dili otomatik yansitirlar; ayrica bir retranslate_ui() gerekmez.
"""
from datetime import date
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app import srs
from app.database import Database, Word
from app.i18n import tr
from app.ui.formatting import word_status_text


class AddFolderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_add_folder_title"))
        self.name_edit = QLineEdit()

        form = QFormLayout()
        form.addRow(tr("folder_name_label"), self.name_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    @property
    def folder_name(self) -> str:
        return self.name_edit.text().strip()


class AddWordDialog(QDialog):
    """Bir klasore yeni kelime eklemek icin kullanilir."""

    def __init__(self, parent=None, title: Optional[str] = None):
        super().__init__(parent)
        self.setWindowTitle(title if title is not None else tr("dlg_add_word_title"))
        self.front_edit = QLineEdit()
        self.back_edit = QLineEdit()

        form = QFormLayout()
        form.addRow(tr("front_label"), self.front_edit)
        form.addRow(tr("back_label"), self.back_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    @property
    def front(self) -> str:
        return self.front_edit.text().strip()

    @property
    def back(self) -> str:
        return self.back_edit.text().strip()


class DerivationAddDialog(QDialog):
    """Tureme kelime eklerken hedef klasor de sectirilir.

    Ebeveyn kelime henuz esik seviyeye ulasmamissa, eklenen tureme
    "beklemede" baslar; ebeveyn esige ulastiginda otomatik aktiflesir.

    Hedef klasor secimi, bir sonraki tureme eklemede varsayilan olarak
    hatirlanir (last_folder_id sinif degiskeninde tutulur).
    """

    last_folder_id: Optional[int] = None

    def __init__(self, db: Database, parent_word: Word, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle(tr("dlg_add_derivation_title"))

        self.front_edit = QLineEdit()
        self.back_edit = QLineEdit()
        self.folder_combo = QComboBox()
        self._folders = db.get_folders()
        for f in self._folders:
            self.folder_combo.addItem(f["name"], f["id"])
        if DerivationAddDialog.last_folder_id is not None:
            idx = self.folder_combo.findData(DerivationAddDialog.last_folder_id)
            if idx >= 0:
                self.folder_combo.setCurrentIndex(idx)

        form = QFormLayout()
        form.addRow(tr("front_label"), self.front_edit)
        form.addRow(tr("back_label"), self.back_edit)
        form.addRow(tr("target_folder_label"), self.folder_combo)

        will_be_pending = not parent_word.is_known and not srs.is_derivation_activation_level(parent_word.level)
        hint = QLabel()
        hint.setWordWrap(True)
        if will_be_pending:
            hint.setText(tr(
                "derivation_pending_hint",
                front=parent_word.front,
                level=parent_word.level,
                threshold=srs.DERIVATION_ACTIVATION_LEVEL,
            ))
        else:
            hint.setText(tr("derivation_active_hint"))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(hint)
        layout.addWidget(buttons)

    @property
    def front(self) -> str:
        return self.front_edit.text().strip()

    @property
    def back(self) -> str:
        return self.back_edit.text().strip()

    @property
    def folder_id(self):
        return self.folder_combo.currentData()


class WordDetailDialog(QDialog):
    """Bir kelimenin durumunu ve bagli turemelerini gosterir."""

    def __init__(self, db: Database, word_id: int, parent=None):
        super().__init__(parent)
        self.db = db
        self.word_id = word_id
        self.setWindowTitle(tr("dlg_word_detail_title"))
        self.setMinimumWidth(420)

        self.info_label = QLabel()
        self.info_label.setWordWrap(True)

        self.derivations_header = QLabel(tr("derivations_header"))
        self.derivations_list = QListWidget()
        self.derivations_list.itemDoubleClicked.connect(self._on_derivation_double_clicked)

        self.add_derivation_btn = QPushButton(tr("add_derivation_btn"))
        self.add_derivation_btn.clicked.connect(self._on_add_derivation)

        self.delete_btn = QPushButton(tr("delete_word_btn"))
        self.delete_btn.clicked.connect(self._on_delete_word)

        close_btn = QPushButton(tr("close"))
        close_btn.clicked.connect(self.accept)

        button_row = QHBoxLayout()
        button_row.addWidget(self.add_derivation_btn)
        button_row.addWidget(self.delete_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.info_label)
        layout.addWidget(self.derivations_header)
        layout.addWidget(self.derivations_list)
        layout.addLayout(button_row)
        layout.addWidget(close_btn)

        self._reload()

    def _reload(self):
        word = self.db.get_word(self.word_id)
        if word is None:
            self.info_label.setText(tr("word_not_found"))
            self.add_derivation_btn.setEnabled(False)
            return

        lines = [
            f"<b>{word.front}</b> &rarr; {word.back}",
            tr("folder_label", name=word.folder_name),
        ]
        if not word.is_active:
            lines.append(tr("status_label", status=f"<b>{word_status_text(word)}</b>"))
        elif word.is_known:
            lines.append(tr("status_label", status=f"<b>{word_status_text(word)}</b>"))
        else:
            lines.append(tr("level_label", level=word.level))
            lines.append(tr("next_review_label", date=word.next_review_date.isoformat()))
            if word.level == srs.MAX_LEVEL:
                lines.append(tr("streak_label", streak=word.streak5, target=srs.KNOWN_STREAK_TARGET))
        if word.parent_id:
            parent = self.db.get_word(word.parent_id)
            if parent:
                lines.append(tr("root_word_label", front=parent.front, folder=parent.folder_name))

        self.info_label.setText("<br>".join(lines))
        self._word = word

        self.derivations_list.clear()
        for d in self.db.get_derivations(self.word_id):
            item = QListWidgetItem(f"{d.front} → {d.back}  [{d.folder_name} · {word_status_text(d)}]")
            item.setData(Qt.UserRole, d.id)
            self.derivations_list.addItem(item)

        # Tureme her zaman eklenebilir; esik seviyeye ulasilmadan eklenirse
        # DerivationAddDialog kullaniciyi "beklemede baslayacak" diye bilgilendirir.
        self.add_derivation_btn.setEnabled(True)

    def _on_add_derivation(self):
        if not self.db.get_folders():
            QMessageBox.warning(self, tr("no_folders_title"), tr("create_folder_first"))
            return

        dialog = DerivationAddDialog(self.db, self._word, self)
        if dialog.exec() == QDialog.Accepted:
            if not dialog.front or not dialog.back:
                QMessageBox.warning(self, tr("missing_info_title"), tr("front_back_empty"))
                return
            DerivationAddDialog.last_folder_id = dialog.folder_id
            self.db.add_word(
                folder_id=dialog.folder_id,
                front=dialog.front,
                back=dialog.back,
                parent_id=self.word_id,
                today=date.today(),
            )
            self._reload()

    def _on_derivation_double_clicked(self, item: QListWidgetItem):
        deriv_id = item.data(Qt.UserRole)
        nested = WordDetailDialog(self.db, deriv_id, self)
        nested.exec()
        self._reload()

    def _on_delete_word(self):
        derivations = self.db.get_derivations(self.word_id)
        if derivations:
            message = tr("confirm_delete_word_with_derivs", front=self._word.front, count=len(derivations))
        else:
            message = tr("confirm_delete_word", front=self._word.front)
        reply = QMessageBox.question(
            self, tr("delete_word_title"), message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_word(self.word_id)
            self.accept()
