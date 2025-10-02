from lys.Qt import QtWidgets
from lys_instr import PreCorrector, gui, dummy

class AppWindow(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._motor = dummy.MultiMotorDummy("x", "y", "z")
        self._corrector = PreCorrector([self._motor])
        self._initLayout()
        self.adjustSize()

    def _initLayout(self):
        _motorGUI = gui.MultiMotorGUI(self._motor, axisNamesSettable=("x", "y"), axisNamesJoggable=("x",)) # only enable "x" axis control
        _correctorGUI = gui.PreCorrectorGUI(self._corrector)

        self._tab = QtWidgets.QTabWidget()
        self._tab.addTab(_motorGUI, "Motor")
        self._tab.addTab(_correctorGUI, "PreCorr")

        VBox = QtWidgets.QVBoxLayout()
        VBox.addWidget(self._tab)

        HBox = QtWidgets.QHBoxLayout()
        HBox.addLayout(VBox)

        self.setLayout(HBox)





if __name__ == "__main__":
    import sys
    from lys.Qt import QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    win = AppWindow()
    win.show()
    sys.exit(app.exec_())