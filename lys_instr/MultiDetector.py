import logging

from lys.Qt import QtCore
from .Interfaces import HardwareInterface


class _AcqThread(QtCore.QThread):
    """
    Acquisition thread for ``DetectorInterface``.

    Runs the detector's acquisition loop as a worker thread and emits signals when new data is acquired.
    """

    #: Signal (dict) emitted when new data is acquired.
    dataAcquired = QtCore.pyqtSignal(dict)

    def __init__(self, detector, iter=1):
        """
        Initialize the acquisition thread for a detector.

        Args:
            detector (DetectorInterface): The detector instance to run acquisition for.
            iter (int, optional): Number of acquisition iterations for this thread. Defaults to 1.
        """
        super().__init__()
        self._detector = detector
        self._detector.updated.connect(self._onUpdated)
        self._iteration = iter

    def run(self, *args, **kwargs):
        """
        Run the detector's acquisition loop.

        Overrides the ``run()`` method of QThread and is called when the worker thread is started.
        """
        self._detector._run(self._iteration)
        self._onUpdated()

    def _onUpdated(self):
        """
        Emit the ``dataAcquired`` signal with the latest acquired data.

        Called in response to the detector's ``updated`` signal.
        """
        self.dataAcquired.emit(self._detector._get())


class DetectorInterface(HardwareInterface):
    """
    Abstract interface for detector devices.

    This class provides background polling, threaded (worker) acquisition, and Qt signal management for detector state and data updates.
    Subclasses must implement device-specific methods: ``_get()``, ``_stop()``, and ``_isAlive()``.
    ``_get()`` and ``_stop()`` should raise ``RuntimeError`` if the device is not responding or a communication error occurs.
    ``_isAlive()`` should always return the current alive state and should not raise ``RuntimeError`` that interrupts monitoring.
    The ``updated`` signal is emitted by the acquisition thread when new data is available.
    """

    #: Signal (bool) emitted when alive state changes.
    aliveStateChanged = QtCore.pyqtSignal(bool)

    #: Signal (bool) emitted when busy state changes.
    busyStateChanged = QtCore.pyqtSignal(bool)

    #: Signal (dict) emitted when data is acquired.
    dataAcquired = QtCore.pyqtSignal(dict)

    #: Signal emitted by the acquisition thread when new data is acquired.
    updated = QtCore.pyqtSignal()

    def __init__(self, exposure=1, **kwargs):
        """
        Initialize the interface.

        Args:
            exposure (float or None): Initial exposure time.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(**kwargs)
        self._exposure = exposure
        self._mutex = QtCore.QMutex()
        self._busy = False

    def _loadState(self):
        """
        Poll the device and update its state.

        Emit the ``aliveStateChanged`` signal if the alive state has changed.
        """
        if not hasattr(self, "_alive"):
            self._alive = True

        al = self._isAlive()
        if self._alive != al:
            self._alive = al
            self.aliveStateChanged.emit(al)

    def startAcq(self, iter=1, wait=False, output=False):
        """
        Start acquisition in an acquisition thread.

        If both `wait` and `output` are True, the method blocks until acquisition completes and returns the acquired data.

        Args:
            iter (int): Number of iterations.
            wait (bool, optional): If True, blocks until acquisition is complete. Defaults to False.
            output (bool, optional): If True, returns acquired data as a dictionary. Defaults to False.

        Returns:
            dict[tuple, np.ndarray] | None: Acquired data that maps index tuples to frames when ``output`` is True; otherwise ``None``.
        """
        if self._busy:
            logging.warning("Detector is busy. Cannot start new acquisition.")
            return
        
        self._busy = True
        self.busyStateChanged.emit(True)

        self._thread = _AcqThread(self, iter=iter)
        self._thread.dataAcquired.connect(self.dataAcquired.emit, type=QtCore.Qt.DirectConnection)
        self._thread.finished.connect(self._onAcqFinished, type=QtCore.Qt.DirectConnection)
        if wait and output:
            buffer = {}
            self._thread.dataAcquired.connect(buffer.update, type=QtCore.Qt.DirectConnection)

        thread = self._thread
        self._thread.start()

        if wait:
            self.waitForReady()
            if output:
                thread.dataAcquired.disconnect(buffer.update)
                return buffer

    def _onAcqFinished(self):
        """
        Clean up after acquisition is finished.

        Reset the acquisition thread reference, update the busy state, and emit the ``busyStateChanged`` signal.
        """
        with QtCore.QMutexLocker(self._mutex):
            self._busy = False
            self.busyStateChanged.emit(False)
            self._thread = None

    def waitForReady(self):
        """
        Block further interaction until the device is no longer busy.

        Returns:
            None
        """
        loop = QtCore.QEventLoop()

        def on_busy_changed(b):
            if not b and loop.isRunning():
                loop.quit()

        with QtCore.QMutexLocker(self._mutex):
            if self._busy is False:
                return
            self.busyStateChanged.connect(on_busy_changed, QtCore.Qt.QueuedConnection)
        loop.exec_()

    def stop(self):
        """
        Stop the acquisition and emit the latest acquired data.

        This method waits for the acquisition worker thread to finish if it is running.
        """
        self._stop()

        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()
        self.dataAcquired.emit(self._get())

    @property
    def exposure(self):
        """
        Exposure time.

        Returns:
            float | None: The exposure time.
        """
        return self._exposure
    
    @exposure.setter
    def exposure(self, value):
        """
        Set the exposure time.

        Args:
            value (float | None): Exposure time to set, or ``None`` to indicate unsupported.
        """
        self._exposure = value

    @property
    def isBusy(self):
        """
        Current busy state of the detector.

        This property reflects the internal busy flag, which is True during acquisition.

        Returns:
            bool: True if the detector is busy, False otherwise.
        """
        return self._busy
    
    @property
    def isAlive(self):
        """
        Current alive state of the detector.

        This property should be implemented in subclasses to provide device-specific logic.

        Returns:
            bool: True if the detector is alive, False otherwise.
        """
        return self._isAlive()
    
    def _get(self):
        """
        Should be implemented in subclasses to provide device-specific logic for getting acquired data.

        Returns:
            dict[tuple, np.ndarray]: Mapping of index tuples to their data frames.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def _stop(self):
        """
        Should be implemented in subclasses to provide device-specific logic for stopping acquisition.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def _isAlive(self):
        """
        Should be implemented in subclasses to provide device-specific logic for returning alive state.
        
        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def _run(self, iter=1):
        """
        Should be implemented in subclasses to provide device-specific logic for running the acquisition.

        Args:
            iter(int): Number of iterations. -1 means continuous run.
        
        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def settingsWidget(self):
        """
        Return a device-specific settings dialog.

        Subclasses should override this to provide a QDialog for device settings.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class MultiDetectorInterface(DetectorInterface):
    """
    Abstract interface for multi-dimensional detector devices.

    This class extends ``DetectorInterface`` to support detectors that acquire data with multi-dimensional indices.
    Subclasses should implement device-specific acquisition and property reporting logic.
    """

    @property
    def axes(self):
        """
        Axis coordinates for the full data.

        Returns:
            list[numpy.ndarray]: Coordinate arrays corresponding to each axis of the index grid.

        Raises:
            NotImplementedError: If the subclass does not implement this property.
        """
        raise NotImplementedError("Subclasses must implement this property.")

    @property
    def frameDim(self):
        """
        Number of dimensions for a single frame of data.

        Returns:
            int: Number of dimensions for a single frame.
        """
        return len(self.frameShape)

    @property
    def indexDim(self):
        """
        Dimension of the index grid.

        Returns:
            int: Dimension of the index grid.
        """
        return len(self.indexShape)

    @property
    def frameShape(self):
        """
        Shape of a single frame.

        Returns:
            tuple[int, ...]: Dimensions of a single frame.

        Raises:
            NotImplementedError: If the subclass does not implement this property.
        """
        raise NotImplementedError("Subclasses must implement this property.")

    @property
    def indexShape(self):
        """
        Shape of the index tuples.

        Returns:
            tuple[int, ...]: Shape of the index tuples.

        Raises:
            NotImplementedError: If the subclass does not implement this property.
        """
        raise NotImplementedError("Subclasses must implement this property.")

    @property
    def dataShape(self):
        """
        Shape of the full data.

        Returns:
            tuple[int, ...]: Combined shape of the full dataset.
        """
        return tuple([*self.indexShape, *self.frameShape])
    
