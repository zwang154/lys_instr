from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class PowerTab(QWidget):
    itemAdded = pyqtSignal(str, dict)

    def __init__(self, callback=None):
        super().__init__()
        lay = QHBoxLayout()
        self.__power_to = QDoubleSpinBox()
        self.__power_to.setMinimum(-10000000)
        self.__power_to.setMaximum(10000000)
        lay.addWidget(QLabel('Power (deg)'))
        lay.addWidget(self.__power_to)
        lay.addStretch()
        lay.addWidget(QPushButton('Add', clicked=self.__addPower))
        self.setLayout(lay)
        if callback is not None:
            self.itemAdded.connect(callback)

    def __addPower(self):
        p = {}
        p['Value'] = self.__power_to.value()
        self.itemAdded.emit('Power', p)
