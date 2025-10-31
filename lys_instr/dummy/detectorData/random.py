import numpy as np
from .interface import DummyDataInterface


class RandomData(DummyDataInterface):
    """
    Dummy random data provider for given index and frame shapes.
    """

    def __init__(self, indexShape, frameShape):
        """
        Initialize the data provider.

        Args:
            indexShape (tuple[int, ...]): Shape of the acquisition index grid.
            frameShape (tuple[int, ...]): Shape of each generated frame.
        """
        self._frameShape = frameShape
        self._indexShape = indexShape

    @classmethod
    def name(cls):
        """
        Return the name of the data provider.

        Returns:
            str: Name of the data provider ("Random").
        """
        return "Random"

    @property
    def frameShape(self):
        """
        Shape of each generated data frame.

        Returns:
            tuple[int, ...]: Shape of each generated data frame.
        """
        return self._frameShape

    @property
    def indexShape(self):
        """
        Shape of the index grid to be filled by generated data frames.

        Returns:
            tuple[int, ...]: Shape of the index grid.
        """
        return self._indexShape

    @property
    def axes(self):
        """
        Axis coordinates for the full data.

        Returns:
            list[numpy.ndarray]: Coordinate arrays corresponding to each axis of the index grid (evenly spaced integers).
        """
        return [np.linspace(0, 1, s) for s in tuple([*self.indexShape, *self.frameShape])]
    
    @property
    def nframes(self):
        """
        Number of sub-frames per yielded frame.

        - If ``len(indexShape) + len(frameShape) <= 3`` -> 1
        - If both are 2-D -> ``indexShape[1]`` (inner/column count)

        Examples:
            - ``indexShape=()`` and ``frameShape=(100, 100)`` -> ``1``
            - ``indexShape=(10,)`` and ``frameShape=(100, 100)`` -> ``1``
            - ``indexShape=(5, 3)`` and ``frameShape=(100, 100)`` -> ``3``

        Returns:
            int: Number of sub-frames per yielded frame.

        Raises:
            NotImplementedError: If the combination of shapes is unsupported.
        """
        if len(self._indexShape) + len(self._frameShape) <= 3:
            return 1
        elif len(self._indexShape) == 2 and len(self._frameShape) == 2:
            return self._indexShape[1]
        else:
            raise NotImplementedError("This shape is not supported.")

    def __iter__(self):
        """
        Return an iterator over (index, frame) pairs and prepare iteration state.

        Replace the index and frame shapes with effective ones when both are 2-D.

        Returns:
            Iterator[tuple, numpy.ndarray]: Iterator over (index, frame) pairs with effective shapes.

        Raises:
            NotImplementedError: If the combination of shapes is unsupported.
        """
        self._n = 0
        if len(self._indexShape) + len(self._frameShape) <= 3:
            self._indexShape_act = self._indexShape
            self._frameShape_act = self._frameShape
        elif len(self._indexShape) == 2 and len(self._frameShape) == 2:
            self._indexShape_act = (self._indexShape[0],)
            self._frameShape_act = tuple([self._indexShape[1], *self._frameShape])
        else:
            raise NotImplementedError("This shape is not supported.")
        return self
    
    def __next__(self):
        """
        Return the next (index, frame) pair.

        Returns:
            tuple[tuple[int, ...], numpy.ndarray]: (index, frame)

        Raises:
            StopIteration: When iteration is complete.
        """
        self._n += 1
        if self._n-1 == np.prod(self._indexShape_act):
            raise StopIteration()
        return np.unravel_index(self._n-1, self._indexShape_act), np.random.rand(*self._frameShape_act)
    
class RandomData2D(RandomData):

    """
    Convenience 2-D random-data provider.
    """

    def __init__(self):
        """
        Initialize as a 2-D random-data generator.

        Calls the base constructor with ``indexShape=()`` and ``frameShape=(100, 100)`` by default.
        """
        super().__init__((), (100, 100))

    @classmethod
    def name(cls):
        """
        Return the name of the data provider.

        Returns:
            str: Name of the data provider ("Random 2D").
        """
        return "Random 2D"