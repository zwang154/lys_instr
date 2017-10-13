from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from ExtendAnalysis.AnalysisWindow import AnalysisWindow
import ExtendAnalysis.MainWindow as main
from Controllers.SingleMotor import *
from Controllers.Camera import *
from Controllers.Hardwares.Soloist.SoloistHLE import SoloistHLE
from Controllers.Hardwares.FEI.TechnaiFemto import TechnaiFemto

class fsTEMMain(AnalysisWindow):
    def __init__(self):
        super().__init__(title="Ultrafast Electron Diffraction/Microscopy Measurements")
        self.__initHardware()
        self.__initlayout()
        self.adjustSize()
    def __initHardware(self):
        self.delay=SoloistHLE('192.168.12.202',8000)
        self.power=SingleMotorDummy()
        self.camera=TechnaiFemto('192.168.12.201',7000,7001)
    def __initlayout(self):
        tab=QTabWidget()
        l=QHBoxLayout()
        lv=QVBoxLayout()
        lv.addWidget(SingleMotorGUI(self.delay,'Delay Stage'))
        lv.addWidget(SingleMotorGUI(self.power,'Pump power'))
        l.addLayout(lv)
        l.addWidget(CameraGUI(self.camera,'TEM Image'))
        wid=QWidget()
        wid.setLayout(l)
        tab.addTab(wid,'Fundamentals')
        tab.addTab(AutoTab(self.delay,self.camera,self.power),'Auto')
        self.setWidget(tab)

class AutoTab(QWidget):
    class _Model(QStandardItemModel):
        def __init__(self):
            super().__init__(0,2)
            self.setHeaderData(0,Qt.Horizontal,'Order')
            self.setHeaderData(1,Qt.Horizontal,'Parameters')
    class OrderExecutor(QThread):
        updated=pyqtSignal(int)
        finished=pyqtSignal()
        def __init__(self,order,camera,delay,power):
            super().__init__()
            self.stopped=False
            self.delay=delay
            self.camera=camera
            self.power=power
            self.mutex=QMutex()
            self.order=order
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
            if order['Order']=='Scan':
                self.scan(eval(order['Params']))
        def scan(self,params):
            if params['Scan type']=='Delay':
                d=self.delay
            if params['Scan type']=='Power':
                d=self.power
            c=self.camera
            start=params['From']
            for i in range(params['Loop']):
                if self.stopped:
                    return
                if params['RefType']=='Delay':
                    d.set(params['RefValue'])
                    d.waitForReady()
                    c.setFolder(params['Folder']+'\\probe')
                    c.startAquire(params['Name']+str(i))
                    c.waitForReady()
                d.set(start+(i+1)*params['Step'])
                d.waitForReady()
                c.setFolder(params['Folder']+'\\pump')
                c.startAquire(params['Name']+str(i))
                c.waitForReady()

    def __init__(self,delay,camera,power):
        super().__init__()
        self.delay=delay
        self.camera=camera
        self.power=power
        self.__initlayout()
    def __initlayout(self):
        l=QHBoxLayout()

        tab=QTabWidget()
        tab.addTab(self.__scantab(),'Scan')

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
        self.__scan_mode.addItems(['Delay','Power'])
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
        gl1.addWidget(QLabel('Folder'),3,0)
        gl1.addWidget(QLabel('Filename'),3,1)
        gl1.addWidget(self.__scan_folder,4,0)
        gl1.addWidget(self.__scan_name,4,1)

        self.__scan_reftype=QComboBox()
        self.__scan_reftype.addItems(['Delay'])
        self.__scan_refval=QDoubleSpinBox()
        self.__scan_refval.setMinimum(-10000000)
        self.__scan_refval.setMaximum(10000000)
        gl1.addWidget(QLabel('Reference'),5,0)
        gl1.addWidget(self.__scan_reftype,6,0)
        gl1.addWidget(self.__scan_refval,6,1)

        self.__scan_add=QPushButton('Add',clicked=self.addScan)
        self.__scan_addloop=QSpinBox()
        self.__scan_addloop.setValue(1)
        gl1.addWidget(self.__scan_add,7,0)
        gl1.addWidget(self.__scan_addloop,7,1)
        gl1.addWidget(QLabel(' times'),7,2)

        w=QWidget()
        w.setLayout(gl1)
        return w
    def addScan(self):
        for i in range(self.__scan_addloop.value()):
            p={}
            p['Scan type']=self.__scan_mode.currentText()
            p['From']=self.__scan_from.value()
            p['Step']=self.__scan_step.value()
            p['Loop']=self.__scan_loop.value()
            p['Folder']=self.__scan_folder.text()+"_"+str(i)
            p['Name']=self.__scan_name.text()
            p['RefType']=self.__scan_reftype.currentText()
            p['RefValue']=self.__scan_refval.value()
            self.addOrder('Scan',p)
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
            for i in indexes:
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
        self.exe=self.OrderExecutor(res,self.camera,self.delay,self.power)
        self.exe.updated.connect(self.OnUpdate)
        self.exe.finished.connect(self.OnFinished)
        self.__start.setEnabled(False)
        self.__stop.clicked.connect(self.exe.kill)
        self.exe.start()
    def OnFinished(self):
        self.__stop.clicked.disconnect(self.exe.kill)
        self.__start.setEnabled(True)
    def __findIndex(self, obj, sum, number):
        print(obj.text(),obj.rowCount(),sum,number)
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

def create():
    fsTEM=fsTEMMain()

main.addMainMenu(['fs-TEM and UED','Measurements'],create)
