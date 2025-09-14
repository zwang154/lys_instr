import numpy as np
from scipy.interpolate import RBFInterpolator

from lys import Wave
from lys.Qt import QtWidgets, QtGui, QtCore
from lys.widgets import LysSubWindow
from lys.decorators import avoidCircularReference

from lys_instr.PreCorrection import _FunctionCombination, _InterpolatedFunction


class PreCorrectorGUI(QtWidgets.QWidget):
    def __init__(self, obj):
        super().__init__()
        self._obj = obj
        self.__initUI()

    def __initUI(self):
        self._tree = _FunctionWidget(self._obj)
        self._tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QLabel("Corrections"))
        hbox.addWidget(QtWidgets.QPushButton("Create new function", clicked=self._new))        

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.addLayout(hbox)
        self._layout.addWidget(self._tree)

        self.setLayout(self._layout)
        self.adjustSize()

    def _new(self):
        gui = _NewFunctionWindow(self._obj)
        gui.show()


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
        additems = [key for key in self._obj.controllers.keys() if key not in self._obj.corrections.keys()]
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
        additems = [key for key in self._obj.controllers.keys() if key not in c.functions.keys()]
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
        input = Wave(self._input.text())
        f = RBFInterpolator(input.x, input.data, kernel="linear")
        return _InterpolatedFunction(f, input.note["variables"])

    def __open(self, lineEdit):
        file, _ = QtWidgets.QFileDialog.getOpenFileName(None, 'Open file', filter="npz(*.npz)")
        if 0 != len(file):
            lineEdit.setText(file)


class _NewFunctionWindow(LysSubWindow):
    def __init__(self, corrector):
        super().__init__()
        self.setWindowTitle("New function")
        self._corrections = {}
        self._cor = corrector
        self.__initUI()

    def __initUI(self):
        self._tree = QtWidgets.QTreeWidget()
        self._tree.setHeaderLabels(["Target", "Arguments", "Num. of points"])
        self._tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._tree.customContextMenuRequested.connect(self._buildMenu)

        footerLayout = QtWidgets.QHBoxLayout()
        footerLayout.addWidget(QtWidgets.QPushButton("add", clicked=self._addValues))
        footerLayout.addWidget(QtWidgets.QPushButton("undo", clicked=self._undoValues))

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.addWidget(self._tree)
        self._layout.addLayout(footerLayout)

        w = QtWidgets.QWidget()
        w.setLayout(self._layout)
        self.setWidget(w)

    def _buildMenu(self):
        menu = QtWidgets.QMenu()
        selected_items = self._tree.selectedItems()


        if len(selected_items) > 0:
            exp = QtWidgets.QAction('Export correction table', triggered = lambda b, item=selected_items[0]: self._exportTable(item))
            clear = QtWidgets.QAction('Clear correction table', triggered = lambda b, item=selected_items[0]: self._clearTable(item))
            rem = QtWidgets.QAction('Remove correction table', triggered = lambda b, item=selected_items[0]: self._delCorrectParams(item))
            menu.addAction(exp)
            menu.addAction(clear)
            menu.addAction(rem)
            menu.addSeparator()

        add = QtWidgets.QAction('Add new correction table', triggered = self._addCorrectParam)
        cl = QtWidgets.QAction('Clear all tables', triggered = self._clearCorrectParams)
        menu.addAction(add)
        menu.addAction(cl)

        menu.exec_(QtGui.QCursor.pos())

    def _addCorrectParam(self):
        d = _MakeFuncDialog(self, self._cor.controllers.keys())
        if d.exec_():
            self._corrections[d.target] = _CorrectionData(d.args)
            item = QtWidgets.QTreeWidgetItem([d.target, ", ".join([str(s) for s in d.args]), "0"])
            self._tree.addTopLevelItem(item)

    def _clearCorrectParams(self):
        ok = QtWidgets.QMessageBox.warning(self, "Clear", "Do you really want to CLEAR the correction tables?", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            self._corrections.clear()
            self._tree.clear()

    def _delCorrectParams(self, item):
        key, _ = self._correction(item)
        ok = QtWidgets.QMessageBox.warning(self, "Delete", 'Do you really want to DELETE the parameter ' + key + '?' , QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            del self._corrections[key]
            self._tree.takeTopLevelItem(self._tree.indexOfTopLevelItem(item))

    def _clearTable(self, item):
        key, d = self._correction(item)
        ok = QtWidgets.QMessageBox.warning(self, "Delete", 'Do you really want to CLEAR the table for  ' + key + '?' , QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            d.clear()
            self._updateTree()

    def _exportTable(self, item):
        path, type = QtWidgets.QFileDialog.getSaveFileName(filter="numpy npz (*.npz)")
        if len(path) != 0:
            key, d = self._correction(item)
            val, args = d.get()
            Wave(val, args, variables=d.argNames).export(path)

    def _addValues(self):
        for key, d in self._corrections.items():
            targ = self._cor.controllers[key].get()[key]
            args = [self._cor.controllers[k].get()[k] for k in d.argNames]
            d.append(targ, args)
        self._updateTree()

    def _undoValues(self):
        for d in self._corrections.values():
            d.undo()
        self._updateTree()

    def _correction(self, item):
        """Get correction object for the item"""
        index = self._tree.indexOfTopLevelItem(item)
        key = list(self._corrections.keys())[index]
        return key, self._corrections[key]

    def _updateTree(self):
        for i, d in enumerate(self._corrections.values()):
            self._tree.topLevelItem(i).setText(2, str(len(d)))


class _MakeFuncDialog(QtWidgets.QDialog):
    def __init__(self, parent, params):
        super().__init__(parent)
        self._params = list(params)
        
        self.setWindowTitle("New function")
        self.__initLayout(params)
        self._updateWidgets()

    def __initLayout(self, params):
        self._targ = QtWidgets.QComboBox()
        self._targ.addItems(params)
        self._targ.currentTextChanged.connect(self._updateWidgets)

        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("Target variable:"), 0, 0)
        grid.addWidget(self._targ, 0, 1)
        grid.addWidget(QtWidgets.QLabel("Arguments:"), 1, 0)

        self._args = [QtWidgets.QComboBox() for _ in range(20)]
        for i, c in enumerate(self._args):
            c.currentTextChanged.connect(self._updateWidgets)
            grid.addWidget(c, i + 1, 1)

        # buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(QtWidgets.QPushButton("O K", clicked=self.accept))
        button_layout.addWidget(QtWidgets.QPushButton("Cancel", clicked=self.reject))

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(grid)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    @avoidCircularReference
    def _updateWidgets(self, *args):
        selected = [self._targ.currentText()] + [c.currentText() for c in self._args]
        for i, c in enumerate(self._args):
            # remove duplicate
            if c.currentText() in selected[:i]:
                c.setCurrentText("")
            # remove empty
            if c.currentText() == "":
                if self._args[i+1].currentText()!="":
                    for j, c2 in enumerate(self._args[i:-1]):
                        c2.setCurrentText(self._args[j].currentText())
                else:
                    break

        selected = [self._targ.currentText()] + [c.currentText() for c in self._args]
        # show only available
        for i, c in enumerate(self._args):
            c.clear()
            c.addItem("")
            c.addItems([p for p in self._params if p not in selected[:i+1]])
            c.setCurrentText(selected[i+1])
        # hide empty box
        for i, c in enumerate(self._args):
            if i == 0: continue
            if self._args[i-1].currentText() == "":
                c.hide()
            else:
                c.show()

    @property
    def target(self):
        return self._targ.currentText()
    
    @property
    def args(self):
        return [c.currentText() for c in self._args if c.currentText() != ""]


class _CorrectionData:
    def __init__(self, argsNames):
        self._argNames = argsNames
        self.clear()

    def clear(self):
        self._values = []
        self._args = []

    def append(self, targ, args):
        self._values.append(targ)
        self._args.append(args)

    def undo(self):
        self._values.pop(-1)
        self._args.pop(-1)

    def get(self):
        return np.array([self._values]).T, np.array(self._args)

    def __len__(self):
        return len(self._values)

    @property
    def argNames(self):
        return self._argNames