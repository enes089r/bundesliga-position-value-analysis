"""Kok ve tureme kelimeleri baloncuk + baglanti cizgisi olarak gosteren agac/ag gorunumu.

Her kelime bir kok kelimeye (parent_id) bagli olabilir; tureme kelimelerin
kendi turemeleri de olabilir (sinirsiz derinlik). Bu widget tum kelimeleri
radyal bir duzende cizer: her kok kelime bir merkezde durur, turemeler
ustunde/altinda degil, dogrudan etrafindaki halkalarda yer alir; daha derin
turemeler (turemenin turemesi) bir sonraki, daha genis halkaya yerlesir.
Beklemedeki (henuz aktiflesmemis) kelimeler daha acik/soluk bir dolgu
rengiyle, aktif kelimeler canli renkte gosterilir; okunabilirlik icin
metinler her zaman tam opaklikta cizilir (soluklugu opacity degil, renk
tonu saglar).
"""
import math

from PySide6.QtCore import QElapsedTimer, QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.database import Database, Word
from app.i18n import tr
from app.ui.dialogs import WordDetailDialog
from app.ui.formatting import word_status_short, word_status_text

MIN_NODE_WIDTH = 56
MAX_NODE_WIDTH = 220
HORIZONTAL_PADDING = 18
VERTICAL_PADDING = 12
LINE_GAP = 2
RADIUS_MARGIN = 70
MIN_RADIUS_STEP = 140
ROOT_SPACING_X = 480
ROOT_SPACING_Y = 420
ROOTS_PER_ROW = 4

COLOR_ACTIVE = QColor(96, 150, 224)
COLOR_KNOWN = QColor(96, 190, 130)
COLOR_PENDING = QColor(222, 222, 222)  # okunabilir kalmasi icin soluk saydamlik yerine acik dolgu rengi
TEXT_COLOR = QColor(25, 25, 25)
STATUS_TEXT_COLOR = QColor(60, 60, 60)

# "Nefes alma" animasyonu: TUM dugumler surekli belirgin sekilde buyuyup
# kuculur; fare uzerine gelince hem genlik hem de hiz artar. Faz, her
# tick'te (dt * o anki hiz) kadar biriktirilir -- boylece hover baslayip
# bitince hiz degisse bile animasyon aniden sicramaz, akici kalir.
BREATH_INTERVAL_MS = 40
BREATH_SPEED = 1.8  # radyan/saniye (normal)
BREATH_SPEED_HOVER = 4.5  # radyan/saniye (fare ustundeyken, cok daha hizli)
BREATH_AMPLITUDE = 0.09  # normalde de rahatca goze carpsin diye belirgin
BREATH_AMPLITUDE_HOVER = 0.22
GOLDEN_ANGLE = 2.399963  # ardisik kelime ID'lerine dagitilmis, tekrarsiz gorunen faz farki


class BreathingEllipseItem(QGraphicsEllipseItem):
    """Her zaman nefes alan (periyodik olcek animasyonlu) baloncuk.

    Faz, WordGraphWidget'in zamanlayicisi tarafindan her tick'te
    (dt * hiz) kadar arttirilir; hiz ve genlik o an fare ustunde olup
    olmamasina (is_hovered) gore secilir.
    """

    def __init__(self, rect: QRectF):
        super().__init__(rect)
        self.setAcceptHoverEvents(True)
        self.word_id: int | None = None
        self.phase = 0.0
        self.is_hovered = False

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        super().hoverLeaveEvent(event)


class GraphView(QGraphicsView):
    """Yakinlastirma (tekerlek) ve kaydirma (surukleme) destekli gorunum."""

    def __init__(self, scene: QGraphicsScene, on_node_double_clicked):
        super().__init__(scene)
        self._on_node_double_clicked = on_node_double_clicked
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        # Hover olaylarinin (nefes alma genligi icin) buton basilmadan da
        # tetiklenmesi icin fare takibi acik olmali.
        self.setMouseTracking(True)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        while item is not None and not hasattr(item, "word_id"):
            item = item.parentItem()
        if item is not None:
            self._on_node_double_clicked(item.word_id)
        super().mouseDoubleClickEvent(event)


class WordGraphWidget(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db

        self.scene = QGraphicsScene(self)
        self.view = GraphView(self.scene, self._on_node_double_clicked)

        self.legend = QLabel()
        self.legend.setWordWrap(True)

        self.refresh_btn = QPushButton()
        self.refresh_btn.clicked.connect(self.refresh)

        top_row = QHBoxLayout()
        top_row.addWidget(self.legend, stretch=1)
        top_row.addWidget(self.refresh_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(top_row)
        layout.addWidget(self.view)

        self._breath_clock = QElapsedTimer()
        self._breath_clock.start()
        self._breath_last_ms = 0
        self._breath_timer = QTimer(self)
        self._breath_timer.setInterval(BREATH_INTERVAL_MS)
        self._breath_timer.timeout.connect(self._on_breath_tick)
        self._breath_timer.start()

        self.retranslate_ui()

    def retranslate_ui(self):
        self.legend.setText(tr("graph_legend"))
        self.refresh_btn.setText(tr("refresh"))
        self.refresh()

    def showEvent(self, event):
        super().showEvent(event)
        self._breath_last_ms = self._breath_clock.elapsed()
        self._breath_timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._breath_timer.stop()

    def _on_breath_tick(self):
        now_ms = self._breath_clock.elapsed()
        # Sekme bir sure gizli kaldiysa (zamanlayici durup yeniden basladiysa)
        # dt'yi sinirlamazsak faz aniden buyuk bir sicrama yapar.
        dt = max(0.0, min((now_ms - self._breath_last_ms) / 1000.0, 0.2))
        self._breath_last_ms = now_ms
        for item in self.scene.items():
            if isinstance(item, BreathingEllipseItem):
                speed = BREATH_SPEED_HOVER if item.is_hovered else BREATH_SPEED
                amplitude = BREATH_AMPLITUDE_HOVER if item.is_hovered else BREATH_AMPLITUDE
                item.phase += speed * dt
                item.setScale(1.0 + amplitude * math.sin(item.phase))

    def _on_node_double_clicked(self, word_id: int):
        dialog = WordDetailDialog(self.db, word_id, self)
        dialog.exec()
        self.refresh()

    def refresh(self):
        self.scene.clear()
        words = self.db.get_all_words()
        if not words:
            self.scene.addText(tr("graph_empty"))
            return

        word_map = {w.id: w for w in words}
        children_map: dict[int, list[int]] = {}
        roots: list[int] = []
        for w in words:
            if w.parent_id is not None and w.parent_id in word_map:
                children_map.setdefault(w.parent_id, []).append(w.id)
            else:
                roots.append(w.id)

        # Her dugumun gercek metin olcusune gore ihtiyac duydugu boyutu onceden
        # hesapla; halkalar arasi mesafe (radius_step) en buyuk dugume gore
        # ayarlanir ki kisa kelimelerde sikisik, uzun kelimelerde genis olsun.
        sizes = {w.id: self._measure_node(w) for w in words}
        max_dim = max((max(s) for s in sizes.values()), default=MIN_NODE_WIDTH)
        radius_step = max(MIN_RADIUS_STEP, max_dim + RADIUS_MARGIN)

        positions = self._compute_layout(roots, children_map, radius_step)

        for w in words:
            if w.parent_id is not None and w.parent_id in positions:
                self._add_edge(positions[w.parent_id], positions[w.id])
        for w in words:
            self._add_node(w, sizes[w.id], *positions[w.id])

        self.view.setSceneRect(self.scene.itemsBoundingRect().adjusted(-40, -40, 40, 40))

    def _compute_layout(
        self, roots: list[int], children_map: dict[int, list[int]], radius_step: float,
    ) -> dict[int, tuple[float, float]]:
        """Radyal agac yerlesimi: her kok kelime bir merkezde durur, cocuklari
        (ve onlarin cocuklari) merkez etrafinda artan yariçapli halkalara,
        alt-agac boyutlarina orantili acisal dilimlere yerlesir. Boylece
        turemeler kok kelimenin altinda degil, etrafinda dagilir."""
        positions: dict[int, tuple[float, float]] = {}
        leaf_counts = self._count_leaves(roots, children_map)

        def layout(node_id: int, depth: int, angle_start: float, angle_end: float,
                   center_x: float, center_y: float):
            angle_mid = (angle_start + angle_end) / 2
            if depth == 0:
                x, y = center_x, center_y
            else:
                radius = depth * radius_step
                x = center_x + radius * math.cos(angle_mid)
                y = center_y + radius * math.sin(angle_mid)
            positions[node_id] = (x, y)

            kids = children_map.get(node_id, [])
            if kids:
                total = sum(leaf_counts[k] for k in kids)
                current = angle_start
                for kid_id in kids:
                    span = (angle_end - angle_start) * (leaf_counts[kid_id] / total)
                    layout(kid_id, depth + 1, current, current + span, center_x, center_y)
                    current += span

        for i, root_id in enumerate(roots):
            row, col = divmod(i, ROOTS_PER_ROW)
            layout(root_id, 0, 0.0, 2 * math.pi, col * ROOT_SPACING_X, row * ROOT_SPACING_Y)

        return positions

    def _count_leaves(self, roots: list[int], children_map: dict[int, list[int]]) -> dict[int, int]:
        """Her dugumun alt agacindaki yaprak sayisi; acisal pay bununla orantili dagitilir."""
        counts: dict[int, int] = {}

        def count(node_id: int) -> int:
            kids = children_map.get(node_id, [])
            if not kids:
                counts[node_id] = 1
                return 1
            total = sum(count(kid_id) for kid_id in kids)
            counts[node_id] = total
            return total

        for root_id in roots:
            count(root_id)
        return counts

    def _add_edge(self, parent_pos: tuple[float, float], child_pos: tuple[float, float]):
        line = QGraphicsLineItem(parent_pos[0], parent_pos[1], child_pos[0], child_pos[1])
        line.setPen(QPen(QColor(130, 130, 130), 1.5))
        line.setZValue(0)
        self.scene.addItem(line)

    def _measure_node(self, word: Word) -> tuple[float, float]:
        """Metne dayali gercek genislik/yukseklik hesaplar (once olcup sonra
        cizmek, sabit karakter-sayisi tahminine gore daha az bosa alan kullanir)."""
        front_item = QGraphicsSimpleTextItem(word.front)
        status_item = QGraphicsSimpleTextItem(word_status_short(word))
        status_font = status_item.font()
        status_font.setPointSize(max(7, status_font.pointSize() - 2))
        status_item.setFont(status_font)

        fr = front_item.boundingRect()
        sr = status_item.boundingRect()
        width = max(MIN_NODE_WIDTH, min(MAX_NODE_WIDTH, max(fr.width(), sr.width()) + HORIZONTAL_PADDING))
        height = fr.height() + sr.height() + LINE_GAP + VERTICAL_PADDING
        return (width, height)

    def _add_node(self, word: Word, size: tuple[float, float], x: float, y: float):
        width, height = size

        if word.is_known:
            fill = COLOR_KNOWN
        elif word.is_active:
            fill = COLOR_ACTIVE
        else:
            fill = COLOR_PENDING

        ellipse = BreathingEllipseItem(QRectF(-width / 2, -height / 2, width, height))
        ellipse.setPos(x, y)
        ellipse.word_id = word.id
        ellipse.phase = (word.id * GOLDEN_ANGLE) % (2 * math.pi)
        ellipse.setBrush(QBrush(fill))
        ellipse.setPen(QPen(fill.darker(130), 1.5))
        ellipse.setZValue(1)
        ellipse.setToolTip(f"{word.front} → {word.back}\n{word_status_text(word)}")

        front_item = QGraphicsSimpleTextItem(word.front, ellipse)
        front_item.setBrush(QBrush(TEXT_COLOR))
        fr = front_item.boundingRect()

        status_font = front_item.font()
        status_font.setPointSize(max(7, status_font.pointSize() - 2))
        status_item = QGraphicsSimpleTextItem(word_status_short(word), ellipse)
        status_item.setFont(status_font)
        status_item.setBrush(QBrush(STATUS_TEXT_COLOR))
        sr = status_item.boundingRect()

        total_text_height = fr.height() + sr.height() + LINE_GAP
        top = -total_text_height / 2
        front_item.setPos(-fr.width() / 2, top)
        status_item.setPos(-sr.width() / 2, top + fr.height() + LINE_GAP)

        self.scene.addItem(ellipse)
