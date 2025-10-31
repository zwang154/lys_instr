import os
import numpy as np
from lys import Wave
from lys.Qt import QtCore


class DataStorage(QtCore.QObject):
    """
    Threaded, asynchronous storage and file management for multi-dimensional data.

    This class reserves disk-backed arrays for incoming frames, buffers updates, and saves buffered data to disk using a background worker thread so the application remains responsive.
    It emits Qt signals to report saving state and to request metadata tags for saved files.
    """

    #: Signal (bool) emitted when saving state changes.
    savingStateChanged = QtCore.pyqtSignal(bool)

    #: Signal (dict) emitted to request metadata tags.
    tagRequest = QtCore.pyqtSignal(dict)

    def __init__(self, **kwargs):
        """
        Initialize the data storage instance.

        Set default storage options and prepare internal buffers.

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
        Base directory for saving data files.

        Returns:
            str: Base directory.
        """
        return self._base

    @base.setter
    def base(self, value):
        """
        Set the base directory for saving data files.
        """
        self._base = value

    @property
    def folder(self):
        """
        Data folder name under the base directory.

        Returns:
            str: Data folder name.
        """
        return self._folder

    @folder.setter
    def folder(self, value):
        """
        Set the data folder name under the base directory.
        """
        self._folder = value

    @property
    def name(self):
        """
        Base file name used when saving data files.

        Returns:
            str: File name.
        """
        return self._name

    @name.setter
    def name(self, value):
        """
        Set the base filename used for saved data files.
        """
        self._name = value

    @property
    def numbered(self):
        """
        Whether automatic file numbering is enabled.

        Returns:
            bool: True if automatic file numbering is enabled, False otherwise.
        """
        return self._numbered

    @numbered.setter
    def numbered(self, value):
        """
        Set whether automatic file numbering is enabled.
        """
        self._numbered = value

    @property
    def enabled(self):
        """
        Whether the data storage instance is enabled.

        Returns:
            bool: True if enabled, False otherwise.
        """
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        """
        Set whether the data storage instance is enabled.
        """
        self._enabled = value

    def getNumber(self):
        """
        Return the next available file number for saving.

        If automatic numbering is enabled the returned number will be appended to the base filename (for example: ``<name>_<number>.npz``).
        If numbering is disabled this method returns ``None``.

        Returns:
            int | None: Next available file number, or ``None`` if numbering is disabled.
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
        Connect this data storage instance to a detector.

        Args:
            detector (``MultiDetectorInterface``): Detector that emits ``dataAcquired`` and ``busyStateChanged`` signals.
        """
        detector.dataAcquired.connect(self.update)
        detector.busyStateChanged.connect(lambda b: self._busyStateChanged(detector, b))

    def _busyStateChanged(self, detector, busy):
        """
        Reserve storage if busy; otherwise save the buffered data.

        Args:
            detector (``MultiDetectorInterface``): Detector that the data storage instance is connected to.
            busy (bool): True to reserve storage, False to save buffered data.
        """
        if busy:
            self.reserve(detector.dataShape)
        else:
            self.save(detector.axes)

    def reserve(self, shape, fillValue=None):
        """
        Reserve storage for a new data array with the specified shape.

        Allocate and initialize an internal NumPy array with the given shape,
        record a file path and tag for the upcoming save, emit ``tagRequest`` to request metadata, 
        and update saving state via the ``savingStateChanged`` signal.

        Args:
            shape (tuple, optional): Shape of the data array to reserve.
            fillValue (float | None, optional): Value to initialize the array with. If ``None`` the array is initialized with NaNs. Defaults to ``None``.

        Returns:
            ``None``
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
        Update the buffered data array with new values.

        Each entry in ``data`` maps an index tuple to a frame array; the buffer is updated in-place at those indices. 

        Args:
            data (dict[tuple, np.ndarray]): Mapping from index tuples to frame arrays used to update the buffer.
        """
        if not self.enabled:
            return
        for idx, value in data.items():
            self._arr[idx] = value

    def save(self, axes):
        """
        Save the buffered data array asynchronously to disk.

        This method constructs a ``lys.Wave`` from the buffered array and provided coordinate arrays, attaches the queued metadata tag to ``lys.Wave.note``, 
        and enqueues the Wave for export on a background worker thread.
        Actual file write occurs in a ``_SaveThread``.

        Args:
            axes (Sequence[np.ndarray]): Coordinate arrays for each data axis used to construct the ``Wave``.
        """
        if not self.enabled:
            return

        wave = Wave(self._arr.copy(), *axes)
        wave.note = self._tags.pop(0)
        path = self._paths.pop(0)

        thread = _SaveThread(wave, path)
        thread.finished.connect(self._savingFinished)
        self._threads.append(thread)
        thread.start()

        self.savingStateChanged.emit(self.saving)

    def _savingFinished(self):
        """
        Handle completion of a save thread.

        Remove any non-running save threads from the internal thread list and emit ``savingStateChanged`` so listeners can update their state.
        """
        for i in reversed(range(len(self._threads))):
            if not self._threads[i].isRunning():
                self._threads.remove(self._threads[i])
        self.savingStateChanged.emit(self.saving)

    @property
    def saving(self):
        """
        Whether a save operation is in progress.

        Returns:
            bool: True if a save operation is in progress, False otherwise.
        """
        return bool(self._threads or self._paths)


class _SaveThread(QtCore.QThread):
    """
    Background thread that writes a ``lys.Wave`` to disk.

    The thread calls ``lys.Wave.export`` on the provided ``Wave`` when started. 
    It is used by ``DataStorage`` to perform non-blocking file writes so the main application thread remains responsive.
    """

    def __init__(self, wave, path):
        """
        Initialize the save thread.

        Args:
            wave (Wave): The ``lys.Wave`` instance to save.
            path (str): Destination file path for the exported Wave.
        """
        super().__init__()
        self.wave = wave
        self.path = path

    def run(self):
        """
        Run the save thread and export the Wave to disk.

        Calls ``lys.Wave.export`` on ``self.wave`` to write the Wave to ``self.path``.
        This runs in the worker thread so the main application thread is not blocked by file I/O.
        """
        self.wave.export(self.path)
