
Basic Examples
==============

Spectrum Acquisition (1D data + 1D Scan)
-----------------------------------------

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

Adding the above code to ``proc.py`` in *lys* and then calling ``WindowEx1()`` in the *lys* command line launches the GUI subwindow shown below:

.. image:: /lys_instr_/tutorial_/Ex1.png


Switch
--------------------------------------

The :doc:`/lys_instr_/tutorial_/scan` has already demonstrated a simple video acquisition GUI using a dummy 1D motor and a dummy 2D detector.
A more extensive example is provided by generalizing the motor concept.
The motor could be a controller of temperature, electric or magnetic field, on/off switch, and miscellaneous.
Then, the same code structure can be used as long as the field application logic can be implemented as an abstract motor instance inheriting from ``MultiMotorInterface``.

By replacing the dummy motor with one generating 2D Gaussian instance, the same GUI can be used for real experiments.
This example demonstrates a simple video acquisition GUI using a dummy 1D motor and a dummy 2D detector.

Suppose we have a detector that acquires 2D images, e.g., from a camera.
The previous dummy detector ``MultiDetectorDummy`` in :doc:`/lys_instr_/tutorial_/detector` simulates such data.
We want to scan the electric or magnetic field applied on the sample while acquiring the image at each field value.


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