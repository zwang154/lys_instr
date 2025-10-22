import numpy as np
import os
from .interface import DummyDataInterface


class RamanData(DummyDataInterface):
    def __init__(self, scanLevel=0):
        here = os.path.dirname(__file__)
        path = os.path.normpath(os.path.join(here, '..', '..', 'resources', 'sampleRamanData.npy'))

        if not os.path.exists(path):
            raise FileNotFoundError(f"sampleRamanData.npy not found at {path}. Put the file in lys_instr/resources/")
        
        sample = np.load(path)
        self._data = sample[:, :, :, 1, :]
        self._axes = [np.linspace(0, 360, self._data.shape[-2], endpoint=False), sample[0, 0, 0, 0, :]][-1 - scanLevel:]
        if scanLevel == 1:
            self._indexShape = (self._data.shape[-2],)
        elif scanLevel == 0:
            self._indexShape = ()
        else:
            raise NotImplementedError("scanLevel must be 0 or 1")
        self._count = 0

    @classmethod
    def name(cls):
        return "Raman"

    @property
    def frameShape(self):
        return (self._data.shape[-1],)

    @property
    def indexShape(self):
        return self._indexShape

    @property
    def axes(self):
        return self._axes
    
    @property
    def nframes(self):
        return 1

    def __iter__(self):
        self._n = 0
        return self
    
    def __next__(self):
        if self._n >= np.prod(self._indexShape):
            raise StopIteration()
        idx = np.unravel_index(self._n, self._indexShape)
        frame = self._data.reshape(-1, self._data.shape[-1])[self._count]
        self._n += 1
        self._count += 1
        return idx, frame
