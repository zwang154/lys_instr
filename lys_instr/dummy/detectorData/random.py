import numpy as np
from .interface import DummyDataInterface


class RandomData(DummyDataInterface):
    def __init__(self, indexShape, frameShape):
        self._frameShape = frameShape
        self._indexShape = indexShape

    @classmethod
    def name(cls):
        return "Random"

    @property
    def frameShape(self):
        return self._frameShape

    @property
    def indexShape(self):
        return self._indexShape

    @property
    def axes(self):
        return [np.linspace(0, 1, s) for s in tuple([*self.indexShape, *self.frameShape])]
    
    @property
    def nframes(self):
        if len(self._indexShape) + len(self._frameShape) <= 3:
            return 1
        elif len(self._indexShape) == 2 and len(self._frameShape) == 2:
            return self._indexShape[1]
        else:
            NotImplementedError("This shape is not supported.")

    def __iter__(self):
        self._n = 0
        if len(self._indexShape) + len(self._frameShape) <= 3:
            self._indexShape_act = self._indexShape
            self._frameShape_act = self._frameShape
        elif len(self._indexShape) == 2 and len(self._frameShape) == 2:
            self._indexShape_act = (self._indexShape[0],)
            self._frameShape_act = tuple([self._indexShape[1], *self._frameShape])
        else:
            NotImplementedError("This shape is not supported.")
        return self
    
    def __next__(self):
        self._n += 1
        if self._n-1 == np.prod(self._indexShape_act):
            raise StopIteration()
        return np.unravel_index(self._n-1, self._indexShape_act), np.random.rand(*self._frameShape_act)
    
class RandomData2D(RandomData):
    def __init__(self):
        super().__init__((), (100, 100))

    @classmethod
    def name(cls):
        return "Random 2D"