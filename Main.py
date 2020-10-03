import logging,time,pyautogui
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from ExtendAnalysis.AnalysisWindow import AnalysisWindow
import ExtendAnalysis.MainWindow as main
from ..PythonHardwares.SingleMotor import *
from ..PythonHardwares.Switch import *
from ..PythonHardwares.Camera import *
from ..PythonHardwares.Hardwares.Soloist.SoloistHLE import SoloistHLE
from ..PythonHardwares.Hardwares.OptoSigma.GSC02 import GSC02
from ..PythonHardwares.Hardwares.SRS.DG645 import DG645
from ..PythonHardwares.Hardwares.FEI.TechnaiFemto import TechnaiFemto
from ..PythonHardwares.Hardwares.QuantumDetector.MerlinEM import MerlinEM
from ..PythonHardwares.Hardwares.Thorlabs.SC10 import SC10

class fsTEMMain(AnalysisWindow):
    def __init__(self):
        super().__init__(title="Ultrafast Electron Diffraction/Microscopy Measurements")
        self.__initHardware()
        self.__initlayout()
        self.adjustSize()
    def __initHardware(self):
        self.delay=SoloistHLE('192.168.12.202',8000)
        #self.delay=DG645('192.168.12.204',mode='ns')
        #self.delay=SingleMotorDummy()

        self.power=GSC02('COM3')
        #self.power=SingleMotorDummy()

        self.tem=TechnaiFemto('192.168.12.201',7000,7001)
        #self.camera=self.tem
        self.camera=MerlinEM('192.168.12.206', mode = 'STEM', tem = self.tem)
        #self.camera=CameraDummy()

        self.pumpsw=SC10('COM4')
        #self.pumpsw=SwitchDummy()

        self.camera.setBeforeAquireCallback(self.beforeAquire)
        print("Hardwares initialized."+str(self.tem.getCameraLength()))
    def __initlayout(self):
        tab=QTabWidget()
        l=QHBoxLayout()
        lv=QVBoxLayout()
        lv.addWidget(SingleMotorGUI(self.delay,'Delay Stage'))
        lv.addWidget(SingleMotorGUI(self.power,'Pump power'))
        lv.addWidget(SwitchGUI(self.pumpsw,'Pump on/off'))
        lv.addWidget(self.camera.SettingGUI())
        lv.addWidget(self.tem.SettingGUI())
        lv.addWidget(QPushButton("STEM Test",clicked=self.STEMTest))
        l.addLayout(lv)
        l.addWidget(CameraGUI(self.camera,'TEM Image'))
        wid=QWidget()
        wid.setLayout(l)
        tab.addTab(wid,'Fundamentals')
        tab.addTab(AutoTab(self.delay,self.camera,self.power,self.camera,self.pumpsw,self.tem),'Auto')
        self.setWidget(tab)
        print("GUIs initialized.")
    def beforeAquire(self,obj):
        obj.setTag("delay",self.delay.get())
        obj.setTag("power",self.power.get())
        #obj.setTag("magnification", self.tem.getMagnification())
        obj.setTag("cameraLength", self.tem.getCameraLength())
    def STEMTest(self):
        self.tem.stopSI()
class AutoTab(QWidget):
    class _Model(QStandardItemModel):
        def __init__(self):
            super().__init__(0,2)
            self.setHeaderData(0,Qt.Horizontal,'Order')
            self.setHeaderData(1,Qt.Horizontal,'Parameters')
    class OrderExecutor(QThread):
        updated=pyqtSignal(int)
        finished=pyqtSignal()
        def __init__(self,order,camera,delay,power,stage,pumpsw,tem):
            super().__init__()
            self.stopped=False
            self.delay=delay
            self.camera=camera
            self.power=power
            self.mutex=QMutex()
            self.order=order
            self.stage=stage
            self.pumpsw=pumpsw
            self.tem=tem
        def run(self):
            n=0
            for o in self.order:
                if self.stopped:
                    self.finished.emit()
                    return
                self.updated.emit(n)
                n+=1
                self.execute(o)
            self.finished.emit()
        def kill(self):
            with QMutexLocker( self.mutex ):
                self.stopped = True
        def execute(self,order):
            #print(order)
            if order['Order']=='Scan':
                self.scan(eval(order['Params']))
            if order['Order']=='Power':
                self.changePower(eval(order['Params']))
            if order['Order']=='StagePosition':
                self.stagePosition(eval(order['Params']))
            if order['Order']=='Defocus':
                self.defocus(eval(order['Params']))
            if order['Order']=='Magnification':
                self.magnify(eval(order['Params']))
        def scan(self,params):
            logging.info('[AutoTab.OrderExecutor] Start scan.')
            if params['Scan type']=='Delay':
                self.scan_delay(params)
            elif params['Scan type']=='Power':
                self.scan_power(params)
            elif params['Scan type'] in ["Stage X","Stage Y","Stage Z","Stage Alpha","Stage Beta"]:
                self.scan_stage(params)
        def scan_delay(self,params):
            logging.info('[AutoTab.OrderExecutor] Start scan.')
            d=self.delay
            c=self.camera
            delay=self.delay.get()
            start=params['From']
            for i in range(params['Loop']):
                if self.stopped:
                    c.stop()
                    return
                if params['RefType']=='Delay':
                    self.setDelay(d,params['RefValue'])
                    self.aquire(c,params['Name']+str(i),params['Exposure'],params['Folder']+'\\probe',params['Scan type'])
                self.setDelay(d,start+(i+1)*params['Step'])
                self.aquire(c,params['Name']+str(i),params['Exposure'],params['Folder']+'\\pump',params['Scan type'])
            logging.info('[AutoTab.OrderExecutor] Finish scan.')
        def scan_stage(self,params):
            logging.info('[AutoTab.OrderExecutor] Start scan.')
            if params['Scan type']=='Stage X':
                axis="x"
            if params['Scan type']=='Stage Y':
                axis="y"
            if params['Scan type']=='Stage Z':
                axis="z"
            if params['Scan type']=='Stage Alpha':
                axis="a"
            if params['Scan type']=='Stage Beta':
                axis="b"
            delay=self.delay.get()
            start=params['From']
            for i in range(params['Loop']):
                if self.stopped:
                    return
                self.stage.setPosition(axis,start+i*params['Step'])
                if params['RefType']=='Delay':
                    self.setDelay(self.delay,params['RefValue'])
                    self.aquire(self.camera,params['Name']+str(i),params['Exposure'],params['Folder']+'\\probe',params['Scan type'])
                self.setDelay(self.delay,delay)
                self.aquire(self.camera,params['Name']+str(i),params['Exposure'],params['Folder']+'\\pump',params['Scan type'])
            logging.info('[AutoTab.OrderExecutor] Finish scan.')
        def scan_power(self,params,rev=True):
            logging.info('[AutoTab.OrderExecutor] Start scan.')
            d=self.power
            c=self.camera
            delay=self.delay.get()
            start=params['From']
            for i in range(params['Loop']):
                if self.stopped:
                    return
                self.setDelay(self.power,start+i*params['Step'])
                if params['RefType']=='Delay':
                    self.setDelay(self.delay,params['RefValue'])
                    self.aquire(c,params['Name']+str(i),params['Exposure'],params['Folder']+'\\probe',params['Scan type'])
                self.setDelay(self.delay,delay)
                self.aquire(c,params['Name']+str(i),params['Exposure'],params['Folder']+'\\pump',params['Scan type'])
            if rev:
                for i in range(params['Loop']):
                    if self.stopped:
                        return
                    self.setDelay(self.power,start+(params['Loop']-i-1)*params['Step'])
                    if params['RefType']=='Delay':
                        self.setDelay(self.delay,params['RefValue'])
                        self.aquire(c,params['Name']+str(params['Loop']+i),params['Exposure'],params['Folder']+'\\probe',params['Scan type'])
                    self.setDelay(self.delay,delay)
                    self.aquire(c,params['Name']+str(params['Loop']+i),params['Exposure'],params['Folder']+'\\pump',params['Scan type'])
            logging.info('[AutoTab.OrderExecutor] Finish scan.')
        def changePower(self,params):
            logging.info('[AutoTab.OrderExecutor] Start power.')
            self.setDelay(self.power, params['Value'])
            logging.info('[AutoTab.OrderExecutor] Finish scan.')
        def setDelay(self,obj,delay):
            logging.debug('[AutoTab.OrderExecutor] Start setDelay')
            while not obj.set(delay):
                logging.warning('[AutoTab.OrderExecutor] Error on setDelay. Try agatin.')
            logging.debug('[AutoTab.OrderExecutor] setDelay middle')
            obj.waitForReady()
            logging.debug('[AutoTab.OrderExecutor] Finish setDelay')
        def defocus(self, params):
            self.tem.setDefocus(params['Value'])
        def magnify(self, params):
            self.tem.setMagnification(params['Value'])
        def aquire(self,obj,name,time,folder,mode='Unknown'):
            logging.debug('[AutoTab.OrderExecutor] Start aquire')
            try:
                obj.setTime(time)
                logging.debug('[AutoTab.OrderExecutor] set Time')
                obj.setTag('mode',mode)
                obj.setTag("Laser:delay",self.delay.get())
                obj.setTag("Laser:power",self.power.get())
                while not obj.setFolder(folder):
                    logging.warning('[AutoTab.OrderExecutor] Error on setFolder. Try again.')
                logging.debug('[AutoTab.OrderExecutor] set Folder finished')
                obj.startAquire(name)
                logging.debug('[AutoTab.OrderExecutor] start Aquire finished')
                obj.waitForReady()
            except:
                logging.warning('[AutoTab.OrderExecutor] Error on aquire. Try again.')
                self.aquire(obj,name,time,folder)
                logging.info('[AutoTab.OrderExecutor] aquire is normally finished in except section.')
            logging.debug('[AutoTab.OrderExecutor] Finish aquire')
        def stagePosition(self,params):
            for key in params.keys():
                self.stage.setPosition(key,params[key])

    def __init__(self,delay,camera,power,stage,pumpsw,tem):
        super().__init__()
        self.delay=delay
        self.camera=camera
        self.power=power
        self.stage=stage
        self.pumpsw=pumpsw
        self.tem=tem
        self.__initlayout()
    def __initlayout(self):
        l=QHBoxLayout()

        tab=QTabWidget()
        tab.addTab(self.__scantab(),'Scan')
        tab.addTab(self.__powertab(),'Power')
        tab.addTab(self.__stagetab(),'Stage')
        tab.addTab(self.__lorentztab(),'Lorentz')
        tab.addTab(self.__pdtab(),'PhaseDiagram')

        lh1=QHBoxLayout()
        self.__start=QPushButton('Start',clicked=self.__startscan)
        self.__stop=QPushButton('Stop')
        lh1.addWidget(self.__start)
        lh1.addWidget(self.__stop)

        lv2=QVBoxLayout()
        lv2.addWidget(tab)
        lv2.addLayout(lh1)

        self.__tree=self.__treeview()
        l.addLayout(lv2)
        l.addWidget(self.__tree)
        self.setLayout(l)
    def __scantab(self):
        gl1=QGridLayout()
        self.__scan_mode=QComboBox()
        self.__scan_mode.addItems(['Delay','Power','Stage X','Stage Y','Stage Z','Stage Alpha','Stage Beta'])
        gl1.addWidget(QLabel('Scan type'),0,0)
        gl1.addWidget(self.__scan_mode,0,1)

        self.__scan_from=QDoubleSpinBox()
        self.__scan_from.setMinimum(-10000000)
        self.__scan_from.setMaximum(10000000)
        self.__scan_step=QDoubleSpinBox()
        self.__scan_step.setValue(1)
        self.__scan_step.setMinimum(-10000000)
        self.__scan_step.setMaximum(10000000)
        self.__scan_loop=QSpinBox()
        self.__scan_loop.setValue(100)
        self.__scan_loop.setMinimum(-10000000)
        self.__scan_loop.setMaximum(10000000)
        gl1.addWidget(QLabel('From'),1,0)
        gl1.addWidget(self.__scan_from,2,0)
        gl1.addWidget(QLabel('Step'),1,1)
        gl1.addWidget(self.__scan_step,2,1)
        gl1.addWidget(QLabel('Loop'),1,2)
        gl1.addWidget(self.__scan_loop,2,2)

        self.__scan_folder=QLineEdit()
        self.__scan_folder.setText('Scan')
        self.__scan_name=QLineEdit()
        self.__scan_name.setText('a')
        self.__scan_expose=QDoubleSpinBox()
        self.__scan_expose.setValue(3)
        self.__scan_expose.setMinimum(0.000001)
        self.__scan_expose.setMaximum(10000)
        gl1.addWidget(QLabel('Folder'),3,0)
        gl1.addWidget(QLabel('Filename'),3,1)
        gl1.addWidget(QLabel('Exposure'),3,2)
        gl1.addWidget(self.__scan_folder,4,0)
        gl1.addWidget(self.__scan_name,4,1)
        gl1.addWidget(self.__scan_expose,4,2)

        self.__scan_reftype=QComboBox()
        self.__scan_reftype.addItems(['Delay','None'])
        self.__scan_refval=QDoubleSpinBox()
        self.__scan_refval.setMinimum(-10000000)
        self.__scan_refval.setMaximum(10000000)
        gl1.addWidget(QLabel('Reference'),5,0)
        gl1.addWidget(self.__scan_reftype,6,0)
        gl1.addWidget(self.__scan_refval,6,1)

        self.__scan_add=QPushButton('Add',clicked=self.addScan)
        self.__scan_addloop=QSpinBox()
        self.__scan_addloop.setMaximum(100000)
        self.__scan_addloop.setValue(1)
        gl1.addWidget(self.__scan_add,7,0)
        gl1.addWidget(self.__scan_addloop,7,1)
        gl1.addWidget(QLabel(' times'),7,2)

        w=QWidget()
        w.setLayout(gl1)
        return w
    def __powertab(self):
        gl1=QGridLayout()
        self.__power_to=QDoubleSpinBox()
        self.__power_to.setMinimum(-10000000)
        self.__power_to.setMaximum(10000000)
        gl1.addWidget(QLabel('To'),1,0)
        gl1.addWidget(self.__power_to,2,0)

        self.__power_add=QPushButton('Add',clicked=self.addPower)
        gl1.addWidget(self.__power_add,3,0)

        w=QWidget()
        w.setLayout(gl1)
        return w
    def __stagetab(self):
        h1=QHBoxLayout()
        v1=QVBoxLayout()
        self.__savepos=QPushButton('Save Positions',clicked=self.__savePosition)
        self.__movepos=QPushButton('Add Move Positions',clicked=self.__addPosition)
        v1.addWidget(self.__savepos)
        v1.addWidget(self.__movepos)

        self.__poslist=QListWidget()
        h1.addLayout(v1)
        h1.addWidget(self.__poslist)

        w=QWidget()
        w.setLayout(h1)
        return w
    def __lorentztab(self):
        self.__mag =QSpinBox()
        self.__defocus=QDoubleSpinBox()
        self.__defocus.setRange(-10000, 10000)
        self.__defocus.setDecimals(5)
        adddefocus=QPushButton('Add',clicked=self.__addDefocus)
        addmag=QPushButton('Add',clicked=self.__addMagnification)
        l = QGridLayout()
        l.addWidget(QLabel("Defocus (um)"), 0, 0)
        l.addWidget(self.__defocus, 0, 1)
        l.addWidget(adddefocus, 0, 2)
        l.addWidget(QLabel("Magnification"), 1, 0)
        l.addWidget(self.__mag, 1, 1)
        l.addWidget(addmag, 1, 2)
        w=QWidget()
        w.setLayout(l)
        return w
    def __pdtab(self):
        gl1=QVBoxLayout()

        self.__PD_add=QPushButton('Add',clicked=self.addPD)
        self.__PD_fold=QLineEdit()
        self.__PD_time=QDoubleSpinBox()
        self.__PD_mag=QSpinBox()

        gl1.addWidget(self.__PD_add)
        gl1.addWidget(QLabel('Folder'))
        gl1.addWidget(self.__PD_fold)
        gl1.addWidget(QLabel('Exposure time'))
        gl1.addWidget(self.__PD_time)
        gl1.addWidget(QLabel('Magnetic Field'))
        gl1.addWidget(self.__PD_mag)

        ldbtn=QPushButton('Load positions',clicked=self.__loadPositions)
        self._lolx=QSpinBox()
        self._lolx.setMaximum(1000000)
        self._loly=QSpinBox()
        self._loly.setMaximum(1000000)
        hbox1=QHBoxLayout()
        hbox1.addWidget(QLabel('Lorentz Button'))
        hbox1.addWidget(self._lolx)
        hbox1.addWidget(self._loly)

        self._magx=QSpinBox()
        self._magx.setMaximum(1000000)
        self._magy=QSpinBox()
        self._magy.setMaximum(1000000)
        hbox2=QHBoxLayout()
        hbox2.addWidget(QLabel('Multifunc Button'))
        hbox2.addWidget(self._magx)
        hbox2.addWidget(self._magy)

        gl1.addWidget(ldbtn)
        gl1.addLayout(hbox1)

        w=QWidget()
        w.setLayout(gl1)
        return w
    def addPD(self):
        self.phaseDiagram()
    def __savePosition(self):
        p=self.stage.getPosition()
        d={}
        d['x']=p[0]
        d['y']=p[1]
        d['z']=p[2]
        d['a']=p[3]
        d['b']=p[4]
        self.__poslist.addItem(str(d))
    def __addPosition(self):
        p=eval(self.__poslist.currentItem().text())
        self.addOrder('StagePosition',p)

    def addScan(self):
        for i in range(self.__scan_addloop.value()):
            p={}
            p['Scan type']=self.__scan_mode.currentText()
            p['From']=self.__scan_from.value()
            p['Step']=self.__scan_step.value()
            p['Loop']=self.__scan_loop.value()
            folder=self.__scan_folder.text()
            name=folder.split('/')
            name=name[len(name)-1]
            p['Folder']=folder+'/'+name+"_"+str(i)
            #p['Folder']=self.__scan_folder.text()+"_"+str(i)
            p['Exposure']=self.__scan_expose.value()
            p['Name']=self.__scan_name.text()
            p['RefType']=self.__scan_reftype.currentText()
            p['RefValue']=self.__scan_refval.value()
            self.addOrder('Scan',p)
    def addPower(self):
        p={}
        p['Value']=self.__power_to.value()
        self.addOrder('Power',p)
    def __addDefocus(self):
        p={}
        p['Value']=self.__defocus.value()
        self.addOrder('Defocus',p)
    def __addMagnification(self):
        p={}
        p['Value']=self.__mag.value()
        self.addOrder('Magnification',p)
    def __treeview(self):
        tree=QTreeView()
        tree.setDragDropMode(QAbstractItemView.InternalMove)
        tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(self.buildContextMenu)
        tree.setDropIndicatorShown(True)
        self.__model=self._Model()
        tree.setModel(self.__model)
        return tree
    def buildContextMenu(self, qPoint):
        menu = QMenu(self)
        menulabels = ['New Group', 'Delete']
        actionlist = []
        for label in menulabels:
            actionlist.append(menu.addAction(label))
        action = menu.exec_(QCursor.pos())
        if action==None:
            return
        elif action.text() == 'New Group':
            self.addOrder('NewGroup',{})
        elif action.text() == 'Delete':
            indexes=self.__tree.selectedIndexes()
            for i in reversed(indexes):
                row=i.row()
                col=i.column()
                if col==0:
                    self.__model.removeRow(row)
    def addOrder(self,name,dic):
        size=self.__model.rowCount()
        self.__model.setItem(size,0,QStandardItem(name))
        self.__model.setItem(size,1,QStandardItem(str(dic)))
    def __construct(self,res,obj1,obj2):
        res.append(dict(Order=obj1.text(),Params=obj2.text()))
        for i in range(obj1.rowCount()):
            self.__construct(res,obj1.child(i,0),obj1.child(i,1))
    def __startscan(self):
        size=self.__model.rowCount()
        selm=self.__tree.selectionModel()
        res=[]
        for i in range(size):
            index0=self.__model.index(i,0)
            index1=self.__model.index(i,1)
            obj1=self.__model.itemFromIndex(index0)
            obj2=self.__model.itemFromIndex(index1)
            self.__construct(res,obj1,obj2)
        self.exe=self.OrderExecutor(res,self.camera,self.delay,self.power,self.stage,self.pumpsw,self.tem)
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
            if sum==number:
                return (obj.child(i,0),obj.child(i,1))
            sum+=1
            res=self.__findIndex(obj.child(i,0),sum,number)
            if isinstance(res,int):
                sum=res
            else:
                return res
        return sum
    def OnUpdate(self,number):
        selm=self.__tree.selectionModel()
        selm.clearSelection()
        sum=0
        obj=self.__findIndex(self.__model.invisibleRootItem(),sum,number)
        selm.select(obj[0].index(),QItemSelectionModel.Select)
        selm.select(obj[1].index(),QItemSelectionModel.Select)
    def aquire(self,obj,name,time,folder,mode='Unknown'):
        logging.debug('[AutoTab.OrderExecutor] Start aquire')
        try:
            obj.setTime(time)
            obj.setTag('mode',mode)
            obj.setTag("Laser:delay",self.delay.get())
            obj.setTag("Laser:power",self.power.get())
            while not obj.setFolder(folder): pass
            obj.startAquire(name)
            #obj.waitForReady()
        except:
            self.aquire(obj,name,time,folder)
    def __loadPositions(self):
        QMessageBox.information(None, 'Info', "Move cursor on the \"Lorentz\" button of TEM User Interface and then press enter.")
        x,y=pyautogui.position()
        self._lolx.setValue(x)
        self._loly.setValue(y)
        QMessageBox.information(None, 'Info', "Move cursor on the \"Multifunc\" button of TEM Control Pads simulator and then press enter.")
        x,y=pyautogui.position()
        self._magx.setValue(x)
        self._magy.setValue(y)
    def phaseDiagram(self):
        sw=self.pumpsw
        pow=self.power
        cam=self.camera
        plist=np.linspace(0, 1, 20)
        alist=np.arcsin(np.sqrt(plist))/2/np.pi*180
        sw.set(False)
        for j in range(self.__PD_mag.value()):
            print("--------------- step"+str(j)+" ---------------")
            for i, a in enumerate(alist):
                #QMessageBox.information(None, 'Info', "Reset magnetic field.")
                pyautogui.click(self._lolx.value(),self._loly.value())
                time.sleep(2)
                pyautogui.click(self._lolx.value(),self._loly.value())
                time.sleep(4)
                print('Magnetic field was reset by Lorentz-TEM-Lorentz mode changes.')
                pow.set(a)
                print('Angle was set to ',a)
                sw.set(True)
                print('Shutter opened. Wait 10 seconds.')
                cam.insertCamera()
                time.sleep(10)
                print('Start aquiring (pump)')
                self.aquire(cam,'data_Mag'+str(j)+'_Pump'+str(i),self.__PD_time.value(),self.__PD_fold.text()+'/pump')
                time.sleep(self.__PD_time.value()+2)
                sw.set(False)
                print('Shutter closed. Wait 10 seconds.')
                cam.insertCamera()
                time.sleep(10)
                print('Start aquiring (nopump)')
                self.aquire(cam,'data_Mag'+str(j)+'_Pump'+str(i),self.__PD_time.value(),self.__PD_fold.text()+'/probe')
                time.sleep(self.__PD_time.value()+2)
            pyautogui.click(self._magx.value(),self._magy.value())
            print('Magnetic field was changed.')
            time.sleep(2)
        QMessageBox.information(None, 'Info', "Finished.")
def create():
    fsTEM=fsTEMMain()

main.addMainMenu(['fs-TEM and UED','Measurements'],create)
