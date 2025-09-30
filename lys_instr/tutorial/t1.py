from lys.Qt import QtWidgets
from lys_instr import PreCorrector, gui, dummy
from lys_instr.PreCorrection import _FunctionCombination, _InterpolatedFunction

class AppWindow(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._motor = dummy.MultiMotorDummy("x", "y")
        self._corrector = PreCorrector([self._motor])
        self._initLayout()
        self.adjustSize()

    def _initLayout(self):
        _motorGUI = gui.MultiMotorGUI(self._motor, axisNamesSettable=("x",), axisNamesJoggable=("x",)) # only enable "x" axis control

        self._corrector.corrections["y"] = _FunctionCombination()
        self._corrector.corrections["y"].functions["x"] = _InterpolatedFunction(lambda x: x, ["x"])
        self._corrector.corrections["y"].expression = "x/2"
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