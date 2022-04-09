from PyQt5.QtWidgets import QHBoxLayout, QWidget
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
    "Stage": ["DummyStage"]}


class GlobalInitializer:
    def __init__(self):
        from PythonHardwares.Hardwares.FEI.TechnaiFemto import TechnaiFemto
        self.tem = TechnaiFemto('192.168.12.210', '192.168.12.201', 7000, 7001)

    def init(self):
        initialize(root, dic, self.generate, self.layout)

    def generate(self, instr):
        if instr is None:
            return None
        elif instr == "Merlin":
            from PythonHardwares.Hardwares.QuantumDetector.MerlinEM import MerlinEM
            self.camera = MerlinEM('192.168.12.206', stem=self.tem.getSTEM())
            return self.camera
        elif instr == 'Digital Micrograph':
            self.camera = self.tem.getCamera()
            return self.camera
        elif instr == 'DummyCamera':
            from PythonHardwares.Camera import CameraDummy
            self.camera = CameraDummy()
            return self.camera
        elif instr == 'fs-fs':
            from PythonHardwares.Hardwares.Soloist.SoloistHLE import SoloistHLE
            self.delay = SoloistHLE('192.168.12.202', 8000)
            return self.delay
        elif instr == 'fs-ns':
            from PythonHardwares.Hardwares.SRS.DG645 import DG645
            self.delay = DG645('192.168.12.204', mode='fs', frequency=25000)
            return self.delay
        elif instr == 'ns-ns':
            from PythonHardwares.Hardwares.SRS.DG645 import DG645
            self.delay = DG645('192.168.12.204', mode='ns')
            return self.delay
        elif instr == 'DummyDelay':
            from PythonHardwares.SingleMotor import SingleMotorDummy
            self.delay = SingleMotorDummy()
            return self.delay
        elif instr == "DummyPump":
            from PythonHardwares.SingleMotor import SingleMotorDummy
            self.pump = SingleMotorDummy()
            return self.pump
        elif instr == "DummyProbe":
            from PythonHardwares.SingleMotor import SingleMotorDummy
            self.probe = SingleMotorDummy()
            return self.probe
        elif instr == "GSC02":
            from PythonHardwares.Hardwares.OptoSigma.GSC02 import GSC02
            self.pump = GSC02('COM3')
            return self.pump
        elif instr == "SC10":
            from PythonHardwares.Hardwares.Thorlabs.SC10 import SC10
            return SC10('COM4')
        elif instr == "DummySwitch":
            from PythonHardwares.Switch import SwitchDummy
            return SwitchDummy()
        elif instr == "DummyStage":
            from PythonHardwares.Stage import StageDummy
            return StageDummy()

    def layout(self):
        h = QHBoxLayout()
        h.addWidget(self.camera.SettingGUI())
        h.addWidget(self.tem.SettingGUI())

        w = QWidget()
        w.setLayout(h)
        return w

    def _setParams(self, dic):
        d = self.delay.get()
        p = self.pump.get()
        dic["delay"] = d
        dic["power"] = p
        dic["Laser:delay"] = d
        dic["Laser:power"] = p


def _makeMenu():
    from lys import glb
    if glb.mainWindow() is not None:
        menu = glb.mainWindow().menuBar()
        calc = menu.addMenu('Measurements')

        act = calc.addAction("UED/UEM")
        act.triggered.connect(gin.init)


gin = GlobalInitializer()
_makeMenu()
