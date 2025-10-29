import numpy as np
from .interface import DummyDataInterface


class RandomData(DummyDataInterface):
    """
    Dummy random data provider for given index and frame shapes.
    """

    def __init__(self, indexShape, frameShape):
        """
        Initializes the data provider.

        Args:
            indexShape (tuple[int, ...]): Shape of the acquisition index grid.
            frameShape (tuple[int, ...]): Shape of each generated frame.
        """
        self._frameShape = frameShape
        self._indexShape = indexShape

    @classmethod
    def name(cls):
        """
        Returns the name of the data provider.

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
        Returns the number of frames produced per iteration.

        The number of frames depends on the combined ranks (number of
        dimensions) of the configured `indexShape` and `frameShape`:

        - If ``len(indexShape) + len(frameShape) <= 3``, a single frame is produced per iteration (common case: 0D/1D index with 2D frame).
        - If both ``indexShape`` and ``frameShape`` are 2D (``len(...) == 2``), the provider yields one frame per index row; the returned value is ``indexShape[1]`` (the inner / column count of the index grid).
        - Other shape combinations are currently not supported.

        Examples:
            - ``indexShape=()`` and ``frameShape=(100, 100)`` -> ``1``
            - ``indexShape=(10,)`` and ``frameShape=(100, 100)`` -> ``1``
            - ``indexShape=(5, 3)`` and ``frameShape=(100, 100)`` -> ``3``

        Returns:
            int: Number of frames produced per iteration.

        Raises:
            NotImplementedError: If the combination of ``indexShape`` and ``frameShape`` is not supported by this provider.
        """
        if len(self._indexShape) + len(self._frameShape) <= 3:
            return 1
        elif len(self._indexShape) == 2 and len(self._frameShape) == 2:
            return self._indexShape[1]
        else:
            raise NotImplementedError("This shape is not supported.")

    def __iter__(self):
        """
        Returns an iterator over (index, frame) pairs and prepares iteration state.

        Prepares internal iteration state and chooses the effective shapes used to generate frames. 

        - If the combined ranks of ``indexShape`` and ``frameShape`` are <= 3, the configured shapes are used unchanged.
        - If both ``indexShape`` and ``frameShape`` are 2-D, the index is treated as a 1-D sequence of rows; the effective frame shape is formed by prepending the index inner-dimension to ``frameShape``.

        Example:
            For ``indexShape=(5, 3)`` and ``frameShape=(100, 100)``, the effective index shape becomes (5,) and frames have shape (3, 100, 100).
        
        Returns:
            Iterator[tuple, numpy.ndarray]: Iterator over (index, frame) pairs with effective shapes.

        Raises:
            NotImplementedError: If the combination of ``indexShape`` and ``frameShape`` is not supported by this provider.
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
        Returns the next (index, frame) pair.

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
        Initializes as a 2-D random-data generator.

        Calls the base constructor with ``indexShape=()`` and ``frameShape=(100, 100)`` by default.
        """
        super().__init__((), (100, 100))

    @classmethod
    def name(cls):
        """
        Returns the name of the data provider.

        Returns:
            str: Name of the data provider ("Random 2D").
        """
        return "Random 2D"