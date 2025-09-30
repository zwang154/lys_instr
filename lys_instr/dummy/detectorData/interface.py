
class DummyDataInterface:
    @property
    def frameShape(self):
        """
        Shape of each data frame acquired by the detector.

        Returns:
            tuple of int: The shape of each data frame.
        """
        raise NotImplementedError("Dummy data class should impolement this method.")

    @property
    def indexShape(self):
        """
        Shape of the index grid for data acquisition.

        Returns:
            tuple of int: The shape of the index grid.
        """
        raise NotImplementedError("Dummy data class should impolement this method.")

    @property
    def axes(self):
        """
        Coordinate axes for each dimension of the data.

        Returns:
            list[numpy.ndarray]: Coordinate axes for each dimension of the data.
        """
        raise NotImplementedError("Dummy data class should impolement this method.")
    
    @property
    def nframes(self):
        """
        Number of frames aqcuired by single iteration.
        """
        raise NotImplementedError("Dummy data class should impolement this method.")

    def __iter__(self):
        raise NotImplementedError("Dummy data class should impolement this method.")
    
    def __next__(self):
        raise NotImplementedError("Dummy data class should impolement this method.")

