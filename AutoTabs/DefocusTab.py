from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class DefocusTab(QWidget):
    itemAdded = pyqtSignal(str, dict)

    def __init__(self, callback=None):
        super().__init__()
        self.__defocus = QDoubleSpinBox()
        self.__defocus.setRange(-10000, 10000)
        self.__defocus.setDecimals(5)
        adddefocus = QPushButton('Add', clicked=self.__addDefocus)
        l = QHBoxLayout()
        l.addWidget(QLabel("Defocus (um)"))
        l.addWidget(self.__defocus)
        l.addStretch()
        l.addWidget(adddefocus)
        self.setLayout(l)
        if callback is not None:
            self.itemAdded.connect(callback)

    def __addDefocus(self):
        p = {}
        p['Value'] = self.__defocus.value()
        self.itemAdded.emit('Defocus', p)
