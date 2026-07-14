"""Encabezado de tabla reutilizable con texto multilínea y altura dinámica."""

from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QHeaderView, QStyle, QStyleOptionHeader


class WordWrapHeaderView(QHeaderView):
    """Dibuja encabezados centrados y ajusta su altura al texto completo."""

    def __init__(self, orientation: Qt.Orientation, parent=None) -> None:
        super().__init__(orientation, parent)
        self._horizontal_padding = 12
        self._vertical_padding = 10
        self._minimum_header_height = 36
        self.setDefaultAlignment(Qt.AlignCenter)
        self.sectionResized.connect(self._schedule_height_update)
        self.sectionCountChanged.connect(self._schedule_height_update)

    def setModel(self, model) -> None:  # noqa: N802 - API de Qt
        previous = self.model()
        if previous is not None:
            try:
                previous.headerDataChanged.disconnect(self._on_header_data_changed)
            except (RuntimeError, TypeError):
                pass
        super().setModel(model)
        if model is not None:
            model.headerDataChanged.connect(self._on_header_data_changed)
        self._schedule_height_update()

    def paintSection(self, painter: QPainter, rect: QRect, logical_index: int) -> None:  # noqa: N802
        if not rect.isValid():
            return
        option = QStyleOptionHeader()
        self.initStyleOption(option)
        option.rect = rect
        option.section = logical_index
        option.text = ""
        option.position = self._section_position(logical_index)
        self.style().drawControl(QStyle.CE_Header, option, painter, self)

        text = self._header_text(logical_index)
        text_rect = rect.adjusted(
            self._horizontal_padding // 2,
            self._vertical_padding // 2,
            -(self._horizontal_padding // 2),
            -(self._vertical_padding // 2),
        )
        painter.save()
        painter.setPen(option.palette.buttonText().color())
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, text)
        painter.restore()

    def sizeHint(self) -> QSize:  # noqa: N802 - API de Qt
        hint = super().sizeHint()
        if self.orientation() == Qt.Horizontal:
            hint.setHeight(self.required_height())
        return hint

    def sectionSizeFromContents(self, logical_index: int) -> QSize:  # noqa: N802
        size = super().sectionSizeFromContents(logical_index)
        if self.orientation() == Qt.Horizontal:
            size.setHeight(self._text_height(logical_index, self.sectionSize(logical_index)))
        return size

    def required_height(self) -> int:
        heights = [
            self._text_height(index, self.sectionSize(index))
            for index in range(self.count())
            if not self.isSectionHidden(index)
        ]
        return max([self._minimum_header_height, *heights])

    def update_height(self) -> None:
        if self.orientation() != Qt.Horizontal:
            return
        height = self.required_height()
        if self.height() != height:
            self.setFixedHeight(height)
        self.updateGeometry()
        self.viewport().update()

    def _schedule_height_update(self, *_args) -> None:
        QTimer.singleShot(0, self.update_height)

    def _on_header_data_changed(self, orientation, _first: int, _last: int) -> None:
        if orientation == self.orientation():
            self._schedule_height_update()

    def _header_text(self, logical_index: int) -> str:
        model = self.model()
        if model is None:
            return ""
        value = model.headerData(logical_index, self.orientation(), Qt.DisplayRole)
        return str(value or "")

    def _text_height(self, logical_index: int, section_width: int) -> int:
        available_width = max(1, section_width - self._horizontal_padding)
        bounds = self.fontMetrics().boundingRect(
            QRect(0, 0, available_width, 10_000),
            Qt.AlignCenter | Qt.TextWordWrap,
            self._header_text(logical_index),
        )
        return max(self._minimum_header_height, bounds.height() + self._vertical_padding)

    def _section_position(self, logical_index: int) -> QStyleOptionHeader.SectionPosition:
        visible = [index for index in range(self.count()) if not self.isSectionHidden(index)]
        if len(visible) <= 1:
            return QStyleOptionHeader.SectionPosition.OnlyOneSection
        if logical_index == visible[0]:
            return QStyleOptionHeader.SectionPosition.Beginning
        if logical_index == visible[-1]:
            return QStyleOptionHeader.SectionPosition.End
        return QStyleOptionHeader.SectionPosition.Middle
