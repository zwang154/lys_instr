
Detector GUI
============

To create the detector GUI subwindow:

1. Launch *lys* and open the ``proc.py`` file (press Ctrl+P).

2. Add the following code to define a class for the detector GUI subwindow and save it (press Ctrl+S).

.. code-block:: python

    from lys.widgets import LysSubWindow
    from lys_instr import dummy, gui

    class Window(LysSubWindow):
        def __init__(self):
            super().__init__()
            detector = dummy.MultiDetectorDummy(frameShape=(256, 256))  # Create the detector instance
            detectorGUI = gui.MultiDetectorGUI(detector)                # Create the detector GUI
            self.setWidget(detectorGUI)                                 # Embed the detector GUI in the lys subwindow
            self.adjustSize()

Calling ``Window()`` in the *lys* command line launches the GUI subwindow as shown below:

.. image:: /lys_instr_/tutorial_/detector_1.png


You can change the exposure time using the spin box or by direct input, then click "Acquire" for a single shot, "Stream" for continuous acquisition, or "Stop" to halt the process.

The indicator at the bottom left shows the connection status—green for a successful connection, and red for a disconnected or error state.

Clicking the "Settings" button opens a dialog.

.. image:: /lys_instr_/tutorial_/detector_2.png
    :scale: 80%

Within the dialog, you can use the spin box next to "Repeat" to set the number of frames per acquisition and the spin box next to "Update every" to change the display refresh rate.
You can also click the "Update" button at any time to refresh the display manually.

See also :doc:`Detector Options </lys_instr_/tutorial_/detectorOptions>` for details on displaying multi-dimensional data with nontrivial data shapes.