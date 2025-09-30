
Basic Examples
==============

Spectroscopy measurement
------------------------

This example demonstrates a simple spectrum acquisition GUI using a dummy 1D motor and a dummy 1D detector.

Suppose we have a detector that acquires optical spectra, i.e., pairs of wavelength and intensity values.
A dummy detector ``DetectorEx1Dummy`` is provided to simulate such data.
We want to change the direction of a polarizer in the optical path by rotating its motor ``MultiMotorDummy`` with axis φ while acquiring the spectrum at each angle.
The GUI for this setup can be constructed as follows:

.. code-block:: python

    from lys.widgets import LysSubWindow
    from lys.Qt import QtWidgets
    from lys_instr import DataStorage, gui, dummy

    class DetectorEx1GUI(gui.MultiDetectorGUI):
        def _update(self):
            if hasattr(self, "_data"):
                self._data.axes = [self._obj.axes[0]]
                self._mcut.cui.setRawWave(self._data)

    class WindowEx1(LysSubWindow):
        def __init__(self):
            super().__init__()
            self._motor = dummy.MultiMotorDummy("phi")
            self._detector = dummy.DetectorEx1Dummy(indexShape=(1,), frameShape=(256,), exposure=0.1)
            self._storage = DataStorage()
            self._storage.connect(self._detector)
            self._initLayout()
            self.adjustSize()

        def _initLayout(self):
            _detectorGUI = DetectorEx1GUI(self._detector)
            _motorGUI = gui.MultiMotorGUI(self._motor)
            _storageGUI = gui.DataStorageGUI(self._storage)

            _scanGUI = gui.ScanWidget(self._storage, [self._motor], {"DetectorEx1Dummy": self._detector})

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

            # Adapt multicut to line plot
            mcut = _detectorGUI._mcut
            graph = mcut.cui._children.addWave([1])
            mcut.display(graph, type="grid", pos=(0, 0), wid=(4, 4))

Adding the above code to ``proc.py`` in *lys* and then calling this ``WindowEx1()`` in the *lys* command line launches the GUI subwindow shown below:

.. image:: /lys_instr_/tutorial_/Ex1.png


Pump-probe Measurement
----------------------

This example demonstrates a combined motor and switch control GUI in a scan.

Suppose we perform a pump-probe measurement, where an image is acquired at each ON/OFF state of the pump light while varying the delay time by moving a motor.
A dummy switch ``MultiSwitchDummy`` and a dummy motor ``MultiMotorDummy`` simulate the pump light ON/OFF control and delay stage motion, respectively.
A dummy detector ``DetectorEx2Dummy`` is provided to simulate the image data acquisition.
A small modification of the previous example allows one to construct the GUI for this setup as follows:

.. code-block:: python

    from lys.widgets import LysSubWindow
    from lys.Qt import QtWidgets
    from lys_instr import DataStorage, dummy, gui

    class WindowEx2(LysSubWindow):
        def __init__(self):
            super().__init__()
            self._motor = dummy.MultiMotorDummy("x")
            self._switch = dummy.MultiSwitchDummy("A")
            self._detector = dummy.DetectorEx2Dummy(indexShape=(1,), frameShape=(256, 256), exposure=0.1)
            self._storage = DataStorage()
            self._storage.connect(self._detector)
            self._initLayout()
            self.adjustSize()

        def _initLayout(self):
            _detectorGUI = gui.MultiDetectorGUI(self._detector)
            _motorGUI = gui.MultiMotorGUI(self._motor)
            _switchGUI = gui.MultiSwitchGUI(self._switch)
            _storageGUI = gui.DataStorageGUI(self._storage)

            _scanGUI = gui.ScanWidget(self._storage, [self._switch, self._motor], {"DetectorEx2Dummy": self._detector})

            self._tab = QtWidgets.QTabWidget()
            self._tab.addTab(_motorGUI, "Motor")
            self._tab.addTab(_switchGUI, "Switch")
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

            mcut = _detectorGUI._mcut
            wave = mcut.cui._children.addWave([1, 2])
            mcut.display(wave, type="grid", pos=(0, 0), wid=(4, 4))

Adding the above code to ``proc.py`` in *lys* and then calling this ``WindowEx2()`` in the *lys* command line launches the GUI subwindow shown below:

.. image:: /lys_instr_/tutorial_/Ex2.png

Here, a "Switch" tab is added. On the "Scan" tab, both the switch axis and the motor axis can be selected for each base process.
Choosing the "Free" mode and inputting a list such as ``[ON, OFF]`` as an expression allows the switch axis to alternate between ON and OFF states, mimicking the pump behavior.