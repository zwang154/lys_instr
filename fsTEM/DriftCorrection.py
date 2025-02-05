import numpy as np
from lys import widgets, filters, Wave
from lys.Qt import QtWidgets, QtCore


class DriftCorrector(QtCore.QObject):
    dataChanged = QtCore.pyqtSignal(object)
    shiftChanged = QtCore.pyqtSignal(object)
    refChanged = QtCore.pyqtSignal(object)

    def __init__(self, tem, type="Beam Shift"):
        super().__init__()
        self._enable = False
        self._enableShift = False
        self._ref = None
        self._filt = filters.EmptyFilter()
        self._type = type
        self._tem = tem
        self._cam = None
        self._corr = filters.DriftCorrection((0, 1), [(0, 0), (0, 0)], apply=False)
        self._shiftMat = None

    def setData(self, data):
        if not self._enable:
            return
        self._data_orig = data.duplicate()
        if self._filt is not None:
            self._data = self._filt.execute(data)
        else:
            self._data = data
        if self._ref is not None:
            self._corr._apply = False
            data = Wave(np.array([self._ref.data, self._data.data]).transpose(1, 2, 0), self._data.x, self._data.y, None)  # [::-1] is needed only in STEM?
            print(np.array([self._ref.data, self._data.data]).transpose(1, 2, 0).shape)
            shift = self._corr.execute(data)
            self.correct(shift[1].data)
            for f in self._corr.getFilters():
                if isinstance(f, filters.DriftCorrection):
                    f._apply = True
            shifted = self._corr.execute(data)
            for f in self._corr.getFilters():
                if isinstance(f, filters.DriftCorrection):
                    f._apply = False
            self.shiftChanged.emit(Wave(shifted.data[:, :, 1], shifted.x, shifted.y))
        self.dataChanged.emit(self._data)

    def correct(self, shift):
        print("shift(px)=", shift)
        if not self._enableShift:
            return
        if self._shiftMat is None:
            return
        if self._type == "Image Shift":
            print("Image shift", self._shiftMat.dot(-shift))
            self._tem.setImageShift(np.array(self._tem.getImageShift()) + self._shiftMat.dot(-shift))
        elif self._type == "Beam Shift":
            print("Beam shift", self._shiftMat.dot(-shift))
            self._tem.setBeamShift(np.array(self._tem.getBeamShift()) + self._shiftMat.dot(-shift))

    def setReference(self, reference):
        self._ref_orig = reference.duplicate()
        if self._filt is not None:
            self._ref = self._filt.execute(reference)
        else:
            self._ref = reference
        self.refChanged.emit(self._ref)

    def setFilter(self, filter, estimator):
        self._filt = filter
        self._corr = estimator
        if self._ref_orig is not None:
            self.setReference(self._ref_orig)
        if self._data_orig is not None:
            self.setData(self._data_orig)

    def setCamera(self, cam):
        self._cam = cam

    def setEnabled(self, estimation, correction):
        self._enable = estimation
        self._enableShift = correction

    def verifyShift(self):
        self._enable = False
        self._shift = ShiftEstimator(self._cam, self._tem, self._filt, self._corr, exposure=0.01, shift=2, type="Beam Shift")
        self._shift.finished.connect(self.__verified)
        self._shift.start()

    def __verified(self):
        self._shiftMat = np.linalg.inv(self._shift.calc())
        print("Shift matrix = ")
        print(self._shiftMat)
        self._shift = None
        self._enable = True

    @property
    def enable(self):
        return self._enable

    def widget(self):
        return DriftCorrectionGUI(self)


class ShiftEstimator(QtCore.QThread):
    def __init__(self, camera, tem, filt, corr, exposure=0.010, shift=2, type="Beam Shift"):
        super().__init__()
        self._cam = camera
        self._tem = tem
        self._filt = filt
        self._corr = corr
        self._exp = exposure
        self._shift = shift
        self._type = type
        self._data = []

    def run(self):
        self._cam.acquireFinished.connect(self._correct)
        if self._type == "Image Shift":
            shift = self._tem.setImageShift
        else:
            shift = self._tem.setBeamShift
        shift([0, 0])
        self._cam.startAcquire(self._exp, wait=True)
        shift([self._shift, 0])
        self._cam.startAcquire(self._exp, wait=True)
        shift([0, self._shift])
        self._cam.startAcquire(self._exp, wait=True)
        shift([0, 0])

    def calc(self):
        print(np.array(self._data).shape)
        data = []
        axes = []
        for d in self._data:
            filted = self._filt.execute(d)
            data.append(filted)
            axes = [filted.x, filted.y]
        data = Wave(np.array(data).transpose(1, 2, 0), *axes, None)
        # data = Wave(np.array([self._filt.execute(d).data for d in self._data]).transpose(1, 2, 0), self._filt.execute(self._data[0]).x, self._filt.execute(self._data[0]).y, None)
        return self._corr.execute(data).data[1:, :].T / self._shift

    def _correct(self, data):
        self._data.append(data)


class DriftCorrectionGUI(QtWidgets.QWidget):
    def __init__(self, obj):
        super().__init__()
        self._obj = obj
        self._obj.dataChanged.connect(self.__dataChanged)
        self._obj.refChanged.connect(self.__refChanged)
        self._obj.shiftChanged.connect(self.__shiftChanged)
        self.__initLayout()
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.resize(100, 100)
        self.adjustSize()

    def __initLayout(self):
        self._enable = QtWidgets.QCheckBox("Enable estimation", toggled=self._enabled)
        self._enableShift = QtWidgets.QCheckBox("Enable correction", toggled=self._enabled)
        h0 = QtWidgets.QHBoxLayout()
        h0.addWidget(self._enable)
        h0.addWidget(self._enableShift)

        self._ref = widgets.lysCanvas()
        self._ref.setCanvasSize("Width", "Absolute", 7)
        self._ref.setCanvasSize("Height", "Absolute", 7)

        self._data = widgets.lysCanvas()
        self._data.setCanvasSize("Width", "Absolute", 7)
        self._data.setCanvasSize("Height", "Absolute", 7)

        self._shift = widgets.lysCanvas()
        self._shift.setCanvasSize("Width", "Absolute", 7)
        self._shift.setCanvasSize("Height", "Absolute", 7)

        self._tab = QtWidgets.QTabWidget()
        self._tab.addTab(self._ref, "Ref")
        self._tab.addTab(self._data, "Data")
        self._tab.addTab(self._shift, "Corrected")

        self._filter = filters.FiltersGUI(dimension=4)
        self._corr = filters.FiltersGUI(dimension=3)
        self._corr.setFilters([self._obj._corr])

        h2 = QtWidgets.QHBoxLayout()
        h2.addWidget(QtWidgets.QPushButton("Set Reference", clicked=self.__setRef))
        h2.addWidget(QtWidgets.QPushButton("Set Filter", clicked=self.__setFilter))

        h3 = QtWidgets.QHBoxLayout()
        h3.addWidget(QtWidgets.QPushButton("calc", clicked=self._obj.verifyShift))

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(h0)
        layout.addWidget(self._filter)
        layout.addWidget(self._corr)
        layout.addLayout(h2)
        layout.addLayout(h3)

        h1 = QtWidgets.QHBoxLayout()
        h1.addLayout(layout)
        h1.addWidget(self._tab)

        self.setLayout(h1)

    def _enabled(self):
        self._obj.setEnabled(self._enable.isChecked(), self._enableShift.isChecked())

    def __setRef(self):
        self._obj.setReference(self._obj._data_orig)
        self._filter.setDimension(self._obj._data_orig.ndim)

    def __setFilter(self):
        self._obj.setFilter(self._filter.getFilters(), self._corr.getFilters())

    def __dataChanged(self, wave):
        self._data.Clear()
        self._data.Append(wave)

    def __refChanged(self, ref):
        self._ref.Clear()
        self._ref.Append(ref)

    def __shiftChanged(self, ref):
        self._shift.Clear()
        self._shift.Append(ref)
