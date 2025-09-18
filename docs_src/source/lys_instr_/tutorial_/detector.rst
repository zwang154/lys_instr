
Detector Control
================

Creating a Detector Instance
----------------------------

A detector instance can be created by inheriting from the ``MultiDetectorInterface`` class, which provides essential features for a multi-dimensional detector.
For real detector hardware, the user should implement device-specific behaviors by overriding the relevant methods in the subclass (see :class:`.MultiDetector.MultiDetectorInterface`).  

For demonstration purposes, a dummy detector class ``MultiDetectorDummy`` is provided, which inherits from ``MultiDetectorInterface`` and simulates detector behavior without connecting to real hardware.
A dummy detector instance collecting two-dimensional data, i.e., images, can be created as follows:

.. code-block:: python

    from lys_instr import dummy

    detector = dummy.MultiDetectorDummy(indexShape=(1,), frameShape=(256, 256), exposure=0.1)

This detector captures a single 256×256 image (filled with random noise) per acquisition, with an exposure time of 0.1 seconds per frame.
``frameShape`` specifies the shape of each frame, i.e., ``(256, 256)`` for a 256×256 image.
``indexShape`` specifies the shape of the indices for the frames within a single acquisition, e.g., ``(1,)`` for a single frame (this case), ``(5,)`` for a sequence of 5 frames, or ``(5, 5)`` for a 5×5 grid of frames.
``exposure`` specifies the exposure time in seconds for each frame.


Creating the Detector GUI in *lys*
----------------------------------

As data acquired by a detector is generically multi-dimensional, we demonstrate creating a detector GUI within *lys*, which offers versatile tools for visualizing such data.

After starting *lys*, open the ``proc.py`` file (press Ctrl+P), add the code below, and save it (press Ctrl+S) to define a class that creates the detector GUI subwindow.

.. code-block:: python

    from lys.widgets import LysSubWindow
    from lys_instr import dummy, gui

    class AppWindow(LysSubWindow):
        def __init__(self):
            super().__init__()
            detector = dummy.MultiDetectorDummy(indexShape=(1,), frameShape=(256, 256), exposure=0.1)
            detectorGUI = gui.MultiDetectorGUI(detector)
            self.setWidget(detectorGUI)
            self.adjustSize()

The code structure is similar to the motor GUI in lys, except the detector GUI is created by passing the detector instance to the ``MultiDetectorGUI`` class.

Calling ``AppWindow()`` in the *lys* command line launches the GUI subwindow like the one below:

.. image:: /lys_instr_/tutorial_/detector_1.png


To set up image display:

1. Drag the lower edge of the detector GUI subwindow to resize it for comfortable viewing.
2. In the "MultiCut" tab, click "Add" and select the data axes for display (``2`` for ``Axis1``, ``3`` for ``Axis2``), then click "OK." (Since this detector captures 2D images with 1D indices, the total data shape is ``(1, 256, 256)``, and the axes for display are the 2nd and 3rd.)

    .. image:: /lys_instr_/tutorial_/detector_2.png
        :scale: 80%

3. In the detector GUI subwindow, click and drag to select the full area for image display.

An 256x256 image filled with random noise will be displayed as below on initialization by default:

.. image:: /lys_instr_/tutorial_/detector_3.png

The user can click the "Acquire" button to start data acquisition for a single frame, which takes 0.1 seconds per frame as specified by the ``Exp.``.
The "Stream" button starts continuous acquisition of frames until the "Stop" button is clicked.
The exposure time can be changed dynamically using the spin box or by direct input.
The "Settings" button allows configuration of sequence acquisition and update frequency.
The green indicators show the connection status of the detector.

For advanced usage, such as displaying multi-dimensional data with nontrivial index shapes, see :doc:`Detector Options </lys_instr_/tutorial_/detectorOptions>`.


Code-Only Implementation
------------------------

The above manual operations can be easily reproduced by adding the following code to ``proc.py`` in *lys* and then calling ``AppWindow()`` in the *lys* command line.

.. code-block:: python

    from lys.widgets import LysSubWindow
    from lys_instr import dummy, gui

    class AppWindow(LysSubWindow):
        def __init__(self):
            super().__init__()
            detector = dummy.MultiDetectorDummy(indexShape=(1,), frameShape=(256, 256), exposure=0.1)
            detectorGUI = gui.MultiDetectorGUI(detector)

            mcut = detectorGUI._mcut
            wave = mcut.cui._children.addWave([1, 2])
            mcut.display(wave, type="grid", pos=(0, 0), wid=(4, 4))

            self.setWidget(detectorGUI)
            self.adjustSize()

