import os
import numpy as np
from lys import widgets, filters, Wave, multicut
from lys.Qt import QtWidgets, QtCore, QtGui


class AdvancedCorrector(QtCore.QObject):
    dataChanged = QtCore.pyqtSignal(object)

    def __init__(self, tem):
        super().__init__()
        self._tem = tem
        self._enable = False
        self._allScanParams = self._tem.getInfo().getScan()
        self._allCorrectParams = self._tem.getStage().getScans()
        self._allCorrectParams.update(self._tem.getInfo().getScan())
        self._allCorrectParams.update(self._tem.getShiftScans())

        self._scanParams = []
        self._correctParams = {}

    def updateScanParams(self, params):
        self._scanParams = params

    def updateCorrectParams(self, params):
        for param in params:
            if param not in self._correctParams.keys():
                self._correctParams[param] = [Wave()]

        keys = list(self._correctParams.keys())
        for param in keys:
            if param not in params:
                del self._correctParams[param]

    def addCurrentValues(self, correctParams):
        #        scanParams = {param: self._allScanParams[param].get() for param in self._scanParams}
        rng = np.random.default_rng()
        scanParams = {param: rng.integers(5) for param in self._scanParams}

        for param in correctParams:
            w = self._correctParams[param][0]
            if w.data.shape == ():
                if "Shift" in param:
                    value = [rng.uniform(-1000, 1000), rng.uniform(-1000, 1000)]
                else:
                    value = rng.uniform(-1000, 1000)  # self._allScanParams[param].get()
                shape = np.ones(len(self._scanParams), dtype=int)
                if "Shift" in param:
                    shape = np.append(shape, *np.array(value).shape)
                w = Wave(data=np.zeros(shape, dtype=float))
                if "Shift" in param:
                    w.data[..., 0, :] = [rng.uniform(-1000, 1000), rng.uniform(-1000, 1000)]  # self._allScanParams[param].get()
                else:
                    w.data[..., 0] = rng.uniform(-1000, 1000)  # self._allScanParams[param].get()
                for i in range(len(self._scanParams)):
                    w.axes[i][0] = scanParams[self._scanParams[i]]
            else:
                w = w.duplicate()
                idxs = []
                for i in range(len(self._scanParams)):
                    idx = w.axes.posToPoint(scanParams[self._scanParams[i]], axis=i)
                    if not np.isclose(w.axes[i][idx], scanParams[self._scanParams[i]]):
                        idx += 1 if w.axes[i][idx] < scanParams[self._scanParams[i]] else 0
                        w.insert(idx, axis=i, axisValue=scanParams[self._scanParams[i]])
                    idxs.append(idx)
                if "Shift" in param:
                    value = [rng.uniform(-1000, 1000), rng.uniform(-1000, 1000)]
                else:
                    value = rng.uniform(-1000, 1000)  # self._allScanParams[param].get()
                tmpdata = w.data
                for i in range(len(self._scanParams) - 1):
                    tmpdata = tmpdata[idxs[i]]
                tmpdata[idxs[-1]] = value

            self._correctParams[param].insert(0, w)

        self._cutOldCorrectParams()
        self.dataChangedFunc(correctParams)

    def undo(self, correctParams):
        for param in correctParams:
            if len(self._correctParams[param]) > 1:
                self._correctParams[param].pop(0)

        self.dataChangedFunc(correctParams)

    def clearValues(self, correctParams):
        for param in correctParams:
            self._correctParams[param].insert(0, Wave())
            self._correctParams[param] = self._correctParams[param][:5]

        self.dataChangedFunc(correctParams)

    def dataChangedFunc(self, correctParams):
        self.dataChanged.emit([waves[0] for param, waves in self._correctParams.items() if param in correctParams])

    def getWaves(self, correctParams):
        return {param: waves[0] for param, waves in self._correctParams.items() if param in correctParams}

    def saveAsFile(self, correctParams, gui=None):
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
            else:
                for param, wave in waves.items():
                    wave.note["correctParam"] = param
                    wave.note["scanParams"] = self._scanParams
                    wave.export(fileName + "_" + param)

    def loadFromFile(self, correctParams, gui=None):
        def __loadWave(fileName, w, correctParam=None, gui=None):
            if correctParam is None:
                correctParam = w.note["correctParam"]
            if "scanParams" not in w.note.keys():
                if len(self._scanParams) == 0:
                    QtWidgets.QMessageBox.critical(gui, "Error", "Failed to load: No scan params found in file.\nFile: " + fileName, QtWidgets.QMessageBox.Ok)
                    return -1
                elif w.data.ndim < len(self._scanParams):
                    QtWidgets.QMessageBox.critical(gui, "Error", "Failed to load: Data dimension in file does not match registered scan params.\nFile: " + fileName, QtWidgets.QMessageBox.Ok)
                    return -1
                elif len(self._scanParams) == 1:
                    w.note["scanParams"] = self._scanParams
                else:
                    axes = []
                    for param in self._scanParams:
                        axis, ok = QtWidgets.QInputDialog.getItem(gui, "Scan param", "Select axis for scan param: " + param, [str(i) for i in range(len(self._scanParams)) if i not in axes], editable=False)
                        if not ok:
                            return -1
                        axes.append(int(axis))
                    w.note["scanParams"] = [self._scanParams[i] for i in axes]
            if len(self._scanParams) == 0:
                self._scanParams = w.note["scanParams"]

            if sorted(self._scanParams) != sorted(w.note["scanParams"]):
                QtWidgets.QMessageBox.critical(gui, "Error", "Failed to load: Scan params in file do not match registered scan params.\nFile: " + fileName, QtWidgets.QMessageBox.Ok)
                return -1

            idxs = [w.note["scanParams"].index(param) for param in self._scanParams]
            if len(idxs) != w.data.ndim:
                idxs.extend([i for i in range(len(idxs), w.data.ndim)])
            idxs = tuple(idxs)
            w.data = w.data.transpose(idxs)
            w.axes = [w.axes[i] for i in idxs]
            if correctParam not in self._correctParams.keys():
                self._correctParams[correctParam] = []
            self._correctParams[correctParam].insert(0, w)

        fileNames = QtWidgets.QFileDialog.getOpenFileNames(gui, "Open file", "", "Numpy npz (*.npz)")[0]
        if len(fileNames) == 0:
            return
        if len(correctParams) == 1:
            w = Wave().importFrom(fileNames[0])
            if "correctParam" not in w.note.keys():
                ok = QtWidgets.QMessageBox.warning(gui, "Caution", "This file was not created by AdvancedCorrection.\nAre you sure to continue?", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
                if ok == QtWidgets.QMessageBox.Cancel:
                    return
            elif w.note["correctParam"] != correctParams[0]:
                ok = QtWidgets.QMessageBox.warning(gui, "Caution", f'This file is not for "{correctParams[0]}" but for "{w.note["correctParam"]}".\nAre you sure to continue?', QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
                if ok == QtWidgets.QMessageBox.Cancel:
                    return

            __loadWave(fileNames[0], w, correctParam=correctParams[0], gui=gui)

        elif len(correctParams) == 0:
            for fileName in fileNames:
                w = Wave().importFrom(fileName)
                if "correctParam" not in w.note.keys():
                    QtWidgets.QMessageBox.critical(gui, "Error", "Failed to load due to undefined correctParam.\nFile: " + fileName, QtWidgets.QMessageBox.Ok)
                    continue

                if w.note["correctParam"] not in self._allCorrectParams.keys():
                    QtWidgets.QMessageBox.critical(gui, "Error", "Failed to load due to the old correctParam name.\nFile: " + fileName, QtWidgets.QMessageBox.Ok)
                    continue

                __loadWave(fileName, w, gui=gui)
        else:
            QtWidgets.QMessageBox.critical(gui, "Error", "Only 1 correctParam can be loaded at a time.", QtWidgets.QMessageBox.Ok)
            return

        self._cutOldCorrectParams()

        self.dataChangedFunc(correctParams)

    def setEnable(self, bool):
        self._enable = bool

    def widget(self):
        return AdvancedCorrectionGUI(self)

    def _cutOldCorrectParams(self, size=5):
        self._correctParams = {param: waves[:size] for param, waves in self._correctParams.items()}


class AdvancedCorrectionGUI(QtWidgets.QWidget):
    def __init__(self, obj):
        super().__init__()
        self._obj = obj
        self.__initLayout()
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.adjustSize()
        self._obj.dataChanged.connect(self.__dataChanged)

    def __initLayout(self):
        self._scanParams = QtWidgets.QListWidget()
        self._scanParams.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._scanBuilder = _contextMenuBuilder(self, self._scanParams, self._obj._allScanParams.keys(), self._obj.updateScanParams)
        self._scanParams.customContextMenuRequested.connect(self._scanBuilder.build)

        self._correctParams = QtWidgets.QListWidget()
        self._correctParams.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._correctParams.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._correctParams.itemSelectionChanged.connect(lambda: self._obj.dataChangedFunc(self.__selectedCorrectParams()))
        self._correctBuilder = _contextMenuBuilder(self, self._correctParams, self._obj._allCorrectParams.keys(), self._obj.updateCorrectParams)
        self._correctParams.customContextMenuRequested.connect(self._correctBuilder.build)

        self._correctFile = QtWidgets.QLineEdit()

        v = QtWidgets.QVBoxLayout()
        v.addWidget(QtWidgets.QCheckBox("Enable Correction", checked=False, clicked=self._obj.setEnable))
        v.addWidget(QtWidgets.QLabel("Scan Params"))
        v.addWidget(self._scanParams)

        v.addWidget(QtWidgets.QWidget())
        v.addWidget(QtWidgets.QLabel("Correct Params"))
        g = QtWidgets.QGridLayout()
        g.addWidget(QtWidgets.QLabel("File"), 0, 0, 1, 1)
        g.addWidget(self._correctFile, 0, 1, 1, 3)
        g.addWidget(QtWidgets.QPushButton("Load", clicked=lambda: self._obj.loadFromFile(self.__selectedCorrectParams(), gui=self)), 1, 3, 1, 1)
        v.addWidget(self._correctParams)
        v.addLayout(g)

        v.addWidget(QtWidgets.QWidget())
        v.addWidget(QtWidgets.QLabel("Register Current Values"))
        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(QtWidgets.QPushButton("Add", clicked=lambda: self._obj.addCurrentValues(self.__selectedCorrectParams())))
        h1.addWidget(QtWidgets.QPushButton("Undo", clicked=lambda: self._obj.undo(self.__selectedCorrectParams())))
        h1.addWidget(QtWidgets.QPushButton("Clear", clicked=lambda: self._obj.clearValues(self.__selectedCorrectParams())))
        h1.addWidget(QtWidgets.QPushButton("Save", clicked=lambda: self._obj.saveAsFile(self.__selectedCorrectParams(), gui=self)))
        v.addLayout(h1)

        h = QtWidgets.QHBoxLayout()
        h.addLayout(v)

        v2 = QtWidgets.QVBoxLayout()
        self._data = widgets.lysCanvas()
        self._data.setCanvasSize("Width", "Absolute", 7)
        self._data.setCanvasSize("Height", "Absolute", 7)
        v2.addWidget(self._data)
        v2.addWidget(QtWidgets.QPushButton("Multicut", clicked=self.__showMulticut))

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
                self._correctParams.addItem(param)
        if len(self._obj._scanParams) != self._scanParams.count():
            self._scanParams.clear()
            for param in self._obj._scanParams:
                self._scanParams.addItem(param)

        self._data.Clear()
        if len(waves) == 1:
            if waves[0].data.ndim in (1, 2):
                self._data.Append(waves[0])

    def __selectedCorrectParams(self):
        return [item.text() for item in self._correctParams.selectedItems()]


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
            self._listwidget.addItem(item)
            self._updatefunc(self.__getListItems())

    def __delete(self):
        items = [item.text() for item in self._listwidget.selectedItems()]
        ok = QtWidgets.QMessageBox.warning(self._parent, "Delete", 'This may delete all registered values. \n Do you really want to DELETE the params? : ' + ", ".join(items), QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok == QtWidgets.QMessageBox.Ok:
            for item in self._listwidget.selectedItems():
                self._listwidget.takeItem(self._listwidget.row(item))
                self._updatefunc(self.__getListItems())

    def __clear(self):
        ok = QtWidgets.QMessageBox.warning(self._parent, "Clear", "This may delete all registered values. \n Do you really want to CLEAR all params?", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok == QtWidgets.QMessageBox.Ok:
            self._listwidget.clear()
            self._updatefunc([])

    def __getListItems(self):
        return [self._listwidget.item(i).text() for i in range(self._listwidget.count())]
