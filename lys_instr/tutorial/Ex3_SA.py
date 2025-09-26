from lys.Qt import QtWidgets
from lys_instr import PreCorrector, gui, dummy
from lys_instr.PreCorrection import _FunctionCombination, _InterpolatedFunction


class window(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setWindowTitle("Example #3")
        self._motor = dummy.MultiMotorDummy("x", "y")
        self._corrector = PreCorrector([self._motor])

        # Add a dependence y = x/2
        self._corrector.corrections["y"] = _FunctionCombination()
        self._corrector.corrections["y"].functions["x"] = _InterpolatedFunction(lambda x: x, ["x"])
        self._corrector.corrections["y"].expression = "x/2"

        self._initLayout()
        self.adjustSize()

    def _initLayout(self):
        _motorGUI = gui.MultiMotorGUI(self._motor, axisNamesSettable=("x",), axisNamesJoggable=("x",))
        _correctorGUI = gui.PreCorrectorGUI(self._corrector)

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