import numpy as np
from lys.Qt import QtCore


class ScanAxis(QtCore.QObject):
    def __init__(self, name, obj, range):
        super().__init__()
        self._name = name
        self._obj = obj
        self._range = range
        self._counter = None
    
    @property
    def name(self):
        """
        Currently selected scan axis name.

        Returns:
            str: Name of the currently selected scan axis.
        """
        return self._name

    @property
    def obj(self):
        """
        Scanner corresponding to the currently selected axis.

        Returns:
            object: Scanner object for the selected axis.
        """
        return self._obj

    @property
    def range(self):
        """
        List of labels that this row will iterate over when executed.

        Returns:
            list[str]: Sequence of label strings (Iteration mode) or expression strings (Free mode).
        """
        return self._range

    @property
    def index(self):
        """
        Index of the current switch state within the scan range.

        Returns:
            int: Index of the value in ``range`` equal to the current scanner reading (switch-axis label).
        """
        if self._counter is not None:
            return self._counter.get()

        value = self.obj.get()[self.name]

        if isinstance(value, str):
            return self.range.index(value)
        return np.argmin(abs(np.array(self.range) - value))

    def setCounter(self, counter):
        """
        Set the counter for this scan row.

        Args:
            counter (_Counter): Counter for tracking scan indices.
        """
        self._counter = counter


class MultiScan(QtCore.QObject):
    """
    Scan configuration and execution panel.

    Provides a list-based GUI for composing a sequence of motor and switch scans, configuring detector/process settings, and starting/stopping scan execution.
    """

    _stop_requested = QtCore.pyqtSignal()

    finished = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()

    def __init__(self, storage, scanlist, detector, exposure, fileName=None):
        """
        Initialize the Scan widget.

        Args:
            storage (DataStorage): The data storage object.
            scanlist (Iterable[ScanRow]): Scan rows to include in the scan.
            detectors (dict): Mapping of detector names to respective detector objects.
            switches (Iterable[MultiSwitchInterface]): Switch controllers available for scanning.
            detectors (dict): Mapping of detector names to respective detector objects.
        """
        super().__init__()
        self._storage = storage
        self._list = scanlist
        self._detector = detector
        self._exposure = exposure
        self._fileName = fileName if fileName is not None else self.defaultFileName
        self._busy = False
        self._stopped = False
    
    def start(self):
        """
        Start the configured scan run.

        Builds the nested process chain from the configured scan list and starts the worker thread.
        """

        self._busy = True
        self._stopped = False

        process = _DetectorProcess(self._detector, self._exposure)
        for s in self._list:
            counter = _Counter()
            s.setCounter(counter)
            process = _ScanProcess(s.name, s.obj, s.range, process, counter)

        process.beforeAcquisition.connect(self._updateName, QtCore.Qt.DirectConnection)

        self._storage.numbered = False
        self._storage.enabled = True
        self._storage.tagRequest.connect(self._setScanNames)

        self._worker = _ScanWorker(process)
        self._thread = QtCore.QThread(self)

        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._workerFinished, QtCore.Qt.DirectConnection)
        self._worker.finished.connect(lambda b: self._thread.quit())
        self._worker.finished.connect(lambda b: self._worker.deleteLater())
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._scanThreadFinished)
        self._stop_requested.connect(self._worker.stop)

        self._oldName = self._storage.name      

        self._thread.start()

    def _workerFinished(self, b):
        self._stopped = not b

    def _scanThreadFinished(self):
        """
        Handle scan completion and restore GUI and storage state.
        """
        self._storage.name = self._oldName
        self._storage.numbered = True

        self._busy = False
        if self._stopped:
            self.stopped.emit()
        else:
            self.finished.emit()
    
    @property
    def defaultFileName(self):
        strings = [self._list[i].name + "_[" + str(i + 1) + "]" for i in reversed(range(len(self._list)))]
        return "/".join(strings)

    def _updateName(self):
        """
        Update the storage file name using current scan parameter values.
        """
        name = str(self._fileName)
        for i, scan in enumerate(self._list):
            value = scan.obj.get()[scan.name]
            index = scan.index
            name = name.replace("{" + str(i + 1) + "}", value) if type(value) == str else name.replace("{" + str(i + 1) + "}", f"{value:.5g}")
            name = name.replace("[" + str(i + 1) + "]", str(index))
        self._storage.name = name

    def stop(self):
        """
        Request the running scan to stop.
        """
        self._stop_requested.emit()

    def _setScanNames(self, scanNamesDict):
        """
        Populate the provided mapping with the current scan axis names.

        Args:
            scanNamesDict (dict): Mutable mapping that will be updated by this method. The key ``'scanNames'`` is set to a list[str] containing the current scan axis names in order.
        """
        scanNamesDict["scanNames"] = [s.name for s in self._list]

    def closeEvent(self, event):
        """
        Event handler for window close event.

        If the scan is running when the window is closed,
        this method will force the scan to stop and wait for the thread to finish before accepting the close event.
        """
        if hasattr(self, "_thread") and self._thread.isRunning():
            QtCore.QMetaObject.invokeMethod(self._worker, "forceStop", QtCore.Qt.BlockingQueuedConnection)
            self._thread.quit()
            self._thread.wait()
        event.accept()


class Loop(QtCore.QObject):
    """
    Dummy loop scanner.
    """

    def __init__(self, name="loop"):
        """
        Create the loop object.

        Args:
            name (str, optional): Key used in mappings for the loop value. Defaults to "loop".
        """
        super().__init__()
        self._name = name
        self._value = None

    def set(self, *args, **kwargs):
        """
        Set the loop value.

        Args:
            *args: If provided, the first positional argument is used as the loop value.
            **kwargs: If no positional args are provided, the first keyword value is used.

        Raises:
            ValueError: If neither positional nor keyword arguments are provided.
        """
        if args:
            self._value = args[0]
        elif kwargs:
            self._value = next(iter(kwargs.values()))
        else:
            raise ValueError("No value provided to _Loop.set()")

    def get(self):
        """
        Return the current loop value as a mapping.

        Returns:
            dict[str, object]: Mapping of the loop names to respective current values.
        """
        return {self._name: self._value}


class _Counter:
    """
    Counter for tracking scan indices for a single scan process.
    """

    def __init__(self):
        """
        Initialize the counter.
        """
        self._count = -1
        self.reset()

    def increment(self):
        """
        Increment the counter.

        Returns:
            int: The new count value.
        """
        self._count += 1
        return self._count

    def get(self):
        """
        Get the current count.

        Returns:
            int: The current count value.
        """
        return self._count

    def reset(self):
        """
        Reset the count to -1.
        """
        self._count = -1


class _ScanWorker(QtCore.QObject):
    """
    Thread wrapper for executing a scan process.
    """
    finished = QtCore.pyqtSignal(bool)

    def __init__(self, process):
        """
        Create a new executor for the given process.

        Args:
            process (object): Object exposing ``execute()`` and ``stop()`` used by the executor.
        """
        super().__init__()
        self._process = process

    def run(self):
        """
        Run the wrapped process's ``execute()`` in this thread.
        """
        b = self._process.execute()
        self.finished.emit(b)

    def stop(self):
        """
        Request the running scan process to stop.
        """
        self._process.stop()


class _DetectorProcess(QtCore.QObject):
    """
    Detector process wrapper.

    Wraps a detector and exposure value and exposes ``execute()`` and ``stop()`` used by the scan executor.
    Emits ``beforeAcquisition`` before starting acquisition.
    """

    # signal emitted before starting acquisition
    beforeAcquisition = QtCore.pyqtSignal()

    # signal emitted after acquisition is finished
    finished = QtCore.pyqtSignal()

    def __init__(self, detector, exposure):
        """
        Create a detector process wrapper.

        Args:
            detector (object): Detector object to control.
            exposure (float): Exposure time to apply before acquisition.
        """
        super().__init__()
        self._detector = detector
        self._exposure = exposure
        self._shouldStop = False
        self._mutex = QtCore.QMutex()

        detector.busyStateChanged.connect(self._busyChanged)

    def execute(self):        
        """
        Execute the detector process.

        Configures exposure if provided, emits ``beforeAcquisition`` and starts the detector.
        """
        self._shouldStop = False
        with QtCore.QMutexLocker(self._mutex):
            if self._shouldStop:
                return False
            if self._detector.exposure is not None:
                self._detector.exposure = self._exposure
            self.beforeAcquisition.emit()
        
        self._detector.startAcq(wait=True)
        return not self._shouldStop

    def _busyChanged(self, busy):
        """
        Handle detector busy-state updates.

        Emits ``finished`` when the detector is not busy anymore.
        """
        if not busy:
            self.finished.emit()

    def stop(self):
        """
        Stop the wrapped detector acquisition.
        """
        with QtCore.QMutexLocker(self._mutex):
            self._shouldStop = True
            self._detector.stop()


class _ScanProcess(QtCore.QObject):
    """
    Scan process wrapper.

    Iterates a sequence of values for a single scan axis and delegates to the nested process for acquisition at each value.
    Exposes ``execute()`` and ``stop()``.
    """

    #: Signal emitted before each acquisition.
    beforeAcquisition = QtCore.pyqtSignal()

    def __init__(self, name, obj, values, process, counter=None):
        """
        Create a scan process for a single axis.

        Args:
            name (str): Axis name used in ``set()`` calls.
            obj (object): Controller exposing ``set(..., wait=True)`` and ``get()``.
            values (Iterable[float | str]): Sequence of values to iterate over (elements are numeric or label strings).
            process (object): Nested process exposing ``execute()`` and ``stop()``.
            level (int): Nesting level of this scan process (0 for innermost).
            counter (_Counter | None): Counter for tracking scan indices. If None, no counting is performed.
        """
        super().__init__()
        self._name = name
        self._obj = obj
        self._values = values
        self._process = process
        self._counter = counter if counter is not None else _Counter()
        self._shouldStop = False
        self._process.beforeAcquisition.connect(self.beforeAcquisition.emit, QtCore.Qt.DirectConnection)
        self._mutex = QtCore.QMutex()

    def execute(self):
        """
        Iterate values, set the axis value and delegate to the nested process.
        """
        self._counter.reset()

        for value in self._values:
            if self._shouldStop:
                return False
            self._counter.increment()
            self._obj.set(**{self._name: value}, wait=True)
            if self._shouldStop:
                return False
            b = self._process.execute()
        
        return b
        

    def stop(self):
        """
        Request the scan to stop and stop the nested process.
        """
        with QtCore.QMutexLocker(self._mutex):
            self._shouldStop = True
        self._process.stop()