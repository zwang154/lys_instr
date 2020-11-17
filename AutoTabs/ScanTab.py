from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class ScanTab(QWidget):
    itemAdded = pyqtSignal(str, dict)

    def __init__(self, callback=None):
        super().__init__()

        gl1 = QGridLayout()
        self.__scan_mode = QComboBox()
        self.__scan_mode.addItems(
            ['Delay', 'Power', 'Focus', 'Stage X', 'Stage Y', 'Stage Z', 'Stage Alpha', 'Stage Beta'])
        gl1.addWidget(QLabel('Scan type'), 0, 0)
        gl1.addWidget(self.__scan_mode, 0, 1)

        self.__scan_from = QDoubleSpinBox()
        self.__scan_from.setMinimum(-10000000)
        self.__scan_from.setMaximum(10000000)
        self.__scan_step = QDoubleSpinBox()
        self.__scan_step.setValue(1)
        self.__scan_step.setMinimum(-10000000)
        self.__scan_step.setMaximum(10000000)
        self.__scan_loop = QSpinBox()
        self.__scan_loop.setValue(100)
        self.__scan_loop.setMinimum(-10000000)
        self.__scan_loop.setMaximum(10000000)
        gl1.addWidget(QLabel('From'), 1, 0)
        gl1.addWidget(self.__scan_from, 2, 0)
        gl1.addWidget(QLabel('Step'), 1, 1)
        gl1.addWidget(self.__scan_step, 2, 1)
        gl1.addWidget(QLabel('Loop'), 1, 2)
        gl1.addWidget(self.__scan_loop, 2, 2)

        self.__scan_folder = QLineEdit()
        self.__scan_folder.setText('Scan')
        self.__scan_name = QLineEdit()
        self.__scan_name.setText('a')
        self.__scan_expose = QDoubleSpinBox()
        self.__scan_expose.setValue(3)
        self.__scan_expose.setMinimum(0.000001)
        self.__scan_expose.setMaximum(10000)
        gl1.addWidget(QLabel('Folder'), 3, 0)
        gl1.addWidget(QLabel('Filename'), 3, 1)
        gl1.addWidget(QLabel('Exposure (s)'), 3, 2)
        gl1.addWidget(self.__scan_folder, 4, 0)
        gl1.addWidget(self.__scan_name, 4, 1)
        gl1.addWidget(self.__scan_expose, 4, 2)

        self.__scan_reftype = QComboBox()
        self.__scan_reftype.addItems(['Delay', 'None'])
        self.__scan_refval = QDoubleSpinBox()
        self.__scan_refval.setMinimum(-10000000)
        self.__scan_refval.setMaximum(10000000)
        gl1.addWidget(QLabel('Reference'), 5, 0)
        gl1.addWidget(self.__scan_reftype, 6, 0)
        gl1.addWidget(self.__scan_refval, 6, 1)

        self.__scan_add = QPushButton('Add', clicked=self.__addScan)
        self.__scan_addloop = QSpinBox()
        self.__scan_addloop.setMaximum(100000)
        self.__scan_addloop.setValue(1)
        gl1.addWidget(self.__scan_add, 7, 0)
        gl1.addWidget(self.__scan_addloop, 7, 1)
        gl1.addWidget(QLabel(' times'), 7, 2)

        lay = QVBoxLayout()
        lay.addLayout(gl1)
        lay.addStretch()

        self.setLayout(lay)
        if callback is not None:
            self.itemAdded.connect(callback)

    def __addScan(self):
        for i in range(self.__scan_addloop.value()):
            p = {}
            p['Scan type'] = self.__scan_mode.currentText()
            p['From'] = self.__scan_from.value()
            p['Step'] = self.__scan_step.value()
            p['Loop'] = self.__scan_loop.value()
            folder = self.__scan_folder.text()
            name = folder.split('/')
            name = name[len(name)-1]
            p['Folder'] = folder+'/'+name+"_"+str(i)
            # p['Folder']=self.__scan_folder.text()+"_"+str(i)
            p['Exposure'] = self.__scan_expose.value()
            p['Name'] = self.__scan_name.text()
            p['RefType'] = self.__scan_reftype.currentText()
            p['RefValue'] = self.__scan_refval.value()
            self.itemAdded.emit('Scan', p)
