import numpy as np
import time
import itertools

from lys_instr import dummy

class DetectorEx1Dummy(dummy.MultiDetectorDummy):
    def __init__(self, indexShape, frameShape, **kwargs):
        super().__init__(indexShape, frameShape, **kwargs)
        self._count = 0

    def _run(self, iter=1):
        self._shouldStop = False

        i = 0
        while i != iter:
            for idx in itertools.product(*(range(s) for s in self.indexShape)):
                if self._shouldStop:
                    return
                time.sleep(self.exposure)
                x = np.linspace(0, 255, 256)
                x0 = (128 + 8 * self._count) % 256
                y = self._gauss1d(x, 1, x0, 32, 0)
                self._data[idx] = y
                self.axes = [x]
                self.updated.emit()
            i += 1
            self._count += 1

    @staticmethod
    def _gauss1d(x, A, x0, sigma, offset):
        return A * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2)) + offset

    @property
    def axes(self):
        return [np.linspace(0, 1, s) for s in self.dataShape]
    
    @axes.setter
    def axes(self, axes):
        self._axes = axes
