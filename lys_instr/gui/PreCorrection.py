from scipy.interpolate import RBFInterpolator

from lys import load
from lys.Qt import QtWidgets, QtGui, QtCore

from lys_instr.PreCorrection import _FunctionCombination, _InterpolatedFunction


class PreCorrectorGUI(QtWidgets.QWidget):
    def __init__(self, obj):
        super().__init__()
        self._obj = obj
        self.__initUI()

    def __initUI(self):
        self._tree = _FunctionWidget(self._obj)
        self._tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.addWidget(QtWidgets.QLabel("Correct Parameters"))
        self._layout.addWidget(self._tree)

        self.setLayout(self._layout)
        self.adjustSize()


class _FunctionWidget(QtWidgets.QTreeWidget):
    def __init__(self, obj):
        super().__init__()
        self._obj = obj
        self.setHeaderLabels(["Target", "Expression"])

        self.customContextMenuRequested.connect(self._buildMenu)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.itemChanged.connect(self._edited)

    def _buildMenu(self):
        menu = QtWidgets.QMenu()

        selected_items = self.selectedItems()
        if len(selected_items) > 0:
            if selected_items[0].parent() is None: # Correction is selected
                add_var = QtWidgets.QAction('Add new variable', triggered = lambda b, item=selected_items[0]: self._addVar(item))
                add_func = QtWidgets.QAction('Add new function', triggered = lambda b, item=selected_items[0]: self._addFunc(item))
                enable = QtWidgets.QAction('Enable/Disable', triggered = lambda b, item=selected_items[0]: self._enable(item))
                del_ = QtWidgets.QAction('Delete target', triggered = lambda b, item=selected_items[0]: self._del(item))
                menu.addAction(add_var)
                menu.addAction(add_func)
                menu.addAction(enable)
                menu.addAction(del_)
            elif "Fix:" not in selected_items[0].text(0):
                fix = QtWidgets.QAction('Fix a parameter', triggered = lambda b, item=selected_items[0]: self._fix(item))
                del_func = QtWidgets.QAction('Delete function', triggered = lambda b, item=selected_items[0]: self._delFunc(item))
                menu.addAction(fix)
                menu.addAction(del_func)
            else:
                del_fix = QtWidgets.QAction('Delete fixed param', triggered = lambda b, item=selected_items[0]: self._delFix(item))
                menu.addAction(del_fix)

            menu.addSeparator()

        add = QtWidgets.QAction('Add new target', triggered = self._add)
        clear = QtWidgets.QAction('Clear all targets', triggered = self._clear)
        menu.addAction(add)
        menu.addAction(clear)

        menu.exec_(QtGui.QCursor.pos())

    def _add(self):
        additems = [key for key in self._obj.parameters if key not in self._obj.corrections.keys()]
        item, ok = QtWidgets.QInputDialog.getItem(self, "Add Correct Params", "Param", additems, editable=False)
        if ok:
            self._obj.corrections[item] = _FunctionCombination()
            tree_item = _EditableItem([item])
            self.addTopLevelItem(tree_item)

    def _clear(self):
        ok = QtWidgets.QMessageBox.warning(self, "Clear", "Do you really want to CLEAR the all target(s)?", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            self._obj.corrections.clear()
            self.clear()

    def _del(self, item):
        ok = QtWidgets.QMessageBox.warning(self, "Clear", "Do you really want to DELETE this target?", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            key, _ = self._correction(item)
            del self._obj.corrections[key]
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))

    def _enable(self, item):
        _, c = self._correction(item)
        c.enabled = not c.enabled
        item.setBackground(0, QtGui.QBrush(QtGui.QColor("white")) if c.enabled else QtGui.QBrush(QtGui.QColor("gray")))
        item.setBackground(1, QtGui.QBrush(QtGui.QColor("white")) if c.enabled else QtGui.QBrush(QtGui.QColor("gray")))

    def _addVar(self, item):
        _, c = self._correction(item)
        additems = [key for key in self._obj.parameters if key not in c.functions.keys()]
        var, ok = QtWidgets.QInputDialog.getItem(self, "Select variables", "Variables", additems, editable=False)
        if ok:
            f = _InterpolatedFunction(lambda x: x[0], [var])
            c.functions[var] = f
            item.addChild(_EditableItem([var]))

    def _addFunc(self, item):
        dialog = _addFuncDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            f = dialog.getFunction()
            _, c = self._correction(item)
            i = 1
            while "func" + str(i) in c.functions.keys():
                i += 1
            c.functions["func"+str(i)] = f
            item.addChild(_EditableItem(["func"+str(i)+"("+",".join(f.argNames())+")"]))

    def _delFunc(self, item):
        ok = QtWidgets.QMessageBox.warning(self, "Clear", "Do you really want to DELETE this function?", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            _, c = self._correction(item.parent())
            key = list(c.functions.keys())[item.parent().indexOfChild(item)]
            del c.functions[key]
            item.parent().removeChild(item)

    def _fix(self, item):
        f = self._function(item)
        params = f.argNames(excludeFixed=True)
        if len(params) == 0:
            QtWidgets.QMessageBox.warning(self, "Warning", "All parameters have been fixed.", QtWidgets.QMessageBox.Ok)
            return
        else:
            p, ok = QtWidgets.QInputDialog.getItem(self, "Fix parameters", "Param", params, editable=False)
            if ok:
                f.fixedValues[p] = 0
                item.addChild(_EditableItem(["Fix:"+" "+p, "0"]))

    def _delFix(self, item):
        p = item.text(0).replace("Fix: ", "")
        del self._function(item).fixedValues[p]
        item.parent().removeChild(item)

    def _edited(self, item, column):
        if column == 1:
            if "Fix: " in item.text(0):
                p = item.text(0).replace("Fix: ", "")
                f = self._function(item.parent())
                f.fixedValues[p] = eval(item.text(1))
            else:
                _, c = self._correction(item)
                c.expression = item.text(1)

    def _correction(self, item):
        """Get correction object for the item"""
        index = self.indexOfTopLevelItem(item)
        key = list(self._obj.corrections.keys())[index]
        return key, self._obj.corrections[key]

    def _function(self, item):
        _, c = self._correction(item.parent())
        key = list(c.functions.keys())[item.parent().indexOfChild(item)]
        return c.functions[key]


class _EditableItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)


class _addFuncDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("New function from data")
        self.__initLayout()

    def __initLayout(self):
        self._input = QtWidgets.QLineEdit()
        self._input.placeholderText = "select .npz file"

        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("Input data:"), 0, 0)
        grid.addWidget(self._input, 1, 0)
        grid.addWidget(QtWidgets.QPushButton("Select", clicked=lambda: self.__open(self._input)), 1, 1)

        # buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(QtWidgets.QPushButton("O K", clicked=self.accept))
        button_layout.addWidget(QtWidgets.QPushButton("Cancel", clicked=self.reject))

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(grid)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def getFunction(self):
        input = load(self._input.text())
        f = RBFInterpolator(input.data, input.x, kernel="linear")
        return _InterpolatedFunction(f, input.note["variables"])

    def __open(self, lineEdit):
        file, _ = QtWidgets.QFileDialog.getOpenFileName(None, 'Open file', filter="npz(*.npz)")
        if 0 != len(file):
            lineEdit.setText(file)

