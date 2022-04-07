from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class MagnificationTab(QWidget):
    itemAdded = pyqtSignal(str, dict)

    def __init__(self, tem, callback=None):
        super().__init__()
        self._tem = tem
        self.__mag = QSpinBox()
        addmag = QPushButton('Add', clicked=self.__addMagnification)
        lay = QHBoxLayout()
        lay.addWidget(QLabel("Magnification"))
        lay.addWidget(self.__mag)
        lay.addStretch()
        lay.addWidget(addmag)
        lv = QVBoxLayout()
        lv.addLayout(lay)
        lv.addWidget(QPushButton("Read present magnification", clicked=lambda: print(
            "Magnification: " + str(self._tem.getMagnification()))))
        self.setLayout(lv)
        if callback is not None:
            self.itemAdded.connect(callback)

    def __addMagnification(self):
        p = {}
        p['Value'] = self.__mag.value()
        self.itemAdded.emit('Magnification', p)
