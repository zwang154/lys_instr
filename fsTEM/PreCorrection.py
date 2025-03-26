import numpy as np
from scipy.interpolate import interp1d, interpn
from lys import widgets, Wave, multicut, glb
from lys.Qt import QtWidgets, QtCore, QtGui


class PreCorrector(QtCore.QObject):
    dataChanged = QtCore.pyqtSignal(object)

    def __init__(self, tem):
        super().__init__()
        self._tem = tem
        self._tem.valueSet.connect(lambda value: self.doCorrection(value), type=QtCore.Qt.DirectConnection)
        self._enable = False
        self._allScanParams = self._tem.getInfo().getScan()
        self._allScanParams.update(self._tem.getTIA().getScans())
        self._allCorrectParams = self._tem.getStage().getScans()
        self._allCorrectParams.update(self._tem.getInfo().getScan(single=False))
        self._allCorrectParams.update(self._tem.getTIA().getScans())
        self._allCorrectParams.update(self._tem.getShiftScans())

        self._scanParams = []
        self._correctParams = {}
        self._initialValues = {}

    def updateScanParams(self, params, gui=None):
        if len(params) == 0 or len(params) < len(self._scanParams) or len(self._correctParams) == 0:
            self._scanParams = params
            self.updateCorrectParams([])
            return

        newParams = [param for param in params if param not in self._scanParams]

        for sparam in newParams:
            value, ok = QtWidgets.QInputDialog.getDouble(gui, "Set value for " + sparam, 'Enter the "' + sparam + '" value of the current data.')
            if not ok:
                break

            for cparam, info in self._correctParams.items():
                waves = info["wave"]
                w = waves[0]
                if w.data.shape == ():
                    self._correctParams[cparam]["wave"].insert(0, Wave())
                else:
                    nw = w.duplicate()
                    if w.data.ndim == len(self._scanParams):
                        nw.data = nw.data.reshape(np.append(nw.data.shape, 1))
                    else:
                        nw.data = nw.data.reshape(np.insert(nw.data.shape, -1, 1))
                    self._correctParams[cparam]["wave"].insert(0, nw)

                    nw.axes[len(params) - 1] = np.array([value])

            self._scanParams.append(sparam)

        self.dataChangedFunc([])

    def updateCorrectParams(self, params):
        for param in params:
            if param not in self._correctParams.keys():
                self._correctParams[param] = {"wave": [Wave()], "relative": False}

        keys = list(self._correctParams.keys())
        for param in keys:
            if param not in params:
                del self._correctParams[param]

        self.dataChangedFunc([])

    def addCurrentValues(self, correctParams):
        if len(correctParams) == 0:
            correctParams = self._correctParams.keys()
        scanParams = {param: self._allScanParams[param].get() for param in self._scanParams}
        # rng = np.random.default_rng()  # for test
        # scanParams = {param: rng.integers(2) for param in self._scanParams}  # for test

        phiName = [name for name in self._scanParams if "beam_phi" in name]
        phiName = "" if len(phiName) == 0 else phiName[0]
        if len(phiName) and np.isclose(scanParams[phiName], 0, atol=1e-2):
            scanParamsList = [scanParams, scanParams.copy()]
            scanParamsList[1][phiName] = 360
        else:
            scanParamsList = [scanParams]
        for scanParams in scanParamsList:
            for param in correctParams:
                w = self._correctParams[param]["wave"][0]
                value = np.array(self._allCorrectParams[param].get())
                if self._correctParams[param]["relative"]:
                    value -= self._initialValues.get(param, 0)
                # if "Shift" in param:  # for test
                #     value = [rng.uniform(-1000, 1000), rng.uniform(-1000, 1000)]
                # else:  # for test
                #     value = rng.uniform(-1000, 1000)
                if w.data.shape == ():
                    shape = np.ones(len(self._scanParams), dtype=int)
                    if value.shape != ():
                        shape = np.append(shape, *value.shape)
                    w = Wave(data=np.zeros(shape, dtype=float))
                    if value.shape != ():
                        w.data[..., 0, :] = value
                    else:
                        w.data[..., 0] = value
                    for i in range(len(self._scanParams)):
                        w.axes[i][0] = scanParams[self._scanParams[i]]
                else:
                    w = w.duplicate()
                    idxs = []
                    for i in range(len(self._scanParams)):
                        idx = w.axes.posToPoint(scanParams[self._scanParams[i]], axis=i)
                        if not np.isclose(w.axes[i][idx], scanParams[self._scanParams[i]], rtol=1e-3):
                            idx += 1 if w.axes[i][idx] < scanParams[self._scanParams[i]] else 0
                            w.insert(idx, axis=i, axisValue=scanParams[self._scanParams[i]])
                        idxs.append(idx)
                    tmpdata = w.data
                    for i in range(len(self._scanParams) - 1):
                        tmpdata = tmpdata[idxs[i]]
                    tmpdata[idxs[-1]] = value

                w.note["File"] = ""
                self._correctParams[param]["wave"].insert(0, w)

        self._cutOldCorrectParams()
        self.dataChangedFunc(correctParams)

    def undo(self, correctParams):
        for param in correctParams:
            if len(self._correctParams[param]["wave"]) > 1:
                self._correctParams[param]["wave"].pop(0)

        self.dataChangedFunc(correctParams)

    def clearValues(self, correctParams):
        for param in correctParams:
            self._correctParams[param]["wave"].insert(0, Wave())
            self._correctParams[param]["wave"] = self._correctParams[param]["wave"][:5]

        self.dataChangedFunc(correctParams)

    def dataChangedFunc(self, correctParams):
        self.dataChanged.emit([info["wave"][0] for param, info in self._correctParams.items() if param in correctParams])

    def getWaves(self, correctParams):
        return {param: info["wave"][0] for param, info in self._correctParams.items() if param in correctParams}

    def saveAsFile(self, correctParams, gui=None):
        if len(correctParams) == 0:
            correctParams = self._correctParams.keys()
        waves = self.getWaves(correctParams)
        if len(waves) == 0:
            return

        fileName = QtWidgets.QFileDialog.getSaveFileName(gui, "Save file", "", "Numpy npz (*.npz)")[0]
        if fileName:
            fileName = fileName.strip(".npz")
            if len(waves) == 1:
                key = list(waves.keys())[0]
                waves[key].note["correctParam"] = key
                waves[key].note["scanParams"] = self._scanParams
                waves[key].export(fileName)
                waves[key].note["File"] = fileName + ".npz"
            else:
                for param, wave in waves.items():
                    wave.note["correctParam"] = param
                    wave.note["scanParams"] = self._scanParams
                    wave.export(fileName + "_" + param)
                    wave.note["File"] = fileName + "_" + param + ".npz"

    def loadFromFile(self, correctParams, gui=None):
        def __loadWave(fileName, w, correctParam=None, gui=None):
            if correctParam is None:
                correctParam = w.note["correctParam"]
            if "scanParams" not in w.note.keys():
                if len(self._scanParams) == 0:
                    QtWidgets.QMessageBox.critical(gui, "Error", "Failed to load: No Scan Parameter found in file.\nFile: " + fileName, QtWidgets.QMessageBox.Ok)
                    return -1
                elif w.data.ndim < len(self._scanParams):
                    QtWidgets.QMessageBox.critical(gui, "Error", "Failed to load: Data dimension in file does not match registered Scan Parameters.\nFile: " + fileName, QtWidgets.QMessageBox.Ok)
                    return -1
                elif len(self._scanParams) == 1:
                    w.note["scanParams"] = self._scanParams
                else:
                    axes = []
                    for param in self._scanParams:
                        axis, ok = QtWidgets.QInputDialog.getItem(gui, "Select axis for Scan Parameter", "Select axis for Scan Parameter: " + param, [str(i) for i in range(len(self._scanParams)) if i not in axes], editable=False)
                        if not ok:
                            return -1
                        axes.append(int(axis))
                    w.note["scanParams"] = [self._scanParams[i] for i in axes]
            if len(self._scanParams) == 0:
                self._scanParams = w.note["scanParams"]

            if sorted(self._scanParams) != sorted(w.note["scanParams"]):  # TODO: Fix to allow loading even if the number of scanParams is insufficient
                QtWidgets.QMessageBox.critical(gui, "Error", "Failed to load: Scan parameters in file do not match registered scan parameters.\nFile: " + fileName, QtWidgets.QMessageBox.Ok)
                return -1

            idxs = [w.note["scanParams"].index(param) for param in self._scanParams]
            if len(idxs) != w.data.ndim:
                idxs.extend([i for i in range(len(idxs), w.data.ndim)])
            idxs = tuple(idxs)
            w.data = w.data.transpose(idxs)
            w.axes = [w.axes[i] for i in idxs]
            w.note["File"] = fileName
            if correctParam not in self._correctParams.keys():
                self._correctParams[correctParam] = {"wave": [], "relative": False}
            self._correctParams[correctParam]["wave"].insert(0, w)

        fileNames = QtWidgets.QFileDialog.getOpenFileNames(gui, "Open file", "", "Numpy npz (*.npz)")[0]
        if len(fileNames) == 0:
            return
        if len(correctParams) == 1:
            w = Wave().importFrom(fileNames[0])
            if ("correctParam" not in w.note.keys()) or (w.note["correctParam"] != correctParams[0]):
                if "correctParam" not in w.note.keys():
                    message = "This file was not created by PreCorrection.\nAre you sure to continue?"
                else:
                    message = f'This file is not for "{correctParams[0]}" but for "{w.note["correctParam"]}".\nAre you sure to continue?'
                dlg = _LoadDialog(message)
                ok = dlg.exec_()
                if not ok:
                    return
                mode = dlg.mode
                if mode == "Multiply the free expression formula":
                    txt, inv = dlg.text, dlg.inverse
                    if len(txt):
                        try:
                            mat = np.array(glb.shell().eval(txt))
                            if mat.shape == (1,):
                                mat = mat[0]
                            if inv:
                                if len(mat.shape) == 2:
                                    mat = np.linalg.inv(mat)
                                else:
                                    mat = 1 / mat
                            w.data = np.dot(mat, w.data.T).T
                        except:
                            QtWidgets.QMessageBox.critical(gui, "Error", "Failed to load because matrix cannot be evaluated or is incorrect.\nFile: " + fileNames[0], QtWidgets.QMessageBox.Ok)
                            return
                elif mode == "Convert from image point to beam_shift":
                    try:
                        mat = - np.array([[0.09013671, 0.18959546], [0.19225284, -0.08975173]]) * 55000 / dlg.magnification
                        w.data = np.dot(mat, w.data.T).T
                    except:
                        QtWidgets.QMessageBox.critical(gui, "Error", "Failed to load because magnification is not integer or file is incorrect.\nFile: " + fileNames[0], QtWidgets.QMessageBox.Ok)
                        return
            __loadWave(fileNames[0], w, correctParam=correctParams[0], gui=gui)

        elif len(correctParams) == 0:
            for fileName in fileNames:
                w = Wave().importFrom(fileName)
                if "correctParam" not in w.note.keys():
                    QtWidgets.QMessageBox.critical(gui, "Error", "Failed to load due to undefined Correct Parameter.\nFile: " + fileName, QtWidgets.QMessageBox.Ok)
                    continue

                if w.note["correctParam"] not in self._allCorrectParams.keys():
                    QtWidgets.QMessageBox.critical(gui, "Error", "Failed to load due to the old Correct Parameter name: " + w.note["correctParam"] + "\nFile: " + fileName, QtWidgets.QMessageBox.Ok)
                    continue

                __loadWave(fileName, w, gui=gui)
        else:
            QtWidgets.QMessageBox.critical(gui, "Error", "Only 1 correctParam can be loaded at a time.", QtWidgets.QMessageBox.Ok)
            return

        self._cutOldCorrectParams()

        self.dataChangedFunc(correctParams)

    def setEnable(self, bool):
        self._enable = bool
        if bool:
            self.saveCurrentValues()
            self.doCorrection()

    @property
    def enable(self):
        return self._enable

    def saveCurrentValues(self):
        self._initialValues = {param: np.array(self._allScanParams[param].get()) for param in self._scanParams}
        self._initialValues.update({param: np.array(self._allCorrectParams[param].get()) for param in self._correctParams})

    def doCorrection(self, values={}):
        if not self._enable:
            return

        if len(values):
            if len(set(self._scanParams) & set(values.keys())) == 0:
                return

        scanValues = [self._allScanParams[param].get() for param in self._scanParams]
        # rng = np.random.default_rng()  # for test
        # scanValues = list(rng.uniform(-10, 10, len(self._scanParams)))  # for test
        if len(scanValues) == 0:
            return

        initialScanValues = [self._initialValues[param] if param in self._initialValues.keys() else 0 for param in self._scanParams]

        for param in self._correctParams.keys():
            wave = self._correctParams[param]["wave"][0]
            axes = wave.axes
            data = wave.data
            if len(scanValues) < len(axes):
                axes = axes[:len(scanValues)]

            tmpScanValues = scanValues
            tmpInitialScanValues = initialScanValues
            while 1 in data.shape:
                dim = data.shape.index(1)
                axes = axes[:dim] + axes[dim + 1:]
                data = np.reshape(data, data.shape[:dim] + data.shape[dim + 1:])
                tmpScanValues = tmpScanValues[:dim] + tmpScanValues[dim + 1:]
                tmpInitialScanValues = tmpInitialScanValues[:dim] + tmpInitialScanValues[dim + 1:]
            if len(tmpScanValues) == 1:
                # print(axes[0], data, tmpScanValues[0])
                # print(type(axes[0]), type(data), type(tmpScanValues[0]))
                f = interp1d(axes[0], data, axis=0, bounds_error=False, fill_value='extrapolate')
                value = f(tmpScanValues[0])
                if self._correctParams[param]["relative"]:
                    value += self._initialValues[param] - f(tmpInitialScanValues[0])
            else:
                # print(axes, data, tmpScanValues)
                # print(type(axes), type(data), type(tmpScanValues))
                value = interpn(axes, data, tmpScanValues, bounds_error=False, fill_value=None)[0]
                if self._correctParams[param]["relative"]:
                    value += self._initialValues[param] - interpn(axes, data, tmpInitialScanValues, bounds_error=False, fill_value=None)[0]
            # print("[Do Correction] Scan values: ", tmpScanValues, ", Correct Param : ", param, ", Set Value: ", value)
            self._allCorrectParams[param].set(value)

    def widget(self):
        return PreCorrectionGUI(self)

    def _cutOldCorrectParams(self, size=10):
        for param, info in self._correctParams.items():
            self._correctParams[param]["wave"] = info["wave"][:size]


class _LoadDialog(QtWidgets.QDialog):
    def __init__(self, message, title="Caution"):
        super().__init__()
        self.setWindowTitle(title)
        g = QtWidgets.QGridLayout()
        icon = QtWidgets.QLabel()
        icon.setPixmap(icon.style().standardPixmap(QtWidgets.QStyle.SP_MessageBoxWarning))
        icon.setAlignment(QtCore.Qt.AlignCenter)
        lbl1 = QtWidgets.QLabel(message)
        lbl2 = QtWidgets.QLabel("Select the operation to apply to the loaded data.")
        self._mode = QtWidgets.QComboBox()
        self._modelist = {}
        self._modelist["Do nothing"] = QtWidgets.QWidget()
        self._modelist["Multiply the free expression formula"] = QtWidgets.QWidget()
        self._modelist["Convert from image point to beam_shift"] = QtWidgets.QWidget()
        self._mode.addItems(self._modelist.keys())
        self._mode.currentTextChanged.connect(self.__changeMode)
        self._txt = QtWidgets.QLineEdit()
        self._inv = QtWidgets.QCheckBox("inverse")
        self._mag = QtWidgets.QLineEdit()
        okbtn = QtWidgets.QPushButton("OK", clicked=self.accept)
        cancelbtn = QtWidgets.QPushButton("Cancel", clicked=self.reject)

        g.addWidget(icon, 0, 0)
        g.addWidget(lbl1, 0, 1, 1, 5)
        g.addWidget(QtWidgets.QLabel(""), 1, 0)
        g.addWidget(lbl2, 2, 0, 1, 6)
        g.addWidget(self._mode, 3, 0, 1, 6)

        w1 = self._modelist["Multiply the free expression formula"]
        g1 = QtWidgets.QGridLayout()
        w1.setLayout(g1)
        g1.addWidget(QtWidgets.QLabel("Enter the matrix expression or number to multiply\nthe loaded data by."), 0, 0, 1, 3)
        g1.addWidget(self._txt, 1, 0, 1, 2)
        g1.addWidget(self._inv, 1, 2, 1, 1)

        w2 = self._modelist["Convert from image point to beam_shift"]
        g2 = QtWidgets.QGridLayout()
        w2.setLayout(g2)
        g2.addWidget(QtWidgets.QLabel("Magnification of loading data"), 0, 0, 1, 2)
        g2.addWidget(self._mag, 0, 2, 1, 1)

        for wid in self._modelist.values():
            g.addWidget(wid, 4, 0, 1, 6)

        g.addWidget(QtWidgets.QLabel(""), 5, 0)
        g.addWidget(okbtn, 6, 0, 1, 3)
        g.addWidget(cancelbtn, 6, 3, 1, 3)
        self.setLayout(g)
        self.__changeMode("Do nothing")

    def __changeMode(self, mode):
        for key, wid in self._modelist.items():
            wid.setVisible(key == mode)

    @property
    def mode(self):
        return self._mode.currentText()

    @property
    def text(self):
        return self._txt.text()

    @property
    def inverse(self):
        return self._inv.isChecked()

    @property
    def magnification(self):
        return int(self._mag.text())


class PreCorrectionGUI(QtWidgets.QWidget):
    def __init__(self, obj):
        super().__init__()
        self._obj = obj
        self.__initLayout()
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.adjustSize()
        self._obj.dataChanged.connect(self.__dataChanged)

    def __initLayout(self):
        self.setStyleSheet("QLineEdit {font-size: 10pt}"
                           "QPushButton {font-size: 12pt}"
                           "QLabel {font-size: 12pt}"
                           "QCheckBox {font-size: 12pt}"
                           "QListWidget {font-size: 14pt}")

        self._scanParams = QtWidgets.QListWidget()
        self._scanParams.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._scanBuilder = _contextMenuBuilder(self, self._scanParams, self._obj._allScanParams.keys(), self._obj.updateScanParams)
        self._scanParams.customContextMenuRequested.connect(self._scanBuilder.build)

        self._correctParams = QtWidgets.QListWidget()
        self._correctParams.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._correctParams.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._correctParams.itemSelectionChanged.connect(lambda: self._obj.dataChangedFunc(self.__selectedCorrectParams()))
        self._correctParams.itemClicked.connect(self.__itemClicked)
        self._correctBuilder = _contextMenuBuilder(self, self._correctParams, self._obj._allCorrectParams.keys(), self._obj.updateCorrectParams)
        self._correctParams.customContextMenuRequested.connect(self._correctBuilder.build)

        self._correctFile = QtWidgets.QLineEdit()
        self._correctFile.isReadOnly = True

        v = QtWidgets.QVBoxLayout()
        v.addWidget(QtWidgets.QCheckBox("Enable Correction", checked=False, clicked=self._obj.setEnable))
        v.addWidget(QtWidgets.QWidget())
        v.addWidget(QtWidgets.QLabel("Scan Parameters"))
        v.addWidget(self._scanParams)

        v.addWidget(QtWidgets.QWidget())
        v.addWidget(QtWidgets.QLabel("Correct Parameters"))
        g = QtWidgets.QGridLayout()
        g.addWidget(QtWidgets.QLabel("File"), 0, 0, 1, 1)
        g.addWidget(self._correctFile, 0, 1, 1, 5)
        g.addWidget(QtWidgets.QPushButton("Load", clicked=lambda: self._obj.loadFromFile(self.__selectedCorrectParams(), gui=self)), 1, 0, 1, 3)
        g.addWidget(QtWidgets.QPushButton("Save", clicked=lambda: self._obj.saveAsFile(self.__selectedCorrectParams(), gui=self)), 1, 3, 1, 3)
        v.addWidget(self._correctParams)
        v.addLayout(g)

        v.addWidget(QtWidgets.QWidget())
        v.addWidget(QtWidgets.QLabel("Register Current Values"))
        v.addWidget(QtWidgets.QPushButton("Set current value as origin", clicked=self._obj.saveCurrentValues))
        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(QtWidgets.QPushButton("Add", clicked=lambda: self._obj.addCurrentValues(self.__selectedCorrectParams())))
        h1.addWidget(QtWidgets.QPushButton("Undo", clicked=lambda: self._obj.undo(self.__selectedCorrectParams())))
        h1.addWidget(QtWidgets.QPushButton("Clear", clicked=lambda: self._obj.clearValues(self.__selectedCorrectParams())))
        v.addLayout(h1)

        h = QtWidgets.QHBoxLayout()
        h.addLayout(v)

        v2 = QtWidgets.QVBoxLayout()
        self._data = widgets.lysCanvas()
        self._data.setCanvasSize("Width", "Absolute", 8)
        self._data.setCanvasSize("Height", "Absolute", 8)
        v2.addWidget(self._data)
        v2.addWidget(QtWidgets.QPushButton("Multicut", clicked=self.__showMulticut))
        v2.addWidget(QtWidgets.QPushButton("DoCorrectionTest", clicked=self._obj.doCorrection))

        h.addLayout(v2)

        self.setLayout(h)

    def __showMulticut(self):
        waves = self._obj.getWaves(self.__selectedCorrectParams())
        if len(waves) == 1:
            key = list(waves.keys())[0]
            if waves[key].data.ndim > 0:
                multicut(waves[key])

    def __dataChanged(self, waves):
        if len(self._obj._correctParams) != self._correctParams.count():
            self._correctParams.clear()
            for param in self._obj._correctParams.keys():
                item = QtWidgets.QListWidgetItem(param)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Checked if self._obj._correctParams[param]["relative"] else QtCore.Qt.Unchecked)
                self._correctParams.addItem(item)
        if len(self._obj._scanParams) != self._scanParams.count():
            self._scanParams.clear()
            for param in self._obj._scanParams:
                self._scanParams.addItem(param)

        self._data.Clear()
        if len(waves) == 1:
            if waves[0].data.ndim in (1, 2):
                self._data.Append(waves[0])
            self._correctFile.setText("" if "File" not in waves[0].note.keys() else waves[0].note["File"])
        else:
            self._correctFile.clear()

    def __selectedCorrectParams(self):
        return [item.text() for item in self._correctParams.selectedItems()]

    def __itemClicked(self, item):
        for i in range(self._correctParams.count()):
            item = self._correctParams.item(i)
            self._obj._correctParams[item.text()]["relative"] = item.checkState() == QtCore.Qt.Checked


class _contextMenuBuilder:
    """Builder of context menu"""

    def __init__(self, parent, listwidget, additems, updatefunc):
        self._parent = parent
        self._listwidget = listwidget
        self._additems = additems
        self._updatefunc = updatefunc
        self._SetDefaultMenu()

    def _SetDefaultMenu(self):
        self._add = QtWidgets.QAction('Add', triggered=self.__add)
        self._delete = QtWidgets.QAction('Delete', triggered=self.__delete)
        self._clear = QtWidgets.QAction('Clear', triggered=self.__clear)

        menu = QtWidgets.QMenu()
        menu.addAction(self._add)
        menu.addAction(self._delete)
        menu.addAction(self._clear)

        self.__actions = menu

    def build(self):
        self.__actions.exec_(QtGui.QCursor.pos())

    def __add(self):
        additems = [item for item in self._additems if item not in self.__getListItems()]
        if len(additems) == 0:
            return
        item, ok = QtWidgets.QInputDialog.getItem(self._parent, "Add Correct Params", "Param", additems, editable=False)
        if ok:
            items = self.__getListItems()
            items.append(item)
            self._updatefunc(items)

    def __delete(self):
        items = [item.text() for item in self._listwidget.selectedItems()]
        ok = QtWidgets.QMessageBox.warning(self._parent, "Delete", 'This will delete all registered correction values. \n Do you really want to DELETE the parameter(s)? : ' + ", ".join(items), QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok == QtWidgets.QMessageBox.Ok:
            for item in self._listwidget.selectedItems():
                self._listwidget.takeItem(self._listwidget.row(item))
                self._updatefunc(self.__getListItems())

    def __clear(self):
        ok = QtWidgets.QMessageBox.warning(self._parent, "Clear", "This will delete all registered correction values. \n Do you really want to CLEAR the all parameter(s)?", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok == QtWidgets.QMessageBox.Ok:
            self._listwidget.clear()
            self._updatefunc([])

    def __getListItems(self):
        return [self._listwidget.item(i).text() for i in range(self._listwidget.count())]
