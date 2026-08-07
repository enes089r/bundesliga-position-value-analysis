"""Ana pencere: sekmeler halinde Tekrar / Klasorler / Bilinenler / Kelime Agaci.

Sag ust kosedeki dil secici, secilen dili aninda tum sekmelere yansitir
(her sekmenin kendi retranslate_ui() metodu vardir) ve settings.json'a
kaydederek bir sonraki acilista hatirlanmasini saglar. Ustteki arama
cubugu, klasor/tur farki gozetmeksizin tum kelimeler icinde arama yapar.
"""
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from app import settings
from app.database import Database
from app.i18n import LANGUAGES, get_language, set_language, tr
from app.ui.folders_widget import FoldersWidget
from app.ui.known_widget import KnownWidget
from app.ui.review_widget import ReviewWidget
from app.ui.search_widget import SearchWidget
from app.ui.word_graph_widget import WordGraphWidget


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.resize(720, 600)

        set_language(settings.load_language())

        self.search_widget = SearchWidget(db)
        self.review_widget = ReviewWidget(db)
        self.folders_widget = FoldersWidget(db)
        self.known_widget = KnownWidget(db)
        self.word_graph_widget = WordGraphWidget(db)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.review_widget, "")
        self.tabs.addTab(self.folders_widget, "")
        self.tabs.addTab(self.known_widget, "")
        self.tabs.addTab(self.word_graph_widget, "")
        self.tabs.currentChanged.connect(self._on_tab_changed)

        self.language_label = QLabel()
        self.language_combo = QComboBox()
        for code, native_name in LANGUAGES:
            self.language_combo.addItem(native_name, code)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)

        top_row = QHBoxLayout()
        top_row.addStretch()
        top_row.addWidget(self.language_label)
        top_row.addWidget(self.language_combo)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(6, 4, 6, 0)
        central_layout.addWidget(self.search_widget)
        central_layout.addLayout(top_row)
        central_layout.addWidget(self.tabs)
        self.setCentralWidget(central)

        self._sync_language_combo()
        self.retranslate_ui()

    def _sync_language_combo(self):
        idx = self.language_combo.findData(get_language())
        if idx >= 0:
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentIndex(idx)
            self.language_combo.blockSignals(False)

    def _on_language_changed(self, _index: int):
        lang = self.language_combo.currentData()
        set_language(lang)
        settings.save_language(lang)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle(tr("app_title"))
        self.language_label.setText(tr("language_label"))
        self.tabs.setTabText(0, tr("tab_review"))
        self.tabs.setTabText(1, tr("tab_folders"))
        self.tabs.setTabText(2, tr("tab_known"))
        self.tabs.setTabText(3, tr("tab_graph"))
        self.search_widget.retranslate_ui()
        self.review_widget.retranslate_ui()
        self.folders_widget.retranslate_ui()
        self.known_widget.retranslate_ui()
        self.word_graph_widget.retranslate_ui()

    def _on_tab_changed(self, _index: int):
        current = self.tabs.currentWidget()
        if current is self.review_widget:
            self.review_widget.show_folder_page()
        elif current is self.folders_widget:
            self.folders_widget.refresh()
        elif current is self.known_widget:
            self.known_widget.refresh()
        elif current is self.word_graph_widget:
            self.word_graph_widget.refresh()
