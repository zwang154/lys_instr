from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
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
        self.power=SingleMotorInterface()
        self.camera=CameraInterface()
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
            start=d.get()
            for i in range(params['Loop']):
                if self.stopped:
                    return
                c.startAquire()
                c.waitForReady()
                d.set(start+(i+1)*params['Step'])
                d.waitForReady()

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
        lv1=QVBoxLayout()
        lv1.addWidget(QLabel('Scan type'))
        self.__scan_mode=QComboBox()
        self.__scan_mode.addItems(['Delay','Power'])
        lv1.addWidget(self.__scan_mode)
        gl1=QGridLayout()
        gl1.addWidget(QLabel('Step'),0,0)
        self.__scan_step=QDoubleSpinBox()
        self.__scan_step.setValue(1)
        gl1.addWidget(self.__scan_step,1,0)
        gl1.addWidget(QLabel('Loop'),0,1)
        self.__scan_loop=QSpinBox()
        self.__scan_loop.setValue(100)
        gl1.addWidget(self.__scan_loop,1,1)
        lv1.addLayout(gl1)
        self.__scan_add=QPushButton('Add',clicked=self.addScan)
        lv1.addWidget(self.__scan_add)
        w=QWidget()
        w.setLayout(lv1)
        return w
    def addScan(self):
        p={}
        p['Scan type']=self.__scan_mode.currentText()
        p['Step']=self.__scan_step.value()
        p['Loop']=self.__scan_loop.value()
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
    def __construct(self,res,obj):
        pass
    def __startscan(self):
        size=self.__model.rowCount()
        selm=self.__tree.selectionModel()
        res=[]
        for i in range(size):
            index0=self.__model.index(i,0)
            index1=self.__model.index(i,1)
            t0=self.__model.itemFromIndex(index0).text()
            t1=self.__model.itemFromIndex(index1).text()
            res.append(dict(Order=t0,Params=t1))
        for d in res:
            print(d)
        self.exe=self.OrderExecutor(res,self.camera,self.delay,self.power)
        self.exe.updated.connect(self.OnUpdate)
        self.exe.finished.connect(self.OnFinished)
        self.__start.setEnabled(False)
        self.__stop.clicked.connect(self.exe.kill)
        self.exe.start()
    def OnFinished(self):
        self.__stop.clicked.disconnect(self.exe.kill)
        self.__start.setEnabled(True)
    def OnUpdate(self,number):
        selm=self.__tree.selectionModel()
        selm.clearSelection()
        index0=self.__model.index(number,0)
        index1=self.__model.index(number,1)
        selm.select(index0,QItemSelectionModel.Select)
        selm.select(index1,QItemSelectionModel.Select)

def create():
    fsTEM=fsTEMMain()

main.addMainMenu(['fs-TEM and UED','Measurements'],create)
