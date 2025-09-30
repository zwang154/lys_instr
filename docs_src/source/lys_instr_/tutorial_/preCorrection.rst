
Axis Calibration and Dependency
===============================

Axis Calibration
----------------

``PreCorrection`` enables axis calibration through user-defined correction functions or data.
Suppose a motor axis "x" requires calibration, and the relationship between the raw position and the corrected position is given by a set of data points.
These data can be stored in a NumPy ``.npz`` file with the following structure:








Axis Dependency
---------------

``PreCorrection`` also supports defining dependencies between axes.
Suppose position of "y" needs to always follow a fix function of that of "x", e.g. ``y = x/2`` and only "x" is controlled directly.

A simple GUI with a motor and a corrector can be constructed as follows:

.. code-block:: python

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
            _correctorGUI = gui.PreCorrectorGUI(self._corrector)

            self._tab = QtWidgets.QTabWidget()
            self._tab.addTab(_motorGUI, "Motor")
            self._tab.addTab(_correctorGUI, "PreCorr")

            VBox = QtWidgets.QVBoxLayout()
            VBox.addWidget(self._tab)

            HBox = QtWidgets.QHBoxLayout()
            HBox.addLayout(VBox)

            self.setLayout(HBox)

The following GUI appears. Note that only the "x" axis is enabled for control.

.. image:: /lys_instr_/tutorial_/preCorrection_1.png
    :scale: 80%

.. image:: /lys_instr_/tutorial_/preCorrection_2.png
    :scale: 80%

In the "PreCorr" tab, right-click on the tree space and select "Add Target" to add a target axis, i.e., "y".
Then, right-click on the target "y" and select "Add Variable", choosing "x" as the dependency axis.
Next, double-click on the expression space of target "y" to enter ``x/2``.

.. image:: /lys_instr_/tutorial_/preCorrection_3.png
    :scale: 80%

Now, when the user inputs a target position for "x" in the "Motor" tab and clicks "Go", the motor will move "x" to the specified position and automatically adjust "y" to be half that of "x".

Alternatively, the user can define the dependency programmatically by adding the following code after creating the ``self._corrector`` instance:

.. code-block:: python

    self._corrector.corrections["y"] = _FunctionCombination()
    self._corrector.corrections["y"].functions["x"] = _InterpolatedFunction(lambda x: x, ["x"])
    self._corrector.corrections["y"].expression = "x/2"
