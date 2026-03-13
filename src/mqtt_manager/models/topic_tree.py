"""TopicTree — Hierarchical topic model backed by topics.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt


class TopicNode:
    """A single node in the topic hierarchy tree."""

    def __init__(self, name: str, parent: TopicNode | None = None):
        self.name = name
        self.parent = parent
        self.children: list[TopicNode] = []
        self.description: str = ""
        self.example_payload: str = ""

    def add_child(self, name: str) -> TopicNode:
        child = TopicNode(name, parent=self)
        self.children.append(child)
        return child

    def remove_child(self, child: TopicNode):
        self.children.remove(child)
        child.parent = None

    def row(self) -> int:
        if self.parent:
            return self.parent.children.index(self)
        return 0

    def topic_path(self) -> str:
        parts: list[str] = []
        node: TopicNode | None = self
        while node and node.parent:
            parts.append(node.name)
            node = node.parent
        return "/".join(reversed(parts))

    # ------------------------------------------------------------------
    # YAML loading
    # ------------------------------------------------------------------

    @classmethod
    def from_yaml(cls, path: str | Path) -> TopicNode:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        root = cls("(root)")
        topics = data.get("topics", data)
        cls._build_tree(root, topics)
        return root

    @classmethod
    def _build_tree(cls, parent: TopicNode, mapping: dict[str, Any]):
        if not isinstance(mapping, dict):
            return
        for key, value in mapping.items():
            if key in ("description", "example_payload"):
                continue
            child = parent.add_child(key)
            if isinstance(value, dict):
                child.description = value.get("description", "")
                child.example_payload = value.get("example_payload", "")
                cls._build_tree(child, value)

    # ------------------------------------------------------------------
    # YAML export
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        d: dict[str, Any] = {}
        for child in self.children:
            if child.children:
                sub = child.to_dict()
                if child.description:
                    sub["description"] = child.description
                if child.example_payload:
                    sub["example_payload"] = child.example_payload
                d[child.name] = sub
            else:
                entry: dict[str, str] = {}
                if child.description:
                    entry["description"] = child.description
                if child.example_payload:
                    entry["example_payload"] = child.example_payload
                d[child.name] = entry if entry else None
        return d

    def to_yaml(self) -> str:
        return yaml.dump({"topics": self.to_dict()}, default_flow_style=False, sort_keys=False)


class TopicTreeModel(QAbstractItemModel):
    """Qt model adapter for TopicNode tree, usable with QTreeView."""

    def __init__(self, root: TopicNode, parent=None):
        super().__init__(parent)
        self._root = root

    @property
    def root(self) -> TopicNode:
        return self._root

    def set_root(self, root: TopicNode):
        self.beginResetModel()
        self._root = root
        self.endResetModel()

    # ------------------------------------------------------------------
    # QAbstractItemModel interface
    # ------------------------------------------------------------------

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parent_node = parent.internalPointer() if parent.isValid() else self._root
        if row < len(parent_node.children):
            return self.createIndex(row, column, parent_node.children[row])
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        node: TopicNode = index.internalPointer()
        parent_node = node.parent
        if parent_node is None or parent_node is self._root:
            return QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        node = parent.internalPointer() if parent.isValid() else self._root
        return len(node.children)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 2  # Name, Description

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        node: TopicNode = index.internalPointer()
        if index.column() == 0:
            return node.name
        elif index.column() == 1:
            return node.description
        return None

    def headerData(self, section: int, orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ("Topic", "Description")[section] if section < 2 else None
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
