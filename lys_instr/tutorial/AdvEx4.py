import numpy as np
import time
import itertools
from lys_instr.resources import sampleRamanData
from lys_instr import DataStorage, gui, dummy

from lys import multicut, Wave
from lys.widgets import LysSubWindow
from lys.Qt import QtWidgets


class SpectrometerDummy(dummy.MultiDetectorDummy):
    def __init__(self, indexShape=(8, 9, 36,), frameShape=(600,), exposure=0.1, **kwargs):
        super().__init__(indexShape, frameShape, exposure=exposure, **kwargs)
        # self._frameCount = 0

    def _run(self, iter=1):
        self._shouldStop = False

        data = sampleRamanData()[:, :, :, 1, :]

        i = 0
        while i != iter:
            for idx in itertools.product(*(range(s) for s in self.indexShape)):
                if self._shouldStop:
                    return
                time.sleep(self.exposure)
                self._data[idx] = data[idx[0], idx[1], idx[2], :]
                # self._data[idx] = data[int(self._frameCount % len(data)), :]
                self.updated.emit()
            i += 1

        self._frameCount += 1

class SpectrometerGUI(gui.MultiDetectorGUI):
    def __init__(self, obj, wait=False, interval=1, iter=1):
        super().__init__(obj, wait=wait, interval=interval, iter=iter)

    def _dataAcquired(self, data):
        if not hasattr(self, "_data"):
            self._frameCount = 0
            self._data = Wave(np.zeros(self._obj.dataShape), *self._obj.axes)

        if data:
            for idx, frame in data.items():
                self._data.data[idx] = frame    # Data registration revised
            self._frameCount += 1

            # Update frame display every frames or on last frame
            if self._frameCount == np.prod(self._obj.indexShape):
                update = True
            else:
                update = False if self._params["interval"] is None else self._frameCount % self._params["interval"] == 0

            if update:
                self._update()
        
class mappingWidget(gui.MultiScan.ScanWidget):
    def __init__(self, storage, motors, detectors):
        super().__init__(storage, motors, detectors)
    
    


class window(LysSubWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Example 4")
        self._storage = DataStorage()
        self._detector = SpectrometerDummy()

        # self._motor = dummy.MultiMotorDummy("x", "y")

        self._storage.connect(self._detector)
        self._initLayout()
        self.setSettingFile("Example4.dic")
        self.adjustSize()

    def _initLayout(self):
        _storageGUI = gui.DataStorageGUI(self._storage)
        _detectorGUI = SpectrometerGUI(self._detector)

        VBox = QtWidgets.QVBoxLayout()
        VBox.addWidget(_storageGUI)
        VBox.addWidget(_detectorGUI)      

        w = QtWidgets.QWidget()
        w.setLayout(VBox)
        self.setWidget(w)


