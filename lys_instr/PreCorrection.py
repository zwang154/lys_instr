from lys import *
from lys.Qt import QtWidgets, QtGui, QtCore
from lys.widgets import LysSubWindow, lysCanvas, ScientificSpinBox
from lys.decorators import avoidCircularReference

import numpy as np
from scipy.interpolate import RBFInterpolator
from lys import Wave, load


class CorrectMaker(QtCore.QObject):
    addCorrectParamSignal = QtCore.pyqtSignal(object)
    delCorrectParamSignal = QtCore.pyqtSignal(object)
    addScanParamSignal = QtCore.pyqtSignal(object)
    delScanParamSignal = QtCore.pyqtSignal(object)
    dataChanged = QtCore.pyqtSignal(object)  # changed correctionParamNames(list)

    def __init__(self, tem):
        super().__init__()
        self._IOs = []
        self._tem = tem
        self._allScanParams = self._tem.getInfo().getScan()
        self._allScanParams.update(self._tem.getTIA().getScans())
        self._allCorrectParams = self._tem.getStage().getScans()
        self._allCorrectParams.update(self._tem.getInfo().getScan(single=False))
        self._allCorrectParams.update(self._tem.getTIA().getScans())
        self._allCorrectParams.update(self._tem.getShiftScans())
        self._dimCorrectParams = dict()
        for correctParamName, value in self._allCorrectParams.items():
            if isinstance(value.get(), tuple):
                self._dimCorrectParams[correctParamName] = len(value.get())
            else:
                self._dimCorrectParams[correctParamName] = 1

    def addCorrectParam(self, correctParamName):
        self._IOs.append({"correctParamName": correctParamName, "scanParamNames": [], "correctWave": Wave(np.array([]).reshape(0, self._dimCorrectParams[correctParamName])), "scanWave": Wave([])})
        self.addCorrectParamSignal.emit(correctParamName)

    def delCorrectParams(self, correctParamNames):
        self._IOs = [IO for IO in self._IOs if not IO["correctParamName"] in correctParamNames]
        self.delCorrectParamSignal.emit(correctParamNames)

    def addScanParam(self, correctParamName, scanParamName, addValue=None):
        for IO in self._IOs:
            if IO["correctParamName"] == correctParamName:
                IO["scanParamNames"].append(scanParamName)
                if IO["scanWave"].size == 0:
                    IO["scanWave"] = Wave(np.array([]).reshape(0, len(IO["scanParamNames"])))
                elif addValue is None:
                    scanWaveData = IO["scanWave"].data
                    IO["scanWave"] = Wave(np.concatenate([scanWaveData, np.ones(scanWaveData.shape[0]).reshape(scanWaveData.shape[0], 1)*self._allScanParams[scanParamName].get()], axis=1), **IO["scanWave"].note)
                else:
                    scanWaveData = IO["scanWave"].data
                    IO["scanWave"] = Wave(np.concatenate([scanWaveData, np.ones(scanWaveData.shape[0]).reshape(scanWaveData.shape[0], 1)*addValue], axis=1), **IO["scanWave"].note)

                self.addScanParamSignal.emit({"correctParamName": correctParamName, "scanParamName": scanParamName})
                self.dataChanged.emit(correctParamName)

    def delScanParams(self, correctParamName, scanParamNames):
        for IO in self._IOs:
            if IO["correctParamName"] == correctParamName:
                deleteIndices = [i for i, scanParamName in enumerate(IO["scanParamNames"]) if scanParamName in scanParamNames]
                if len(deleteIndices) > 0:
                    IO["scanParamNames"] = [scanParamName for scanParamName in IO["scanParamNames"] if not scanParamName in scanParamNames]
                    scanWave = IO["scanWave"]
                    newWaveData = np.delete(scanWave.data, deleteIndices, axis=1)
                    IO["scanWave"] = Wave(newWaveData, **IO["scanWave"].note)

                    self.delScanParamSignal.emit({"correctParamName": correctParamName, "scanParamNames": scanParamNames})
                    self.dataChanged.emit(correctParamName)

    def addValues(self, correctParamNames):
        if len(self._IOs) == 0:
            return

        if len(correctParamNames) == 0:
            correctParamNames = [IO["correctParamName"] for IO in self._IOs]

        usedScanParamNames = set()
        for IO in self._IOs:
            usedScanParamNames |= set(IO["scanParamNames"])

        usedScanParams = dict()
        for scanParamName in usedScanParamNames:
            usedScanParams[scanParamName] = self._allScanParams[scanParamName].get()

        usedCorrectParams = {IO["correctParamName"]: self._allCorrectParams[IO["correctParamName"]].get() for IO in self._IOs}

        for IO in self._IOs:
            if IO["correctParamName"] in correctParamNames:
                scanData = IO["scanWave"].data
                scanNewColumn = np.array([[usedScanParams[scanParamName] for scanParamName in IO["scanParamNames"]]]).reshape(1, len(IO["scanParamNames"]))
                scanNewData = np.concatenate((scanData, scanNewColumn), axis=0)
                IO["scanWave"] = Wave(scanNewData)

                correctData = IO["correctWave"].data
                correctNewColumn = np.array(usedCorrectParams[IO["correctParamName"]]).reshape(1, self._dimCorrectParams[IO["correctParamName"]])
                correctNewData = np.concatenate((correctData, correctNewColumn), axis=0)
                IO["correctWave"] = Wave(correctNewData)

        self.dataChanged.emit(correctParamNames)

    def undoValues(self, correctParamNames):
        if len(correctParamNames) == 0:
            correctParamNames = [IO["correctParamName"] for IO in self._IOs]

        for IO in self._IOs:
            if IO["correctParamName"] in correctParamNames:
                IO["correctWave"] = IO["correctWave"][:-1, :]
                IO["scanWave"] = IO["scanWave"][:-1, :]

        self.dataChanged.emit(correctParamNames)

    def clearValues(self, correctParamNames):
        for IO in self._IOs:
            if IO["correctParamName"] in correctParamNames:
                IO["correctWave"] = Wave(np.array([]).reshape(0, self._dimCorrectParams[IO["correctParamName"]]))
                IO["scanWave"] = Wave(np.array([]).reshape(0, len(IO["scanParamNames"])))
        self.dataChanged.emit(correctParamNames)

    def getIOs(self, correctParamNames):
        if isinstance(correctParamNames, str):
            for IO in self._IOs:
                if IO["correctParamName"] == correctParamNames:
                    return IO
        else:
            return [IO for IO in self._IOs if IO["correctParamName"] in correctParamNames]

    def saveAsFile(self, correctParamNames, gui=None):
        savedIOs = self.getIOs(correctParamNames) if len(correctParamNames) != 0 else self._IOs

        if len(savedIOs) == 0:
            return

        fileName = QtWidgets.QFileDialog.getSaveFileName(gui, "Save file", "", "Numpy npz (*.npz)")[0]
        if fileName:
            fileName = fileName.strip(".npz")
            for IO in savedIOs:
                inputWave = IO["scanWave"]
                outputWave = IO["correctWave"]
                inputWave.note["scanParamNames"] = IO["scanParamNames"]
                outputWave.note["scanParamNames"] = IO["scanParamNames"]
                inputWave.note["correctParamName"] = IO["correctParamName"]
                outputWave.note["correctParamName"] = IO["correctParamName"]
                inputWave.export(fileName + "_input_for_" + IO["correctParamName"])
                outputWave.export(fileName + "_output_for_" + IO["correctParamName"])


class PreCorrector(QtCore.QObject):
    addCorrectParamSignal = QtCore.pyqtSignal(object)
    delCorrectParamSignal = QtCore.pyqtSignal(object)
    addFuncSignal = QtCore.pyqtSignal(object)

    def __init__(self, tem):
        super().__init__()
        self._tem = tem
        self._enable = False
        self._allScanParams = self._tem.getInfo().getScan()
        self._allScanParams.update(self._tem.getTIA().getScans())
        self._allCorrectParams = self._tem.getStage().getScans()
        self._allCorrectParams.update(self._tem.getInfo().getScan(single=False))
        self._allCorrectParams.update(self._tem.getTIA().getScans())
        self._allCorrectParams.update(self._tem.getShiftScans())

        self._tem.valueSet.connect(self.doCorrection)

        self._correctParams = dict()

    def addCorrectParam(self, correctParamName):
        if correctParamName not in self._correctParams.keys():
            correctParam = _CorrectParameter(correctParamName, self._allCorrectParams[correctParamName])
            self._correctParams[correctParamName] = correctParam
            self.addCorrectParamSignal.emit({"correctParamName": correctParamName, "correctParam": correctParam})

    def delCorrectParams(self, paramNames):
        for paramName in list(self._correctParams.keys()):
            if paramName in paramNames:
                del self._correctParams[paramName]
        self.delCorrectParamSignal.emit(paramNames)

    def setEnabledCorrectParam(self, paramName, bool):
        self._correctParams[paramName].enable = bool

    def _getEnabledScanParams(self):
        return set.union(*[correctParam.getEnabledArgNames() for correctParam in self._correctParams.values()])

    def _getEnabledCorrectParams(self):
        return [key for key, value in self._correctParams.items() if value.enable]

    @avoidCircularReference
    def doCorrection(self, values={}):
        print("doCorre")
        if not self._enable:
            print("disable")
            return

        if not isinstance(values, (int, float)):
            if bool(len(values)) == 0:
                print("tuple?")
                if len(set(self._getEnabledScanParams()) & set(values.keys())) == 0:
                    return

        if len(self._getEnabledCorrectParams()) == 0:
            print("non CorrectParam")
            return

        usedScanValues = {paramName: self._allScanParams[paramName].get() for paramName in self._getEnabledScanParams()}

        usedCorrectParams = self._getEnabledCorrectParams()

        for used in usedCorrectParams:
            value = self._correctParams[used].getCorrectValue(usedScanValues)
            if value.size == 1:
                self._correctParams[used].set(value.item())
            else:
                self._correctParams[used].set(tuple(list(value.flat)))


class _CorrectParameter(QtCore.QObject):
    addFuncSignal = QtCore.pyqtSignal(object)  # with {"funcName":funcName, "func":func}
    delFuncsSignal = QtCore.pyqtSignal(object)  # with funcNames
    enableChanged = QtCore.pyqtSignal(object)
    formulaChanged = QtCore.pyqtSignal(object)  # formula
    correctParamNameError = QtCore.pyqtSignal(object)  # errorCorrectParamName

    def __init__(self, correctParamName, scaner):
        super().__init__()
        self._scaner = scaner
        self._enable = True

        self._corrector = _CorrectSetup(correctParamName, self)
        self._corrector.addFuncSignal.connect(self.addFuncSignal.emit)
        self._corrector.delFuncsSignal.connect(self.delFuncsSignal.emit)
        self._corrector.formulaChanged.connect(self.formulaChanged.emit)
        self._corrector.correctParamNameError.connect(self.correctParamNameError.emit)

    def get(self):
        return self._scaner.get()

    def set(self, value):
        return self._scaner.set(value)

    @property
    def enable(self):
        return self._enable

    @enable.setter
    def enable(self, bool):
        self._enable = bool
        self.enableChanged.emit(bool)

    def __getattr__(self, attr):
        return getattr(self._corrector, attr)


class _CorrectSetup(QtCore.QObject):
    addFuncSignal = QtCore.pyqtSignal(object)  # {"funcName":funcName, "func":func}
    delFuncsSignal = QtCore.pyqtSignal(object)  # funcsNames
    formulaChanged = QtCore.pyqtSignal(object)  # formula
    correctParamNameError = QtCore.pyqtSignal(object)  # correctParamName of load File

    def __init__(self, correctParamName, correctParam):
        super().__init__()
        self._correctParamName = correctParamName
        self._correctParam = correctParam
        self._dimCorrect = 1 if isinstance(self._correctParam.get(), (int, float)) else len(self._correctParam.get())
        self._funcs = dict()
        self._funcsID = 0
        self._formula = None

    def getCorrectValue(self, scanParams):
        if self._formula is None:
            firstFunc = next(iter(self._funcs.values()))
            correctValue = firstFunc(*[scanParams[argName] for argName in firstFunc.getEnabledArgNames()])
        else:
            localVariables = {funcName: func(*[scanParams[argName] for argName in func.getEnabledArgNames()]) for funcName, func in self._funcs.items()}
            correctValue = eval(self._formula, {"__builtins__": None}, localVariables)
        return correctValue

    def addFuncFromGrid(self, gridWave):
        data = gridWave.data
        axes = gridWave.axes
        note = gridWave.note

        outputAxis = -1  # if necessary, make it optional
        if self._dimCorrect == 1 and data.shape[outputAxis] != 1:
            data = data[:, :, np.newaxis]
            axes.append(np.array([0]))

        numOfPoints = np.prod((data.shape[:outputAxis]))  # if made optional, needs update
        dimOutput = data.shape[outputAxis]
        outputs = data.reshape(numOfPoints, dimOutput)

        grids = np.array(np.meshgrid(*axes[:outputAxis], indexing="ij"))  # if made optional, needs update
        inputs = grids.reshape(grids.shape[0], np.prod(grids.shape[1:])).T  # inputs.shape = (numOfPoints, dimInput)

        inputWave = Wave(inputs, scanParamNames=note["scanParamNames"])
        outputWave = Wave(outputs, correctParamName=note["correctParamName"])

        self.addFuncFromIO(inputWave, outputWave)

    def addFuncFromIO(self, inputWave, outputWave):
        if outputWave.note["correctParamName"] != self._correctParamName:
            self.correctParamNameError.emit(outputWave.note["correctParamName"])
            return

        argNames = inputWave.note["scanParamNames"]
        funcName = "func"+str(self._funcsID)
        func = _NamedInterpolatedFunction(inputWave.data, outputWave.data, argNames)
        self._funcs[funcName] = func
        self._funcsID += 1
        self.addFuncSignal.emit({"funcName": funcName, "func": func})

    def delFuncs(self, funcsNames):
        for key in list(self._funcs.keys()):
            if key in funcsNames:
                del self._funcs[key]
        self.delFuncsSignal.emit(funcsNames)

    def setFormula(self, formula):
        self._formula = formula

    def getEnabledArgNames(self):
        return set.union(*[func.getEnabledArgNames() for func in self._funcs.values()])


class _InterpolatedFunction(QtCore.QObject):
    fixedValueChanged = QtCore.pyqtSignal(object)

    def __init__(self, inputs, outputs):
        super().__init__()
        inputAxis = outputAxis = -1  # if necessary, make it optional

        self._dimInput = inputs.shape[inputAxis]
        self._dimOutput = outputs.shape[outputAxis]

        self._interpolator = RBFInterpolator(inputs, outputs, kernel="linear")
        self._fixedValues = [None]*self._dimInput

    def __call__(self, *args):
        args = list(args)
        for i, value in enumerate(self._fixedValues):
            if value is not None:
                args.insert(i, value)

        return self._interpolator([args])

    def getDimInput(self):
        return self._dimInput

    def getDimOutput(self):
        return self._dimOutput

    def setFixedValue(self, index, value):
        self._fixedValues[index] = value
        self.fixedValueChanged.emit((index, value))

    def getFixedValue(self):
        return self._fixedValues


class _NamedInterpolatedFunction(_InterpolatedFunction):
    def __init__(self, inputs, outputs, argNames):
        super().__init__(inputs, outputs)
        self._argNames = argNames

    def getArgNames(self):
        return self._argNames

    def getEnabledArgNames(self):
        return set(argName for argName, fixedValue in zip(self._argNames, self._fixedValues) if fixedValue is None)


class CorrectMakerGUI(QtWidgets.QWidget):
    def __init__(self, obj: CorrectMaker):
        super().__init__()
        self._obj = obj
        self.__initUI()
        self._signalConnect()

    def _signalConnect(self):
        self._obj.addCorrectParamSignal.connect(self.__addIOWidget)
        self._obj.delCorrectParamSignal.connect(self.__delIOsWidget)
        self._obj.addScanParamSignal.connect(lambda dict: self.__addScanWidget(**dict))
        self._obj.delScanParamSignal.connect(lambda dict: self.__delScansWidget(**dict))
        self._correctBuilder.addRequest.connect(self._addCorrectParam)
        self._correctBuilder.delRequest.connect(self._delCorrectParams)
        self._correctBuilder.clearRequest.connect(self._clearCorrectParams)
        self._addButton.clicked.connect(self._addValues)
        self._undoButton.clicked.connect(self._undoValues)
        self._clearButton.clicked.connect(self._clearValues)
        self._exportButton.clicked.connect(self._exportValues)

    def __initUI(self):
        self._correctParamsList = QtWidgets.QListWidget()
        self._correctParamsList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._correctParamsList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._correctBuilder = _contextMenuBuilder()
        self._correctParamsList.customContextMenuRequested.connect(self._correctBuilder.build)

        footerLayout = QtWidgets.QHBoxLayout()
        self._addButton = QtWidgets.QPushButton("add")
        self._undoButton = QtWidgets.QPushButton("undo")
        self._clearButton = QtWidgets.QPushButton("clear")
        self._exportButton = QtWidgets.QPushButton("export")
        footerLayout.addWidget(self._addButton)
        footerLayout.addWidget(self._undoButton)
        footerLayout.addWidget(self._clearButton)
        footerLayout.addWidget(self._exportButton)

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.addWidget(QtWidgets.QLabel("Correct Parameters"))
        self._layout.addWidget(self._correctParamsList)
        self._layout.addLayout(footerLayout)

        self.setLayout(self._layout)
        self.adjustSize()

    def _addCorrectParam(self):
        selectedCorrectParamNames = [IO["correctParamName"] for IO in self._obj._IOs]
        additems = [key for key in self._obj._allCorrectParams.keys() if key not in selectedCorrectParamNames]

        if len(additems) == 0:
            return

        item, ok = QtWidgets.QInputDialog.getItem(self._correctParamsList, "Add Correct Params", "Param", additems, editable=False)
        if ok:
            self._obj.addCorrectParam(item)

    def _delCorrectParams(self):
        correctParamNames = [self._correctParamsList.itemWidget(item).getCorrectParamName() for item in self._correctParamsList.selectedItems()]
        ok = QtWidgets.QMessageBox.warning(self._correctParamsList, "Delete", 'This will delete all registered correction values. \n Do you really want to DELETE the parameter(s)? : ' + ", ".join(correctParamNames), QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            self._obj.delCorrectParams(correctParamNames)

    def _clearCorrectParams(self):
        allItem = [self._correctParamsList.item(i) for i in range(self._correctParamsList.count())]
        allCorrectPramNames = [self._correctParamsList.itemWidget(item).getCorrectParamName() for item in allItem]
        ok = QtWidgets.QMessageBox.warning(self._correctParamsList, "Clear", "This will delete all registered correction values. \n Do you really want to CLEAR the all parameter(s)?", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            self._obj.delCorrectParams(allCorrectPramNames)

    def __addIOWidget(self, correctParamName):
        item = QtWidgets.QListWidgetItem()
        widget = _IOWidget(self._obj, correctParamName)
        widget.sizeChanged.connect(lambda sizeHint: item.setSizeHint(sizeHint))
        item.setSizeHint(widget.sizeHint())
        self._correctParamsList.addItem(item)
        self._correctParamsList.setItemWidget(item, widget)

    def __delIOsWidget(self, correctParamNames):
        for i in reversed(range(self._correctParamsList.count())):
            if self._correctParamsList.itemWidget(self._correctParamsList.item(i)).getCorrectParamName() in correctParamNames:
                self._correctParamsList.takeItem(i)

    def __addScanWidget(self, correctParamName, scanParamName):
        for i in reversed(range(self._correctParamsList.count())):
            if correctParamName == self._correctParamsList.itemWidget(self._correctParamsList.item(i)).getCorrectParamName():
                IOWidget = self._correctParamsList.itemWidget(self._correctParamsList.item(i))
                IOWidget.addScanWidget(scanParamName)

    def __delScansWidget(self, correctParamName, scanParamNames):
        for i in reversed(range(self._correctParamsList.count())):
            if correctParamName == self._correctParamsList.itemWidget(self._correctParamsList.item(i)).getCorrectParamName():
                IOWidget = self._correctParamsList.itemWidget(self._correctParamsList.item(i))
                IOWidget.delScansWidget(scanParamNames)

    def _addValues(self):
        selectedCorrectParamNames = [self._correctParamsList.itemWidget(item).getCorrectParamName() for item in self._correctParamsList.selectedItems()]
        self._obj.addValues(selectedCorrectParamNames)

    def _undoValues(self):
        selectedCorrectParamNames = [self._correctParamsList.itemWidget(item).getCorrectParamName() for item in self._correctParamsList.selectedItems()]
        self._obj.undoValues(selectedCorrectParamNames)

    def _clearValues(self):
        selectedCorrectParamNames = [self._correctParamsList.itemWidget(item).getCorrectParamName() for item in self._correctParamsList.selectedItems()]
        ok = QtWidgets.QMessageBox.warning(self._correctParamsList, "Delete", 'This will delete all registered correction values. \n Do you really want to DELETE the parameter(s)? : ' + ", ".join(selectedCorrectParamNames), QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            self._obj.clearValues(selectedCorrectParamNames)

    def _exportValues(self):
        selectedCorrectParamNames = [self._correctParamsList.itemWidget(item).getCorrectParamName() for item in self._correctParamsList.selectedItems()]
        self._obj.saveAsFile(selectedCorrectParamNames, self._correctParamsList)


class _IOWidget(QtWidgets.QWidget):
    sizeChanged = QtCore.pyqtSignal(object)

    def __init__(self, obj: CorrectMaker, correctParamName):
        super().__init__()
        self._obj = obj
        self._correctParamName = correctParamName
        self._IO = self._obj.getIOs(correctParamName)
        self.__initUI()
        self._signalConnect()

    def getCorrectParamName(self):
        return self._correctParamName

    def _signalConnect(self):
        self._scanParamsListBilder.addRequest.connect(self._addScan)
        self._scanParamsListBilder.delRequest.connect(self._delScans)
        self._scanParamsListBilder.clearRequest.connect(self._clearScans)
        self._obj.dataChanged.connect(self._updataData)

    def __initUI(self):
        layout = QtWidgets.QVBoxLayout(self)

        # header
        header_widget, self._shapeLabel = self.__makeHeader(self._correctParamName)
        layout.addWidget(header_widget)

        # detail_layout
        self.detail_widget = QtWidgets.QWidget()
        self.detail_Layout = QtWidgets.QVBoxLayout(self.detail_widget)
        self.scanParamsListWidget, self._scanParamsList, self._scanParamsListBilder = self.__makeScanParamsListWidget()

        self.detail_Layout.addWidget(self.scanParamsListWidget)

        layout.addWidget(self.detail_widget)

    def __makeHeader(self, correctParamName):
        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.toggle_button = QtWidgets.QToolButton()
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.clicked.connect(self.__toggle_detail)
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow if not self.toggle_button.isChecked() else QtCore.Qt.DownArrow)

        inputShape = self._IO["scanWave"].shape
        outputShape = self._IO["scanWave"].shape
        shapeLabel = QtWidgets.QLabel("input wave shape" + str(inputShape) + "\n output wave shape" + str(outputShape))

        header_layout.addWidget(self.toggle_button)
        header_layout.addWidget(QtWidgets.QLabel(correctParamName))
        header_layout.addWidget(shapeLabel)
        header_layout.addStretch()

        return header_widget, shapeLabel

    def __toggle_detail(self):
        self.detail_widget.setVisible(self.toggle_button.isChecked())
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow if not self.toggle_button.isChecked() else QtCore.Qt.DownArrow)
        self.sizeChanged.emit(self.sizeHint())

    def __makeScanParamsListWidget(self):
        scanParamsListWidget = QtWidgets.QWidget()
        scanParamsListBox = QtWidgets.QVBoxLayout(scanParamsListWidget)

        scanParamsList = QtWidgets.QListWidget()
        scanParamsList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        scanParamsList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        scanParamsListBuilder = _contextMenuBuilder()
        scanParamsList.customContextMenuRequested.connect(scanParamsListBuilder.build)
        scanParamsList.setFixedHeight(70)

        scanParamsListBox.addWidget(QtWidgets.QLabel("scan parameter list"))
        scanParamsListBox.addWidget(scanParamsList)
        return scanParamsListWidget, scanParamsList, scanParamsListBuilder

    def _addScan(self):
        selectedScanParamNames = self._IO["scanParamNames"]
        additems = [key for key in self._obj._allScanParams.keys() if key not in selectedScanParamNames]

        if len(additems) == 0:
            return

        item, ok = QtWidgets.QInputDialog.getItem(self._scanParamsList, "Add scan Parameters", "Param", additems, editable=False)
        if ok:
            self._obj.addScanParam(self._correctParamName, item)

    def _delScans(self):
        selectedScanParamNames = [self._scanParamsList.itemWidget(item).text() for item in self._scanParamsList.selectedItems()]
        ok = QtWidgets.QMessageBox.warning(self._scanParamsList, "Delete", 'This will delete registered correction values. \n Do you really want to DELETE the parameter(s)? : ' + ", ".join(selectedScanParamNames), QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            self._obj.delScanParams(self._correctParamName, selectedScanParamNames)

    def _clearScans(self):
        allScanParamItems = [self._scanParamsList.item(i) for i in range(self._scanParamsList.count())]
        allScanParamNames = [self._scanParamsList.itemWidget(item).text() for item in allScanParamItems]
        ok = QtWidgets.QMessageBox.warning(self._scanParamsList, "Clear", "This will delete all registered correction values. \n Do you really want to CLEAR the all parameter(s)?", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            self._obj.delScanParams(self._correctParamName, allScanParamNames)

    def addScanWidget(self, scanParamName):
        item = QtWidgets.QListWidgetItem()
        widget = QtWidgets.QLabel(str(scanParamName))
        self._scanParamsList.addItem(item)
        self._scanParamsList.setItemWidget(item, widget)
        item.setSizeHint(widget.sizeHint())

    def delScansWidget(self, scanParamNames):
        for i in reversed(range(self._scanParamsList.count())):
            if self._scanParamsList.itemWidget(self._scanParamsList.item(i)).text() in scanParamNames:
                self._scanParamsList.takeItem(i)

    def _updataData(self):
        inputShape = self._IO["scanWave"].shape
        outputShape = self._IO["scanWave"].shape
        self._shapeLabel.setText("input wave shape" + str(inputShape) + "\noutput wave shape" + str(outputShape))


class PreCorrectorGUI(QtWidgets.QWidget):
    def __init__(self, obj):
        super().__init__()
        self._obj = obj
        self.__initUI()
        self._signalConnect()

    def _signalConnect(self):
        self._obj.addCorrectParamSignal.connect(lambda kargs: self.__addCorrectParamsWidget(**kargs))
        self._obj.delCorrectParamSignal.connect(self.__delCorrectParamsWidget)
        self._correctBuilder.addRequest.connect(self._addCorrectParam)
        self._correctBuilder.delRequest.connect(self._delCorrectParams)
        self._correctBuilder.clearRequest.connect(self._clearCorrectParams)

    def __initUI(self):
        self._correctParamsList = QtWidgets.QListWidget()
        self._correctParamsList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._correctParamsList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._correctBuilder = _contextMenuBuilder()
        self._correctParamsList.customContextMenuRequested.connect(self._correctBuilder.build)

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.addWidget(QtWidgets.QLabel("Correct Parameters"))
        self._layout.addWidget(self._correctParamsList)

        self.setLayout(self._layout)
        self.adjustSize()

    def _addCorrectParam(self):
        additems = [key for key in self._obj._allCorrectParams.keys() if key not in self._obj._correctParams.keys()]
        if len(additems) == 0:
            return

        item, ok = QtWidgets.QInputDialog.getItem(self._correctParamsList, "Add Correct Params", "Param", additems, editable=False)
        if ok:
            self._obj.addCorrectParam(item)

    def _delCorrectParams(self):
        correctParamNames = [self._correctParamsList.itemWidget(item).getCorrectParamName() for item in self._correctParamsList.selectedItems()]
        ok = QtWidgets.QMessageBox.warning(self._correctParamsList, "Delete", 'This will delete all registered correction values. \n Do you really want to DELETE the parameter(s)? : ' + ", ".join(correctParamNames), QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            self._obj.delCorrectParams(correctParamNames)

    def _clearCorrectParams(self):
        allItem = [self._correctParamsList.item(i) for i in range(self._correctParamsList.count())]
        allCorrectPramNames = [self._correctParamsList.itemWidget(item).getCorrectParamName() for item in allItem]
        ok = QtWidgets.QMessageBox.warning(self._correctParamsList, "Clear", "This will delete all registered correction values. \n Do you really want to CLEAR the all parameter(s)?", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            self._obj.delCorrectParams(allCorrectPramNames)

    def __addCorrectParamsWidget(self, correctParamName, correctParam):
        item = QtWidgets.QListWidgetItem()
        widget = CorrectParamWidget(correctParamName, correctParam)
        widget.sizeChanged.connect(lambda sizeHint: item.setSizeHint(sizeHint))
        item.setSizeHint(widget.sizeHint())
        self._correctParamsList.addItem(item)
        self._correctParamsList.setItemWidget(item, widget)

    def __delCorrectParamsWidget(self, correctParamNames):
        for i in reversed(range(self._correctParamsList.count())):
            if self._correctParamsList.itemWidget(self._correctParamsList.item(i)).getCorrectParamName() in correctParamNames:
                self._correctParamsList.takeItem(i)


class _contextMenuBuilder(QtCore.QObject):
    addRequest = QtCore.pyqtSignal()
    delRequest = QtCore.pyqtSignal()
    clearRequest = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self._SetDefaultMenu()

    def _SetDefaultMenu(self):
        self._add = QtWidgets.QAction('Add', triggered=self.addRequest.emit)
        self._delete = QtWidgets.QAction('Delete', triggered=self.delRequest.emit)
        self._clear = QtWidgets.QAction('Clear', triggered=self.clearRequest.emit)

        menu = QtWidgets.QMenu()
        menu.addAction(self._add)
        menu.addAction(self._delete)
        menu.addAction(self._clear)

        self.__actions = menu

    def build(self):
        self.__actions.exec_(QtGui.QCursor.pos())


class CorrectParamWidget(QtWidgets.QWidget):
    sizeChanged = QtCore.pyqtSignal(object)

    def __init__(self, correctParamName, correctParam: _CorrectParameter):
        super().__init__()
        self._correctParamName = correctParamName
        self._correctParam = correctParam
        self.__initUI()
        self._funcIdCountor = 0
        self._signalConnect()

    def getCorrectParamName(self):
        return self._correctParamName

    def _signalConnect(self):
        self._funcsListBilder.addRequest.connect(self._addFunc)
        self._funcsListBilder.delRequest.connect(self._delFuncs)
        self._funcsListBilder.clearRequest.connect(self._clearFuncs)
        self._correctParam.addFuncSignal.connect(lambda kargs: self.__addFuncWidget(**kargs))
        self._correctParam.addFuncSignal.connect(lambda _: self.__setFormulaWidgetVisible())
        self._correctParam.delFuncsSignal.connect(lambda funcNames: self.__delFuncsWidget(funcNames))
        self._correctParam.delFuncsSignal.connect(lambda _: self.__setFormulaWidgetVisible())
        self._correctParam.correctParamNameError.connect(self.__raiseErrorMessage)
        self.checkbox.toggled.connect(self._setEnabled)
        self.formulaEdit.textChanged.connect(self._setFormula)

    def __initUI(self):
        layout = QtWidgets.QVBoxLayout(self)

        # header
        header_widget, self.checkbox = self.__makeHeader(self._correctParamName)
        layout.addWidget(header_widget)

        # detail_layout
        self.detail_widget = QtWidgets.QWidget()
        self.detail_Layout = QtWidgets.QVBoxLayout(self.detail_widget)
        self.funcsListWidget, self._funcsList, self._funcsListBilder = self.__makeFuncListWidget()
        self.formulaWidget, self.formulaEdit = self.__makeFormulaWidget()
        self.formulaWidget.setVisible(False)

        self.detail_Layout.addWidget(self.funcsListWidget)
        self.detail_Layout.addWidget(self.formulaWidget)

        layout.addWidget(self.detail_widget)

    def __makeHeader(self, correctParamName):
        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.toggle_button = QtWidgets.QToolButton()
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.clicked.connect(self.__toggle_detail)
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow if not self.toggle_button.isChecked() else QtCore.Qt.DownArrow)
        header_layout.addWidget(self.toggle_button)

        checkbox = QtWidgets.QCheckBox()
        checkbox.setChecked(self._correctParam.enable)
        header_layout.addWidget(checkbox)

        label = QtWidgets.QLabel(correctParamName)
        header_layout.addWidget(label)

        header_layout.addStretch()

        return header_widget, checkbox

    def __toggle_detail(self):
        self.detail_widget.setVisible(self.toggle_button.isChecked())
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow if not self.toggle_button.isChecked() else QtCore.Qt.DownArrow)
        self.sizeChanged.emit(self.sizeHint())

    def __makeFuncListWidget(self):
        funcsListWidget = QtWidgets.QWidget()
        funcsListBox = QtWidgets.QVBoxLayout(funcsListWidget)

        funcsList = QtWidgets.QListWidget()
        funcsList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        funcsList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        funcsListBuilder = _contextMenuBuilder()
        funcsList.customContextMenuRequested.connect(funcsListBuilder.build)

        funcsListBox.addWidget(QtWidgets.QLabel("function list"))
        funcsListBox.addWidget(funcsList)
        return funcsListWidget, funcsList, funcsListBuilder

    def __makeFormulaWidget(self):
        formulaWidget = QtWidgets.QWidget()
        formulaBox = QtWidgets.QVBoxLayout(formulaWidget)

        formulaBox.addWidget(QtWidgets.QLabel("define correct value as formula by function Names (ex. func0 + func1*func2 - func3/func4 + 10.48) <br> If fomular None, correct value is func<i>N<\i> value (the N is the smallest number in function list)"))
        formulaEdit = QtWidgets.QLineEdit()
        formulaBox.addWidget(formulaEdit)
        return formulaWidget, formulaEdit

    def __setFormulaWidgetVisible(self):
        self.formulaWidget.setVisible(self._funcsList.count() >= 2)
        self.sizeChanged.emit(self.sizeHint())

    def _addFunc(self):
        dialog = _addFuncDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            if dialog.getMode() == "gridData":
                gridDataPath = dialog.getGridDataPath()
                self._correctParam.addFuncFromGrid(load(gridDataPath))
            else:
                inputPath = dialog.getInputPath()
                outputPath = dialog.getOutputPath()
                self._correctParam.addFuncFromIO(load(inputPath), load(outputPath))

    def _delFuncs(self):
        selectedFuncNames = [self._funcsList.itemWidget(item).getFuncName() for item in self._funcsList.selectedItems()]
        ok = QtWidgets.QMessageBox.warning(self._funcsList, "Delete", 'This will delete all registered correction values. \n Do you really want to DELETE the parameter(s)? : ' + ", ".join(selectedFuncNames), QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            self._correctParam.delFuncs(selectedFuncNames)

    def _clearFuncs(self):
        allFuncItems = [self._funcsList.item(i) for i in range(self._funcsList.count())]
        allFuncNames = [self._funcsList.itemWidget(item).getFuncName() for item in allFuncItems]
        ok = QtWidgets.QMessageBox.warning(self._funcsList, "Clear", "This will delete all registered correction values. \n Do you really want to CLEAR the all parameter(s)?", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
        if ok:
            self._obj.delCorrectParams(allFuncNames)

    def __addFuncWidget(self, funcName, func):
        item = QtWidgets.QListWidgetItem()
        widget = FuncWidget(funcName, func)
        self._funcsList.addItem(item)
        self._funcsList.setItemWidget(item, widget)
        item.setSizeHint(widget.sizeHint())
        self.sizeChanged.emit(self.sizeHint())

    def __delFuncsWidget(self, funcNames):
        for i in reversed(range(self._funcsList.count())):
            if self._funcsList.itemWidget(self._funcsList.item(i)).getFuncName() in funcNames:
                self._funcsList.takeItem(i)
        self.sizeChanged.emit(self.sizeHint())

    def _setEnabled(self, checked):
        self._correctParam.enable = checked

    def _enableChanged(self, checked):
        if checked == self.checkbox.isChecked():
            return

        self.checkbox.setChecked(checked)

    def _setFormula(self, formula):
        self._correctParam.setFormula(formula)

    def _formulaChanged(self, formula):
        if formula == self.formula.text():
            return
        self.formulaEdit.setText(formula)

    def __raiseErrorMessage(self, errorCorrectParamName):
        ok = QtWidgets.QMessageBox.warning(self._funcsList, "Error", "The loaded wave does not match the correctParamsName. loaded Wave:" + str(errorCorrectParamName), QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)


class _addFuncDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("add function")

        layout = QtWidgets.QVBoxLayout()

        modeBox, self.radioButtonGrid, self.radioButtonIO = self.__makeModeBox()
        self.gridDataWidget, self.gridDataLineEdit = self.__makeGridDataWidget()
        self.IODataWidget, self.inputLineEdit, self.outputLineEdit = self.__makeIOWidget()

        # buttons
        button_layout = QtWidgets.QHBoxLayout()
        ok_button = QtWidgets.QPushButton("add")
        cancel_button = QtWidgets.QPushButton("cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(modeBox)
        layout.addWidget(self.gridDataWidget)
        layout.addWidget(self.IODataWidget)
        layout.addLayout(button_layout)

        self.radioButtonIO.setChecked(True)

        self.setLayout(layout)

    def getMode(self):
        if self.radioButtonGrid.isChecked():
            return "gridData"
        else:
            return "IOData"

    def getInputPath(self):
        return self.inputLineEdit.text()

    def getOutputPath(self):
        return self.outputLineEdit.text()

    def getGridDataPath(self):
        return self.gridDataLineEdit.text()

    def __makeModeBox(self):
        modeBox = QtWidgets.QHBoxLayout()
        radio1 = QtWidgets.QRadioButton("grid data")
        radio2 = QtWidgets.QRadioButton("I/O data")
        group = QtWidgets.QButtonGroup()
        group.addButton(radio1)
        group.addButton(radio2)
        radio1.toggled.connect(self.__toggleMode)
        radio2.toggled.connect(self.__toggleMode)
        modeBox.addWidget(radio1)
        modeBox.addWidget(radio2)
        return modeBox, radio1, radio2

    def __toggleMode(self):
        if self.radioButtonGrid.isChecked():
            self.gridDataWidget.show()
            self.IODataWidget.hide()
        else:
            self.gridDataWidget.hide()
            self.IODataWidget.show()

    def __makeGridDataWidget(self):
        gridDataWidget = QtWidgets.QWidget()
        gridDataBox = QtWidgets.QVBoxLayout(gridDataWidget)

        gridDataLayout = QtWidgets.QHBoxLayout()
        gridData = QtWidgets.QLineEdit("selct .npz file")
        gridDataLayout.addWidget(QtWidgets.QLabel("grid wave data as shape(N1,N2,...,Nn,dimCorrectParam)"))
        gridDataLayout.addWidget(gridData)
        gridDataLayout.addWidget(QtWidgets.QPushButton("Select", clicked=lambda: self.__open(gridData)))

        gridDataBox.addLayout(gridDataLayout)
        return gridDataWidget, gridData

    def __makeIOWidget(self):
        IOWidget = QtWidgets.QWidget()
        IOBox = QtWidgets.QVBoxLayout(IOWidget)

        inputLayout = QtWidgets.QHBoxLayout()
        input = QtWidgets.QLineEdit("select .npz file")
        inputLayout.addWidget(QtWidgets.QLabel("input data as shape (Npoint, Num of Scan Parameters)"))
        inputLayout.addWidget(input)
        inputLayout.addWidget(QtWidgets.QPushButton("Select", clicked=lambda: self.__open(input)))

        outputLayout = QtWidgets.QHBoxLayout()
        output = QtWidgets.QLineEdit("select .npz file")
        outputLayout.addWidget(QtWidgets.QLabel("output data as shape (Npoint, dim of correct Parameter)"))
        outputLayout.addWidget(output)
        outputLayout.addWidget(QtWidgets.QPushButton("Select", clicked=lambda: self.__open(output)))

        IOBox.addLayout(inputLayout)
        IOBox.addLayout(outputLayout)
        return IOWidget, input, output

    def __open(self, lineEdit):
        file, _ = QtWidgets.QFileDialog.getOpenFileName(None, 'Open file', filter="npz(*.npz)")
        if 0 != len(file):
            lineEdit.setText(file)


class FuncWidget(QtWidgets.QWidget):
    def __init__(self, funcName, func):
        super().__init__()
        self._funcName = funcName
        self._func = func
        self._items = func.getArgNames()
        self.__initUI()
        self._func.fixedValueChanged.connect(lambda signal: self._fixedValueChanged(*signal))

    def __initUI(self):
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addWidget(QtWidgets.QLabel(self._funcName))

        self.argsInfo = []
        for i in range(self._func.getDimInput()):
            hLayout = QtWidgets.QHBoxLayout()

            argNameLabel = QtWidgets.QLabel(f"scanParam{i + 1}")
            argNameWidget = QtWidgets.QLabel(self._func.getArgNames()[i])

            enableLabel = QtWidgets.QLabel("enable")
            enableWidget = QtWidgets.QCheckBox()
            enableWidget.setChecked(True)

            fixedValueLabel = QtWidgets.QLabel("fixed value")
            fixedValueWidget = ScientificSpinBox()
            fixedValueWidget.setDisabled(enableWidget.isChecked())

            enableWidget.toggled.connect(lambda checked, index=i: self._setEnabled(index, checked))
            fixedValueWidget.valueChanged.connect(lambda value, index=i: self._setFixedValue(index, value))

            hLayout.addWidget(argNameLabel)
            hLayout.addWidget(argNameWidget)
            hLayout.addWidget(enableLabel)
            hLayout.addWidget(enableWidget)
            hLayout.addWidget(fixedValueLabel)
            hLayout.addWidget(fixedValueWidget)

            mainLayout.addLayout(hLayout)

            argInfo = {"argNameWidget": argNameWidget, "enableWidget": enableWidget, "fixedValueWidget": fixedValueWidget}
            self.argsInfo.append(argInfo)

        self.warningLabel = QtWidgets.QLabel("!Duplicate scan parameters have been selected")
        self.warningLabel.setStyleSheet("color: red; font-weight: bold;")
        self.warningLabel.hide()
        mainLayout.addWidget(self.warningLabel)

        self.setLayout(mainLayout)

    def getFuncName(self):
        return self._funcName

    def _setEnabled(self, index, checked):
        self.argsInfo[index]["fixedValueWidget"].setDisabled(checked)
        if checked:
            self._setFixedValue(index, None)
        else:
            self._setFixedValue(index, self.argsInfo[index]["fixedValueWidget"].value())

    def _setFixedValue(self, index, value):
        currentValues = [argInfo["fixedValueWidget"].value() if argInfo["enableWidget"].isChecked() else None for argInfo in self.argsInfo]
        if currentValues[index] == value:
            return
        self._func.setFixedValue(index, value)

    def _fixedValueChanged(self, index, value):
        currentValues = [argInfo["fixedValueWidget"].value() if argInfo["enableWidget"].isChecked() else None for argInfo in self.argsInfo]
        if currentValues[index] == value:
            return

        if value is None:
            self.argsInfo[index]["enableWidget"].setChecked(True)
            self.argsInfo[index]["fixedValueWidget"].setDisabled(True)
        else:
            self.argsInfo[index]["enableWidget"].setChecked(False)
            self.argsInfo[index]["fixedValueWidget"].setDisabled(False)
            self.argsInfo[index]["fixedValueWidget"].setValue(value)
