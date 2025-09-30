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

        i = 0
        while i != iter:
            for idx in itertools.product(*[range(j) for j in self.indexShape]):
                if self._count >= totalFrames:
                    self._count = 0
                if self._shouldStop:
                    return
                time.sleep(self.exposure)
                idx = allIndices[self._count]
                self._data[idx[-1] if self.indexShape[-1] > 1 else 0] = data[idx][1]
                self._axes = [np.linspace(0, 360, data.shape[2], endpoint=False), data[idx][0]] if self.indexShape[-1] > 1 else data[idx][0]
                self.updated.emit()
                self._count += 1
            i += 1

    @property
    def axes(self):
        if hasattr(self, "_axes"):
            return self._axes
        return [np.linspace(0, 1, s) for s in self.dataShape]
