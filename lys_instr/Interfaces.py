import time

from lys.Qt import QtCore


class HardwareInterface(QtCore.QThread):
    __list = []

    errorStateChanged = QtCore.pyqtSignal(bool)

    def __init__(self, interval=0.1):
        super().__init__()
        self.__interval = interval
        self.__stopped = False
        self.__mutex = QtCore.QMutex()
        self.__alive = True
        HardwareInterface.__list.append(self)

    def run(self):
        while(True):
            if self.__stopped:
                return
            self._loadState()
            alive = self.alive()
            if self.__alive != alive:
                self.__alive = alive
                self.errorStateChanged.emit(self.__alive)
            time.sleep(self.__interval)

    def kill(self):
        with QtCore.QMutexLocker(self.__mutex):
            self.__stopped = True

    def alive(self):
        return True

    def _loadState(self):
        pass

    @classmethod
    def killAll(cls):
        for h in cls.__list:
            h.kill()
        cls.__list = []
