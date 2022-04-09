import logging
import os

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from lys.widgets import LysSubWindow

from PythonHardwares.SingleMotor import SingleMotorGUI
from PythonHardwares.Camera import CameraGUI
from PythonHardwares.Switch import SwitchGUI
from PythonHardwares.Stage import StageGUI

from .DataStorage import DataStorage, DataStorageGUI
from .AutoTabs import *


class fsTEMMain(LysSubWindow):
    _path = ".lys/fsTEM/settings.dic"
    tagRequest = pyqtSignal(dict)

    def __init__(self, root, hardwares, lay_others):
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
        self.__initlayout(hardwares, lay_others)
        self.restoreSettings(self._path)
        self.closed.connect(lambda: self.saveSettings(self._path))
        self.camera.aquireFinished.connect(self._data.saveImage)
        print("[fsTEM] Hardwares initialized. Data are storaged in", root)
        self.adjustSize()

    def __initlayout(self, hardwares, lay_other):
        tab = QTabWidget()
        tab.addTab(self.__laserTab(hardwares), "Laser")
        tab.addTab(StageGUI(hardwares["Stage"], "Stage"), "Stage")
        tab.addTab(lay_other, "Other")

        v1 = QVBoxLayout()
        self.__data = DataStorageGUI(self._data)
        v1.addWidget(self.__data)
        v1.addWidget(tab)

        h1 = QHBoxLayout()
        h1.addLayout(v1)
        h1.addWidget(CameraGUI(hardwares["Camera"], 'TEM Image'))

        wid = QWidget()
        wid.setLayout(h1)

        tab = QTabWidget()
        tab.addTab(wid, 'Fundamentals')
        #tab.addTab(AutoTab(self.delay, self.camera, self.power, self.tem, self.pumpsw, self.tem), 'Auto')
        self.setWidget(tab)

    def __laserTab(self, hardwares):
        g = QGridLayout()
        g.addWidget(SingleMotorGUI(hardwares["Delay Stage"], 'Delay Stage'), 0, 0)
        g.addWidget(SingleMotorGUI(hardwares["Pump Power"], 'Pump power'), 1, 0)
        g.addWidget(SingleMotorGUI(hardwares["Probe Power"], 'Probe power'), 1, 1)
        g.addWidget(SwitchGUI(hardwares["Pump Shutter"], 'Pump on/off'), 2, 0)
        g.addWidget(SwitchGUI(hardwares["Probe Shutter"], 'Probe on/off'), 2, 1)
        g.setColumnStretch(0, 1)
        g.setColumnStretch(1, 1)
        w = QWidget()
        w.setLayout(g)
        return w


class AutoTab(QWidget):
    class _Model(QStandardItemModel):
        def __init__(self):
            super().__init__(0, 2)
            self.setHeaderData(0, Qt.Horizontal, 'Order')
            self.setHeaderData(1, Qt.Horizontal, 'Parameters')

    def __init__(self, delay, camera, power, stage, pumpsw, tem):
        super().__init__()
        self.delay = delay
        self.camera = camera
        self.power = power
        self.stage = stage
        self.pumpsw = pumpsw
        self.tem = tem
        self.__initlayout()

    def __initlayout(self):
        l = QHBoxLayout()

        tab = QTabWidget()
        tab.addTab(ScanTab(callback=self.addOrder), 'Scan')
        tab.addTab(ParamsTab(tem=self.tem, callback=self.addOrder), 'Params')
        tab.addTab(StageTab(stage=self.stage, callback=self.addOrder), 'Stage')
        tab.addTab(PhaseDiagramTab(callback=self.addOrder), 'PhaseDiagram')

        lh1 = QHBoxLayout()
        self.__start = QPushButton('Start', clicked=self.__startscan)
        self.__stop = QPushButton('Stop')
        lh1.addWidget(self.__start)
        lh1.addWidget(self.__stop)

        lv2 = QVBoxLayout()
        lv2.addWidget(tab)
        lv2.addLayout(lh1)

        self.__tree = self.__treeview()
        l.addLayout(lv2)
        l.addWidget(self.__tree)
        self.setLayout(l)

    def __treeview(self):
        tree = QTreeView()
        tree.setDragDropMode(QAbstractItemView.InternalMove)
        tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(self.buildContextMenu)
        tree.setDropIndicatorShown(True)
        self.__model = self._Model()
        tree.setModel(self.__model)
        return tree

    def buildContextMenu(self, qPoint):
        menu = QMenu(self)
        menulabels = ['New Group', 'Delete']
        actionlist = []
        for label in menulabels:
            actionlist.append(menu.addAction(label))
        action = menu.exec_(QCursor.pos())
        if action == None:
            return
        elif action.text() == 'New Group':
            self.addOrder('NewGroup', {})
        elif action.text() == 'Delete':
            indexes = self.__tree.selectedIndexes()
            for i in reversed(indexes):
                row = i.row()
                col = i.column()
                if col == 0:
                    self.__model.removeRow(row)

    def addOrder(self, name, dic):
        size = self.__model.rowCount()
        self.__model.setItem(size, 0, QStandardItem(name))
        self.__model.setItem(size, 1, QStandardItem(str(dic)))

    def __construct(self, res, obj1, obj2):
        res.append(dict(Order=obj1.text(), Params=obj2.text()))
        for i in range(obj1.rowCount()):
            self.__construct(res, obj1.child(i, 0), obj1.child(i, 1))

    def __startscan(self):
        size = self.__model.rowCount()
        selm = self.__tree.selectionModel()
        res = []
        for i in range(size):
            index0 = self.__model.index(i, 0)
            index1 = self.__model.index(i, 1)
            obj1 = self.__model.itemFromIndex(index0)
            obj2 = self.__model.itemFromIndex(index1)
            self.__construct(res, obj1, obj2)
        self.exe = OrderExecutor(
            res, self.camera, self.delay, self.power, self.stage, self.pumpsw, self.tem)
        self.exe.updated.connect(self.OnUpdate)
        self.exe.finished.connect(self.OnFinished)
        self.__start.setEnabled(False)
        self.__stop.clicked.connect(self.exe.kill)
        self.exe.start()

    def OnFinished(self):
        self.__stop.clicked.disconnect(self.exe.kill)
        self.__start.setEnabled(True)

    def __findIndex(self, obj, sum, number):
        for i in range(obj.rowCount()):
            if sum == number:
                return (obj.child(i, 0), obj.child(i, 1))
            sum += 1
            res = self.__findIndex(obj.child(i, 0), sum, number)
            if isinstance(res, int):
                sum = res
            else:
                return res
        return sum

    def OnUpdate(self, number):
        selm = self.__tree.selectionModel()
        selm.clearSelection()
        sum = 0
        obj = self.__findIndex(self.__model.invisibleRootItem(), sum, number)
        selm.select(obj[0].index(), QItemSelectionModel.Select)
        selm.select(obj[1].index(), QItemSelectionModel.Select)


class OrderExecutor(QThread):
    updated = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, order, camera, delay, power, stage, pumpsw, tem):
        super().__init__()
        self.stopped = False
        self.delay = delay
        self.camera = camera
        self.power = power
        self.mutex = QMutex()
        self.order = order
        self.stage = stage
        self.pumpsw = pumpsw
        self.tem = tem

    def run(self):
        n = 0
        for o in self.order:
            if self.stopped:
                self.finished.emit()
                return
            self.updated.emit(n)
            n += 1
            self.execute(o)
        self.finished.emit()

    def kill(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

    def execute(self, order):
        # print(order)
        if order['Order'] == 'Scan':
            self.scan(eval(order['Params']))
        if order['Order'] == 'Power':
            self.changePower(eval(order['Params']))
        if order['Order'] == 'StagePosition':
            self.stagePosition(eval(order['Params']))
        if order['Order'] == 'Defocus':
            self.defocus(eval(order['Params']))
        if order['Order'] == 'Magnification':
            self.magnify(eval(order['Params']))

    def scan(self, params):
        logging.info('[AutoTab.OrderExecutor] Selecting scan type.')
        if params['Scan type'] == 'Delay':
            self.scan_delay(params)
        if params['Scan type'] == 'Focus':
            self.scan_focus(params)
        elif params['Scan type'] == 'Power':
            self.scan_power(params)
        elif params['Scan type'] in ["Stage X", "Stage Y", "Stage Z", "Stage Alpha", "Stage Beta"]:
            self.scan_stage(params)

    def scan_delay(self, params):
        logging.info('[AutoTab.OrderExecutor] Start scan (delay).')
        d = self.delay
        c = self.camera
        delay = self.delay.get()
        start = params['From']
        for i in range(params['Loop']):
            if self.stopped:
                c.stop()
                return
            if params['RefType'] == 'Delay':
                self.setDelay(d, params['RefValue'])
                self.aquire(c, params['Name'] + str(i), params['Exposure'], params['Folder'] + '\\probe', params['Scan type'])
            self.setDelay(d, start + i * params['Step'])
            self.aquire(c, params['Name'] + str(i), params['Exposure'], params['Folder'] + '\\pump', params['Scan type'])
        logging.info('[AutoTab.OrderExecutor] Finish scan.')

    def scan_focus(self, params):
        logging.info('[AutoTab.OrderExecutor] Start scan (focus).')
        d = self.delay
        c = self.camera
        delay = self.delay.get()
        start = params['From']
        for i in range(params['Loop']):
            if self.stopped:
                c.stop()
                return
            if params['RefType'] == 'Delay':
                self.setDelay(d, params['RefValue'])
                self.aquire(c, params['Name'] + str(i), params['Exposure'],
                            params['Folder'] + '\\probe', params['Scan type'])
                self.setDelay(d, delay)
            self.tem.setDefocus(start + i * params['Step'])
            self.aquire(c, params['Name'] + str(i), params['Exposure'],
                        params['Folder'] + '\\pump', params['Scan type'])
        logging.info('[AutoTab.OrderExecutor] Finish scan.')

    def scan_stage(self, params):
        logging.info('[AutoTab.OrderExecutor] Start scan.')
        if params['Scan type'] == 'Stage X':
            axis = "x"
        if params['Scan type'] == 'Stage Y':
            axis = "y"
        if params['Scan type'] == 'Stage Z':
            axis = "z"
        if params['Scan type'] == 'Stage Alpha':
            axis = "a"
        if params['Scan type'] == 'Stage Beta':
            axis = "b"
        delay = self.delay.get()
        start = params['From']
        for i in range(params['Loop']):
            if self.stopped:
                return
            self.stage.setPosition(axis, start + i * params['Step'])
            if params['RefType'] == 'Delay':
                self.setDelay(self.delay, params['RefValue'])
                self.aquire(self.camera, params['Name'] + str(
                    i), params['Exposure'], params['Folder'] + '\\probe', params['Scan type'])
            self.setDelay(self.delay, delay)
            self.aquire(self.camera, params['Name'] + str(
                i), params['Exposure'], params['Folder'] + '\\pump', params['Scan type'])
        logging.info('[AutoTab.OrderExecutor] Finish scan.')

    def scan_power(self, params, rev=True):
        logging.info('[AutoTab.OrderExecutor] Start scan.')
        d = self.power
        c = self.camera
        delay = self.delay.get()
        start = params['From']
        for i in range(params['Loop']):
            if self.stopped:
                return
            self.setDelay(self.power, start + i * params['Step'])
            if params['RefType'] == 'Delay':
                self.setDelay(self.delay, params['RefValue'])
                self.aquire(c, params['Name'] + str(i), params['Exposure'],
                            params['Folder'] + '\\probe', params['Scan type'])
                self.setDelay(self.delay, delay)
            self.aquire(c, params['Name'] + str(i), params['Exposure'],
                        params['Folder'] + '\\pump', params['Scan type'])
        if rev:
            for i in range(params['Loop']):
                if self.stopped:
                    return
                self.setDelay(self.power, start +
                              (params['Loop'] - i - 1) * params['Step'])
                if params['RefType'] == 'Delay':
                    self.setDelay(self.delay, params['RefValue'])
                    self.aquire(c, params['Name'] + str(params['Loop'] + i),
                                params['Exposure'], params['Folder'] + '\\probe', params['Scan type'])
                self.setDelay(self.delay, delay)
                self.aquire(c, params['Name'] + str(params['Loop'] + i),
                            params['Exposure'], params['Folder'] + '\\pump', params['Scan type'])
        logging.info('[AutoTab.OrderExecutor] Finish scan.')

    def changePower(self, params):
        logging.info('[AutoTab.OrderExecutor] Start power.')
        self.setDelay(self.power, params['Value'])
        logging.info('[AutoTab.OrderExecutor] Finish scan.')

    def setDelay(self, obj, delay):
        logging.debug('[AutoTab.OrderExecutor] Start setDelay')
        while not obj.set(delay):
            logging.warning('[AutoTab.OrderExecutor] Error on setDelay. Try agatin.')
        obj.waitForReady()
        logging.debug('[AutoTab.OrderExecutor] Finish setDelay')

    def defocus(self, params):
        self.tem.setDefocus(params['Value'])

    def magnify(self, params):
        self.tem.setMagnification(params['Value'])

    def aquire(self, obj, name, time, folder, mode='Unknown'):
        logging.info('[AutoTab.OrderExecutor] Start aquire')
        obj.setTime(time)
        while not obj.setFolder(folder):
            logging.warning('[AutoTab.OrderExecutor] Error on setFolder. Try again.')
        obj.startAquire(name)
        logging.info('[AutoTab.OrderExecutor] Wait for Camera ready')
        obj.waitForReady()
        logging.info('[AutoTab.OrderExecutor] Finish aquire')

    def stagePosition(self, params):
        for key in params.keys():
            self.stage.setPosition(key, params[key])
