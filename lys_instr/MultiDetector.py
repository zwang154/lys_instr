import logging
import time
import abc

from .Interfaces import HardwareInterface
from lys.Qt import QtCore, QtWidgets


class _AcqThread(QtCore.QThread):
    """
    Acquisition thread for ``DetectorInterface``.

    Runs the detector's acquisition loop as a worker thread and emits signals when new data is acquired.
    """

    # Signal (dict) emitted when new data is acquired.
    dataAcquired = QtCore.pyqtSignal(dict)

    def __init__(self, detector):
        """
        Initializes the acquisition thread for the detector.

        Args:
            detector (DetectorInterface): The detector instance to run acquisition for.
        """
        super().__init__()
        self._detector = detector
        self._detector.updated.connect(self._onUpdated)

    def run(self, *args, **kwargs):
        """
        Runs the detector's acquisition loop.

        Overrides the ``run()`` method of QThread and is called when the worker thread is started.
        """
        try:
            self._detector._run(*args, **kwargs)
            self._onUpdated()
        except Exception as e:
            logging.exception("Error in acquisition thread")

    def _onUpdated(self):
        """
        Emits the ``dataAcquired`` signal with the latest acquired data.

        Called in response to the detector's ``updated`` signal.
        """
        self.dataAcquired.emit(self._detector._get())


class DetectorInterface(HardwareInterface):
    """
    Abstract interface for detector devices.

    This class provides background polling, threaded (worker) acquisition, and Qt signal management for detector state and data updates.
    Subclasses must implement device-specific methods: ``_get()``, ``_stop()``, and ``_isAlive()``.
    ``_get()`` and ``_stop()`` should raise ``RuntimeError`` if the device is not responding or a communication error occurs.
    ``_isAlive()`` should always return the current alive state and should not raise ``RuntimeError`` that causes interruption.
    The ``updated`` signal should be emitted by the acquisition thread to inform when new data is acquired.

    Args:
        **kwargs: Additional keyword arguments passed to QThread.
    """

    #: Signal (bool) emitted when alive state changes.
    aliveStateChanged = QtCore.pyqtSignal(bool)

    #: Signal (bool) emitted when busy state changes.
    busyStateChanged = QtCore.pyqtSignal(bool)

    #: Signal (dict) emitted when data is acquired.
    dataAcquired = QtCore.pyqtSignal(dict)

    #: Signal emitted by the acquisition thread when new data is acquired.
    updated = QtCore.pyqtSignal()

    def __init__(self, **kwargs):
        """
        Initializes the detector interface.

        Sets up initial state and internal flags.

        Args:
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(**kwargs)
        self.busy = False
        self._alive = True

    def _loadState(self):
        """
        Polls the device and updates its state.

        Emits the ``aliveStateChanged`` signal if the alive state has changed.
        """
        al = self._isAlive()
        if self._alive != al:
            self._alive = al
            self.aliveStateChanged.emit(al)

    def startAcq(self, wait=False, output=False, **kwargs):
        """
        Starts acquisition in an acquisition thread.

        If both `wait` and `output` are True, the method blocks until acquisition is complete and returns the acquired data.

        Args:
            wait (bool, optional): If True, blocks until acquisition is complete. Defaults to False.
            output (bool, optional): If True, returns acquired data as a dictionary. Defaults to False.
            **kwargs: Additional keyword arguments passed to the acquisition thread.

        Returns:
            dict or None: Acquired data if output is True, otherwise None.
        """
        if self.busy:
            logging.warning("Detector is busy. Cannot start new acquisition.")
            return
        
        self.busy = True
        self.busyStateChanged.emit(True)

        self._thread = _AcqThread(self)
        if wait and output:
            buffer = {}
            def bufferSlot(data):
                buffer.update(data)
            self._bufferSlot = bufferSlot
            self._thread.dataAcquired.connect(self._bufferSlot, type=QtCore.Qt.DirectConnection)
        self._thread.dataAcquired.connect(self.dataAcquired.emit)
        self._thread.finished.connect(self._onAcqFinished, type=QtCore.Qt.DirectConnection)
        self._thread.start()

        if wait:
            self.waitForReady()
            if output:
                try:
                    self.dataAcquired.disconnect(self._bufferSlot)
                except (TypeError, RuntimeError):
                    logging.warning("Tried to disconnect a slot that was not connected")
                # print(buffer.keys())
                return buffer

    def _onAcqFinished(self):
        """
        Cleans up after acquisition is finished.

        Resets the acquisition thread reference, updates the busy state, and emits the ``busyStateChanged`` signal to notify listeners.
        """
        self._thread = None
        self.busy = False
        self.busyStateChanged.emit(False)

    def waitForReady(self, interval=0.1):
        """
        Blocks further interaction until the device is no longer busy.

        Args:
            interval (float, optional): Polling interval in seconds. Defaults to 0.1.

        Returns:
            bool: True once all axes become idle.
        """
        while True:
            if self.isBusy:
                time.sleep(interval)
            else:
                return True

    @property
    def isBusy(self):
        """
        Returns whether the detector is currently busy.

        This property reflects the internal busy flag, which is True during acquisition.

        Returns:
            bool: True if the detector is busy, False otherwise.
        """
        return self.busy
    
    @property
    def isAlive(self):
        """
        Returns the current alive state of the detector.

        This property should be implemented in subclasses to provide device-specific logic.

        Returns:
            bool: True if the detector is alive, False otherwise.
        """
        return self._isAlive()

    def stop(self):
        """
        Stops the acquisition and emits the latest acquired data.

        This method waits for the acquisition worker thread to finish if it is running.
        """
        try:
            self._stop()
        except Exception as e:
            logging.exception("Error stopping detector")

        if self._thread is not None and self._thread.isRunning():
            try:
                self._thread.quit()
                self._thread.wait()
            except Exception as e:
                logging.exception("Error shutting down acquisition thread")
        try:
            self.dataAcquired.emit(self._get())
        except Exception as e:
            logging.exception("Error emitting acquired data")
    
    def settingWidget(self, parent=None):
        """
        Returns a generic settings dialog.

        This method is intended to be overridden in subclasses to provide a device-specific settings UI.

        Args:
            parent (QWidget, optional): Parent widget for the dialog.

        Returns:
            QDialog: The settings dialog.
        """
        return QtWidgets.QDialog()

    @abc.abstractmethod
    def _get(self):
        """
        Should be implemented in subclasses to provide device-specific logic for getting acquired data.

        Returns:
            dict: Mapping of indices (tuple) to their data frames (np.ndarray).
        """
        pass

    @abc.abstractmethod
    def _stop(self):
        """
        Should be implemented in subclasses to provide device-specific logic for stopping acquisition.
        """
        pass

    @abc.abstractmethod
    def _isAlive(self):
        """
        Should be implemented in subclasses to provide device-specific logic for returning alive state.
        """
        pass



class MultiDetectorInterface(DetectorInterface):
    """
    Abstract interface for multi-detector devices.

    This class extends DetectorInterface to support detectors that acquire multi-dimensional data frames.
    Subclasses should implement device-specific logic for data acquisition and shape reporting.
    """

    def __init__(self, indexDim=None, **kwargs):
        """
        Initializes the multi-detector interface.

        Args:
            indexDim (tuple or None): Dimensions for indexing acquired data.
            **kwargs: Additional keyword arguments passed to DetectorInterface.
        """
        super().__init__(**kwargs)
        self._indexDim = indexDim
        self._acquiredIndices = []

    @property
    def indexDim(self):
        """
        Returns the dimensions for indexing acquired data frames.

        Returns:
            tuple or None: Dimensions for indexing acquired data, or None if not set.
        """
        return self._indexDim

    @property
    def acquiredIndices(self):
        """
        Returns the list of acquired indices.

        Each index corresponds to a data frame acquired by the multi-detector.

        Returns:
            list: List of acquired data indices.
        """
        return self._acquiredIndices

    @property
    def dataShape(self):
        """
        Returns the shape of the acquired data.

        This property should be implemented in subclasses to provide the specific shape of the data frames.

        Returns:
            tuple: Shape of the acquired data.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method to return the shape of the acquired data.")
    
