import numpy as np
import time
from lys_instr.MultiDetector import MultiDetectorInterface


class MultiDetectorDummy(MultiDetectorInterface):
    def __init__(self, indexDim=None, frameDim=None, frameTime=None, resumeIdx=False, **kwargs):
        super().__init__(indexDim=indexDim, **kwargs)
        self._data = {}
        self._frameDim = frameDim
        self._frameTime = frameTime
        self._resumeIdx = resumeIdx
        self._error = False
        self._numFrames = None
        self.start()

    def _run(self):
        if not self._resumeIdx:
            self._acquiredIndices = []
        startNum = 0 if not self._resumeIdx else len(self._acquiredIndices)
        endNum = None if self._numFrames is None else startNum + self._numFrames

        self._shouldStop = False

        i = startNum
        while not self._shouldStop and (endNum is None or i < endNum):
            time.sleep(self._frameTime)
            idx = (i // np.product(self._indexDim), i % np.product(self._indexDim) % self._indexDim[0], i % np.product(self._indexDim) // self._indexDim[0])
            self._data[idx] = np.random.rand(*self._frameDim)
            self._acquiredIndices.append(idx)
            self.updated.emit()
            i += 1

    def _stop(self):
        self._shouldStop = True

    def _get(self): 
        data = self._data.copy()
        self._data.clear()
        return data

    def _isAlive(self):
        """
        Gets the alive state of the simulated detector.

        Returns:
            bool: True if the detector is alive, False if it is dead.
        """
        return not self._error

    
