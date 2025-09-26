
Advanced Examples
=================

Spectrum Scanning
-----------------

For a more intuitive demonstration of the *lys_instr* package, we provide several real-world examples that illustrate how multiple components can be integrated into a complete experimental workflow.

Consider the task of acquiring a series of Raman spectra while systematically scanning the light polarization angle and performing spatial mapping across a two-dimensional sample region. In this setup:
- The polarization angle is controlled by a half-wave plate mounted on a rotation stage (simulated by the ``phi`` axis of ``MultiMotorDummy``).
- Sample positioning for spatial mapping is achieved using an XY motorized stage (simulated by the ``x`` and ``y`` axes of ``MultiMotorDummy``).
- Raman spectra are collected using a spectrometer (simulated by ``DetectorAdvEx1Dummy``), providing 36 polarization angles at each of 8×9 spatial positions, with a 10° interval between angles.

The instrument control GUI can be constructed as follows:

.. code-block:: python

    import pyqtgraph as pg
    from lys.widgets import LysSubWindow
    from lys.Qt import QtWidgets
    from lys_instr import DataStorage, gui, dummy

    class DetectorAdvEx1GUI(gui.MultiDetectorGUI):
        # Disable exposure time control in the detector GUI (set exposure time from the scan tab).
        def __init__(self, obj, wait=False, interval=1, iter=1):
            super().__init__(obj, wait=wait, interval=interval, iter=iter)
            if hasattr(self, "_expTime"):
                self._expTime.setValue(0)
                self._expTime.setEnabled(False)

        # Update logic: refresh both the live frame visualization and the polarization-dependence plot.
        def _update(self):
            if hasattr(self, "_data"):
                self._data.axes = self._obj.axes[-2:]
                self._mcut.cui.setRawWave(self._data)
            if hasattr(self._obj, "_frame"):
                self._framePlot.clear()
                self._framePlot.plot(self._obj._frame[0], self._obj._frame[1])

    class AppWindow(LysSubWindow):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Advanced Example #1")      # Set window title
            self._storage = DataStorage()
            self._detector = dummy.DetectorAdvEx1Dummy(indexShape=(36,), frameShape=(600,), exposure=0.1)
            self._motor = dummy.MultiMotorDummy("x", "y", "phi")
            self._storage.connect(self._detector)
            self._initLayout()
            self.setSettingFile("AdvEx1.dic")               # Memorize last settings
            self.adjustSize()

        def _initLayout(self):
            _storageGUI = gui.DataStorageGUI(self._storage)
            _detectorGUI = DetectorAdvEx1GUI(self._detector)
            _motorGUI = gui.MultiMotorGUI(self._motor)
            _scanGUI = gui.MultiScan.ScanWidget(self._storage, [self._motor], {"DetectorAdvEx1Dummy": self._detector}, numScans=3)

            self._tab = QtWidgets.QTabWidget()
            self._tab.addTab(_motorGUI, "Motor")
            self._tab.addTab(_scanGUI, "Scan")

            VBox = QtWidgets.QVBoxLayout()
            VBox.addWidget(_storageGUI)
            VBox.addWidget(self._tab)

            HBox = QtWidgets.QHBoxLayout()
            HBox.addLayout(VBox)
            HBox.addWidget(_detectorGUI)
            
            w = QtWidgets.QWidget()
            w.setLayout(HBox)
            self.setWidget(w)

            # Set display
            # Set the top graph to display intensity vs. angle at specific spatial positions
            mcut = _detectorGUI._mcut
            graph1 = mcut.cui._children.addWave([1, 0])
            mcut.display(graph1, type="grid", pos=(0, 0), wid=(3, 4))
            # Set the bottom graph to display the live Raman spectrum
            self._framePlot = pg.PlotWidget()
            mcut._grid.layout.addWidget(self._framePlot, 4, 0, 1, 4)
            _detectorGUI._framePlot = self._framePlot

            # Set scan parameters
            # Set scan axis 0 (first row) to 'phi', linear mode, from 0, step 10, 36 steps
            _scanGUI._scanRangeRows[0]._scanAxis.setCurrentText("phi")
            _scanGUI._scanRangeRows[0]._step.setValue(0.1)
            _scanGUI._scanRangeRows[0]._numSteps.setValue(9)
            # Set scan axis 1 (second row) to 'y', linear mode, from 0, step 0.1, 9 steps
            _scanGUI._scanRangeRows[0]._scanAxis.setCurrentText("y")
            _scanGUI._scanRangeRows[0]._step.setValue(0.1)
            _scanGUI._scanRangeRows[0]._numSteps.setValue(9)
            # Set scan axis 2 (third row) to 'x', linear mode, from 0, step 0.1, 8 steps
            _scanGUI._scanRangeRows[1]._scanAxis.setCurrentText("x")
            _scanGUI._scanRangeRows[1]._step.setValue(0.1)
            _scanGUI._scanRangeRows[1]._numSteps.setValue(8)
            _scanGUI._exposure.setValue(0.1)


Adding the above code to ``proc.py`` in *lys* and calling ``AppWindow()`` from the *lys* command line will display the following GUI:

.. image:: /lys_instr_/tutorial_/advExamples_1.png

The top graph displays the polarization dependence data (intensity vs. angle) at specific spatial positions, 
while the bottom graph shows the live Raman spectrum being acquired.

The ``DetectorAdvEx1GUI`` customizes the detector GUI update logic for both live frame and the polarization dependence plot.
The ``AppWindow`` class sets up the overall GUI layout and scan parameters.
The "Set scan parameters" section in the code can also be manually configured on the GUI.



Pump-Probe TEM Experiment
-------------------------

Consider a system in which a laser pulse is used to excite the sample, and the resulting changes are probed with an electron beam in a transmission electron microscope (TEM). 
At each time delay, the electron beam is raster-scanned across the sample plane (2D grid, ``indexShape=(8, 8)``), and at each spatial position a diffraction pattern (2D image, ``frameShape=(256, 256)``) is acquired.
This can be considered a time-resolved 4D-STEM experiment.

The instrument control GUI can be constructed as follows:

.. code-block:: python

    from lys.widgets import LysSubWindow
    from lys.Qt import QtWidgets
    from lys_instr import DataStorage, PreCorrector, gui, dummy
    from lys_instr.gui.MultiScan import ScanWidget

    class AppWindow(LysSubWindow):
        def __init__(self, parent=None):
            super().__init__(parent)
            # self.setWindowTitle("Advanced Example 2")
            self._storage = DataStorage()
            self._detector = dummy.MultiDetectorDummy((5, 5), (256, 256), exposure=0.1)
            self._motor = dummy.MultiMotorDummy("x", "y", "t")
            self._pre = PreCorrector([self._motor])
            self._switch = dummy.MultiSwitchDummy("A")
            self._storage.connect(self._detector)
            self._initLayout()
            self.adjustSize()

        def _initLayout(self):
            _storageGUI = gui.DataStorageGUI(self._storage)
            _motorGUI = gui.MultiMotorGUI(self._motor, axisNamesSettable=("x", "y", "t"), axisNamesJoggable=("t"), axisNamesOffsettable=("x", "y", "t"))
            _switchGUI = gui.MultiSwitchGUI(self._switch)
            _detectorGUI = gui.MultiDetectorGUI(self._detector)
            _correctorGUI = gui.PreCorrectorGUI(self._pre)
            _scanGUI = ScanWidget(self._storage, [self._switch, self._motor], {"MultiDetectorDummy": self._detector}, numScans=2)

            self._tab = QtWidgets.QTabWidget()
            self._tab.addTab(_motorGUI, "Motor")
            self._tab.addTab(_switchGUI, "Switch")
            self._tab.addTab(_scanGUI, "Scan")
            self._tab.addTab(_correctorGUI, "PreCorr")

            VBox = QtWidgets.QVBoxLayout()
            VBox.addWidget(_storageGUI)
            VBox.addWidget(self._tab)

            HBox = QtWidgets.QHBoxLayout()
            HBox.addLayout(VBox)
            HBox.addWidget(_detectorGUI)
            
            w = QtWidgets.QWidget()
            w.setLayout(HBox)
            self.setWidget(w)

            # Set multicut display style
            mcut = _detectorGUI._mcut
            graph1 = mcut.cui._children.addWave([0, 1])
            mcut.display(graph1, type="grid", pos=(0, 0), wid=(4, 2))
            graph2 = mcut.cui._children.addWave([2, 3])
            mcut.display(graph2, type="grid", pos=(0, 2), wid=(4, 2))

            # Set scan parameters
            _scanGUI._scanRangeRows[0]._scanAxis.setCurrentText("A")
            _scanGUI._scanRangeRows[0]._scanMode.setCurrentText("Free")
            _scanGUI._scanRangeRows[0]._freeExpr.setText(str([True,]))
            _scanGUI._scanRangeRows[1]._scanAxis.setCurrentText("t")
            _scanGUI._scanRangeRows[1]._step.setValue(0.1)
            _scanGUI._scanRangeRows[1]._numSteps.setValue(9)
            _scanGUI._check_ref.setChecked(True)
            _scanGUI._combo_ref.setCurrentText("A")      # Reference axis is "A"
            _scanGUI._value_ref.setValue(False)          # Reference value is pump OFF

Adding the above code to ``proc.py`` in *lys* and calling ``AppWindow()`` from the *lys* command line will display the following GUI:

.. image:: /lys_instr_/tutorial_/advExamples_2.png

The left graph displays the 2D spatial mapping data at a specific time delay (a STEM image), while the right graph shows the live diffraction pattern being acquired.
Scan axis "A" represents the pump laser state (ON/OFF), and axis "t" represents the time delay between the pump laser pulse and the probe electron pulse.




