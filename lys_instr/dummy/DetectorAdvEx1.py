import time
import itertools
import numpy as np

from . import MultiDetectorDummy
from lys_instr.resources import sampleRamanData


class DetectorAdvEx1Dummy(MultiDetectorDummy):
    def __init__(self, indexShape, frameShape, **kwargs):
        super().__init__(indexShape, frameShape, **kwargs)
        self._count = 0

    def _run(self, iter=1):
        self._shouldStop = False

        data = sampleRamanData()     # shape: (8, 9, 36, 2, 600)
        allIndices = list(itertools.product(*(range(s) for s in data.shape[:3])))
        totalFrames = len(allIndices)

        for _ in range(iter):
            if self._count >= totalFrames:
                self._count = 0
            if self._shouldStop:
                return
            time.sleep(self.exposure)
            idx = allIndices[self._count]
            self._frame = data[idx]
            self._data[idx] = data[idx][1]
            self._axes = [np.linspace(0, 1, s) for s in self.indexShape[:2]] + [np.linspace(0, 360, data.shape[2], endpoint=False), data[idx][0]]
            self.updated.emit()
            self._count += 1

    @property
    def axes(self):
        if hasattr(self, "_axes"):
            return self._axes
        return [np.linspace(0, 1, s) for s in self.dataShape]
