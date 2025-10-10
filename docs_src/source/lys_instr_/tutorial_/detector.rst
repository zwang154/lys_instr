
Detector
========

Creating a Detector Instance
----------------------------

A detector instance is created by subclassing ``MultiDetectorInterface``, which provides essential features for a multi-dimensional detector.
For real hardware, you should implement device-specific communication methods in your subclass (see ... for details).  

For demonstration, we use the dummy detector ``MultiDetectorDummy`` (a subclass of ``MultiDetectorInterface``) to simulate detector behavior without connecting to real hardware.
A dummy detector instance with user-defined data dimensions (here configured to capture 2D 256×256 images as an example) can be created as follows:

.. code-block:: python

    from lys_instr import dummy

    detector = dummy.MultiDetectorDummy(frameShape=(256, 256))

``frameShape`` specifies the shape of each frame (here, ``(256, 256)`` for a 256×256 image).
Each acquisition from the dummy detector produces an image filled with random noise.


Creating the Detector GUI
-------------------------

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