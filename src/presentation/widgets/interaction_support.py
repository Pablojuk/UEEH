"""Interacciones globales consistentes para tablas y textos de la interfaz."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QLineEdit,
    QMenu,
    QPlainTextEdit,
    QTableView,
    QTextEdit,
)


def _index_text(view: QTableView, index) -> str:
    widget = view.indexWidget(index)
    if isinstance(widget, QComboBox):
        return widget.currentText()
    if isinstance(widget, QLineEdit):
        return widget.text()
    if isinstance(widget, QLabel):
        return widget.text()
    value = index.data(Qt.DisplayRole)
    return "" if value is None else str(value)


def selected_table_tsv(view: QTableView) -> str:
    """Devuelve únicamente la selección visible en orden visual y formato TSV."""
    selected = [
        index
        for index in view.selectedIndexes()
        if not view.isColumnHidden(index.column()) and not view.isRowHidden(index.row())
    ]
    if not selected:
        return ""

    selected_positions = {(index.row(), index.column()) for index in selected}
    rows = sorted({index.row() for index in selected}, key=view.verticalHeader().visualIndex)
    columns = sorted({index.column() for index in selected}, key=view.horizontalHeader().visualIndex)
    lines: list[str] = []
    model = view.model()
    for row in rows:
        values = []
        for column in columns:
            if (row, column) not in selected_positions:
                values.append("")
                continue
            values.append(_index_text(view, model.index(row, column)))
        lines.append("\t".join(values))
    return "\n".join(lines)


def copy_table_selection(view: QTableView) -> str:
    text = selected_table_tsv(view)
    if text:
        QApplication.clipboard().setText(text)
    return text


def build_table_context_menu(view: QTableView) -> QMenu:
    menu = QMenu(view)
    copy_action = menu.addAction("Copiar")
    copy_action.setEnabled(bool(view.selectedIndexes()))
    copy_action.triggered.connect(lambda: copy_table_selection(view))
    select_all_action = menu.addAction("Seleccionar todo")
    select_all_action.triggered.connect(view.selectAll)
    return menu


def _has_selection(widget) -> bool:
    if isinstance(widget, QLineEdit):
        return widget.hasSelectedText()
    return widget.textCursor().hasSelection()


def _delete_selection(widget) -> None:
    if isinstance(widget, QLineEdit):
        if widget.hasSelectedText():
            widget.del_()
        return
    cursor = widget.textCursor()
    cursor.removeSelectedText()
    widget.setTextCursor(cursor)


def build_edit_context_menu(widget: QLineEdit | QTextEdit | QPlainTextEdit) -> QMenu:
    menu = QMenu(widget)
    read_only = widget.isReadOnly()
    selected = _has_selection(widget)

    undo_action = menu.addAction("Deshacer")
    undo_action.setEnabled(not read_only and widget.isUndoAvailable())
    undo_action.triggered.connect(widget.undo)
    redo_action = menu.addAction("Rehacer")
    redo_action.setEnabled(not read_only and widget.isRedoAvailable())
    redo_action.triggered.connect(widget.redo)
    menu.addSeparator()

    cut_action = menu.addAction("Cortar")
    cut_action.setEnabled(not read_only and selected)
    cut_action.triggered.connect(widget.cut)
    copy_action = menu.addAction("Copiar")
    copy_action.setEnabled(selected)
    copy_action.triggered.connect(widget.copy)
    paste_action = menu.addAction("Pegar")
    paste_action.setEnabled(not read_only and bool(QApplication.clipboard().text()))
    paste_action.triggered.connect(widget.paste)
    delete_action = menu.addAction("Eliminar")
    delete_action.setEnabled(not read_only and selected)
    delete_action.triggered.connect(lambda: _delete_selection(widget))
    menu.addSeparator()

    select_all_action = menu.addAction("Seleccionar todo")
    select_all_action.setEnabled(bool(widget.text() if isinstance(widget, QLineEdit) else widget.toPlainText()))
    select_all_action.triggered.connect(widget.selectAll)
    return menu


def enable_copyable_label(label: QLabel) -> None:
    label.setTextInteractionFlags(label.textInteractionFlags() | Qt.TextSelectableByMouse)
    label.setProperty("copyableText", True)


def build_label_context_menu(label: QLabel) -> QMenu:
    menu = QMenu(label)
    copy_action = menu.addAction("Copiar")
    copy_action.setEnabled(bool(label.text()))
    copy_action.triggered.connect(
        lambda: QApplication.clipboard().setText(label.selectedText() or label.text())
    )
    select_all_action = menu.addAction("Seleccionar todo")
    select_all_action.setEnabled(bool(label.text()))
    select_all_action.triggered.connect(lambda: label.setSelection(0, len(label.text())))
    return menu


class GlobalInteractionSupport(QObject):
    """Centraliza atajos y menús sin alterar validaciones propias de los formularios."""

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        table = watched if isinstance(watched, QTableView) else None
        if table is None and isinstance(watched.parent(), QTableView):
            table = watched.parent()

        if event.type() == QEvent.KeyPress and table is not None:
            if event.matches(QKeySequence.Copy):
                copy_table_selection(table)
                return True
            if event.matches(QKeySequence.SelectAll):
                table.selectAll()
                return True

        if event.type() != QEvent.ContextMenu:
            return super().eventFilter(watched, event)

        menu = None
        if table is not None:
            menu = build_table_context_menu(table)
        elif isinstance(watched, (QLineEdit, QTextEdit, QPlainTextEdit)):
            menu = build_edit_context_menu(watched)
        elif isinstance(watched, QLabel) and watched.property("copyableText"):
            menu = build_label_context_menu(watched)
        if menu is None:
            return super().eventFilter(watched, event)
        menu.exec(event.globalPos())
        return True


def install_global_interaction_support(app: QApplication) -> GlobalInteractionSupport:
    existing = getattr(app, "_ueeh_interaction_support", None)
    if isinstance(existing, GlobalInteractionSupport):
        return existing
    support = GlobalInteractionSupport(app)
    app.installEventFilter(support)
    app._ueeh_interaction_support = support
    return support
