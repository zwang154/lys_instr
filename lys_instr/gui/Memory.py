import os
import json
from lys.Qt import QtWidgets, QtCore


class ControllerMemory(QtWidgets.QWidget):
    """
    Memory panel for controller positions.

    Displays saved controller positions, allows saving/loading/deleting entries, and stores positions in a JSON file under the local ``.lys`` directory.
    """

    def __init__(self, objs, path=None, parent=None):
        """
        Create the memory panel and load saved positions.

        Args:
            objs (Sequence): Sequence of controller objects used to read/write positions.
            path (str | None): Optional file name to use for saved positions (stored under ``.lys/.lys_instr``).
            parent (QWidget | None): Optional parent widget.
        """
        super().__init__(parent)
        self._objs = objs
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self.__initLayout()

        self._savedPositions = []
        self._import(path)
        self._updateMemory()

    def __initLayout(self):
        """
        Create and arrange widgets for the memory panel.
        """
        self._positionList = QtWidgets.QTreeWidget()
        self._positionList.setColumnCount(3)
        self._positionList.setHeaderLabels(["Label", "Position", "Memo"])
        self._positionList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._positionList.itemSelectionChanged.connect(lambda: self._updateMemoryBtns(load, delete))
        self._positionList.setIndentation(0)
        self._positionList.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.SelectedClicked)
        self._positionList.itemChanged.connect(self._memoEdited)
        self._positionList.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self._positionList.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self._positionList.header().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self._positionList.setItemDelegateForColumn(0, _NoEditDelegate(self._positionList))
        self._positionList.setItemDelegateForColumn(1, _NoEditDelegate(self._positionList))

        save = QtWidgets.QPushButton("Save", clicked=self._save)
        save.setEnabled(True)
        load = QtWidgets.QPushButton("Load", clicked=self._load)
        load.setEnabled(False)
        delete = QtWidgets.QPushButton("Delete", clicked=self._delete)
        delete.setEnabled(False)

        self._memoryBtnsLayout = QtWidgets.QHBoxLayout()
        self._memoryBtnsLayout.addWidget(save)
        self._memoryBtnsLayout.addWidget(load)
        self._memoryBtnsLayout.addWidget(delete)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Memory"))
        layout.addWidget(self._positionList)
        layout.addLayout(self._memoryBtnsLayout)
        self.setLayout(layout)

    def _import(self, path):
        """
        Import saved positions from disk and set the memory file path.

        Args:
            path (str | None): Optional file name in the local memory directory (``.lys/.lys_instr``) to load. If ``None``, no file is loaded.
        """
        if path is None:
            self._path = None

        # Load memory file
        dir = os.path.join(".lys", ".lys_instr")
        os.makedirs(dir, exist_ok=True)
        self._path = os.path.join(dir, path)

        if os.path.exists(self._path):
            with open(self._path, "r") as f:
                self._savedPositions = json.load(f)

    def _export(self):
        """
        Write the current saved positions to the configured memory file.
        """
        if self._path is None:
            return
        with open(self._path, "w") as f:
            json.dump(self._savedPositions, f)

    def _save(self):
        """
        Save the current axis positions to the memory file.
        """
        labels = {item["label"] for item in self._savedPositions}
        i = 1
        while f"{i}" in labels:
            i += 1
        position = {}
        for obj in self._objs:
            position.update(obj.get())
        self._savedPositions.append({"label": f"{i}", "position": position, "memo": ""})
        self._export()
        self._updateMemory()

    def _load(self):
        """
        Load the selected saved axis position and apply it to the controllers.
        """
        selections = self._positionList.selectedItems()
        if not selections:
            return
        selectedlabel = selections[0].text(0)
        itemDict = next(item for item in self._savedPositions if item["label"] == selectedlabel)
        loadedValues = itemDict["position"]
        for obj in self._objs:
            value = {name: loadedValues[name] for name in obj.nameList}
            obj.set(**value)

    def _delete(self):
        """
        Delete selected saved positions from the memory file.
        """
        selectedlabels = {i.text(0) for i in self._positionList.selectedItems()}
        self._savedPositions = [item for item in self._savedPositions if item["label"] not in selectedlabels]
        self._export()
        self._updateMemory()

    def _memoEdited(self, item, column):
        """
        Handle edits to the memo field in the memory panel.

        Args:
            item (QTreeWidgetItem): The edited item.
            column (int): The column index that was edited.
        """
        if column == 2:
            label = item.text(0)
            memo = item.text(2)
            for idx, pos in enumerate(self._savedPositions):
                if pos["label"] == label:
                    self._savedPositions[idx]["memo"] = memo
                    self._export()
                    break

    def _updateMemory(self):
        """
        Update the memory panel with the latest saved positions.
        """
        self._positionList.clear()
        for itemDict in self._savedPositions:
            displayedPosition = ", ".join(f"{v:.3f}" for v in itemDict["position"].values())
            item = QtWidgets.QTreeWidgetItem([itemDict["label"], displayedPosition, itemDict["memo"]])

            # Protect columns 0 and 1 from editing
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            self._positionList.addTopLevelItem(item)

        for col in range(self._positionList.columnCount()):
            self._positionList.resizeColumnToContents(col)

    def _updateMemoryBtns(self, loadBtn, deleteBtn):
        """
        Enable or disable memory panel buttons based on selection.

        Args:
            loadBtn (QPushButton): The load button.
            deleteBtn (QPushButton): The delete button.
        """
        selected = len(self._positionList.selectedItems()) > 0
        loadBtn.setEnabled(selected)
        deleteBtn.setEnabled(selected)


class _NoEditDelegate(QtWidgets.QStyledItemDelegate):
    """
    Delegate to prevent editing of certain columns in a QTreeWidget.
    """

    def createEditor(self, parent, option, index):
        """
        Prevent editing by always returning None.

        Returns:
            ``None``
        """
        return None
