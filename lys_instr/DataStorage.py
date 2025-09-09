import os
import numpy as np
import logging
from lys import Wave
from lys.Qt import QtCore


class DataStorage(QtCore.QObject):
    """
    Threaded data storage and file management for multi-dimensional data.

    This class reserves disk space for data arrays, buffers and updates them with new values, and saves the buffered data to disk.
    Saving is performed asynchronously in a background thread, keeping the main application responsive.
    Qt signals are emitted to notify when the save path or saving state changes.

    Args:
        **kwargs: Additional keyword arguments passed to QObject.
    """

    #: Signal emitted when storage path changes.
    pathChanged = QtCore.pyqtSignal()

    #: Signal (bool) emitted when saving state changes.
    savingStateChanged = QtCore.pyqtSignal(bool)

    #: Signal (dict) emitted to request metadata tags.
    tagRequest = QtCore.pyqtSignal(dict)

    def __init__(self, **kwargs):
        """
        Initializes the ``DataStorage`` instance.

        Sets up initial state.

        Args:
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__()
        self._base = "."
        self._folder = "folder"
        self._name = "data"
        self._enabled = True
        self._numbered = True
        self._threads = []
        self._tags = []
        self._paths = []
        self._arr = None
        self._notes = None

    @property
    def base(self):
        """
        Returns the base directory for saving data files.

        Returns:
            str: Base directory.
        """
        return self._base

    @base.setter
    def base(self, value):
        """
        Sets the base directory for saving data files.
        """
        self._base = value

    @property
    def folder(self):
        """
        Returns the data folder name under base directory.

        Returns:
            str: Data folder name.
        """
        return self._folder

    @folder.setter
    def folder(self, value):
        """
        Sets the data folder name under base directory.
        """
        self._folder = value

    @property
    def name(self):
        """
        Returns the base file name for saving data files.

        Returns:
            str: File name.
        """
        return self._name

    @name.setter
    def name(self, value):
        """
        Sets the base file name for saving data files.
        """
        self._name = value

    @property
    def numbered(self):
        """
        Returns whether automatic file numbering is enabled.

        Returns:
            bool: True if automatic file numbering is enabled, False otherwise.
        """
        return self._numbered

    @numbered.setter
    def numbered(self, value):
        """
        Sets whether to enable automatic file numbering.
        """
        self._numbered = value

    @property
    def enabled(self):
        """
        Returns whether the ``DataStorage`` instance is enabled.

        Returns:
            bool: True if the ``DataStorage`` instance is enabled, False otherwise.
        """
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        """
        Sets whether to enable the ``DataStorage`` instance.
        """
        self._enabled = value

    def getNumber(self):
        """
        Gets the next available file number for saving.

        The number will be appended to the file name when saving if automatic numbering is enabled.

        Returns:
            int or None: Next available file number, or None if numbering is disabled.
        """
        if not self.numbered:
            return None

        reserved = set([thread.path for thread in self._threads] + self._paths)
        i = 0
        while True:
            candidate = os.path.join(self.base, self.folder, f"{self.name}_{i}.npz")
            if not os.path.exists(candidate) and candidate not in reserved:
                return i
            i += 1

    def connect(self, detector):
        """
        Connects this ``DataStorage`` instance to a detector.

        Args:
            detector (object): Detector instance emitting ``dataAcquired`` and ``busyStateChanged`` signals.
        """
        detector.dataAcquired.connect(self._dataAcquired)
        detector.busyStateChanged.connect(lambda b: self._busyStateChanged(detector, b))

    def _dataAcquired(self, data):
        """
        Slot to handle new data acquired from the detector.
        """
        self.update(data)

    def _busyStateChanged(self, detector, busy):
        """
        Reserves storage if busy, otherwise saves the buffered data.

        Args:
            busy (bool): If True, reserve storage; if False, save the buffered data.
        """
        if busy:
            self.reserve(detector.dataShape)
        else:
            self.save()

    def reserve(self, shape, fillValue=None):
        """
        Reserves storage for a new data array with the specified shape.

        Args:
            shape (tuple, optional): Shape of the data array to reserve.
            fillValue (float, optional): Value to initialize the array with (default: NaN).
        """
        if not self.enabled:
            self.savingStateChanged.emit(self.saving)
            return

        tag = {"Notes": self._notes}
        self.tagRequest.emit(tag)

        number = self.getNumber()
        numberedName = f"{self.name}_{number}.npz" if number is not None else f"{self.name}.npz"
        folder = os.path.join(self.base, self.folder)
        path = os.path.join(folder, numberedName)

        self._tags.append(tag)
        self._paths.append(path)
        os.makedirs(folder, exist_ok=True)

        self._arr = np.full(shape, np.nan if fillValue is None else fillValue, dtype=float)
        self.savingStateChanged.emit(self.saving)

    def update(self, data):
        """
        Updates the buffered data array with new values.

        Args:
            indexShape (tuple): Index shape for the data.
            data (dict[str, np.ndarray]): Dictionary mapping indices to data arrays for updating the buffer.
        """
        if not self.enabled:
            return
        for idx, value in data.items():
            self._arr[idx] = value

    def save(self):
        """
        Saves the buffered data array asynchronously to disk.

        This method starts a worker thread to write the buffered data array and emits signals for path and saving state updates.
        """
        if not self.enabled:
            return

        wave = Wave(self._arr.copy())
        wave.note = self._tags.pop(0)
        path = self._paths.pop(0)

        thread = _SaveThread(wave, path)
        thread.finished.connect(self._savingFinished)
        self._threads.append(thread)
        thread.start()

        self.pathChanged.emit()
        self.savingStateChanged.emit(self.saving)

    def _savingFinished(self):
        """
        Slot called when a save thread finishes.

        Updates the saving state and emits the ``savingStateChanged`` signal.
        """
        for i in reversed(range(len(self._threads))):
            if not self._threads[i].isRunning():
                self._threads.remove(self._threads[i])
        self.savingStateChanged.emit(self.saving)

    @property
    def saving(self):
        """
        Returns whether a save operation is currently in progress.

        Returns:
            bool: True if a save operation is in progress, False otherwise.
        """
        return bool(self._threads or self._paths)


class _SaveThread(QtCore.QThread):
    """
    Save thread for ``DataStorage``.

    Writes the provided Wave object asynchronously to disk at the specified path as a worker thread.
    """

    def __init__(self, wave, path):
        """
        Initialize the save thread with a Wave object and a file path.

        Args:
            wave (Wave): The Wave object to be saved.
            path (str): File path where the Wave object will be saved.
        """
        super().__init__()
        self.wave = wave
        self.path = path

    def run(self):
        """
        Runs the save thread, exporting the Wave object to the specified path.
        """
        self.wave.export(self.path)
