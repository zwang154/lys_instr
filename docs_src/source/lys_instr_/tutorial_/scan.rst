
Scan Configuration
==================

Basic Scan GUI
--------------

An automated measurement often involves repeatedly executing of a sequence of operations while varying certain parameter(s).
We call this a "scan" of a base process over a parameter.

Here, we provide a basic ``Scan`` GUI widget for the simplest scan configuration (see :class:`.gui.MultiScan` for code details).
This setup allows a detector instance to acquire data while the motor axes are scanned over a range of positions.

Using the previous dummy 2-axis motor, dummy 256×256 detector, and data storage for demonstration, 
a scan GUI can be constructed as follows:

.. code-block:: python

    from lys.widgets import LysSubWindow
    from lys.Qt import QtWidgets
    from lys_instr import DataStorage, dummy, gui

    class AppWindow(LysSubWindow):
        def __init__(self):
            super().__init__()
            self._motor = dummy.MultiMotorDummy("x", "y")
            self._detector = dummy.MultiDetectorDummy(indexShape=(1,), frameShape=(256, 256), exposure=0.1)
            self._storage = DataStorage()
            self._storage.connect(self._detector)
            self._initLayout()
            self.adjustSize()

        def _initLayout(self):
            _detectorGUI = gui.MultiDetectorGUI(self._detector)
            _motorGUI = gui.MultiMotorGUI(self._motor)
            _storageGUI = gui.DataStorageGUI(self._storage)

            _scanGUI = gui.ScanWidget(self._storage, [self._motor], {"MultiDetectorDummy": self._detector})

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

            mcut = _detectorGUI._mcut
            wave = mcut.cui._children.addWave([1, 2])
            mcut.display(wave, type="grid", pos=(0, 0), wid=(4, 4))


Adding the above code to ``proc.py`` in *lys* and then calling ``AppWindow()`` in the *lys* command line launches the GUI subwindow as follows:

.. image:: /lys_instr_/tutorial_/scan_1.png

Opening the "Scan" tab shows the scan configuration. 
Setting the parameters as shown below enables nested scans in a depth-first manner—that is, 
the y-axis is scanned from 0 to 1 with a step size of 0.1 for each position of the x-axis, 
which is scanned from 0 to 1 with a step size of 0.2.

.. image:: /lys_instr_/tutorial_/scan_2.png


User customization
------------------

Users can create custom scan processes and GUI widgets by appropriately combining ``MultiMotor``, ``MultiDetector``, and ``DataStorage`` instances.
See the next page for more example configurations.
