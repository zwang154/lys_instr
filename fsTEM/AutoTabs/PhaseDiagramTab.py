
import pyautogui

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class PhaseDiagramTab(QWidget):
    itemAdded = pyqtSignal(str, dict)

    def __init__(self, callback=None):
        super().__init__()
        gl1 = QVBoxLayout()

        self.__PD_add = QPushButton('Add', clicked=self.addPD)
        self.__PD_fold = QLineEdit()
        self.__PD_time = QDoubleSpinBox()
        self.__PD_mag = QSpinBox()

        gl1.addWidget(self.__PD_add)
        gl1.addWidget(QLabel('Folder'))
        gl1.addWidget(self.__PD_fold)
        gl1.addWidget(QLabel('Exposure time'))
        gl1.addWidget(self.__PD_time)
        gl1.addWidget(QLabel('Magnetic Field'))
        gl1.addWidget(self.__PD_mag)

        ldbtn = QPushButton('Load positions', clicked=self.__loadPositions)
        self._lolx = QSpinBox()
        self._lolx.setMaximum(1000000)
        self._loly = QSpinBox()
        self._loly.setMaximum(1000000)
        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel('Lorentz Button'))
        hbox1.addWidget(self._lolx)
        hbox1.addWidget(self._loly)

        self._magx = QSpinBox()
        self._magx.setMaximum(1000000)
        self._magy = QSpinBox()
        self._magy.setMaximum(1000000)
        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel('Multifunc Button'))
        hbox2.addWidget(self._magx)
        hbox2.addWidget(self._magy)

        gl1.addWidget(ldbtn)
        gl1.addLayout(hbox1)

        self.setLayout(gl1)
        if callback is not None:
            self.itemAdded.connect(callback)

    def addPD(self):
        print("This function is not valid at present. Please check source code.")
        #p = {}
        #self.itemAdded.emit('Power', p)

    def __loadPositions(self):
        QMessageBox.information(
            None, 'Info', "Move cursor on the \"Lorentz\" button of TEM User Interface and then press enter.")
        x, y = pyautogui.position()
        self._lolx.setValue(x)
        self._loly.setValue(y)
        QMessageBox.information(
            None, 'Info', "Move cursor on the \"Multifunc\" button of TEM Control Pads simulator and then press enter.")
        x, y = pyautogui.position()
        self._magx.setValue(x)
        self._magy.setValue(y)

    def phaseDiagram(self, sw, pow, cam):
        sw = self.pumpsw
        pow = self.power
        cam = self.camera
        plist = np.linspace(0, 1, 20)
        alist = np.arcsin(np.sqrt(plist))/2/np.pi*180
        sw.set(False)
        for j in range(self.__PD_mag.value()):
            print("--------------- step"+str(j)+" ---------------")
            for i, a in enumerate(alist):
                #QMessageBox.information(None, 'Info', "Reset magnetic field.")
                pyautogui.click(self._lolx.value(), self._loly.value())
                time.sleep(2)
                pyautogui.click(self._lolx.value(), self._loly.value())
                time.sleep(4)
                print('Magnetic field was reset by Lorentz-TEM-Lorentz mode changes.')
                pow.set(a)
                print('Angle was set to ', a)
                sw.set(True)
                print('Shutter opened. Wait 10 seconds.')
                cam.insertCamera()
                time.sleep(10)
                print('Start aquiring (pump)')
                self.aquire(cam, 'data_Mag'+str(j)+'_Pump'+str(i),
                            self.__PD_time.value(), self.__PD_fold.text()+'/pump')
                time.sleep(self.__PD_time.value()+2)
                sw.set(False)
                print('Shutter closed. Wait 10 seconds.')
                cam.insertCamera()
                time.sleep(10)
                print('Start aquiring (nopump)')
                self.aquire(cam, 'data_Mag'+str(j)+'_Pump'+str(i),
                            self.__PD_time.value(), self.__PD_fold.text()+'/probe')
                time.sleep(self.__PD_time.value()+2)
            pyautogui.click(self._magx.value(), self._magy.value())
            print('Magnetic field was changed.')
            time.sleep(2)
        QMessageBox.information(None, 'Info', "Finished.")

    def aquire(self, obj, name, time, folder, mode='Unknown'):
        logging.debug('[AutoTab.OrderExecutor] Start aquire')
        try:
            obj.setTime(time)
            obj.setTag('mode', mode)
            obj.setTag("Laser:delay", self.delay.get())
            obj.setTag("Laser:power", self.power.get())
            while not obj.setFolder(folder):
                pass
            obj.startAquire(name)
            # obj.waitForReady()
        except:
            self.aquire(obj, name, time, folder)
