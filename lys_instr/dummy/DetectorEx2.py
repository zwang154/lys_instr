import numpy as np
import time
import itertools

from lys_instr import dummy

class DetectorEx2Dummy(dummy.MultiDetectorDummy):
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
                if self._count % 2 == 0:
                    x0 = (128 + 8 * self._count) % 256
                    x, y = np.meshgrid(np.linspace(0, 255, self.frameShape[1]), np.linspace(0, 255, self.frameShape[0]))
                    self._data[idx] = self._gauss2d(x, y, 1, x0, 128, 32, 32, 0)
                else:
                    self._data[idx] = np.random.random(self.frameShape)
                self.updated.emit()
            i += 1
            self._count += 1

    @staticmethod
    def _gauss2d(x, y, A, x0, y0, sigma_x, sigma_y, offset):
        return A * np.exp(-((x - x0) ** 2 / (2 * sigma_x ** 2) + (y - y0) ** 2 / (2 * sigma_y ** 2))) + offset
