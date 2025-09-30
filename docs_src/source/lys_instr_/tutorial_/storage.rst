
Data Storage
============

Creating a Data Storage Instance
--------------------------------

A data storage instance can be created by inheriting from the ``DataStorage`` class, 
which provides essential functions for storing acquired data (see :class:`.DataStorage.DataStorage`).

A data storage instance can be created as follows:

.. code-block:: python

    from lys_instr import DataStorage

    storage = DataStorage()


Creating the Data Storage GUI
-----------------------------

A GUI for the data storage can be created by passing the data storage instance to the ``DataStorageGUI`` class. 
Continuing from the previous example:

.. code-block:: python

    import sys
    from lys.Qt import QtWidgets
    from lys_instr import gui

    app = QtWidgets.QApplication(sys.argv)
    storageGUI = gui.DataStorageGUI(storage)
    storageGUI.show()
    sys.exit(app.exec_())

A GUI window like the one below will appear:

.. image:: /lys_instr_/tutorial_/storage_1.png
    :scale: 80%

Clicking the "File" button allows to choose the data-saving directory ("Base Folder"), 
under which a "Folder Name" and "File Name" can be specified by direct input.
The "Numbered" checkbox enables automatic numbering in file names.
The "Enabled" checkbox toggles data saving on and off.
Data will be saved in NumPy ndarray format.


Starting the GUI in *lys*
-------------------------

The data storage GUI can be launched from within the *lys* application, 
by adding the code below to the ``proc.py`` file and execute `AppWindow()` in the *lys* command line:

.. code-block:: python

    from lys.widgets import LysSubWindow
    from lys_instr import DataStorage, gui

    class AppWindow(LysSubWindow):
        def __init__(self):
            super().__init__()
            storage = DataStorage()
            storageGUI = gui.DataStorageGUI(storage)
            self.setWidget(storageGUI)
            self.adjustSize()


Connecting Data Storage to Detector
-----------------------------------

In practice, the data storage instance is used to store data acquired by a detector and should be connected to a detector instance.
This can be done using the ``connect()`` method of the ``DataStorage`` class.
For example, using the same detector instance as on the previous page:

.. code-block:: python

    from lys_instr import DataStorage, dummy

    detector = dummy.MultiDetectorDummy(indexShape=(1,), frameShape=(256, 256), exposure=0.1)
    storage = DataStorage()
    storage.connect(detector)

To create a combined detector and data storage GUI in *lys*, add the code below to the ``proc.py`` file:

.. code-block:: python

    from lys.widgets import LysSubWindow
    from lys.Qt import QtWidgets
    from lys_instr import DataStorage, dummy, gui

    class AppWindow(LysSubWindow):
        def __init__(self):
            super().__init__()
            self._detector = dummy.MultiDetectorDummy(indexShape=(1,), frameShape=(256, 256), exposure=0.1)
            self._storage = DataStorage()
            self._storage.connect(self._detector)
            self._initLayout()
            self.adjustSize()

        def _initLayout(self):
            detectorGUI = gui.MultiDetectorGUI(self._detector)
            storageGUI = gui.DataStorageGUI(self._storage)

            VBox = QtWidgets.QVBoxLayout()
            VBox.addWidget(storageGUI)
            VBox.addWidget(detectorGUI)
            
            w = QtWidgets.QWidget()
            w.setLayout(VBox)
            self.setWidget(w)

            mcut = detectorGUI._mcut
            wave = mcut.cui._children.addWave([1, 2])
            mcut.display(wave, type="grid", pos=(0, 0), wid=(4, 4))

Entering ``AppWindow()`` in the *lys* command line launches the combined GUI subwindow as shown below:

.. image:: /lys_instr_/tutorial_/storage_2.png

With this GUI, users can save detector-acquired data to files. 
Recall that for real applications the user needs to connect the data storage instance to a device-specific detector instance.

