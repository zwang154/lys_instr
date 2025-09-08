# Start on lys

from lys.widgets import LysSubWindow
from lys.Qt import QtWidgets, QtCore
from lys_instr import MultiMotor, PreCorrector, gui, dummy


# class MultiMotorEx3(MultiMotor):
#     def waitForReady(self, interval=0.1):
#         loop = QtCore.QEventLoop()
#         def _onFinished():
#             if not any(self.isBusy.values()):
#                 self.quitRequested.emit()
#                 self.quitRequested.disconnect(loop.quit)
#                 self.busyStateChanged.disconnect(_onFinished)
#         self.quitRequested.connect(loop.quit)
#         self.busyStateChanged.connect(_onFinished)
#         loop.exec_()

# class MultiMotorEx3(MultiMotor):
#     def waitForReady(self, interval=0.1):
#         loop = QtCore.QEventLoop()
#         def check():
#             if any(self.isBusy.values()):
#                 QtCore.QTimer.singleShot(int(interval * 1000), check)
#             else:
#                 loop.quit()
#         check()
#         loop.exec_()
#         return True

# class MultiMotorEx3(MultiMotor):
#     def waitForReady(self, interval=0.1):
#         def check():
#             if any(self.isBusy.values()):
#                 QtCore.QTimer.singleShot(int(interval * 1000), check)
#             else:
#                 pass
#         check()


# class window(LysSubWindow):
class window(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Example #3")
        self._motor = dummy.MultiMotorDummy("x", "y", "z", "α", "β", "γ")
        self._pre = PreCorrector([self._motor])
        self._initLayout()
        # self.setSettingFile("Ex3.dic")
        self.adjustSize()

    def _initLayout(self):
        _motorGUI = gui.MultiMotorGUI(self._motor)
        _correctorGUI = gui.PreCorrectorGUI(self._pre)

        self._tab = QtWidgets.QTabWidget()
        self._tab.addTab(_motorGUI, "Motor")
        self._tab.addTab(_correctorGUI, "PreCorr")

        VBox = QtWidgets.QVBoxLayout()
        VBox.addWidget(self._tab)

        HBox = QtWidgets.QHBoxLayout()
        HBox.addLayout(VBox)

        # w = QtWidgets.QWidget()
        # w.setLayout(HBox)
        # self.setWidget(w)

        self.setLayout(HBox)




# To Test the GUI run in the src\python: python -m lys_instr.tutorial.Ex3
if __name__ == "__main__":
    import sys
    from lys.Qt import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    gui = window()
    gui.show()
    sys.exit(app.exec_())