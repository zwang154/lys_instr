import os
import numpy as np

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QGridLayout, QDoubleSpinBox, QLabel, QComboBox
from PyQt5.QtCore import pyqtSignal, QObject

from lys import glb
from lys.widgets import LysSubWindow

from PythonHardwares.SingleMotor import SingleMotorGUI
from PythonHardwares.Camera import CameraGUI
from PythonHardwares.Switch import SwitchGUI
from PythonHardwares.Stage import StageGUI

from .DataStorage import DataStorage, DataStorageGUI
from .Scan import ScanTab


class fsTEMMain(LysSubWindow):
    _path = ".lys/fsTEM/settings.dic"
    tagRequest = pyqtSignal(dict)

    def __init__(self, root, hardwares, wid_others={}, scans={}):
        super().__init__()
        self.setWindowTitle("Ultrafast Electron Diffraction/Microscopy Measurements")
        os.makedirs(".lys/fsTEM", exist_ok=True)

        self.delay = hardwares["Delay Stage"]
        self.probe = hardwares["Probe Power"]
        self.power = hardwares["Pump Power"]
        self.camera = hardwares["Camera"]
        self.pumpsw = hardwares["Pump Shutter"]
        self.probesw = hardwares["Probe Shutter"]
        self.stage = hardwares["Stage"]

        self._data = DataStorage(root)
        self._data.tagRequest.connect(self.tagRequest)
        self._data.tagRequest.connect(self._setParams)
        self.__initlayout(hardwares, wid_others, scans)
        self.restoreSettings(self._path)
        self.closed.connect(lambda: self.saveSettings(self._path))
        glb.mainWindow().closed.connect(lambda: self.saveSettings(self._path))
        self.camera.aquireStarted.connect(self._data.reserve)
        self.camera.aquireFinished.connect(self._data.saveImage)
        print("[fsTEM] Hardwares initialized. Data are storaged in", root)
        self.adjustSize()

    def __initlayout(self, hardwares, lay_other, scan_other):
        scan = {"delay": self.delay, "pump": self.power, "probe": self.probe}
        scan.update(self.stage.getScans())
        scan.update(scan_other)
        proc = {"Camera": RefCameraWidget(self.camera, self.delay)}
        self._scan = ScanTab(self._data, scan, proc)
        tab = QTabWidget()
        tab.addTab(self.__laserTab(hardwares), "Laser")
        stage = StageGUI(hardwares["Stage"], "Stage")
        tab.addTab(self.__wrapWidget(stage), "Stage")
        for key, widget in lay_other.items():
            tab.addTab(widget, key)
        tab.addTab(self._scan, "Scan")

        v1 = QVBoxLayout()
        self.__data = DataStorageGUI(self._data)
        v1.addWidget(self.__data)
        v1.addWidget(tab)

        h1 = QHBoxLayout()
        h1.addLayout(v1)
        cgui = CameraGUI(hardwares["Camera"], 'TEM Image')
        cgui.continuous.connect(lambda b: self._data.setEnabled(not b))
        h1.addWidget(cgui)

        wid = QWidget()
        wid.setLayout(h1)
        self.setWidget(wid)

    def __wrapWidget(self, w, layout=False):
        v = QVBoxLayout()
        if layout:
            v.addLayout(w)
        else:
            v.addWidget(w)
        v.addStretch()
        wid = QWidget()
        wid.setLayout(v)
        return wid

    def __laserTab(self, hardwares):
        g = QGridLayout()
        g.addWidget(SingleMotorGUI(hardwares["Delay Stage"], 'Delay Stage'), 0, 0)
        g.addWidget(SingleMotorGUI(hardwares["Pump Power"], 'Pump power'), 1, 0)
        g.addWidget(SingleMotorGUI(hardwares["Probe Power"], 'Probe power'), 1, 1)
        g.addWidget(SwitchGUI(hardwares["Pump Shutter"], 'Pump on/off'), 2, 0)
        g.addWidget(SwitchGUI(hardwares["Probe Shutter"], 'Probe on/off'), 2, 1)
        g.setColumnStretch(0, 1)
        g.setColumnStretch(1, 1)

        return self.__wrapWidget(g, layout=True)

    def _setParams(self, dic):
        dic["delay"] = self.delay.get()
        dic["power"] = self.power.get()
        dic["stage"] = tuple(self.stage.get())


class RefCameraProcess(QObject):
    updated = pyqtSignal(str)

    def __init__(self, camera, exposure, delay=None, reference=None):
        super().__init__()
        self._camera = camera
        self._delay = delay
        self._exposure = exposure
        self._reference = reference

    def execute(self, storage):
        folder = storage.getFolder()
        storage.setFolder(folder + "/pump")
        self.updated.emit("Aquiring pump image: " + storage.getFilename())
        self._camera.startAquire(self._exposure, wait=True)
        if self._reference is not None:
            storage.setFolder(folder + "/probe")
            self.updated.emit("Going to reference delay")
            self._delay.set(self._reference, wait=True)
            self.updated.emit("Aquiring reference image: " + storage.getFilename())
            self._camera.startAquire(self._exposure, wait=True)
        self.updated.emit("Going to next point")
        storage.setFolder(folder)

    def stop(self):
        pass


class RefCameraWidget(QWidget):
    def __init__(self, camera, delay):
        super().__init__()
        self._camera = camera
        self._delay = delay
        self._exposure = QDoubleSpinBox(objectName="RefCamera_exposure")
        self._exposure.setRange(0, np.inf)
        self._exposure.setDecimals(4)

        self._refType = QComboBox(objectName="RefCamera_refType")
        self._refType.addItems(["None", "Delay"])
        self._refType.currentTextChanged.connect(lambda text: self._reference.setEnabled(text != "None"))

        self._reference = QDoubleSpinBox(objectName="RefCamera_reference")
        self._reference.setRange(-np.inf, np.inf)
        self._reference.setDecimals(4)
        self._reference.setEnabled(False)

        g = QGridLayout()
        g.addWidget(QLabel("Exposure (s)"), 0, 0)
        g.addWidget(QLabel("Reference"), 0, 1)
        g.addWidget(QLabel("Ref. Delay"), 0, 2)
        g.addWidget(self._exposure, 1, 0)
        g.addWidget(self._refType, 1, 1)
        g.addWidget(self._reference, 1, 2)

        self.setLayout(g)

    def getProcess(self):
        if self._refType.currentText() == "None":
            ref = None
        else:
            ref = self._reference.value()
        return RefCameraProcess(self._camera, self._exposure.value(), self._delay, ref)
