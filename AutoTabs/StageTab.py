from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class StageTab(QWidget):
    itemAdded = pyqtSignal(str, dict)

    def __init__(self, stage, callback=None):
        super().__init__()
        self.stage = stage
        h1 = QHBoxLayout()
        self.__savepos = QPushButton(
            'Save Positions', clicked=self.__savePosition)
        self.__movepos = QPushButton(
            'Add Move Positions', clicked=self.__addPosition)
        h1.addWidget(self.__savepos)
        h1.addWidget(self.__movepos)

        self.__poslist = QListWidget()
        v1 = QVBoxLayout()
        v1.addWidget(self.__poslist)
        v1.addLayout(h1)

        self.setLayout(v1)
        if callback is not None:
            self.itemAdded.connect(callback)

    def __addPosition(self):
        p = eval(self.__poslist.currentItem().text())
        self.itemAdded.emit('StagePosition', p)

    def __savePosition(self):
        p = self.stage.getPosition()
        d = {}
        d['x'] = p[0]
        d['y'] = p[1]
        d['z'] = p[2]
        d['a'] = p[3]
        d['b'] = p[4]
        self.__poslist.addItem(str(d))
