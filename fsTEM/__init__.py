from tokenize import Single
from lys.Qt import QtWidgets
from PythonHardwares.Hardwares.OptoSigma.RMC102 import RMC102

from PythonHardwares.Interfaces import HardwareInterface
from PythonHardwares import Dummy

from PythonHardwares.SingleMotor import SingleMotorGUI
from PythonHardwares.Hardwares.FEI.TecnaiFemto import TecnaiFemto
from .Initializer import initialize
from .DriftCorrection import DriftCorrector, DriftCorrectionGUI
from .AdvancedCorrection import AdvancedCorrector, AdvancedCorrectionGUI

root = "\\\\192.168.12.203\\smb\\data2\\"
# root = home() + "/data"

dic = {
    "Camera": ["Merlin", "Digital Micrograph", "EELS map", "DummyCamera"],
    "Delay Stage": ["fs-fs", "fs-ns", "ns-ns", "fs-pump2", "ns-current", "DummyDelay"],
    "Pump Power": ["Pump1.Power", "Pump2.Power", "Pump Voltage", "DummyPump"],
    "Probe Power": ["Probe.Power", "DummyProbe"],
    "Probe Align": ["Probe.Align", "DummyProbe"],
    "Pump Shutter": ["Pump1", "Pump2", "DummySwitch"],
    "Probe Shutter": ["Probe", "DummySwitch"],
    "Stage": ["SingleTilt", "DoubleTilt", "DummyStage"]}


class GlobalInitializer:
    def __init__(self):
        self._tem = None
        self._merlin = None
        self._eels = None
        self._rmc = None
        self._info = None
        self._dg645 = None

    def init(self):
        self._tem = TecnaiFemto('192.168.12.210', '192.168.12.201', 7000, 7001)
        self._info = self._tem.getInfo()
        self._drift = DriftCorrector(self._tem)
        self._advanced = AdvancedCorrector(self._tem)

        gui = initialize(root, dic, self._generate, self._layout, self._scan)
        if gui is None:
            return
        gui.tagRequest.connect(self._setParams)
        gui.closed.connect(self._closed)
        self._drift.setCamera(gui._camera)

    def _generate(self, instr):
        if instr is None:
            return None
        elif instr == "Merlin":
            from PythonHardwares.Hardwares.QuantumDetector.MerlinEM import TEMCamera
            self._merlin = TEMCamera("Merlin", '192.168.12.206', info=self._info, tem=self._tem, stem=self._tem.getSTEM())
            return self._merlin
        elif instr == 'Digital Micrograph':
            return self._tem.getCamera()
        elif instr == 'EELS map':
            self._eels = self._tem.getEELSMap()
            return self._eels
        elif instr == 'DummyCamera':
            return Dummy.CameraDummy()
        elif instr == 'fs-fs':
            from PythonHardwares.Hardwares.Soloist.SoloistHLE import SoloistHLE
            return SoloistHLE('192.168.12.202', 8000)
        elif instr == 'fs-ns':
            from PythonHardwares.Hardwares.SRS.DG645 import DG645
            return DG645('192.168.12.204', mode='fs', frequency=25000)
        elif instr == 'ns-ns':
            from PythonHardwares.Hardwares.SRS.DG645 import DG645
            return DG645('192.168.12.204', mode='ns')
        elif instr == 'ns-current':
            if self._dg645 is None:
                from PythonHardwares.Hardwares.SRS.DG645 import DG645
                self._dg645 = DG645('192.168.12.204', mode='current')
            return self._dg645
        elif instr == 'DummyDelay':
            from PythonHardwares.SingleMotor import SingleMotorDummy
            return SingleMotorDummy()
        elif instr == "DummyPump":
            from PythonHardwares.SingleMotor import SingleMotorDummy
            return SingleMotorDummy()
        elif instr == "DummyProbe":
            from PythonHardwares.SingleMotor import SingleMotorDummy
            return SingleMotorDummy()
        elif instr == "Pump2.Power":
            from PythonHardwares.Hardwares.OptoSigma.GSC02 import GSC02
            return GSC02('COM3', channel=2)
        elif instr == "Probe.Power":
            from PythonHardwares.Hardwares.OptoSigma.GSC02 import GSC02
            return GSC02('COM3', channel=1)
        elif instr == "fs-pump2":
            from PythonHardwares.Hardwares.OptoSigma.SHOT702H import SHOT702H
            return SHOT702H('COM4', channel=1, rate=15, offset=0, max=100000000, min=-100000000)
        elif instr == "SC10":
            from PythonHardwares.Hardwares.Thorlabs.SC10 import SC10
            return SC10('COM4')
        elif instr == "Pump1":
            from PythonHardwares.Hardwares.Thorlabs import KSC101
            return KSC101('68001089')
        elif instr == "Pump2":
            from PythonHardwares.Hardwares.Thorlabs import KSC101
            return KSC101('68001101')
        elif instr == "Pump Voltage":
            if self._dg645 is None:
                from PythonHardwares.Hardwares.SRS.DG645 import DG645
                self._dg645 = DG645('192.168.12.204', mode='current')
            return self._dg645.getPumpVoltageModule()
        elif instr == "Probe":
            from PythonHardwares.Hardwares.Thorlabs import KSC101
            return KSC101('68001109')
        elif instr == "Pump1.Power":
            from PythonHardwares.Hardwares.Thorlabs import K10CR1
            return K10CR1('55273464', offset=0)
        elif instr == "DummySwitch":
            from PythonHardwares.Switch import SwitchDummy
            return SwitchDummy()
        elif instr == "DummyStage":
            from PythonHardwares.Stage import StageDummy
            return StageDummy()
        elif instr == "SingleTilt":
            return self._tem.getStage()
        elif instr == "Probe.Align":
            self._rmc = RMC102('COM12', channel=1), RMC102('COM12', channel=2)
            return self._rmc

    def _layout(self):
        d = {}
        if self._tem is not None:
            d["TEM"] = self._tem.getWidget()
        if self._merlin is not None:
            self._merlin.setDrift(self._drift)
            d["Merlin"] = self._merlin.SettingGUI()
        if self._eels is not None:
            d["EELS"] = self._eels.SettingGUI()
        if self._drift is not None:
            d["Drift"] = DriftCorrectionGUI(self._drift)
        if self._advanced is not None:
            d["Advanced Correction"] = AdvancedCorrectionGUI(self._advanced)
        if self._rmc is not None:
            w1 = SingleMotorGUI(self._rmc[0], 'Laser x')
            w2 = SingleMotorGUI(self._rmc[1], 'Laser y')

            v2 = QtWidgets.QVBoxLayout()
            v2.addWidget(w1)
            v2.addWidget(w2)
            v2.addStretch()

            w = QtWidgets.QWidget()
            w.setLayout(v2)
            d["LaserPos"] = w
        if self._dg645 is not None:
            from PythonHardwares.Hardwares.SRS.DG645 import DG645GUI
            gui = DG645GUI(self._dg645)
            d["Delay Gen."] = gui
        return d

    def _scan(self):
        if self._info is not None:
            return self._info.getScan()

    def _setParams(self, dic):
        if self._info is not None:
            dic["TEM"] = self._info.get()

    def _closed(self):
        HardwareInterface.killAll()
        self._tem = None
        self._rmc = None


def _makeMenu():
    from lys import glb
    if glb.mainWindow() is not None:
        menu = glb.mainWindow().menuBar()
        calc = menu.addMenu('Measurements')

        act = calc.addAction("UED/UEM")
        act.triggered.connect(gin.init)


gin = GlobalInitializer()
_makeMenu()
