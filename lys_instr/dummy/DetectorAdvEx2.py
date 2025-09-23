import time
import itertools
import numpy as np

from . import MultiDetectorDummy
from lys_instr.resources import sampleRamanData


class DetectorAdvEx2Dummy(MultiDetectorDummy):
    def __init__(self, indexShape, frameShape, **kwargs):
        super().__init__(indexShape, frameShape, **kwargs)
        self._count = 0

    def _run(self, iter=1):
        self._shouldStop = False

        data = sampleRamanData()     # shape: (8, 9, 36, 2, 600)
        allIndices = list(itertools.product(*(range(s) for s in (8, 9, 36))))
        totalFrames = len(allIndices)

        i = 0
        while i != iter:
            for idx in itertools.product(*(range(s) for s in self.indexShape)):
                if self._shouldStop:
                    return
                time.sleep(self.exposure)
                ijk = allIndices[(self._count * np.prod(self.indexShape) + np.ravel_multi_index(idx, self.indexShape)) % totalFrames]
                self._frame = data[ijk]
                self._data[idx] = data[ijk][1]
                self._axes = [np.linspace(0, 1, s) for s in self.indexShape[:2]] + [np.linspace(0, 360, 36, endpoint=False), data[ijk][0]]
                self.updated.emit()
            i += 1
            self._count += 1

    @property
    def axes(self):
        if hasattr(self, "_axes"):
            return self._axes
        return [np.linspace(0, 1, s) for s in self.dataShape]
