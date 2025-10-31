
class DummyDataInterface:
    """
    Abstract interface for dummy detector data providers.

    Subclasses should provide an iterable sequence of frames and metadata describing frame shape, index grid shape, and coordinate axes.
    """
    @classmethod
    def name(cls):
        """
        Return the name of the dummy data set.

        Returns:
            str: Name of the dummy data set.
        """
        raise NotImplementedError("Dummy data class should implement this method.")
    
    @property
    def frameShape(self):
        """
        Shape of each data frame.

        Returns:
            tuple[int, ...]: Shape of each data frame.
        """
        raise NotImplementedError("Dummy data class should implement this method.")

    @property
    def indexShape(self):
        """
        Shape of the index grid for data frames.

        Returns:
            tuple[int, ...]: Shape of the index grid.
        """
        raise NotImplementedError("Dummy data class should implement this method.")

    @property
    def axes(self):
        """
        Axis coordinates for the full data.

        Returns:
            list[numpy.ndarray]: Coordinate arrays corresponding to each axis of the index grid.
        """
        raise NotImplementedError("Dummy data class should implement this method.")
    
    @property
    def nframes(self):
        """
        Number of sub-frames per yielded frame.

        Values > 1 indicate multi-slice frames (e.g., when an index row is treated as a leading frame dimension).

        Returns:
            int: Number of sub-frames per yielded frame.
        """
        raise NotImplementedError("Dummy data class should impolement this method.")

    def __iter__(self):
        """
        Return an iterator over (index, frame) pairs.

        Subclasses should yield frames where each frame's shape matches ``frameShape``.

        Returns:
            Iterator: Iterator over (index, frame) pairs.
        """
        raise NotImplementedError("Dummy data class should implement this method.")
    
    def __next__(self):
        """
        Return the next (index, frame) pair.

        Subclasses must return the next frame and raise ``StopIteration`` when the sequence is exhausted.

        Returns:
            tuple[tuple[int, ...], numpy.ndarray]: (index, frame)

        Raises:
            StopIteration: When no more frames are available.
        """
        raise NotImplementedError("Dummy data class should implement this method.")

