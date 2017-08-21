from PyQt5.QtWidgets import *
from ExtendAnalysis.AnalysisWindow import AnalysisWindow
import ExtendAnalysis.MainWindow as main
from Controllers.SingleMotor import *
from Controllers.Camera import *

class fsTEMMain(AnalysisWindow):
    def __init__(self):
        super().__init__(title="Ultrafast Electron Diffraction/Microscopy Measurements")
        self.__initHardware()
        self.__initlayout()
        self.adjustSize()
    def __initHardware(self):
        self.delay=SingleMotorInterface()
        self.camera=CameraInterface()
    def __initlayout(self):
        tab=QTabWidget()
        l=QHBoxLayout()
        l.addWidget(SingleMotorGUI(self.delay))
        l.addWidget(CameraGUI(self.camera))
        wid=QWidget()
        wid.setLayout(l)
        tab.addTab((wid),'Fundamentals')
        self.setWidget(tab)

def create():
    fsTEM=fsTEMMain()

main.addMainMenu(['fs-TEM','Main Window'],create)
