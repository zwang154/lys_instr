import numpy as np
import os
from .interface import DummyDataInterface


class RamanData(DummyDataInterface):
    """
    Dummy Raman data provider backed by NumPy sample data.

    The class loads ``resources/sampleRamanData.npy`` from the package and exposes frames, index shape and coordinate axes.
    It supports two ``scanLevel`` modes (0 or 1).
    """

    def __init__(self, scanLevel=0):
        """
        Initialize the data provider by loading the sample data.

        Args:
            scanLevel (int): 0 for no index dimension, 1 for a single index axis.

        Raises:
            FileNotFoundError: If the sample data file is missing.
            NotImplementedError: If an unsupported ``scanLevel`` is passed.
        """
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
        """
        Return the name of the data provider.

        Returns:
            str: Name of the data provider ("Raman").
        """
        return "Raman"

    @property
    def frameShape(self):
        """
        Shape of each data frame.

        Returns:
            tuple[int, ...]: Shape of each data frame.
        """
        return (self._data.shape[-1],)

    @property
    def indexShape(self):
        """
        Shape of the index grid to be filled by data frames.

        Returns:
            tuple[int, ...]: Shape of the index grid (empty tuple when no index).
        """
        return self._indexShape

    @property
    def axes(self):
        """
        Axis coordinates for the full data.

        Returns:
            list[numpy.ndarray]: Coordinate arrays corresponding to each axis of the index grid.
        """
        return self._axes
    
    @property
    def nframes(self):
        """
        Number of sub-frames per yielded frame.

        Returns:
            int: Number of sub-frames per yielded frame (always 1 for this provider).
        """
        return 1

    def __iter__(self):
        """
        Return an iterator over (index, frame) pairs.

        Returns:
            Iterator[tuple, numpy.ndarray]: Iterator over (index, frame) pairs.
        """
        self._n = 0
        return self
    
    def __next__(self):
        """
        Return the next (index, frame) pair.

        Returns:
            tuple[tuple[int, ...], numpy.ndarray]: (index, frame)

        Raises:
            StopIteration: When no more frames are available.
        """
        if self._n >= np.prod(self._indexShape):
            raise StopIteration()
        idx = np.unravel_index(self._n, self._indexShape)
        frame = self._data.reshape(-1, self._data.shape[-1])[self._count]
        self._n += 1
        self._count += 1
        return idx, frame
