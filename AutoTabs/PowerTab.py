from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


class PowerTab(QWidget):
    itemAdded = pyqtSignal(str, dict)

    def __init__(self):
        gl1 = QGridLayout()
        self.__power_to = QDoubleSpinBox()
        self.__power_to.setMinimum(-10000000)
        self.__power_to.setMaximum(10000000)
        gl1.addWidget(QLabel('To'), 1, 0)
        gl1.addWidget(self.__power_to, 2, 0)

        self.__power_add = QPushButton('Add', clicked=self.addPower)
        gl1.addWidget(self.__power_add, 3, 0)
        self.setLayout(gl1)

    def addPower(self):
        p = {}
        p['Value'] = self.__power_to.value()
        self.itemAdded.emit('Power', p)
