from PyQt5.QtWidgets import QHBoxLayout, QWidget

from PythonHardwares.Interfaces import HardwareInterface
from .Initializer import initialize
from lys import home

#root = "\\\\192.168.12.203\\smb\\data2\\"
root = home() + "/data"

dic = {
    "Camera": ["Merlin", "Digital Micrograph", "DummyCamera"],
    "Delay Stage": ["fs-fs", "fs-ns", "ns-ns", "DummyDelay"],
    "Pump Power": ["GSC02", "DummyPump"],
    "Probe Power": ["DummyProbe"],
    "Pump Shutter": ["SC10", "DummySwitch"],
    "Probe Shutter": ["DummySwitch"],
    "Stage": ["SingleTilt", "DoubleTilt", "DummyStage"]}


class GlobalInitializer:
    def __init__(self):
        from PythonHardwares.Hardwares.FEI.TechnaiFemto import TechnaiFemto
        self.tem = TechnaiFemto('192.168.12.210', '192.168.12.201', 7000, 7001)
        self.merlin = None

    def init(self):
        gui = initialize(root, dic, self.generate, self.layout)
        gui.tagRequest.connect(self._setParams)
        gui.closed.connect(self._closed)

    def generate(self, instr):
        if instr is None:
            return None
        elif instr == "Merlin":
            from PythonHardwares.Hardwares.QuantumDetector.MerlinEM import MerlinEM
            self.merlin = MerlinEM('192.168.12.206', stem=self.tem.getSTEM())
            return self.merlin
        elif instr == 'Digital Micrograph':
            return self.tem.getCamera()
        elif instr == 'DummyCamera':
            from PythonHardwares.Camera import CameraDummy
            return CameraDummy()
        elif instr == 'fs-fs':
            from PythonHardwares.Hardwares.Soloist.SoloistHLE import SoloistHLE
            return SoloistHLE('192.168.12.202', 8000)
        elif instr == 'fs-ns':
            from PythonHardwares.Hardwares.SRS.DG645 import DG645
            return DG645('192.168.12.204', mode='fs', frequency=25000)
        elif instr == 'ns-ns':
            from PythonHardwares.Hardwares.SRS.DG645 import DG645
            return DG645('192.168.12.204', mode='ns')
        elif instr == 'DummyDelay':
            from PythonHardwares.SingleMotor import SingleMotorDummy
            return SingleMotorDummy()
        elif instr == "DummyPump":
            from PythonHardwares.SingleMotor import SingleMotorDummy
            return SingleMotorDummy()
        elif instr == "DummyProbe":
            from PythonHardwares.SingleMotor import SingleMotorDummy
            return SingleMotorDummy()
        elif instr == "GSC02":
            from PythonHardwares.Hardwares.OptoSigma.GSC02 import GSC02
            return GSC02('COM3')
        elif instr == "SC10":
            from PythonHardwares.Hardwares.Thorlabs.SC10 import SC10
            return SC10('COM4')
        elif instr == "DummySwitch":
            from PythonHardwares.Switch import SwitchDummy
            return SwitchDummy()
        elif instr == "DummyStage":
            from PythonHardwares.Stage import StageDummy
            return StageDummy()
        elif instr == "SingleTilt":
            return self.tem.getStage()

    def layout(self):
        h = QHBoxLayout()
        if self.merlin is not None:
            h.addWidget(self.camera.SettingGUI())
        h.addWidget(self.tem.SettingGUI())

        w = QWidget()
        w.setLayout(h)
        return w

    def _setParams(self, dic):
        pass

    def _closed(self):
        HardwareInterface.killAll()
        self.tem = None


def _makeMenu():
    from lys import glb
    if glb.mainWindow() is not None:
        menu = glb.mainWindow().menuBar()
        calc = menu.addMenu('Measurements')

        act = calc.addAction("UED/UEM")
        act.triggered.connect(gin.init)


gin = GlobalInitializer()
_makeMenu()
