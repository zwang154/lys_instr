from lys.Qt import QtWidgets, QtCore
from lys.decorators import avoidCircularReference

import numpy as np
from lys import Wave


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


class PreCorrector:
    def __init__(self, controllers):
        super().__init__()
        self._enabled = True
        self._controllers = {}
        for c in controllers:
            c.valueChanged.connect(self._correct)
            self._controllers.update({name: c for name in c.nameList})

        self._correctParams = dict()

    @property
    def parameters(self):
        return self._controllers.keys()
    
    @property
    def corrections(self):
        return self._correctParams

    @avoidCircularReference
    def _correct(self, values={}):
        if not self._enabled:
            return
        
        for name, func in self._correctParams.items():
            if not func.enabled:
                continue
            elif any([arg in values for arg in func.argNames(excludeFixed=False)]):
                params = {arg: self._controllers[arg].get()[arg] for arg in func.argNames()}
                self._controllers[name].set(**{name: func(**params)})


class _FunctionCombination:
    def __init__(self):
        super().__init__()
        self._funcs = dict()
        self._formula = None
        self.enabled = True

    def __call__(self, **scanParams):
        if self._formula is None:
            firstFunc = next(iter(self._funcs.values()))
            correctValue = firstFunc(**scanParams)
        else:
            localVariables = {funcName: func(**scanParams) for funcName, func in self._funcs.items()}
            correctValue = eval(self._formula, {"__builtins__": None}, localVariables)
        return correctValue

    @property
    def functions(self):
        return self._funcs
    
    @property
    def expression(self):
        return self._formula
    
    @expression.setter
    def expression(self, value):
        self._formula = value

    def argNames(self, excludeFixed=True):
        res = []
        for func in self._funcs.values():
            for arg in func.argNames(excludeFixed=excludeFixed):
                if arg not in res:
                    res.append(arg)
        return res


class _InterpolatedFunction:
    """
    This class represents a function f(x,y) with the information of arguments name such as 'x'.

    Evaluation of the function can be done by __call__ like f(x=1, y=2).
    """

    def __init__(self, interpolator, argNames):
        super().__init__()
        self._argNames = argNames
        self._interpolator = interpolator
        self._fixedValues = {}

    def __call__(self, **kwargs):
        return self._interpolator([[self._fixedValues.get(arg, kwargs.get(arg, None)) for arg in self.argNames()]])[0]
    
    @property
    def fixedValues(self):
        """ a dictionary that specifies the fixed value."""
        return self._fixedValues

    def argNames(self, excludeFixed=False):
        """Returns all arguments names of this function."""
        if excludeFixed:
            return [arg for arg in self._argNames if arg not in self._fixedValues]
        else:
            return self._argNames


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

