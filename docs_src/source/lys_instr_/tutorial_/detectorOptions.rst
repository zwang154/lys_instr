
Detector Options
================

Creating Indexed Detector GUI
---------------------------------

In measurements where a detector captures multiple frames per acquisition, the index shape becomes nontrivial. 
For example, if the detector is set to capture a (8, 8) array of frames per acquisition, the index shape becomes ``(8, 8)``.

The GUI displaying such indexed data can be set up similarly, with two cuts defined in the "MultiCut" tab:
one with ``3`` for ``Axis1`` and ``4`` for ``Axis2`` to display each frame, and another with ``1`` for ``Axis1`` and ``2`` for ``Axis2`` to navigate through the indices.

A code-only implementation of this setup is shown as follows:

.. code-block:: python

    from lys.widgets import LysSubWindow
    from lys_instr.gui.MultiDetector import MultiDetectorGUI
    from lys_instr.dummy.MultiDetector import MultiDetectorDummy

    class AppWindow(LysSubWindow):
        def __init__(self):
            super().__init__()
            detector = MultiDetectorDummy(indexShape=(8, 8), frameShape=(256, 256), exposure=0.1)
            gui = MultiDetectorGUI(detector)

            mcut = gui._mcut
            wave1 = mcut.cui._children.addWave([1, 2])
            mcut.display(wave1, type="grid", pos=(0, 0), wid=(2, 4))
            wave2 = mcut.cui._children.addWave([3, 4])
            mcut.display(wave2, type="grid", pos=(2, 0), wid=(2, 4))

            self.setWidget(gui)
            self.adjustSize()