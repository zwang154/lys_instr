import numpy as np
from scipy.interpolate import RBFInterpolator

from lys import Wave
from lys.Qt import QtWidgets, QtGui, QtCore
from lys.widgets import LysSubWindow
from lys.decorators import avoidCircularReference

from lys_instr.PreCorrection import _FunctionCombination, _InterpolatedFunction



class PreCorrectorGUI(QtWidgets.QWidget):
    """
    Correction GUI subwindow.

    Provides a tree view for editing correction targets (motor-axes) and their correction functions, and a control to create new ones.
    """

    def __init__(self, obj):
        """
        Initialize the GUI.

        Args:
            obj (object): Corrector (typically a ``PreCorrector``).
        """
        super().__init__()
        self._obj = obj
        self.__initUI()

    def __initUI(self):
        """
        Create and arrange widgets for the correction GUI.
        """
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
        """
        Open a dialog (``_NewFunctionWindow``) for creating a new correction function.
        """
        gui = _NewFunctionWindow(self._obj)
        gui.show()


class _FunctionWidget(QtWidgets.QTreeWidget):
    """
    Tree widget for editing correction targets (motor-axes) and their correction functions.

    Displays targets as top-level items and their functions and fixed parameters as child items. 
    Supports adding, removing and reordering entries, and saving and loading the ``corrections`` mapping.
    """

    def __init__(self, obj):
        """
        Initialize the tree widget.

        Args:
            obj (object): Corrector (typically a ``PreCorrector``) providing a ``controllers`` mapping (name -> controller) and a ``corrections`` mapping (target -> correction). 
        """
        super().__init__()
        self._obj = obj
        self.setHeaderLabels(["Target", "Expression"])

        self.customContextMenuRequested.connect(self._buildMenu)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.itemChanged.connect(self._edited)

    def _buildMenu(self):
        """
        Build and show the context menu for the selected tree item.

        The menu exposes actions appropriate for the selected item (target, function, or fixed parameter) and global actions such as copy and paste.
        """
        menu = QtWidgets.QMenu()

        selected_items = self.selectedItems()
        if len(selected_items) > 0:
            if selected_items[0].parent() is None:  # Correction is selected
                add_var = QtWidgets.QAction('Add new variable', triggered=lambda b, item=selected_items[0]: self._addVar(item))
                add_func = QtWidgets.QAction('Add new function', triggered=lambda b, item=selected_items[0]: self._addFunc(item))
                enable = QtWidgets.QAction('Enable/Disable', triggered=lambda b, item=selected_items[0]: self._enable(item))
                del_ = QtWidgets.QAction('Delete target', triggered=lambda b, item=selected_items[0]: self._del(item))
                menu.addAction(add_var)
                menu.addAction(add_func)
                menu.addAction(enable)
                menu.addAction(del_)
            elif "Fix:" not in selected_items[0].text(0):
                fix = QtWidgets.QAction('Fix a parameter', triggered=lambda b, item=selected_items[0]: self._fix(item))
                del_func = QtWidgets.QAction('Delete function', triggered=lambda b, item=selected_items[0]: self._delFunc(item))
                menu.addAction(fix)
                menu.addAction(del_func)
            else:
                del_fix = QtWidgets.QAction('Delete fixed param', triggered=lambda b, item=selected_items[0]: self._delFix(item))
                menu.addAction(del_fix)

            menu.addSeparator()

        add = QtWidgets.QAction('Add new target', triggered=self._add)
        clear = QtWidgets.QAction('Clear all targets', triggered=self._clear)
        menu.addAction(add)
        menu.addAction(clear)

        copy = QtWidgets.QAction('Copy targets and functions', triggered=self._copy)
        paste = QtWidgets.QAction('Paste targets and functions', triggered=self._paste)
        menu.addAction(copy)
        menu.addAction(paste)

        menu.exec_(QtGui.QCursor.pos())

    def _add(self):
        """
        Add a new correction target.

        Prompt the user to select an available target (motor-axis) and create an empty ``_FunctionCombination`` for it, adding the new entry to the corrector's ``corrections`` mapping.
        """
        additems = [key for key in self._obj.controllers.keys() if key not in self._obj.corrections.keys()]
        item, ok = QtWidgets.QInputDialog.getItem(self, "Add Correct Params", "Param", additems, editable=False)
        if ok:
            self._setTerget(item)

    def _setTerget(self, item):
        """
        Create and add a correction target.

        Args:
            item (str): Name of the target (motor-axis) to add. This will be used as the key in the corrector's ``corrections`` mapping.
        """
        self._obj.corrections[item] = _FunctionCombination()
        tree_item = _EditableItem([item])
        self.addTopLevelItem(tree_item)

    def _clear(self):
        """
        Clear all correction targets.

        After user confirmation, remove all entries from the corrector's ``corrections`` mapping and clear the tree widget.
        """
        ok = QtWidgets.QMessageBox.warning(self, "Clear", "Do you want to CLEAR all target(s)?", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            self._obj.corrections.clear()
            self.clear()

    def _del(self, item):
        """
        Delete a correction target.

        After user confirmation, remove the corresponding entry from the corrector's ``corrections`` mapping and the target.

        Args:
            item (QTreeWidgetItem): Top-level tree item identifying the correction target to delete.
        """
        ok = QtWidgets.QMessageBox.warning(self, "Clear", "Do you want to DELETE this target?", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            key, _ = self._correction(item)
            del self._obj.corrections[key]
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))

    def _enable(self, item):
        """
        Enable or disable a correction.

        Toggle the correction's ``enabled`` flag and update the item's background to reflect the new enabled/disabled state.

        Args:
            item (QTreeWidgetItem): Top-level tree item identifying the correction target to toggle.
        """
        _, c = self._correction(item)
        c.enabled = not c.enabled
        item.setBackground(0, QtGui.QBrush(QtGui.QColor("white")) if c.enabled else QtGui.QBrush(QtGui.QColor("gray")))
        item.setBackground(1, QtGui.QBrush(QtGui.QColor("white")) if c.enabled else QtGui.QBrush(QtGui.QColor("gray")))

    def _addVar(self, item):
        """
        Add a control variable (motor-axis) to a correction.

        Open a dialog to select a motor-axis as the variable, create an identity `_InterpolatedFunction` for that axis, and register it on the correction using ``_setVar()``.

        Args:
            item (QTreeWidgetItem): Top-level tree item identifying the correction target.
        """
        _, c = self._correction(item)
        additems = [key for key in self._obj.controllers.keys() if key not in c.functions.keys()]
        var, ok = QtWidgets.QInputDialog.getItem(self, "Select variables", "Variables", additems, editable=False)
        if ok:
            self._setVar(item, var)

    def _setVar(self, item, var):
        """
        Set an identity interpolator for a control variable (motor-axis) on a correction (motor-axis).

        Register an identity ``_InterpolatedFunction`` in the correction's ``functions`` mapping for the specified variable name.

        Args:
            item (QTreeWidgetItem): Top-level tree item identifying the correction target.
            var (str): Name of the variable (motor-axis) to add.
        """
        _, c = self._correction(item)
        f = _InterpolatedFunction(lambda x: x[0], [var])
        c.functions[var] = f
        item.addChild(_EditableItem([var]))

    def _addFunc(self, item):
        """
        Add a function to a correction.

        Open a dialog to select a data file, construct the ``_InterpolatedFunction`` from the file, and register it on the correction using ``_setFunc()``.

        Args:
            item (QTreeWidgetItem): Top-level tree item identifying the correction target.
        """
        dialog = _addFuncDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            f = dialog.getFunction()
            self._setFunc(item, f)

    def _setFunc(self, item, func):
        """
        Set a function on a correction target (motor-axis).

        Register the provided function in the correction's ``functions`` mapping under a generated name (for example ``funcN``).

        Args:
            item (QTreeWidgetItem): Top-level tree item identifying the correction target.
            func (callable): Callable that implements ``argNames()`` (returns the function's variable names).
        """
        _, c = self._correction(item)
        i = 1
        while "func" + str(i) in c.functions.keys():
            i += 1
        c.functions["func"+str(i)] = func
        item.addChild(_EditableItem(["func"+str(i)+"("+",".join(func.argNames())+")"]))

    def _delFunc(self, item):
        """
        Delete a function attached to a correction (motor-axis).

        Remove the callable from the correction's ``functions`` mapping and remove the corresponding child item from the tree.

        Args:
            item (QTreeWidgetItem): Function item to delete.
        """
        ok = QtWidgets.QMessageBox.warning(self, "Clear", "Do you want to DELETE this function?", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            _, c = self._correction(item.parent())
            key = list(c.functions.keys())[item.parent().indexOfChild(item)]
            del c.functions[key]
            item.parent().removeChild(item)

    def _fix(self, item):
        """
        Fix a correction function parameter (motor-axis) to a constant value.

        Args:
            item (QTreeWidgetItem): Child item representing the correction function to modify.
        """
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
        """
        Delete a fixed parameter from a correction function.

        Args:
            item (QTreeWidgetItem): Child item representing the fixed parameter to delete.
        """
        p = item.text(0).replace("Fix: ", "")
        del self._function(item).fixedValues[p]
        item.parent().removeChild(item)

    def _edited(self, item, column):
        """
        Handle edits to the expression column of a correction target (motor-axis).

        If the edited item is a fixed parameter (its label starts with "Fix:"), parse and store the provided value. 
        Otherwise, treat the edited text as the correction expression for the target.

        Args:
            item (QTreeWidgetItem): Target item to edit.
            column (int): Index of the edited column.
        """
        if column == 1:
            if "Fix: " in item.text(0):
                p = item.text(0).replace("Fix: ", "")
                f = self._function(item.parent())
                f.fixedValues[p] = eval(item.text(1))
            else:
                _, c = self._correction(item)
                c.expression = item.text(1)

    def _correction(self, item):
        """
        Get the correction object for a target (motor-axis).

        Return the correction key and the corresponding correction function (typically a ``_FunctionCombination``) for a correction target.

        Args:
            item (QTreeWidgetItem): Top-level tree item identifying the correction target.

        Returns:
            tuple: (key (str), correction function (typically ``_FunctionCombination``)).
        """
        index = self.indexOfTopLevelItem(item)
        key = list(self._obj.corrections.keys())[index]
        return key, self._obj.corrections[key]

    def _function(self, item):
        """
        Get the function object corresponding to a child item of the correction tree.

        Args:
            item (QTreeWidgetItem): Child item representing a correction function.

        Returns:
            callable: Callable stored in the correction's ``functions`` mapping (typically an ``_InterpolatedFunction`` or ``_InterpolatedFunctionFromFile``).
        """
        _, c = self._correction(item.parent())
        key = list(c.functions.keys())[item.parent().indexOfChild(item)]
        return c.functions[key]

    def refresh(self):
        """
        Refresh the tree contents from the corrector's ``corrections`` mapping.

        Recreate top-level items (correction targets) for each correction and populate child items for functions and fixed parameters.
        """
        self.clear()
        for key, c in self._obj.corrections.items():
            argSet = set()
            for func in c.functions.values():
                if hasattr(func, 'argNames'):
                    argSet.update(func.argNames())
            expr = getattr(c, "expression", ', '.join(sorted(argSet)))
            top = _EditableItem([key, expr])
            self.addTopLevelItem(top)
            for funcName, func in c.functions.items():
                if hasattr(func, 'argNames'):
                    funcExpr = f"{funcName}({', '.join(func.argNames())})"
                else:
                    funcExpr = funcName
                top.addChild(_EditableItem([funcName, funcExpr]))
            
    def _copy(self):
        """
        Save a portable representation of the current corrections mapping.
        """
        dics = []
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            key, _ = self._correction(item)

            expression = item.text(1)
            childItems = [item.child(i) for i in range(item.childCount())]
            funcPathes = [self._function(child).path for child in childItems if type(self._function(child)) is _InterpolatedFunctionFromFile]
            variables = [self._function(child).argNames()[0] for child in childItems if type(self._function(child)) is _InterpolatedFunction]
            dics.append({"terget": key, "expression": expression, "funcs": funcPathes, "variables": variables})

        with open(".lys_instr/copyPreCorrection.txt", 'w') as f:
            f.write(str(dics))

    def _paste(self):
        """
        Load and apply a previously saved corrections mapping.
        """
        self._obj.corrections.clear()
        self.clear()

        with open(".lys_instr/copyPreCorrection.txt", 'r') as f:
            dicsAsStr = f.read()
        dics = eval(dicsAsStr)

        i = 0
        for dic in dics:
            self._setTerget(dic["terget"])
            item = self.topLevelItem(i)
            item.setText(1, str(dic["expression"]))

            if len(dic["funcs"]) > 0:
                for funcPath in dic["funcs"]:
                    input = Wave(funcPath)
                    f = RBFInterpolator(input.x, input.data, kernel="linear")
                    func = _InterpolatedFunctionFromFile(f, input.note["variables"], funcPath)
                    self._setFunc(item, func)

            if len(dic["variables"]) > 0:
                for var in dic["variables"]:
                    self._setVar(item, var)
            i += 1


class _EditableItem(QtWidgets.QTreeWidgetItem):
    """
    Editable tree widget item.

    QTreeWidgetItem subclass that makes the item editable by enabling the Qt.ItemIsEditable flag.
    """

    def __init__(self, *args, **kwargs):
        """
        Create the editable item and enable the editable flag.

        Args:
            *args: Positional arguments forwarded to QTreeWidgetItem.
            **kwargs: Keyword arguments forwarded to QTreeWidgetItem.
        """
        super().__init__(*args, **kwargs)
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)


class _addFuncDialog(QtWidgets.QDialog):
    """
    Dialog for building an interpolated function from a data file.

    Prompts for a numpy ``.npz`` file and constructs an ``_InterpolatedFunctionFromFile`` instance when the dialog is accepted.
    """

    def __init__(self, parent):
        """
        Initialize the dialog.

        Args:
            parent (QWidget): Parent widget for the dialog.
        """
        super().__init__(parent)
        self.setWindowTitle("New function from data")
        self.__initLayout()

    def __initLayout(self):
        """
        Create and arrange widgets for file selection and action buttons.
        """
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
        """
        Construct and return an interpolated function from the selected file.

        Returns:
            _InterpolatedFunctionFromFile: Wrapper around the scipy interpolator and the original file path.
        """
        input = Wave(self._input.text())
        f = RBFInterpolator(input.x, input.data, kernel="linear")
        return _InterpolatedFunctionFromFile(f, input.note["variables"], self._input.text())

    def getFunctionPath(self):
        """
        Return the selected function file path.

        Returns:
            str: Path to the ``.npz`` file as entered or selected in the dialog.
        """
        return self._input.text()

    def __open(self, lineEdit):
        """
        Open a file dialog and set the chosen path into the provided line edit.

        Args:
            lineEdit (QLineEdit): Line edit to set the selected file path into.
        """
        file, _ = QtWidgets.QFileDialog.getOpenFileName(None, 'Open file', filter="npz(*.npz)")
        if 0 != len(file):
            lineEdit.setText(file)


class _NewFunctionWindow(LysSubWindow):
    """
    Subwindow for assembling new correction functions from tables.

    Collects sampled points for a target and exports them as a numpy ``.npz`` file that can later be used to build an interpolator.
    """

    def __init__(self, corrector):
        """
        Initialize the new-function subwindow.

        Args:
            corrector (object): Corrector providing access to controllers (mapping of axis names to motors).
        """
        super().__init__()
        self.setWindowTitle("New function")
        self._corrections = {}
        self._cor = corrector
        self.__initUI()

    def __initUI(self):
        """
        Create widgets and layout for the subwindow.
        """
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
        """
        Build and show the context menu for the corrections tree.
        """
        menu = QtWidgets.QMenu()
        selected_items = self._tree.selectedItems()

        if len(selected_items) > 0:
            exp = QtWidgets.QAction('Export correction table', triggered=lambda b, item=selected_items[0]: self._exportTable(item))
            clear = QtWidgets.QAction('Clear correction table', triggered=lambda b, item=selected_items[0]: self._clearTable(item))
            rem = QtWidgets.QAction('Remove correction table', triggered=lambda b, item=selected_items[0]: self._delCorrectParams(item))
            menu.addAction(exp)
            menu.addAction(clear)
            menu.addAction(rem)
            menu.addSeparator()

        add = QtWidgets.QAction('Add new correction table', triggered=self._addCorrectParam)
        cl = QtWidgets.QAction('Clear all tables', triggered=self._clearCorrectParams)
        menu.addAction(add)
        menu.addAction(cl)

        menu.exec_(QtGui.QCursor.pos())

    def _addCorrectParam(self):
        """
        Prompt for a new correction table and add it to the working set.

        Open a dialog and register an in-memory working table for the chosen correction target.
        """
        d = _MakeFuncDialog(self, self._cor.controllers.keys())
        if d.exec_():
            self._corrections[d.target] = _CorrectionData(d.args)
            item = QtWidgets.QTreeWidgetItem([d.target, ", ".join([str(s) for s in d.args]), "0"])
            self._tree.addTopLevelItem(item)

    def _clearCorrectParams(self):
        """
        Clear all temporary correction tables after confirmation.
        """
        ok = QtWidgets.QMessageBox.warning(self, "Clear", "Do you want to CLEAR the correction tables?", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            self._corrections.clear()
            self._tree.clear()

    def _delCorrectParams(self, item):
        """
        Delete a single correction table after confirmation.

        Args:
            item (QTreeWidgetItem): Top-level tree item (correction target) identifying the correction table to remove.
        """
        key, _ = self._correction(item)
        ok = QtWidgets.QMessageBox.warning(self, "Delete", 'Do you want to DELETE the parameter ' + key + '?', QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            del self._corrections[key]
            self._tree.takeTopLevelItem(self._tree.indexOfTopLevelItem(item))

    def _clearTable(self, item):
        """
        Clear sampled rows for a named correction table.

        Args:
            item (QTreeWidgetItem): Top-level item (correction target) identifying the correction table to clear.
        """
        key, d = self._correction(item)
        ok = QtWidgets.QMessageBox.warning(self, "Delete", 'Do you want to CLEAR the table for  ' + key + '?', QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            d.clear()
            self._updateTree()

    def _exportTable(self, item):
        """
        Export a correction table to a numpy ``.npz`` file.

        Prompt for a file path and export the sampled values and variable (motor-axis) names.
        """
        path, type = QtWidgets.QFileDialog.getSaveFileName(filter="numpy npz (*.npz)")
        if len(path) != 0:
            key, d = self._correction(item)
            val, args = d.get()
            Wave(val, args, variables=d.argNames).export(path)

    def _addValues(self):
        """
        Sample current controller values and append them to working tables.
        """
        for key, d in self._corrections.items():
            targ = self._cor.controllers[key].get()[key]
            args = [self._cor.controllers[k].get()[k] for k in d.argNames]
            d.append(targ, args)
        self._updateTree()

    def _undoValues(self):
        """
        Remove the most recently added sample from each working table.
        """
        for d in self._corrections.values():
            d.undo()
        self._updateTree()

    def _correction(self, item):
        """
        Get the correction object for a target (motor-axis).

        Return the correction key and the corresponding in-memory correction table (a ``_CorrectionData`` instance) for the given target.

        Args:
            item (QTreeWidgetItem): Top-level tree item identifying the correction target.

        Returns:
            tuple: (key (str), _CorrectionData instance)
        """
        index = self._tree.indexOfTopLevelItem(item)
        key = list(self._corrections.keys())[index]
        return key, self._corrections[key]

    def _updateTree(self):
        """
        Refresh the displayed sample counts for each working correction table.
        """
        for i, d in enumerate(self._corrections.values()):
            self._tree.topLevelItem(i).setText(2, str(len(d)))


class _MakeFuncDialog(QtWidgets.QDialog):
    """
    Dialog to configure arguments for a new correction table.

    Present a correction target selector and up to 20 correction variable selectors.
    """

    def __init__(self, parent, params):
        """
        Initialize the dialog with available motor-axis names.

        Args:
            parent (QWidget): Parent widget.
            params (Iterable[str]): Iterable of available motor-axis names.
        """
        super().__init__(parent)
        self._params = list(params)

        self.setWindowTitle("New function")
        self.__initLayout(params)
        self._updateWidgets()

    def __initLayout(self, params):
        """
        Create widgets for selecting correction targets and variables (both are motor-axes).

        Args:
            params (Iterable[str]): Iterable of available variable names.
        """
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
        """
        Update comboboxes to avoid duplicates and show available options.

        Protected against circular calls by the ``avoidCircularReference`` decorator.
        """
        selected = [self._targ.currentText()] + [c.currentText() for c in self._args]
        for i, c in enumerate(self._args):
            # remove duplicate
            if c.currentText() in selected[:i]:
                c.setCurrentText("")
            # remove empty
            if c.currentText() == "":
                if self._args[i+1].currentText() != "":
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
            if i == 0:
                continue
            if self._args[i-1].currentText() == "":
                c.hide()
            else:
                c.show()

    @property
    def target(self):
        """
        Selected correction target (motor-axis) name.
        
        Returns:
            str: Selected correction target name.
        """
        return self._targ.currentText()

    @property
    def args(self):
        """
        Selected correction variable (motor-axis) names.

        Returns:
            list[str]: Selected correction variable names.
        """
        return [c.currentText() for c in self._args if c.currentText() != ""]


class _CorrectionData:
    """
    In-memory container for sampled correction data.

    Store sampled target values and corresponding variables until the user exports them.
    """

    def __init__(self, argsNames):
        """
        Initialize an empty correction table.

        Args:
            argsNames (Sequence[str]): Ordered list of variable (motor-axis) names for the table.
        """
        self._argNames = argsNames
        self.clear()

    def clear(self):
        """
        Remove all sampled rows from the table.
        """
        self._values = []
        self._args = []

    def append(self, targ, args):
        """
        Append a sampled row to the table.

        Args:
            targ (numeric): Sampled target value.
            args (Sequence[float]): Variables for the sample.
        """
        self._values.append(targ)
        self._args.append(args)

    def undo(self):
        """
        Remove the most-recently appended sample from the table.
        """
        self._values.pop(-1)
        self._args.pop(-1)

    def get(self):
        """
        Return sampled values and variables for export.

        Returns:
            tuple: (values (ndarray, shape (N, 1)), variables (ndarray, shape (N, M))).
        """
        return np.array([self._values]).T, np.array(self._args)

    def __len__(self):
        """
        Return the number of sampled rows in the table.

        Returns:
            int: Number of sampled rows.
        """
        return len(self._values)

    @property
    def argNames(self):
        """
        Ordered list of variable (motor-axis) names for this table.

        Returns:
            Sequence[str]: Variable names.
        """
        return self._argNames


class _InterpolatedFunctionFromFile(_InterpolatedFunction):
    """
    Interpolated-function wrapper that records its source file.

    Wrapper for an interpolator created from a file. 
    The class records the original file path so calling code can reproduce or inspect file-backed functions (for example when copying/pasting corrections).
    """

    def __init__(self, interpolator, argNames, path):
        """
        Initialize the wrapper with an interpolator and its source path.

        Args:
            interpolator (callable): Interpolator that maps input points to values.
            argNames (Sequence[str]): Ordered variable (motor-axis) names expected by the interpolator.
            path (str): Original file path the interpolator was created from.
        """
        super().__init__(interpolator, argNames)
        self._path = path

    @property
    def path(self):
        """
        Return the source file path for the interpolator.

        Returns:
            str: Path to the original ``.npz`` file used to create the interpolator.
        """
        return self._path
