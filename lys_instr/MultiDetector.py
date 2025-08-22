import logging
import time

from .Interfaces import HardwareInterface
from lys.Qt import QtCore, QtWidgets


class _AcqThread(QtCore.QThread):
    """
    Acquisition thread for ``DetectorInterface``.

    Runs the detector's acquisition loop as a worker thread and emits signals when new data is acquired.
    """

    # Signal (dict) emitted when new data is acquired.
    dataAcquired = QtCore.pyqtSignal(dict)

    def __init__(self, detector, streaming):
        """
        Initializes the acquisition thread for the detector.

        Args:
            detector (DetectorInterface): The detector instance to run acquisition for.
        """
        super().__init__()
        self._detector = detector
        self._detector.updated.connect(self._onUpdated)
        self._streaming = streaming

    def run(self, *args, **kwargs):
        """
        Runs the detector's acquisition loop.

        Overrides the ``run()`` method of QThread and is called when the worker thread is started.
        """
        self._detector._run(self._streaming)
        self._onUpdated()

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
        exposure(float or None): The initial exposure time. If the device does not support the exposure time, None should be set.
        **kwargs: Additional keyword arguments passed to QThread.
    """

    aliveStateChanged = QtCore.pyqtSignal(bool)
    """Emitted when alive state changes."""

    busyStateChanged = QtCore.pyqtSignal(bool)
    """Emitted when busy state changes."""

    dataAcquired = QtCore.pyqtSignal(dict)
    """emitted when data is acquired."""

    updated = QtCore.pyqtSignal()
    """emitted by the acquisition thread when new data is acquired."""

    def __init__(self, exposure=1, **kwargs):
        super().__init__(**kwargs)
        self._exposure = exposure
        self._busy = False

    def _loadState(self):
        """
        Polls the device and updates its state.

        Emits the ``aliveStateChanged`` signal if the alive state has changed.
        """
        if not hasattr(self, "_alive"):
            self._alive = True

        al = self._isAlive()
        if self._alive != al:
            self._alive = al
            self.aliveStateChanged.emit(al)

    def startAcq(self, streaming=False, wait=False, output=False):
        """
        Starts acquisition in an acquisition thread.

        If both `wait` and `output` are True, the method blocks until acquisition is complete and returns the acquired data.

        Args:
            wait (bool, optional): If True, blocks until acquisition is complete. Defaults to False.
            output (bool, optional): If True, returns acquired data as a dictionary. Defaults to False.

        Returns:
            dict or None: Acquired data if output is True, otherwise None.
        """
        if self._busy:
            logging.warning("Detector is busy. Cannot start new acquisition.")
            return
        
        self._busy = True
        self.busyStateChanged.emit(True)

        self._thread = _AcqThread(self, streaming=streaming)
        self._thread.dataAcquired.connect(self.dataAcquired.emit)
        self._thread.finished.connect(self._onAcqFinished, type=QtCore.Qt.DirectConnection)
        if wait and output:
            buffer = {}
            self._thread.dataAcquired.connect(buffer.update, type=QtCore.Qt.DirectConnection)

        self._thread.start()


        if wait:
            self.waitForReady()
            if output:
                self.dataAcquired.disconnect(buffer.update)
                return buffer

    def _onAcqFinished(self):
        """
        Cleans up after acquisition is finished.

        Resets the acquisition thread reference, updates the busy state, and emits the ``busyStateChanged`` signal to notify listeners.
        """
        self._thread = None
        self._busy = False
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
    def exposure(self):
        """
        Return the exposure time.
        If the detector does not support the exposure time, None will be returned.

        Returns:
            float or None: The exposure time
        """
        return self._exposure
    
    @exposure.setter
    def exposure(self, value):
        """
        Set the exposure time.

        Args:
            value(float): The exporesure time to be set.
        """
        self._exposure = value

    @property
    def isBusy(self):
        """
        Returns whether the detector is currently busy.

        This property reflects the internal busy flag, which is True during acquisition.

        Returns:
            bool: True if the detector is busy, False otherwise.
        """
        return self._busy
    
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
        self._stop()

        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()
        self.dataAcquired.emit(self._get())
    
    def settingWidget(self):
        """
        Returns a generic settings dialog.

        This method is intended to be overridden in subclasses to provide a device-specific settings UI.

        Args:
            parent (QWidget, optional): Parent widget for the dialog.

        Returns:
            QDialog: The settings dialog.
        """
        raise NotImplementedError("Subclass should implement this method.")

    def _get(self):
        """
        Should be implemented in subclasses to provide device-specific logic for getting acquired data.

        Returns:
            dict: Mapping of indices (tuple) to their data frames (np.ndarray).
        """
        raise NotImplementedError("Sub-class should implement this method.")

    def _stop(self):
        """
        Should be implemented in subclasses to provide device-specific logic for stopping acquisition.
        """
        raise NotImplementedError("Sub-class should implement this method.")

    def _isAlive(self):
        """
        Should be implemented in subclasses to provide device-specific logic for returning alive state.
        """
        raise NotImplementedError("Sub-class should implement this method.")

    def _run(self, streaming):
        """
        The sub-class of this class should implement _run method.

        Args:
            streaming(bool): Whether the measurement should be continuous.
        """
        raise NotImplementedError("This method should be implemented in sub class.")



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
    
