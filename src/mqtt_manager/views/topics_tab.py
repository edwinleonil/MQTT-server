"""Topics Tab — Browse and edit the MQTT topic hierarchy."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from mqtt_manager.models.topic_tree import TopicNode, TopicTreeModel


class TopicsTab(QWidget):
    """Tab for viewing and editing the topic hierarchy tree."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._root = TopicNode("(root)")
        self._model = TopicTreeModel(self._root)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Topic Structure (template / reference):"))

        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setColumnWidth(0, 250)
        self._tree.setAlternatingRowColors(True)
        layout.addWidget(self._tree)

        btn_row = QHBoxLayout()
        self._add_btn = QPushButton("Add Topic")
        self._remove_btn = QPushButton("Remove Topic")
        self._rename_btn = QPushButton("Rename")
        self._load_btn = QPushButton("Load YAML")
        self._save_btn = QPushButton("Export YAML")
        btn_row.addWidget(self._add_btn)
        btn_row.addWidget(self._remove_btn)
        btn_row.addWidget(self._rename_btn)
        btn_row.addWidget(self._load_btn)
        btn_row.addWidget(self._save_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

    def _connect_signals(self):
        self._add_btn.clicked.connect(self._add_topic)
        self._remove_btn.clicked.connect(self._remove_topic)
        self._rename_btn.clicked.connect(self._rename_topic)
        self._load_btn.clicked.connect(self._load_yaml)
        self._save_btn.clicked.connect(self._export_yaml)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _selected_node(self) -> TopicNode | None:
        index = self._tree.currentIndex()
        if index.isValid():
            return index.internalPointer()
        return None

    def _add_topic(self):
        parent = self._selected_node() or self._root
        name, ok = QInputDialog.getText(self, "Add Topic", "Topic name:")
        if ok and name.strip():
            self._model.beginResetModel()
            parent.add_child(name.strip())
            self._model.endResetModel()
            self._tree.expandAll()

    def _remove_topic(self):
        node = self._selected_node()
        if not node or node is self._root:
            return
        reply = QMessageBox.question(
            self, "Remove Topic",
            f"Remove '{node.name}' and all children?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._model.beginResetModel()
            node.parent.remove_child(node)
            self._model.endResetModel()

    def _rename_topic(self):
        node = self._selected_node()
        if not node or node is self._root:
            return
        name, ok = QInputDialog.getText(self, "Rename Topic", "New name:", text=node.name)
        if ok and name.strip():
            self._model.beginResetModel()
            node.name = name.strip()
            self._model.endResetModel()

    def _load_yaml(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Topic YAML", "", "YAML (*.yaml *.yml)")
        if path:
            try:
                self._root = TopicNode.from_yaml(path)
                self._model.set_root(self._root)
                self._tree.expandAll()
                self._status_label.setText(f"Loaded: {path}")
            except Exception as exc:
                QMessageBox.warning(self, "Load Error", str(exc))

    def _export_yaml(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Topic YAML", "topics.yaml", "YAML (*.yaml *.yml)")
        if path:
            try:
                content = self._root.to_yaml()
                Path(path).write_text(content)
                self._status_label.setText(f"Exported: {path}")
            except Exception as exc:
                QMessageBox.warning(self, "Export Error", str(exc))

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def load_default_topics(self, yaml_path: str | Path):
        """Load the default topic structure from a YAML file."""
        try:
            self._root = TopicNode.from_yaml(yaml_path)
            self._model.set_root(self._root)
            self._tree.expandAll()
        except Exception:
            pass  # Default topics not critical
