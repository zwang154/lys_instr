import os
import queue
import logging
from lys.Qt import QtCore
from .Interfaces import HardwareInterface, lock

logging.basicConfig(level=logging.INFO)


class DataStorageInterface(HardwareInterface):

    savingStateChanged = QtCore.pyqtSignal(bool)

    def __init__(self, maxQueueSize=0, bufferThreshold=1, interval=0.5, buffered=False, **kwargs):
        super().__init__(interval=interval, **kwargs)
        self._path = None
        self._saveThread = SaveThread(saveFunc=self.write, maxQueueSize=maxQueueSize)
        self._saveThread.savingStateChanged.connect(self.savingStateChanged.emit)
        self._saveThread.start()

        self._mutex = QtCore.QMutex()
        self._bufferThreshold = bufferThreshold
        self._buffered = buffered
        self._buffer = {}
        self.setBuffered(buffered)

    @lock
    def _loadState(self):
        if self.getBufferSize() > self._bufferThreshold:
            self.flushBuffer()

    def flushBuffer(self):
        if self._buffered and self._buffer:
            self._saveThread.enqueue(self._buffer.copy())
            self._buffer.clear()

    @lock
    def getBuffer(self):
        return self._buffer

    @lock
    def getBufferSize(self):
        return sum(getattr(frame, 'nbytes', 0) / (1024 * 1024) for frame in self._buffer.values())

    @lock
    def update(self, data):
        if self._buffered:
            self._buffer.update(data)
        else:
            self._saveThread.enqueue(data)

    def setPath(self, fileDir, fileName, fileType):
        ext = {'hdf5': 'h5', 'zarr': 'zarr'}.get(fileType)
        self._path = os.path.join(fileDir, f"{fileName}.{ext}")
        self._type = fileType

    def setBuffered(self, buffered):
        if self._buffered == buffered:
            return

        self._buffered = buffered

        if self._buffered:
            # self._mutex = QtCore.QMutex()
            self.start()
        else:
            if self._buffer:
                self.flushBuffer()
            self._buffer.clear()
            self.kill()
            self.wait()

    def stop(self):
        if self._saveThread.isRunning():
            self._saveThread.kill()
            self._saveThread.wait()

    def write(self, data):
        try:
            self._write(data, path=self._path, type=self._type)
        except Exception as e:
            logging.error(f"Error saving data: {e}")

    def read(self, keys=None):        # Key is a collection of indices
        if not self._path or not self._type:
            logging.error("Path or type not set for reading.")
            return {}
        if not os.path.exists(self._path):
            logging.error(f"File does not exist: {self._path}")
            return {}

        try:
            return self._read(path=self._path, type=self._type, keys=keys)
        except Exception as e:
            logging.error(f"Error reading data: {e}")
            return {}
    
    @lock
    def setBufferThreshold(self, bufferThreshold):
        self._bufferThreshold = bufferThreshold


class SaveThread(QtCore.QThread):

    savingStateChanged = QtCore.pyqtSignal(bool)

    def __init__(self, saveFunc, maxQueueSize=0):
        super().__init__()
        self.saveFunc = saveFunc
        self._queue = queue.Queue(maxsize=maxQueueSize)
        self._running = True

    def run(self):
        while self._running:
            try:
                data = self._queue.get(timeout=0.1)
                self.saveFunc(data)
                self.savingStateChanged.emit(False)
            except queue.Empty:
                continue

    def enqueue(self, data):
        self.savingStateChanged.emit(True)
        self._queue.put(data)

    def getQueueSize(self):
        return self._queue.qsize()

    def isRunning(self):
        return self._running

    def kill(self):
        self._running = False



