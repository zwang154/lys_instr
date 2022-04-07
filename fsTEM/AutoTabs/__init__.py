from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from .PowerTab import PowerTab
from .DefocusTab import DefocusTab
from .MagnificationTab import MagnificationTab
from .StageTab import StageTab
from .ScanTab import ScanTab
from .PhaseDiagramTab import PhaseDiagramTab


class ParamsTab(QWidget):
    def __init__(self, tem=None, callback=None):
        super().__init__()
        lay = QVBoxLayout()
        lay.addWidget(PowerTab(callback=callback))
        if tem is not None:
            lay.addWidget(DefocusTab(callback=callback))
            lay.addWidget(MagnificationTab(tem=tem, callback=callback))
        lay.addStretch()
        self.setLayout(lay)
